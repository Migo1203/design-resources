#!/usr/bin/env python3
"""读取已登记的本地插画，生成总览、每套PNG和集中管理的HTML／检查JSON。

需要Playwright及Chromium。不下载、生图、改写SVG或确认项目采用。
"""
import functools
import hashlib
import http.server
import json
import os
from pathlib import Path
import shutil
import threading
from urllib.parse import quote

from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]

def main():
 manifest=json.loads((ROOT/'素材清单.json').read_text());packs=manifest['插画套装清单'];management=manifest['插画管理资料']
 page_path=ROOT/management['HTML'];page_path.parent.mkdir(parents=True,exist_ok=True)
 raw=[x for x in manifest['素材'] if x['分类']=='插画与矢量图']
 records=[]
 for pack in packs:
  for item in sorted([x for x in raw if x['套装']==pack['名称']],key=lambda x:x['文件']):
   records.append({'id':item['编号'],'name':Path(item['文件']).stem,'file':os.path.relpath(ROOT/item['文件'],page_path.parent).replace(os.sep,'/'),
                   'pack':pack['标识'],'group':pack['用途类别'],'author':pack['作者'],'license':pack['许可'],
                   'kind':'pattern' if pack['标识']=='hero' else ('raster' if item['格式']=='PNG' else 'figure')})
 source=json.dumps(records,ensure_ascii=False).replace('<','\\u003c')
 options=''.join(f'<option value="{p["标识"]}">{p["名称"]} / {p["用途类别"]}</option>' for p in packs)
 template='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>插画与矢量图候选预览</title><style>
