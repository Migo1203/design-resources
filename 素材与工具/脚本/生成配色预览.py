#!/usr/bin/env python3
"""解析本地官方ASE／GPL／CSS／JSON并生成配色预览；不下载或定义品牌色。

格式解析只用标准库；生成PNG需要Playwright和Chromium。
"""
import functools
import hashlib
import http.server
import json
import math
import os
from pathlib import Path
import re
import shutil
import struct
import threading
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]

def parse_color_file(path):
    """只解析本批验证的RGB ASE与六位十六进制色值，不执行外部文件。"""
    path = Path(path)
    colors = []
    if path.suffix.lower() == '.ase':
        data = path.read_bytes()
        if len(data)<12 or data[:8] != b'ASEF\x00\x01\x00\x00':
            raise ValueError('无效或不支持的ASE头：'+str(path))
        count = struct.unpack_from('>I', data, 8)[0]; pos = 12; groups = 0
        for _ in range(count):
            if pos+6>len(data): raise ValueError('ASE块头不完整')
            typ,size = struct.unpack_from('>HI', data, pos); pos+=6
            if pos+size>len(data): raise ValueError('ASE块体不完整')
            block = data[pos:pos+size]; pos+=size
            if typ==0xc001: groups+=1; continue
            if typ==0xc002:
                groups-=1
                if groups<0: raise ValueError('ASE分组不平衡')
                continue
            if typ!=1: raise ValueError('不支持的ASE块类型')
            length = struct.unpack_from('>H',block)[0]; offset = 2+length*2
            name = block[2:offset].decode('utf-16-be').rstrip('\0')
            if block[offset:offset+4]!=b'RGB ' or offset+18!=len(block):
                raise ValueError('仅支持完整的RGB ASE颜色块')
            rgb = struct.unpack_from('>fff',block,offset+4)
            if not all(math.isfinite(x) and 0<=x<=1 for x in rgb): raise ValueError('ASE颜色范围有误')
            colors.append({'name':name,'hex':'#'+''.join(f'{round(x*255):02x}' for x in rgb)})
        if groups or pos!=len(data): raise ValueError('ASE分组或文件长度不匹配')
    elif path.suffix.lower()=='.gpl':
        lines=path.read_text().splitlines()
        if not lines or lines[0]!='GIMP Palette': raise ValueError('无效GPL头')
        for line in lines[1:]:
            if not line.strip() or line.startswith(('#','Name:','Columns:')): continue
            m=re.fullmatch(r'\s*(\d+)\s+(\d+)\s+(\d+)\s+(.+?)\s*',line)
            if not m: raise ValueError('无效GPL颜色行')
            rgb=[int(x) for x in m.groups()[:3]]
            if not all(0<=x<=255 for x in rgb): raise ValueError('GPL颜色范围有误')
            colors.append({'name':m[4],'hex':'#'+''.join(f'{x:02x}' for x in rgb)})
    elif path.suffix.lower()=='.css':
        source=re.sub(r'/\*.*?\*/','',path.read_text(),flags=re.S)
        if re.search(r'@import|url\s*\(',source,re.I): raise ValueError('色板CSS存在主动外部引用')
        colors=[{'name':m[1],'hex':m[2].lower()} for m in re.finditer(r'(--[\w-]+)\s*:\s*(#[0-9a-fA-F]{6})\s*;',source)]
    elif path.suffix.lower()=='.json':
        for key,values in json.loads(path.read_text()).items():
            if isinstance(values,str): colors.append({'name':key,'hex':values.lower()})
            elif isinstance(values,list): colors.extend({'name':key+str(n),'hex':v.lower()} for n,v in enumerate(values))
            else: raise ValueError('不支持的JSON色值结构')
    else: raise ValueError('不支持的色板格式')
    if not colors or len({c['name'] for c in colors})!=len(colors) or any(not re.fullmatch('#[0-9a-f]{6}',c['hex']) for c in colors):
        raise ValueError('色名重复或色值格式有误：'+str(path))
    return colors

def validate_pack(pack,items):
    members=[x for x in items if x.get('套装')==pack['名称']]
    parsed={x['格式']:parse_color_file(ROOT/x['文件']) for x in members}
    if set(parsed) not in [{'ASE','GPL','CSS'},{'ASE','GPL','CSS','JSON'}]: raise ValueError('配色格式集合有误')
    core=parsed['GPL']; values=[x['hex'] for x in core]
    if values!=[x['hex'] for x in parsed['ASE']] or len(core)!=pack['核心色数']:
        raise ValueError('ASE与GPL核心色值或次序不一致')
    codes={x['hex'] for x in parsed['CSS']};extra=codes-set(values)
    if len(parsed['CSS'])!=pack['核心色数']+pack['代码附加色数'] or not set(values)<=codes:
        raise ValueError('CSS与核心色值不一致')
    if extra!=({'#000000','#ffffff'} if pack['名称']=='Open Color' else set()):
        raise ValueError('CSS附加色超出官方已记录范围')
    if 'JSON' in parsed and (len(parsed['JSON'])!=len(parsed['CSS']) or {x['hex'] for x in parsed['JSON']}!=codes):
        raise ValueError('JSON与CSS色值不一致')
    mapping={c['hex']:c['name'] for c in parsed['CSS']}
    display=[{**c,'variable':mapping[c['hex']]} for c in core]
    display.extend({'name':c['name'],'hex':c['hex'],'variable':c['name'],'extra':True} for c in parsed['CSS'] if c['hex'] in extra)
    return parsed,display

