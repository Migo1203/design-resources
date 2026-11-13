#!/usr/bin/env python3
"""本地CSS设备样机预览：生成占位PNG并验证本地截图替换，不下载或生图。

需要Playwright、Chromium及Pillow；技术HTML和JSON统一放在样机/管理资料。
"""
import functools
import hashlib
import http.server
from io import BytesIO
import json
import os
from pathlib import Path
import shutil
import threading
from urllib.parse import quote

from PIL import Image
from playwright.sync_api import sync_playwright

BASE=Path(__file__).resolve().parents[1]

def main():
 m=json.loads((BASE/'素材清单.json').read_text());pack=m['样机套装清单'][0]
 html_path=BASE/pack['HTML'];html_path.parent.mkdir(parents=True,exist_ok=True)
 source=next(x for x in m['素材'] if x['编号']==pack['原件编号'])
 css_relative=os.path.relpath(BASE/source['文件'],html_path.parent).replace(os.sep,'/')
 cards=[]
 for item in pack['展示模板']:
  ident=item['id'];kind=item['名称'];klass=item['类名']
  cards.append(f'''<article data-id="{ident}"><h2>{kind}</h2><p class="kind">{klass}</p><div class="stage"><div class="device {klass}"><div class="device-frame"><img class="device-screen" alt="{kind}中的占位设计"></div><div class="device-stripe"></div><div class="device-header"></div><div class="device-sensors"></div><div class="device-btns"></div><div class="device-power"></div><div class="device-home"></div></div></div><label>替换本地PNG／JPEG／WebP<input type="file" id="{ident}" accept="image/png,image/jpeg,image/webp"></label><button type="button" data-reset="{ident}">恢复占位图</button><p class="screen-info"></p></article>''')
 template='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>设备样机候选预览</title><link rel="stylesheet" href="__CSS__"><style>
