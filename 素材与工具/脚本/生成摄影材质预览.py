#!/usr/bin/env python3
"""使用本地JPEG生成摄影／材质联系表；不下载、不改原件、不确认项目采用。

依赖Playwright、Chromium。HTML和检查JSON集中到各分类的管理资料。
"""
import functools
import hashlib
import html
import http.server
import json
import os
from pathlib import Path
import shutil
import threading
from urllib.parse import quote

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]

def main():
    data = json.loads((ROOT/'素材清单.json').read_text())
    packs = data['图像套装清单']
    class Handler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args): pass
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Handler, directory=str(ROOT)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    origin = f'http://127.0.0.1:{server.server_port}'
    executable = os.environ.get('MIGO_CHROMIUM_EXECUTABLE') or shutil.which('chromium') or shutil.which('chromium-browser')
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(**({'executable_path': executable} if executable else {}), headless=True, args=['--no-sandbox'])
            for pack in packs:
                items = [x for x in data['素材'] if x.get('套装') == pack['名称']]
                path = ROOT/pack['HTML']; path.parent.mkdir(parents=True, exist_ok=True)
                cards = []
                for x in items:
                    rel = os.path.relpath(ROOT/x['文件'], path.parent).replace(os.sep, '/')
                    e = html.escape
                    cards.append(f'<article><a href="{e(rel)}" target="_blank" rel="noreferrer"><img src="{e(rel)}" alt="{e(x["名称"])}" data-id="{x["编号"]}"></a><h2>{x["编号"]} · {e(x["名称"])}</h2><p>{e(x["原始文件名"])}</p><p>{x["图像结构"]["宽"]}×{x["图像结构"]["高"]} · {x["文件字节数"]:,}字节 · 原件未改</p><p>{e(x["作者或维护者"])} · CC0 1.0</p><p><a href="{e(x["来源页面"])}">原始来源</a> · <a href="{e(x["授权来源"])}">授权依据</a></p></article>')
                is_photo = pack['分类'] == '摄影图片'
                note = '历史CC0工作台摄影；不得冒称Migo本人工作室、本人摄影或客户项目实拍。' if is_photo else 'Poly Haven官方2K颜色／漫反射贴图；仅为二维材质图，不是完整PBR材质或三维模型。'
                page_html = '''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>__TITLE__</title><style>
*{box-sizing:border-box}body{margin:0;background:#eeeee9;color:#222;font:15px/1.55 system-ui,sans-serif}main{padding:30px;max-width:1700px;margin:auto}h1{font-size:30px;margin:6px 0}h2{font-size:18px;margin:12px 0 4px}header p{margin:6px 0}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px;margin:24px 0}article{min-width:0;background:#fff;border:1px solid #d3d3ce;padding:14px}article>a{display:block;background:#f7f7f4}img{display:block;width:100%;height:__HEIGHT__px;object-fit:contain}article p{font-size:13px;overflow-wrap:anywhere;margin:4px 0;color:#555}a{color:inherit}footer{font-size:13px}@media(max-width:600px){main{padding:20px 14px}.grid{grid-template-columns:1fr}img{height:230px}h1{font-size:24px}}
</style><main><header><div>2026-11-14 · Migo素材与工具 · 候选／未采用</div><h1>__TITLE__</h1><p>__NOTE__</p><p>点击图片打开本地完整JPEG；仅缩放排版，不裁切、不调色。来源链接访问外部网站。</p></header><section class="grid">__CARDS__</section><footer>作者与出处见每张图下方。许可为CC0 1.0；本页是本地文件预览，不调用外部图片或字体。用户认可与实际项目采用另行记录。</footer></main></html>'''
                page_html = page_html.replace('__TITLE__', html.escape(pack['名称'])).replace('__HEIGHT__', '340' if is_photo else '430').replace('__NOTE__', html.escape(note)).replace('__CARDS__', '\n'.join(cards))
                path.write_text(page_html)
                page = browser.new_page(viewport={'width':1600, 'height':1000}, device_scale_factor=1)
                errors, external = [], []
                page.on('pageerror', lambda e: errors.append(str(e)))
                page.on('requestfailed', lambda r: errors.append(r.url+' '+str(r.failure)))
                page.on('request', lambda r: external.append(r.url) if not r.url.startswith(origin+'/') else None)
                url = origin+'/'+quote(str(path.relative_to(ROOT)))
                page.goto(url, wait_until='networkidle')
                page.evaluate('Promise.all([...document.images].map(i=>i.decode()))')
                proof = page.evaluate('''[...document.images].map(i=>({编号:i.dataset.id,宽:i.naturalWidth,高:i.naturalHeight,读取:i.complete&&i.naturalWidth>0}))''')
                assert len(proof)==len(items)
                for x, check in zip(items, proof):
                    assert check == {'编号':x['编号'], '宽':x['图像结构']['宽'], '高':x['图像结构']['高'], '读取':True}
                report = {'日期':'2026-11-14', '套装':pack['名称'], '浏览器':browser.version, '图像读取':proof, '截图':[]}
                for output, width in [(pack['总览图'],1600), (pack['预览图'],1400)]:
                    page.set_viewport_size({'width':width,'height':1000})
                    assert page.evaluate('document.documentElement.scrollWidth')<=width
                    page.screenshot(path=str(ROOT/output), full_page=True)
                    report['截图'].append({'文件':output,'SHA256':hashlib.sha256((ROOT/output).read_bytes()).hexdigest(),'视口宽度':width})
                # Follow the actual local image link and verify response MIME and bytes.
                first_href = page.locator('article>a').first.get_attribute('href')
                with page.expect_popup() as popup_info:
                    page.locator('article>a').first.click()
                popup = popup_info.value; popup.wait_for_load_state()
                response = page.request.get(popup.url)
                assert response.ok and response.headers.get('content-type','').startswith('image/jpeg')
                assert hashlib.sha256(response.body()).hexdigest()==items[0]['SHA256']
                popup.close()
                page.set_viewport_size({'width':390,'height':844})
                assert page.evaluate('document.documentElement.scrollWidth')<=390
                assert not errors and not external
                report['交互检查']={'原件链接':'已实际点击首图，HTTP MIME与SHA256通过','首图链接':first_href,'390px横向溢出':False,'脚本或加载错误':errors,'外部请求数':len(external)}
                report['人工查看']={'状态':'待查看','说明':'自动加载不能代替人工观察。'}
                (ROOT/pack['检查记录']).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
                page.close()
                print(pack['名称']+'：实际解码、两张PNG、原件链接及手机宽度通过。')
            browser.close()
    finally:
        server.shutdown(); server.server_close()

if __name__ == '__main__': main()
