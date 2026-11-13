#!/usr/bin/env python3
"""从本地SVG生成常用图及九页总览；HTML、检查JSON集中在图标/管理资料。

依赖Playwright和Chromium，不下载图标、不改变用户认可或项目采用状态。
"""
import functools
import hashlib
import http.server
import json
import math
import os
from pathlib import Path
import shutil
import threading
from urllib.parse import quote

from playwright.sync_api import sync_playwright

BASE=Path(__file__).resolve().parents[1]
ICONS=BASE/'图标'
MANAGEMENT=ICONS/'管理资料'
PAGE_SIZE=240
CATEGORIES={
 'accessibility':'无障碍','account':'账户','animals':'动物','arrows':'箭头','buildings':'建筑',
 'charts':'图表','communication':'沟通','connectivity':'连接','cursors':'光标','design':'设计',
 'development':'开发','devices':'设备','emoji':'表情','files':'文件','finance':'金融',
 'food-beverage':'食物与饮品','gaming':'游戏','home':'家居','layout':'布局','letters-digits':'字母与数字',
 'mail':'邮件','math':'数学','medical':'医疗','multimedia':'多媒体','nature':'自然','navigation':'导航',
 'notifications':'通知','people':'人物','photography':'摄影','science':'科学','seasons':'季节',
 'security':'安全','shapes':'形状','shopping':'购物','social':'社交','sports':'运动',
 'sustainability':'可持续','text':'文本','time':'时间','tools':'工具','transportation':'交通',
 'travel':'旅行','weather':'天气'}

