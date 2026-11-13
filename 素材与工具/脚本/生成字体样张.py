#!/usr/bin/env python3
"""从已登记的本地字体生成HTML、每家族PNG及总览PNG，不下载字体。

需要fontTools、Playwright与Chromium；在仓库根目录运行。
PNG保留在字体目录；HTML与检查JSON集中写入管理资料，不改变候选或采用状态。
"""
import functools
import hashlib
import html
import http.server
import json
import os
from pathlib import Path
import shutil
import tempfile
import threading
from urllib.parse import quote

from fontTools.ttLib import TTFont
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
FONTS = ROOT/'字体'
MANAGEMENT = FONTS/'管理资料'

CSS = '''
*{box-sizing:border-box}body{margin:0;color:#202020;background:#f1f1ef;font:16px/1.6 system-ui,sans-serif}
main{max-width:1500px;margin:auto;padding:36px}header{margin-bottom:24px}h1{font-size:32px;margin:8px 0}header p{margin:8px 0;color:#505050}
.eyebrow{font-size:13px;color:#555;letter-spacing:.08em}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:24px}
article{min-width:0;padding:28px;background:white;border:1px solid #d2d2ce}article h2{font-size:28px;line-height:1.3;margin:4px 0 12px}
.meta,.foot{font-size:13px;color:#555}.meta{margin:6px 0}.specimen{margin:22px 0}.ink{font-synthesis:none;font-optical-sizing:auto;overflow-wrap:anywhere}
.headline{font-size:38px;line-height:1.5;margin:12px 0}.reading{font-size:20px;line-height:1.8;margin:12px 0}.digits{font-size:21px;margin:12px 0}
.weight-row{display:grid;grid-template-columns:52px minmax(0,1fr);gap:10px;align-items:baseline;margin:10px 0}.weight-row label{font-size:12px;color:#666}.weight-row .ink{font-size:25px}
.italic{padding-top:12px;border-top:1px solid #ddd}.italic .ink{font-size:26px;line-height:1.6;margin:8px 0}.italic label{font-size:12px;color:#555}
.foot{border-top:1px solid #ddd;margin-top:20px;padding-top:14px}footer{font-size:13px;color:#555;margin-top:24px}#load-status{font-size:14px;padding:10px 14px;border:1px solid #ccc;background:white}
.single main{max-width:1200px}.single .grid{grid-template-columns:minmax(0,1fr)}.single .headline{font-size:46px}.single .weight-row .ink{font-size:30px}
@media(max-width:700px){main{padding:20px 16px}.grid{grid-template-columns:minmax(0,1fr);gap:20px}article{padding:20px}h1{font-size:26px}article h2{font-size:26px}.headline,.single .headline{font-size:30px}.weight-row .ink,.single .weight-row .ink{font-size:23px}.reading{font-size:18px}}
'''

def esc(value):
    return html.escape(str(value), quote=True)

def alias(item):
    return 'LocalFont'+item['编号'].replace('字','')

def texts(chinese):
    if chinese:
        return {'headline':'你好，我是Migo。','bold':'好奇探索，认真设计。',
                'reading':'让想法变得清晰。作品 / 关于 / 联系',
                'digits':'0123456789 ，。！？：；（）','weight':'好奇探索，认真设计。'}
    return {'headline':'Migo Personal Portfolio','bold':'NED Eric Lamp',
            'reading':'Curious thinking, careful design. Work / About / Contact',
            'digits':'Aa Gg Rr Ii Ll 1 O 0 / 0123456789','weight':'Curious thinking, careful design.'}