def luminance(code):
    rgb=[int(code[i:i+2],16)/255 for i in (1,3,5)]
    linear=[x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4 for x in rgb]
    return sum(x*y for x,y in zip(linear,(.2126,.7152,.0722)))

def main():
    from playwright.sync_api import sync_playwright
    manifest=json.loads((ROOT/'素材清单.json').read_text());packs=manifest['配色套装清单'];management=manifest['配色管理资料']
    html_path=ROOT/management['HTML'];html_path.parent.mkdir(parents=True,exist_ok=True)
    records=[];css_urls=[];format_checks=[]
    for pack in packs:
        parsed,display=validate_pack(pack,manifest['素材'])
        css=next(x for x in manifest['素材'] if x.get('套装')==pack['名称'] and x['格式']=='CSS')
        css_urls.append(os.path.relpath(ROOT/css['文件'],html_path.parent).replace(os.sep,'/'))
        format_checks.append({'名称':pack['名称'],'各格式实际色数':{k:len(v) for k,v in parsed.items()},'ASE与GPL色值和次序一致':True,'代码与核心色值一致':True,'代码附加色值':[c['hex'] for c in display if c.get('extra')]})
        for c in display:
            lum=luminance(c['hex']);black=(lum+.05)/.05;white=1.05/(lum+.05)
            c.update(pack=pack['名称'],ink='#000000' if black>=white else '#ffffff',contrast=max(black,white))
            records.append(c)
    payload=json.dumps(records,ensure_ascii=False).replace('<','\\u003c')
    links=''.join('<link rel="stylesheet" href="'+quote(u,safe='/')+'">' for u in css_urls)
    template='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>配色资源候选预览</title>__LINKS__<style>