*{box-sizing:border-box}body{margin:0;background:#f0f0ed;color:#222;font:15px/1.6 system-ui,sans-serif}main{max-width:1700px;margin:auto;padding:30px}h1{font-size:29px;margin:6px 0}.note{font-size:14px;color:#555}.controls{display:flex;gap:14px;flex-wrap:wrap;margin:18px 0}label{flex:1;min-width:180px}input,select{font:inherit;display:block;width:100%;padding:8px 12px;border:1px solid #bbb;background:white;margin-top:4px}.grid{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:12px}.tile{min-width:0;display:block;padding:10px;background:#fff;border:1px solid #d6d6d0;color:inherit;text-decoration:none}.artbox{height:170px;background:#f7f7f4;display:flex;align-items:center;justify-content:center;position:relative;overflow:hidden}.artbox img{display:block;max-width:100%;max-height:100%;object-fit:contain}.pattern .artbox::before{content:"";position:absolute;inset:0;background-image:var(--pattern);background-repeat:repeat;background-size:100px auto;opacity:.28}.pattern img{opacity:0;position:absolute;width:1px;height:1px}.name{display:block;overflow-wrap:anywhere;font-size:12px;margin-top:8px}.caption{font-size:11px;color:#666}.single .grid{grid-template-columns:1fr}.single .artbox{height:600px}.single main{max-width:1100px}footer{font-size:12px;color:#555;margin-top:22px}footer a{color:inherit}@media(max-width:700px){main{padding:20px 14px}.grid{grid-template-columns:repeat(2,minmax(0,1fr))}.artbox{height:145px}label{min-width:130px}.single .artbox{height:300px}h1{font-size:24px}}
</style></head><body><main><div class="note">Migo素材与工具 · 2026-11-14 · 候选／未采用</div><h1 id="title">插画与矢量图 · 全部原件预览</h1><p class="note">背景图案、人物／动物动作与立体物体配图。120个SVG与1个PNG；PNG不属于矢量文件。点击素材可打开本地原件。</p><div class="controls"><label>选择套装<select id="pack"><option value="">全部套装</option>__OPTIONS__</select></label><label>按原文件名搜索<input id="query" type="search" placeholder="例如 reading、dots、notebook"></label></div><p id="count" role="status"></p><div id="grid" class="grid"></div><footer>
Hero Patterns © <a href="https://heropatterns.com/">Steve Schoger</a>，<a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>；Open Doodles by <a href="https://www.opendoodles.com/about">Pablo Stanley</a>，CC0；3dicons by <a href="https://github.com/realvjy/3dicons">Vijay Verma</a>，CC0。<br>原件未修改。预览对背景图案做重复平铺、缩放和透明度展示调整，其他素材仅缩放排版；许可和作者署名随原件保留。本图不代表Migo品牌视觉、Beedog形象或已采用方案。
</footer></main><script>
const data=__DATA__,selector=document.querySelector('#pack'),query=document.querySelector('#query'),grid=document.querySelector('#grid');
selector.value=new URLSearchParams(location.search).get('pack')||'';let serial=0;
async function render(){
 const own=++serial;document.documentElement.dataset.ready='false';
 const q=query.value.trim().toLowerCase(),items=data.filter(x=>(!selector.value||x.pack===selector.value)&&(!q||x.name.toLowerCase().includes(q)));
 grid.replaceChildren();document.body.classList.toggle('single',items.length===1);
 document.querySelector('#title').textContent=selector.value?selector.options[selector.selectedIndex].textContent:'插画与矢量图 · 全部原件预览';
 document.querySelector('#count').textContent=`当前${items.length}件原件 · 仅作候选查看，尚未采用`;
 const images=[];
 for(const x of items){const tile=document.createElement('a');tile.className='tile '+x.kind;tile.href=x.file;tile.target='_blank';tile.rel='noreferrer';tile.setAttribute('aria-label',x.name+' / '+x.group);
  const box=document.createElement('div');box.className='artbox';if(x.kind==='pattern')box.style.setProperty('--pattern',`url("${x.file}")`);
  const img=document.createElement('img');img.src=x.file;img.alt='';box.append(img);images.push(img);tile.append(box);
  const name=document.createElement('span');name.className='name';name.textContent=x.id+' / '+x.name;tile.append(name);
  const caption=document.createElement('span');caption.className='caption';caption.textContent=x.group+' · '+x.license;tile.append(caption);grid.append(tile);
 }
 try{await Promise.all(images.map(i=>i.decode()));if(own!==serial)return;window.artProof={原件数:items.length,编号:items.map(x=>x.id),文件:items.map(x=>x.file),图片读取:images.every(i=>i.complete&&i.naturalWidth>0)};document.documentElement.dataset.ready='true'}
 catch(e){if(own===serial){document.querySelector('#count').textContent='图片加载失败：'+e.message;document.documentElement.dataset.ready='error'}}
}
selector.addEventListener('change',render);query.addEventListener('input',render);render();
</script></body></html>'''
 page_path.write_text(template.replace('__OPTIONS__',options).replace('__DATA__',source))
 class Handler(http.server.SimpleHTTPRequestHandler):
  def log_message(self,*args):pass
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(ROOT)))
 threading.Thread(target=server.serve_forever,daemon=True).start();origin=f'http://127.0.0.1:{server.server_port}'
 url=origin+'/'+quote(str(page_path.relative_to(ROOT)))
 jobs=[('全部',url,management['总览PNG'],1600,[x['编号'] for x in raw])]
 for p in packs:jobs.append((p['名称'],url+'?pack='+p['标识'],p['预览图'],1400,[x['编号'] for x in raw if x['套装']==p['名称']]))
 report={'日期':'2026-11-14','说明':'原件读取和预览检查，不代表用户认可、最终品牌设计或项目应用。','截图':[]}
 executable=os.environ.get('MIGO_CHROMIUM_EXECUTABLE') or shutil.which('chromium') or shutil.which('chromium-browser')
 try:
  with sync_playwright() as p:
   browser=p.chromium.launch(**({'executable_path':executable} if executable else {}),headless=True,args=['--no-sandbox']);report['浏览器']=browser.version
   page=browser.new_page(viewport={'width':1600,'height':1000},device_scale_factor=1);errors=[];external=[]
   page.on('pageerror',lambda e:errors.append(str(e)));page.on('requestfailed',lambda r:errors.append(r.url+' '+str(r.failure)))
   page.on('request',lambda r:external.append(r.url) if not r.url.startswith(origin+'/') else None)
   def ready():page.wait_for_selector('html[data-ready="true"]',state='attached',timeout=30000)
   for name,target,image,width,expected in jobs:
    page.set_viewport_size({'width':width,'height':1000});page.goto(target,wait_until='networkidle');ready();result=page.evaluate('window.artProof')
    assert set(result['编号'])==set(expected) and result['图片读取'],(name,result)
    assert page.evaluate('document.documentElement.scrollWidth')<=width
    page.screenshot(path=str(ROOT/image),full_page=True)
    report['截图'].append({'名称':name,'文件':image,'SHA256':hashlib.sha256((ROOT/image).read_bytes()).hexdigest(),'视口宽度':width,'实际结果':result})
   page.goto(url,wait_until='networkidle');ready();page.locator('#pack').select_option('doodles');ready();assert page.evaluate('window.artProof.原件数')==33
   page.locator('#pack').select_option('');ready();page.locator('#query').fill('reading');ready();assert page.evaluate('window.artProof.原件数')==3
   page.locator('#query').fill('zz-no-such-art');ready();assert page.evaluate('window.artProof.原件数')==0
   page.locator('#query').fill('');ready();page.set_viewport_size({'width':390,'height':844});assert page.evaluate('document.documentElement.scrollWidth')<=390
   assert not errors and not external,(errors,external)
   report['交互检查']={'套装筛选':'33件Open Doodles通过','文件名搜索':'reading命中3件','无结果搜索':'0件正常显示','390px横向溢出':False,'脚本或加载错误':errors,'外部请求数':len(external)}
   browser.close()
 finally:server.shutdown();server.server_close()
 (ROOT/management['检查记录']).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print('121个原件及三套独立预览全部加载通过；生成四张PNG；筛选、搜索和手机宽度检查通过。')

if __name__=='__main__':main()