*{box-sizing:border-box}body{margin:0;background:#f1f1ee;color:#222;font:15px/1.6 system-ui,sans-serif}main{max-width:1800px;margin:auto;padding:32px}h1{font-size:30px;margin:6px 0}header p{color:#555}#status{background:white;border:1px solid #ccc;padding:10px 14px}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:20px}article{min-width:0;background:white;border:1px solid #d4d4d0;padding:20px}h2{margin:0;font-size:21px}.kind{font-size:12px;color:#666}.stage{position:relative;height:470px;overflow:hidden;background:#f5f5f3;margin:16px 0}.stage .device{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%) scale(var(--scale, .4));transform-origin:center}.device .device-screen{object-fit:contain;background:#fff}input{display:block;max-width:100%;margin:6px 0 12px;font:inherit;font-size:12px}button{border:1px solid #aaa;background:white;padding:6px 12px;font:inherit}.screen-info,footer{font-size:12px;color:#555}footer{margin-top:22px}@media(max-width:1000px){main{padding:20px 14px}.grid{grid-template-columns:1fr}.stage{height:430px}h1{font-size:25px}}
</style></head><body><main><header><div>Devices.css · CSS样机资源 · 候选／未采用</div><h1>电脑、手机、平板：三种设备展示</h1><p>图片为中性占位设计，不是Migo网站UI或品牌成果。可在本地选择截图替换；文件仅在浏览器内读取，不上传。</p><p id="status" role="status">正在加载本地样机……</p></header><div class="grid">__CARDS__</div><footer>框架来自Yan Zhu的Devices.css，完整MIT许可随原件保存。该包是CSS设备边框，不是写实PSD或Photoshop智能对象。画面为模拟展示，不代表真实硬件测试；仅验证以上三种设备。</footer></main><script>
const articles=[...document.querySelectorAll('article')],urls=new Map();
function placeholder(w,h){const svg=`<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}"><rect width="100%" height="100%" fill="#f1f0eb"/><rect x="${w*.08}" y="${h*.10}" width="${w*.36}" height="${h*.025}" fill="#444"/><text x="${w*.08}" y="${h*.30}" font-family="sans-serif" font-size="${w*.065}" fill="#222">YOUR DESIGN</text><rect x="${w*.08}" y="${h*.38}" width="${w*.84}" height="${h*.34}" fill="#c8ccc8"/><rect x="${w*.08}" y="${h*.79}" width="${w*.70}" height="${h*.017}" fill="#777"/><rect x="${w*.08}" y="${h*.84}" width="${w*.50}" height="${h*.017}" fill="#aaa"/></svg>`;return 'data:image/svg+xml;charset=utf-8,'+encodeURIComponent(svg)}
function fit(){for(const a of articles){const d=a.querySelector('.device'),s=a.querySelector('.stage');d.style.setProperty('--scale',Math.min((s.clientWidth-24)/d.offsetWidth,(s.clientHeight-24)/d.offsetHeight,1))}}
async function reset(a){const img=a.querySelector('img');img.src=a.dataset.placeholder;await img.decode();a.dataset.loaded='placeholder'}
function discard(id){if(urls.has(id)){URL.revokeObjectURL(urls.get(id));urls.delete(id)}}
(async()=>{try{
 for(const a of articles){const img=a.querySelector('img'),s=getComputedStyle(img);const w=parseFloat(s.width),h=parseFloat(s.height);a.dataset.placeholder=placeholder(w,h);await reset(a);a.querySelector('.screen-info').textContent=`屏幕显示区：${w} × ${h} CSS像素；保持图片比例，不强制拉伸。`;
  const input=a.querySelector('input');input.addEventListener('change',async()=>{if(!input.files.length)return;const file=input.files[0];if(!['image/png','image/jpeg','image/webp'].includes(file.type)){document.querySelector('#status').textContent='请选择PNG、JPEG或WebP图片';return}discard(a.dataset.id);const url=URL.createObjectURL(file);urls.set(a.dataset.id,url);img.src=url;try{await img.decode();a.dataset.loaded='user';document.querySelector('#status').textContent='本地截图已替换，仅在当前浏览器中显示。'}catch(e){document.querySelector('#status').textContent='图片读取失败：'+e.message}});
  a.querySelector('button').addEventListener('click',async()=>{discard(a.dataset.id);input.value='';await reset(a);document.querySelector('#status').textContent='已恢复占位图。'});
 }
 fit();window.addEventListener('resize',fit);document.documentElement.dataset.ready='true';document.querySelector('#status').textContent='本地CSS与三个屏幕占位图已加载；可选择自己的截图试用。';
 }catch(e){document.querySelector('#status').textContent='加载失败：'+e.message;document.documentElement.dataset.ready='error'}})();
</script></body></html>'''
 html_path.write_text(template.replace('__CSS__',quote(css_relative,safe='/.')).replace('__CARDS__',''.join(cards)))
 class Handler(http.server.SimpleHTTPRequestHandler):
  def log_message(self,*args):pass
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(BASE)))
 threading.Thread(target=server.serve_forever,daemon=True).start();origin=f'http://127.0.0.1:{server.server_port}'
 report={'日期':m['更新日期'],'说明':'本地CSS设备样机，只验证三种设备及本地截图替换；未验证PSD、Photoshop或完整23类。','截图':[]}
 executable=os.environ.get('MIGO_CHROMIUM_EXECUTABLE') or shutil.which('chromium') or shutil.which('chromium-browser')
 try:
  with sync_playwright() as p:
   browser=p.chromium.launch(**({'executable_path':executable} if executable else {}),headless=True,args=['--no-sandbox'])
   report['浏览器']=browser.version
   page=browser.new_page(viewport={'width':1800,'height':1000},device_scale_factor=1)
   errors=[];outbound=[]
   page.on('pageerror',lambda e:errors.append(str(e)))
   page.on('requestfailed',lambda r:errors.append(str(r.failure)+' '+r.url))
   page.on('request',lambda r:outbound.append(r.url) if not r.url.startswith((origin+'/','blob:','data:')) else None)
   page.goto(origin+'/'+quote(str(html_path.relative_to(BASE))),wait_until='networkidle');page.wait_for_selector('html[data-ready="true"]',state='attached')
   report['设备']=page.evaluate('''()=>[...document.querySelectorAll('article')].map(a=>{const d=a.querySelector('.device'),i=a.querySelector('img'),s=getComputedStyle(i);return {名称:a.querySelector('h2').textContent,类名:d.className,边框宽:d.offsetWidth,边框高:d.offsetHeight,屏幕宽:s.width,屏幕高:s.height,图片可读:i.complete&&i.naturalWidth>0}})''')
   assert all(x['图片可读'] and x['边框宽']>100 and x['边框高']>100 for x in report['设备'])
   for name,width,path in [('总览',1800,pack['总览PNG']),('套装纵览',920,pack['套装PNG'])]:
    page.set_viewport_size({'width':width,'height':1000});page.screenshot(path=str(BASE/path),full_page=True)
    assert page.evaluate('document.documentElement.scrollWidth')<=width
    report['截图'].append({'名称':name,'文件':path,'SHA256':hashlib.sha256((BASE/path).read_bytes()).hexdigest(),'视口宽度':width})
   sample=BytesIO();Image.new('RGB',(600,400),'#668899').save(sample,format='PNG')
   for ident in ['desktop','phone','tablet']:
    page.locator('#'+ident).set_input_files({'name':'local-test.png','mimeType':'image/png','buffer':sample.getvalue()})
    page.wait_for_selector(f'article[data-id="{ident}"][data-loaded="user"]',state='attached')
    assert page.locator(f'article[data-id="{ident}"] img').evaluate('(i)=>i.naturalWidth===600&&i.naturalHeight===400')
    page.locator(f'button[data-reset="{ident}"]').click();page.wait_for_selector(f'article[data-id="{ident}"][data-loaded="placeholder"]',state='attached')
   page.set_viewport_size({'width':390,'height':844});assert page.evaluate('document.documentElement.scrollWidth')<=390
   assert not errors and not outbound,(errors,outbound)
   report['交互检查']={'本地图片替换':'三种设备全部通过','恢复占位图':'三种全部通过','390px横向溢出':False,'脚本或加载错误':errors,'外部请求数':len(outbound)}
   browser.close()
 finally:server.shutdown();server.server_close()
 (BASE/pack['检查记录']).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print('CSS三种设备加载、本地截图替换与重置、总览和纵览PNG、390px宽度检查通过。')

if __name__=='__main__':main()