def content(group, items):
    regular = next(x for x in items if x['样式']=='normal')
    chinese = group['语言']=='简体中文'
    t = texts(chinese)
    blocks = []
    samples = []
    def ink(text, item, weight=400, css=''):
        style = item['样式']
        samples.append({'编号':item['编号'],'别名':alias(item),'字重':weight,'样式':style,'文字':text})
        return f'<p class="ink {css}" data-font-id="{esc(item["编号"])}" style="font-family:{alias(item)};font-weight:{weight};font-style:{style}">{esc(text)}</p>'
    axes = ' / '.join(f'{key} {v["最小"]:g}–{v["最大"]:g}' for key,v in regular['可变轴'].items())
    blocks.extend([f'<article data-family="{esc(group["名称"])}"><div class="eyebrow">{esc(group["分类说明"])} · 候选／未采用</div>',
                   f'<h2>{esc(group["名称"])}</h2>',f'<p class="meta">{len(items)}个本地TTF · {esc(axes)}</p>',
                   '<div class="specimen">',ink(t['headline'],regular,400,'headline'),ink(t['bold'],regular,700,'headline'),
                   ink(t['reading'],regular,400,'reading'),ink(t['digits'],regular,400,'digits'),'</div>'])
    for weight in [400,500,700]:
        blocks.append(f'<div class="weight-row"><label>{weight}</label>'+ink(t['weight'],regular,weight)+'</div>')
    for item in items:
        if item['样式']=='italic':
            blocks.extend(['<div class="italic"><label>真斜体 · 独立字体文件 · 400 / 700</label>',
                           ink('Curious thinking, careful design.',item,400),ink('Migo / NED Eric Lamp',item,700),'</div>'])
    if not any(x['样式']=='italic' for x in items):
        blocks.append('<p class="meta">本次官方文件范围无独立斜体；此样张不合成斜体。</p>')
    blocks.append(f'<div class="foot">用途候选：{esc(group["用途"])}。<br>Google Fonts固定版本 · SIL OFL 1.1 · 原件与许可见本家族目录。</div></article>')
    return ''.join(blocks),samples

def make_page(groups, manifest, destination, single=False):
    items = [x for x in manifest['素材'] if x['分类']=='字体' and x['字体家族目录'] in {g['目录'] for g in groups}]
    declarations=[]
    for item in items:
        relative = os.path.relpath(ROOT/item['文件'],destination.parent).replace(os.sep,'/')
        axis=item['可变轴']['wght']
        declarations.append(f'@font-face{{font-family:{alias(item)};src:url("{quote(relative,safe="/.")}") format("truetype");font-weight:{axis["最小"]:g} {axis["最大"]:g};font-style:{item["样式"]};font-display:swap}}')
    cards=[];requests=[]
    for group in groups:
        card,samples = content(group,[x for x in items if x['字体家族目录']==group['目录']])
        cards.append(card);requests.extend(samples)
    for item in items:
        required=''.join(r['文字'] for r in requests if r['编号']==item['编号'])
        with TTFont(ROOT/item['文件']) as font:
            missing=sorted({c for c in required if not c.isspace() and ord(c) not in font.getBestCmap()})
            if missing:raise ValueError(f'{item["编号"]}实际样张缺字：{missing}')
    title = groups[0]['名称']+'｜字体样张' if single else '全部字体样张总览'
    req=json.dumps(requests,ensure_ascii=False)
    script='''
(async()=>{
  const requests=REQUESTS;
  try{
    const results=await Promise.all(requests.map(async r=>{
      const spec=`${r.样式} ${r.字重} 24px ${r.别名}`;
      const faces=await document.fonts.load(spec,r.文字);
      if(!faces.length||!document.fonts.check(spec,r.文字))throw new Error(r.编号+' '+r.样式+' '+r.字重+'加载失败');
      return {...r,加载:true};
    }));
    await document.fonts.ready;
    window.fontProof=results;
    const count=new Set(results.map(r=>r.编号)).size;
    document.querySelector('#load-status').textContent=`已加载${count}个本地字体文件，样张使用真实字形；全部为未采用候选。`;
    document.documentElement.dataset.fontsReady='true';
  }catch(e){document.querySelector('#load-status').textContent='检查失败：'+e.message;document.documentElement.dataset.fontsReady='false';}
})();
'''.replace('REQUESTS',req)
    destination.write_text(f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)}</title><style>{''.join(declarations)}{CSS}</style></head>
