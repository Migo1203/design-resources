#!/usr/bin/env python3
"""从本地原件生成波形、手动试听页和技术检查；不下载、不转码原件，不代替人耳试听。"""
import array
import hashlib
import html
import http.server
import json
import math
import subprocess
import sys
import threading
from functools import partial
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    from playwright.sync_api import sync_playwright
    data = json.loads((ROOT / '素材清单.json').read_text())
    items = [x for x in data['素材'] if x['分类'] == '音乐与音效']
    management = ROOT / '音乐与音效/管理资料'
    management.mkdir(parents=True, exist_ok=True)
    cards, proofs = [], []
    for item in items:
        source = ROOT / item['文件']
        if sha(source) != item['SHA256']:
            raise ValueError('原件哈希不符：' + item['编号'])
        probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(source)]))
        stream = next(x for x in probe['streams'] if x['codec_type'] == 'audio')
        original_info = {'时长秒': float(probe['format']['duration']), '采样率Hz': int(stream['sample_rate']),
                         '声道数': stream['channels'], '编码': stream['codec_name']}
        if original_info != item['音频结构']:
            raise ValueError('音频结构与清单不符')
        decoded_pcm = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(source), '-vn', '-ac', '1', '-f', 'f32le', '-'], check=True, capture_output=True)
        if decoded_pcm.stderr.strip():
            raise ValueError('FFmpeg报告解码错误：'+decoded_pcm.stderr.decode(errors='replace'))
        raw = decoded_pcm.stdout
        samples = array.array('f'); samples.frombytes(raw)
        if sys.byteorder != 'little':
            samples.byteswap()
        if not samples or not all(math.isfinite(x) for x in samples):
            raise ValueError('无有效PCM采样')
        # 逐列显示实际单声道混合采样的最小／最大值；不是频谱或响度认证。
        segments = []
        for i in range(300):
            block = samples[i * len(samples) // 300:(i + 1) * len(samples) // 300]
            low, high = min(block, default=0), max(block, default=0)
            segments.append(f'M{i + 10},{45 - high * 39:.2f}V{45 - low * 39:.2f}')
        waveform = '<svg role="img" aria-label="实际音频波形，单声道混合" viewBox="0 0 320 90"><path d="M10,45H310" stroke="#bbb"/><path d="' + ' '.join(segments) + '" stroke="#343e50"/></svg>'
        url = quote('../../' + item['文件'])
        pack = html.escape(item['套装'], quote=True)
        info = item['音频结构']
        cards.append(f'<article data-pack="{pack}" id="{item["编号"]}"><small>{item["编号"]} · {pack}</small><h2>{html.escape(item["名称"])}</h2>{waveform}<p>{info["时长秒"]:.3f}秒 · {info["采样率Hz"]} Hz · {info["声道数"]}声道 · {item["格式"]}</p><audio controls preload="metadata" src="{url}"></audio><p><a download href="{url}">下载原件</a> · CC0 · 候选／未采用</p></article>')
        proofs.append({'编号': item['编号'], '原件SHA256': sha(source), '结构': original_info,
                       'FFmpeg完整解码': True, '单声道混合采样数': len(samples),
                       '单声道峰值': max(abs(x) for x in samples), '人耳试听': '待用户确认'})
    document = '''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>音乐与音效｜本地手动试听</title>
<style>*{box-sizing:border-box}body{margin:0;background:#f5f5f3;color:#242830;font:16px/1.6 system-ui,"Noto Sans CJK SC",sans-serif}main{max-width:1220px;margin:auto;padding:28px}h1{font-size:30px;margin:0}h2{font-size:20px;margin:4px 0}p{margin:6px 0}small{color:#555}#cards{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px;margin-top:20px}article{border:1px solid #c6c9cc;background:white;padding:16px;min-width:0}svg,audio{display:block;width:100%;max-width:100%}svg{height:90px}audio{margin:12px 0}label{display:block;margin:16px 0}select{font:inherit;max-width:100%;padding:8px}a{color:#293e67}[hidden]{display:none!important}@media(max-width:650px){main{padding:18px}#cards{grid-template-columns:1fr}h1{font-size:25px}}</style>
<main><h1>音乐与音效｜手动试听</h1><p>1首短音乐＋6个界面音效。波形来自本地原件；CC0，候选／未采用。</p><p>仅点击播放后出声；一次播放一项。请先调低设备音量。技术解码与浏览器播放不代表已做人耳听感评价。</p><p>用途名称继承作者命名；芯片音乐用于实验，不是Migo网站背景音乐方案。</p><label>套装 <select id="pack"><option value="">全部</option>''' + ''.join(f'<option>{html.escape(x["名称"])}</option>' for x in data['音乐套装清单']) + '''</select></label><section id="cards">''' + ''.join(cards) + '''</section><p>运行环境：本地HTTP服务；无外部资源请求，无默认循环、自动播放、用户跟踪或上传。</p></main>
<script>const audios=[...document.querySelectorAll('audio')];audios.forEach(a=>a.addEventListener('play',()=>audios.forEach(b=>{if(b!==a)b.pause()})));const select=document.querySelector('#pack');function filter(){audios.forEach(a=>a.pause());document.querySelectorAll('article').forEach(a=>a.hidden=!!select.value&&a.dataset.pack!==select.value)}select.addEventListener('change',filter);select.value=new URLSearchParams(location.search).get('pack')||'';filter();window.ready=true;</script></html>'''
    pagefile = management / '音频试听.html'; pagefile.write_text(document, encoding='utf-8')
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), partial(Quiet, directory=str(ROOT)))
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    errors, external, bad_http = [], [], []
    shots, decoded, played = [], [], []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--no-sandbox'])
            page = browser.new_page(viewport={'width': 1280, 'height': 900})
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.on('request', lambda r: external.append(r.url) if not r.url.startswith(f'http://127.0.0.1:{server.server_port}/') else None)
            page.on('response', lambda r: bad_http.append([r.url, r.status]) if r.status >= 400 else None)
            url = f'http://127.0.0.1:{server.server_port}/' + quote(str(pagefile.relative_to(ROOT)))
            page.goto(url); page.wait_for_function('window.ready===true')
            initial = page.evaluate('Array.from(document.querySelectorAll("audio")).every(a=>a.paused&&!a.autoplay&&!a.loop)')
            decoded = page.evaluate('''async()=>{const c=new AudioContext();try{return await Promise.all(Array.from(document.querySelectorAll('audio')).map(async a=>{const b=await c.decodeAudioData(await(await fetch(a.src)).arrayBuffer());return {编号:a.closest('article').id,采样率Hz:b.sampleRate,声道数:b.numberOfChannels,采样数:b.length,时长秒:b.duration}}))}finally{await c.close()}}''')
            for item in items:
                # 测试按钮由真实点击触发，遵守浏览器手势规则；短音效用playing/ended事件检查。
                page.evaluate('''id=>{const a=document.getElementById(id).querySelector('audio');window.playProof={playing:false,ended:false};a.addEventListener('playing',()=>window.playProof.playing=true,{once:true});a.addEventListener('ended',()=>window.playProof.ended=true,{once:true});let b=document.createElement('button');b.id='test-play';b.textContent='技术播放检查';b.onclick=()=>a.play();document.body.append(b)}''', item['编号'])
                page.locator('#test-play').click()
                page.wait_for_function('window.playProof.playing')
                if item['音频结构']['时长秒'] < 1:
                    page.wait_for_function('window.playProof.ended')
                else:
                    page.wait_for_function(f'document.getElementById("{item["编号"]}").querySelector("audio").currentTime>0.15')
                result = page.evaluate('''id=>{const a=document.getElementById(id).querySelector('audio');const r={编号:id,...window.playProof,播放位置秒:a.currentTime,媒体错误:a.error?.code||null};a.pause();a.currentTime=0;document.querySelector('#test-play').remove();return r}''', item['编号'])
                played.append(result)
            # 两个play调用同一次用户手势触发，确认第二项会暂停第一项。
            page.evaluate('''()=>{let b=document.createElement('button');b.id='test-pair';b.textContent='互斥播放检查';b.onclick=async()=>{await document.querySelector('#音007 audio').play();await document.querySelector('#音001 audio').play()};document.body.append(b)}''')
            page.locator('#test-pair').click();page.wait_for_function('document.querySelector("#音007 audio").paused')
            exclusive = page.evaluate('document.querySelector("#音007 audio").paused')
            page.evaluate('document.querySelectorAll("audio").forEach(a=>{a.pause();a.currentTime=0});document.querySelector("#test-pair").remove()')
            targets = [('', 1280, data['音乐管理资料']['总览PNG'])] + [(x['名称'], 1280, x['预览图']) for x in data['音乐套装清单']] + [('', 390, '音乐与音效/管理资料/手机试听预览.png')]
            for pack, width, destination in targets:
                page.set_viewport_size({'width': width, 'height': 900})
                page.locator('#pack').select_option(pack)
                no_overflow = page.evaluate('document.documentElement.scrollWidth<=innerWidth')
                assert no_overflow
                path = ROOT / destination
                page.screenshot(path=str(path), full_page=True)
                shots.append({'文件': destination, 'SHA256': sha(path), '宽度': width, '无横向溢出': no_overflow})
            browser.close()
    finally:
        server.shutdown();server.server_close()
    assert initial and exclusive and len(decoded) == len(items) and not errors and not external and not bad_http
    report = {'原件读取': proofs, '浏览器解码': decoded, '用户手势播放': played, '初始无自动播放': initial,
              '同时仅播放一项': exclusive, '截图': shots, 'HTML_SHA256': sha(pagefile),
              '脚本或加载错误': errors, '外部请求': external, 'HTTP错误': bad_http,
              '查看边界': '技术解码、手动触发播放与波形截图；不是人耳试听、无缝循环或真实移动设备兼容性验收。'}
    (management / '音频检查记录.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'通过：{len(items)}个音频解码与手势播放，{len(shots)}张实际截图；人耳试听待用户确认。')


if __name__ == '__main__':
    main()