*{box-sizing:border-box}body{margin:0;background:#efefeb;color:#222;font:15px/1.5 system-ui,sans-serif}main{max-width:1800px;margin:auto;padding:28px}h1{font-size:30px;margin:5px 0}h2{margin:24px 0 8px;font-size:22px}p{margin:7px 0}.note,footer{font-size:13px;color:#555}select{font:inherit;padding:7px;margin:14px 0}.grid{display:grid;grid-template-columns:repeat(10,minmax(0,1fr));gap:6px}.grid.nord{grid-template-columns:repeat(8,minmax(0,1fr))}.swatch{font:inherit;border:1px solid #bbb;min-width:0;text-align:left;padding:10px 7px;cursor:pointer;min-height:82px;display:flex;flex-direction:column;justify-content:space-between}.swatch:focus-visible{outline:3px solid #222;outline-offset:2px}.name{font-size:11px;overflow-wrap:anywhere}.hex{font-size:14px;font-weight:600}footer{margin-top:22px}#status{min-height:24px}@media(max-width:650px){main{padding:18px 12px}.grid,.grid.nord{grid-template-columns:repeat(2,minmax(0,1fr))}h1{font-size:24px}.swatch{min-height:70px}}
</style></head><body><main><header><div class="note">2026-11-14 · Migo素材与工具 · 候选／未采用</div><h1>配色资源 · 全部预览</h1><p id="scope">正在读取本地色板。</p><label>选择套装 <select id="pack"><option value="">全部</option><option>Open Color</option><option>Nord</option></select></label><p id="status" role="status">点击色块复制HEX；颜色由本地官方CSS变量实际渲染。</p></header><div id="content"></div><footer>Open Color © heeyeun；Nord © Sven Greb。两套均按各自MIT许可保留原件与版权。<br>本图只改变展示排版，不修改源色值；屏幕RGB预览不构成CMYK印刷标准。文字黑白自动选择仅用于本页标签，不代表任意颜色搭配都符合无障碍标准。</footer></main><script>
const data=__DATA__,select=document.querySelector('#pack'),content=document.querySelector('#content');
select.value=new URLSearchParams(location.search).get('pack')||'';
function render(){content.replaceChildren();const selected=data.filter(x=>!select.value||x.pack===select.value);document.querySelector('#scope').textContent=`当前核心色板${selected.filter(x=>!x.extra).length}色，代码附加${selected.filter(x=>x.extra).length}色，共展示${selected.length}个色值。不是Migo品牌色或网站UI方案。`;for(const group of ['Open Color','Nord']){const own=selected.filter(x=>x.pack===group);if(!own.length)continue;const section=document.createElement('section'),h=document.createElement('h2');h.textContent=group+(group==='Open Color'?' · 13组×10阶＋代码黑白2色':' · 16色');section.append(h);const grid=document.createElement('div');grid.className='grid'+(group==='Nord'?' nord':'');for(const x of own){const button=document.createElement('button');button.className='swatch';button.type='button';button.dataset.hex=x.hex;button.dataset.variable=x.variable;button.style.backgroundColor=`var(${x.variable})`;button.style.color=x.ink;button.setAttribute('aria-label',x.pack+' '+x.name+' '+x.hex+(x.extra?' 代码附加色':''));const name=document.createElement('span');name.className='name';name.textContent=x.name+(x.extra?' · 代码附加':'');const hex=document.createElement('span');hex.className='hex';hex.textContent=x.hex.toUpperCase();button.append(name,hex);button.addEventListener('click',async()=>{try{await navigator.clipboard.writeText(x.hex);document.querySelector('#status').textContent='已复制 '+x.hex}catch{document.querySelector('#status').textContent='无法自动复制，请选择色值文字手动复制：'+x.hex}});grid.append(button)}section.append(grid);content.append(section)}document.querySelector('h1').textContent=select.value?select.value+' · 候选配色':'配色资源 · 全部预览';window.shownColors=selected;}
select.addEventListener('change',render);render();
</script></body></html>'''
    html_path.write_text(template.replace('__LINKS__',links).replace('__DATA__',payload))
    class Handler(http.server.SimpleHTTPRequestHandler):
        def log_message(self,*args):pass
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(ROOT)))
    threading.Thread(target=server.serve_forever,daemon=True).start();origin=f'http://127.0.0.1:{server.server_port}'
    url=origin+'/'+quote(str(html_path.relative_to(ROOT)))
    jobs=[('全部',url,management['总览PNG'],1600,records)]
    jobs.extend((p['名称'],url+'?pack='+quote(p['名称']),p['预览图'],1400,[x for x in records if x['pack']==p['名称']]) for p in packs)
    report={'日期':'2026-11-14','格式核对':format_checks,'截图':[],'人工查看':{'状态':'待查看'},'说明':'格式解析和CSS实际渲染；未测试PS／AI／GIMP导入，不确认用户认可或品牌采用。'}
    executable=os.environ.get('MIGO_CHROMIUM_EXECUTABLE') or shutil.which('chromium') or shutil.which('chromium-browser')
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(**({'executable_path':executable} if executable else {}),headless=True,args=['--no-sandbox']);report['浏览器']=browser.version
            context=browser.new_context(viewport={'width':1600,'height':1000},permissions=['clipboard-read','clipboard-write'])
            page=context.new_page();errors=[];external=[]
            page.on('pageerror',lambda e:errors.append(str(e)));page.on('requestfailed',lambda r:errors.append(r.url+' '+str(r.failure)))
            page.on('request',lambda r:external.append(r.url) if not r.url.startswith(origin+'/') else None)
            for name,target,output,width,expected in jobs:
                page.set_viewport_size({'width':width,'height':1000});page.goto(target,wait_until='networkidle')
                actual=page.locator('.swatch').evaluate_all('(els)=>els.map(e=>({hex:e.dataset.hex,background:getComputedStyle(e).backgroundColor}))')
                assert len(actual)==len(expected)
                for item,color in zip(actual,expected):
                    rgb=tuple(int(color['hex'][i:i+2],16) for i in (1,3,5))
                    assert item['hex']==color['hex'] and item['background']=='rgb'+str(rgb),(name,item,color)
                assert page.evaluate('document.documentElement.scrollWidth')<=width
                page.locator('main').screenshot(path=str(ROOT/output))
                report['截图'].append({'名称':name,'文件':output,'SHA256':hashlib.sha256((ROOT/output).read_bytes()).hexdigest(),'展示色值':[x['hex'] for x in expected],'CSS实际颜色逐项一致':True,'视口宽度':width})
            page.goto(url,wait_until='networkidle');page.locator('#pack').select_option('Nord');assert page.locator('.swatch').count()==16
            first=page.locator('.swatch').first;page.locator('#pack').focus();page.keyboard.press('Tab');assert first.evaluate('(e)=>document.activeElement===e');page.keyboard.press('Enter');page.wait_for_function("document.querySelector('#status').textContent.startsWith('已复制')")
            assert page.evaluate('navigator.clipboard.readText()')=='#2e3440'
            page.locator('#pack').select_option('Open Color');assert page.locator('.swatch').count()==132
            page.set_viewport_size({'width':390,'height':844});assert page.evaluate('document.documentElement.scrollWidth')<=390
            assert not errors and not external
            report['交互检查']={'套装筛选':'Open Color 132／Nord 16通过','键盘与复制':'实际Tab进入首个按钮，Enter复制Nord色值#2e3440通过','390px横向溢出':False,'脚本或加载错误':errors,'外部请求数':len(external)}
            report['标签对比度']={'仅用于预览页黑白标签':'按sRGB相对亮度选择更高对比的黑字或白字，不代表完整网站无障碍验收','最小值':min(c['contrast'] for c in records),'全部不少于4.5':all(c['contrast']>=4.5 for c in records)}
            context.close();browser.close()
    finally:server.shutdown();server.server_close()
    (ROOT/management['检查记录']).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('两套官方色板解析通过：ASE／GPL核心146色，CSS展示148色；三张PNG、实际色值、筛选、复制和手机宽度通过。')

if __name__=='__main__':main()