<body class="{'single' if single else 'overview'}"><main><header><div class="eyebrow">Migo素材与工具 · {esc(manifest['更新日期'])}</div><h1>{esc(title)}</h1><p>中文／英文 × 无衬线／衬线。统一样文比较；字体尚未确认为Migo品牌标准。</p><p id="load-status" role="status">正在加载本地字体……</p></header><div class="grid">{''.join(cards)}</div><footer>该图用于字体文件检查与选型讨论，不是网站UI稿。字形覆盖已检查本图样文；光学尺寸按浏览器auto处理，未逐一验证全部轴位置。来源版本与完整许可见素材清单。</footer></main><script>{script}</script></body></html>
''')
    return items

class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*args):
        pass

def generate():
    manifest=json.loads((ROOT/'素材清单.json').read_text())
    groups=manifest['字体家族清单']
    jobs=[]
    overview=MANAGEMENT/'网页样张/全部字体样张.html'
    jobs.append(('总览',overview,FONTS/'全部字体预览.png',make_page(groups,manifest,overview),1500))
    for group in groups:
        page=ROOT/group['样张HTML']
        jobs.append((group['名称'],page,ROOT/group['样张图'],make_page([group],manifest,page,True),1200))
    handler=functools.partial(QuietHandler,directory=str(ROOT))
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),handler)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    origin=f'http://127.0.0.1:{server.server_port}'
    report={'日期':manifest['更新日期'],'说明':'只验证本地样张；不确认用户偏好、软件安装或项目采用。','检查':[]}
    executable=os.environ.get('MIGO_CHROMIUM_EXECUTABLE') or shutil.which('chromium') or shutil.which('chromium-browser')
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(**({'executable_path':executable} if executable else {}),headless=True,args=['--no-sandbox'])
            report['浏览器']=browser.version
            for name,path,png,items,width in jobs:
                page=browser.new_page(viewport={'width':width,'height':1000},device_scale_factor=1)
                errors=[];outbound=[]
                page.on('pageerror',lambda e:errors.append(str(e)))
                page.on('requestfailed',lambda r:errors.append(r.url+' '+str(r.failure)))
                page.on('request',lambda r:outbound.append(r.url) if not r.url.startswith(origin+'/') else None)
                page.goto(origin+'/'+quote(str(path.relative_to(ROOT))),wait_until='networkidle')
                page.wait_for_selector('html[data-fonts-ready="true"]',state='attached',timeout=30000)
                proof=page.evaluate('({样文:window.fontProof,页面宽度:document.documentElement.scrollWidth,视口宽度:innerWidth,字体:[...document.fonts].map(f=>({名称:f.family,状态:f.status}))})')
                assert not errors and not outbound,(errors,outbound)
                assert proof['页面宽度'] <= width,proof
                assert {r['编号'] for r in proof['样文']} == {x['编号'] for x in items}
                assert all(x['状态']=='loaded' for x in proof['字体']),proof
                page.screenshot(path=str(png),full_page=True)
                report['检查'].append({'名称':name,'HTML':str(path.relative_to(ROOT)),'PNG':str(png.relative_to(ROOT)),
                                      '截图SHA256':hashlib.sha256(png.read_bytes()).hexdigest(),'视口宽度':width,'实际结果':proof,'脚本或加载错误':errors,'外部请求数':len(outbound)})
                if name=='总览':
                    page.set_viewport_size({'width':390,'height':844})
                    assert page.evaluate('document.documentElement.scrollWidth') <= 390
                    phone=Path(tempfile.gettempdir())/'migo-字体总览手机.png'
                    page.screenshot(path=str(phone),full_page=True)
                    report['手机总览']={'视口':'390×844','横向溢出':False,'字体文件数':len(items),'截图':'临时核对截图，未入库'}
                page.close()
            browser.close()
    finally:
        server.shutdown();server.server_close()
    (MANAGEMENT/'字体样张检查记录.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('生成并检查：4个家族独立PNG及总览；5个HTML和检查JSON集中在管理资料；6个真实字体文件全部加载。')

if __name__=='__main__':
    generate()