def main():
 manifest=json.loads((BASE/'素材清单.json').read_text())
 pack=manifest['图标套装清单'][0]
 icons=sorted([x for x in manifest['素材'] if x.get('套装')=='Lucide'],key=lambda x:x['原始文件名'])
 assert len(icons)==pack['SVG原件数']
 MANAGEMENT.mkdir(parents=True,exist_ok=True)
 (ICONS/'全部图标预览').mkdir(exist_ok=True)
 page_path=BASE/pack['HTML']
 data=[]
 for item in icons:
  assert set(item['官方分类']) <= CATEGORIES.keys(),item['官方分类']
  data.append({'name':item['原始文件名'][:-4],
   'file':os.path.relpath(BASE/item['文件'],page_path.parent).replace(os.sep,'/'),
   'categories':item['官方分类'],'tags':item['官方搜索词'],
   'chinese':item.get('中文建议名',''),'usage':item.get('建议用途','')})
 payload=json.dumps(data,ensure_ascii=False).replace('<','\\u003c')
 common=json.dumps([x['源名称'] for x in pack['常用图标']],ensure_ascii=False)
 categories=json.dumps(CATEGORIES,ensure_ascii=False)
 template='''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Lucide图标候选预览</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#f3f3f1;color:#222;font:14px/1.6 system-ui,sans-serif}main{padding:30px;max-width:1700px;margin:auto}h1{font-size:30px;margin:6px 0}.note{color:#555;margin:8px 0}.controls{display:flex;gap:14px;flex-wrap:wrap;margin:20px 0}label{display:block;flex:1;min-width:150px}input,select,button{font:inherit;padding:8px 12px;border:1px solid #bbb;background:white;color:inherit;max-width:100%}input,select{display:block;width:100%;margin-top:4px}.pager{display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin:16px 0}button:disabled{opacity:.45}.grid{display:grid;grid-template-columns:repeat(12,minmax(0,1fr));gap:10px}.tile{display:flex;flex-direction:column;align-items:center;justify-content:flex-start;gap:7px;min-width:0;height:132px;padding:14px 7px 8px;background:white;border:1px solid #ddd;color:inherit;text-decoration:none}.tile img{display:block;width:32px;height:32px;flex-shrink:0}.name{font-size:11px;line-height:1.35;overflow-wrap:anywhere;text-align:center}.chinese{font-size:13px;line-height:1.3;text-align:center}.usage{font-size:11px;color:#666;text-align:center}.common .grid{grid-template-columns:repeat(6,minmax(0,1fr))}.common .tile{height:146px}.common .tile img{width:36px;height:36px}.common .name{font-size:12px}footer{color:#555;font-size:12px;margin-top:22px}@media(max-width:700px){main{padding:20px 14px}h1{font-size:25px}.grid,.common .grid{grid-template-columns:repeat(3,minmax(0,1fr))}label{min-width:120px}.controls{gap:10px}}
</style></head><body><main>
<div class="note">Migo素材与工具 · Lucide固定版本 · 候选／未采用</div><h1 id="title">Lucide图标预览</h1>
<p class="note">原始SVG：24×24画布、2单位描边。中文名称与用途为本库检索建议；官方名称保留。点击图标查看本地SVG。</p>
<div class="controls"><label>搜索名称／关键词<input id="query" type="search" placeholder="例如 menu、arrow、邮箱"></label><label>官方分类<select id="category"><option value="">全部分类</option></select></label></div>
<div class="pager"><button id="previous" type="button">上一页</button><span id="count" role="status"></span><button id="next" type="button">下一页</button></div>
<div id="grid" class="grid"></div><footer>本页面与PNG仅为素材读取预览，不代表Migo最终图标系统、Logo或Beedog设计。ISC及Feather MIT完整许可见Lucide目录。没有远程字体或外部图片请求。</footer>
</main><script>
const all=__DATA__,common=__COMMON__,categories=__CATEGORIES__;
const params=new URLSearchParams(location.search),isCommon=params.get('view')==='common';
document.body.classList.toggle('common',isCommon);document.querySelector('#title').textContent=isCommon?'网站常用图标候选 · 24枚':'Lucide全部图标候选 · 2055枚';
const byName=new Map(all.map(x=>[x.name,x]));const source=isCommon?common.map(n=>byName.get(n)):all;
const selector=document.querySelector('#category'),query=document.querySelector('#query'),grid=document.querySelector('#grid');
for(const [key,label] of Object.entries(categories)){const o=document.createElement('option');o.value=key;o.textContent=label+' / '+key;selector.append(o)}
let page=Math.max(0,Number(params.get('page')||1)-1),serial=0;
async function render(){
 const own=++serial;document.documentElement.dataset.iconsReady='false';
 const q=query.value.trim().toLowerCase(),category=selector.value;
 const filtered=source.filter(x=>(!category||x.categories.includes(category))&&(!q||[x.name,x.chinese,x.usage,...x.tags,...x.categories.map(c=>categories[c])].join(' ').toLowerCase().includes(q)));
 const pages=Math.max(1,Math.ceil(filtered.length/240));page=Math.min(Math.max(page,0),pages-1);
 const visible=filtered.slice(page*240,(page+1)*240);grid.replaceChildren();
 const images=[];
 for(const x of visible){
  const tile=document.createElement('a');tile.className='tile';tile.href=x.file;tile.target='_blank';tile.rel='noreferrer';tile.setAttribute('aria-label',x.chinese?x.chinese+' / '+x.name:x.name);
  const img=document.createElement('img');img.src=x.file;img.alt='';img.width=32;img.height=32;tile.append(img);images.push(img);
  if(isCommon&&x.chinese){const label=document.createElement('span');label.className='chinese';label.textContent=x.chinese;tile.append(label)}
  const name=document.createElement('span');name.className='name';name.textContent=x.name;tile.append(name);
  if(isCommon){const use=document.createElement('span');use.className='usage';use.textContent=x.usage;tile.append(use)}grid.append(tile);
 }
 document.querySelector('#previous').disabled=page===0;document.querySelector('#next').disabled=page>=pages-1;
 document.querySelector('#count').textContent=`共${filtered.length}枚 · 第${page+1}/${pages}页 · 本页${visible.length}枚`;
 try{await Promise.all(images.map(i=>i.decode()));if(own!==serial)return;window.iconProof={总数:filtered.length,页码:page+1,总页数:pages,当前名称:visible.map(x=>x.name),图片读取:images.every(i=>i.complete&&i.naturalWidth>0)};document.documentElement.dataset.iconsReady='true'}
 catch(e){if(own===serial){document.querySelector('#count').textContent='图片加载失败：'+e.message;document.documentElement.dataset.iconsReady='error'}}
}
query.addEventListener('input',()=>{page=0;render()});selector.addEventListener('change',()=>{page=0;render()});
document.querySelector('#previous').addEventListener('click',()=>{page--;render()});document.querySelector('#next').addEventListener('click',()=>{page++;render()});render();
</script></body></html>'''
 page_path.write_text(template.replace('__DATA__',payload).replace('__COMMON__',common).replace('__CATEGORIES__',categories))
 class Handler(http.server.SimpleHTTPRequestHandler):
  def log_message(self,*args):pass
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(BASE)))
 threading.Thread(target=server.serve_forever,daemon=True).start()
 origin=f'http://127.0.0.1:{server.server_port}'
 url=origin+'/'+quote(str(page_path.relative_to(BASE)))
 report={'日期':manifest['更新日期'],'说明':'全部SVG已核对来源与结构；本记录为本地渲染检查，不等于用户认可或逐枚审美评估。','检查':[]}
 pages=math.ceil(len(icons)/PAGE_SIZE)
 jobs=[('常用',url+'?view=common',BASE/pack['常用预览'],1200,[x['源名称'] for x in pack['常用图标']])]
 for n in range(pages):
  jobs.append((f'总览{n+1:02}',url+f'?page={n+1}',ICONS/'全部图标预览'/f'图标总览_{n+1:02}.png',1700,[x['原始文件名'][:-4] for x in icons[n*PAGE_SIZE:(n+1)*PAGE_SIZE]]))
 executable=os.environ.get('MIGO_CHROMIUM_EXECUTABLE') or shutil.which('chromium') or shutil.which('chromium-browser')
 try:
  with sync_playwright() as p:
   browser=p.chromium.launch(**({'executable_path':executable} if executable else {}),headless=True,args=['--no-sandbox'])
   report['浏览器']=browser.version
   page=browser.new_page(viewport={'width':1700,'height':1000},device_scale_factor=1)
   errors=[];outbound=[]
   page.on('pageerror',lambda e:errors.append(str(e)))
   page.on('requestfailed',lambda r:errors.append(str(r.failure)+' '+r.url))
   page.on('request',lambda r:outbound.append(r.url) if not r.url.startswith(origin+'/') else None)
   def ready():page.wait_for_selector('html[data-icons-ready="true"]',state='attached',timeout=30000)
   for name,target,png,width,expected in jobs:
    page.set_viewport_size({'width':width,'height':1000});page.goto(target,wait_until='networkidle');ready()
    result=page.evaluate('window.iconProof')
    assert result['当前名称']==expected and result['图片读取'],(name,result)
    assert page.evaluate('document.documentElement.scrollWidth')<=width,name
    assert not errors and not outbound,(errors,outbound)
    page.screenshot(path=str(png),full_page=True)
    report['检查'].append({'名称':name,'PNG':str(png.relative_to(BASE)),'截图SHA256':hashlib.sha256(png.read_bytes()).hexdigest(),'实际结果':result,'视口宽度':width,'脚本或加载错误':[],'外部请求数':0})
   page.goto(url,wait_until='networkidle');ready()
   page.locator('#next').click();ready();assert page.evaluate('window.iconProof.页码')==2
   page.locator('#previous').click();ready();assert page.evaluate('window.iconProof.页码')==1
   page.locator('#query').fill('邮箱');ready();assert page.evaluate('window.iconProof.当前名称')==['copy','mail']
   page.locator('#query').fill('zz-no-such-icon');ready();assert page.evaluate('window.iconProof.总数')==0
   page.locator('#query').fill('');ready();page.locator('#category').select_option('arrows');ready()
   expected_arrows=sum('arrows' in x['官方分类'] for x in icons)
   assert page.evaluate('window.iconProof.总数')==expected_arrows
   page.locator('#category').select_option('');ready();page.set_viewport_size({'width':390,'height':844})
   assert page.evaluate('document.documentElement.scrollWidth')<=390
   report['交互检查']={'上一页与下一页':'通过','中文搜索邮箱':'命中mail及带有复制邮箱用途的copy','无结果搜索':'0项，正常显示','官方箭头分类':expected_arrows,'手机390px横向溢出':False}
   browser.close()
 finally:server.shutdown();server.server_close()
 (BASE/pack['检查记录']).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 # 人读索引只记录每个源图标一次，分类允许多选，不重复复制SVG。
 lines=['# Lucide图标索引','','完整范围：所选固定版本的2,055枚SVG。按官方名称排序；中文分类为检索翻译，不代表用户认可。使用浏览器查找名称或分类，或打开管理资料里的可搜索HTML。','','[返回图标入口](README.md) · [常用预览](常用图标预览.png)','','| 官方名称 | 中文分类 | SVG原件 |','| --- | --- | --- |']
 for item in icons:
  local=Path(item['文件']).relative_to('图标')
  cats='、'.join(CATEGORIES[c] for c in item['官方分类']) or '未分类'
  lines.append(f"| {item['原始文件名'][:-4]} | {cats} | [打开]({local}) |")
 (ICONS/'图标索引.md').write_text('\n'.join(lines)+'\n')
 print(f'已生成常用图及{pages}页总览，2,055枚SVG逐页加载通过；搜索、分类、翻页与手机宽度检查通过。')

if __name__=='__main__':main()
