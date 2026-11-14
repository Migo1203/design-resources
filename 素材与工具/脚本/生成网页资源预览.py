#!/usr/bin/env python3
"""构建归档Astro示例、组合三个官方组件、验证Pico样式并生成真实截图。

依赖：Node/npm、Playwright、Chromium。依赖安装和构建仅发生在临时目录。
默认使用已保存的锁文件npm ci（忽略安装脚本），不修改官方原件或网站项目。
"""
import argparse
import functools
import hashlib
import html
import http.server
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]

def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    from playwright.sync_api import sync_playwright
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work-dir',type=Path,help='仅接受新目录或有本脚本标记的临时验证目录')
    parser.add_argument('--reuse-deps',action='store_true',help='复用指定验证目录中已安装且符合锁文件的依赖')
    args=parser.parse_args()
    manifest=json.loads((ROOT/'素材清单.json').read_text());packs=manifest['网页套装清单'];meta=manifest['网页验证资料']
    template,components,pico=packs
    work=args.work_dir.resolve() if args.work_dir else Path(tempfile.mkdtemp(prefix='migo-web-resource-'))
    if work.is_relative_to(ROOT.parent): raise ValueError('验证目录不能位于资源仓库内部')
    marker=work/'.migo-web-resource-check'
    if work.exists() and any(work.iterdir()) and not marker.is_file(): raise ValueError('拒绝覆盖未标记目录')
    work.mkdir(parents=True,exist_ok=True);marker.write_text('Migo资源隔离验证目录\n')
    shutil.copytree(ROOT/template['目录']/'原件',work,dirs_exist_ok=True)
    shutil.copytree(ROOT/components['目录']/'原件/src/components',work/'src/components/archive',dirs_exist_ok=True)
    shutil.copyfile(ROOT/meta['组件验证页'],work/'src/pages/components.astro')
    shutil.copyfile(ROOT/meta['依赖锁文件'],work/'package-lock.json')
    env=os.environ.copy();env['ASTRO_TELEMETRY_DISABLED']='1'
    def run(argv):
        p=subprocess.run(argv,cwd=work,env=env,text=True,capture_output=True)
        if p.returncode: raise RuntimeError('命令失败：'+repr(argv)+'\n'+p.stdout[-5000:]+p.stderr[-5000:])
        return p.stdout
    npm=['npm','--cache',str(work/'npm-cache')]
    if not args.reuse_deps:run(npm+['ci','--ignore-scripts','--no-audit','--no-fund','--loglevel','error'])
    installed=json.loads(run(npm+['ls','--json','--depth=0']))
    lock=json.loads((work/'package-lock.json').read_text())
    declared=json.loads((work/'package.json').read_text())['dependencies']
    versions={name:installed['dependencies'][name]['version'] for name in declared}
    for name,version in versions.items():
        if lock['packages']['node_modules/'+name]['version']!=version: raise ValueError('验证依赖与锁文件不符：'+name)
    build=run(npm+['run','build'])
    for route in ['index.html','markdown-page/index.html','components/index.html']:
        if not (work/'dist'/route).is_file():raise ValueError('构建未生成预期页面：'+route)
    class Handler(http.server.SimpleHTTPRequestHandler):
        def log_message(self,*args):pass
    servers=[]
    def serve(folder):
        server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(folder)))
        threading.Thread(target=server.serve_forever,daemon=True).start();servers.append(server)
        return f'http://127.0.0.1:{server.server_port}'
    origin=serve(ROOT);astro=serve(work/'dist')
    pico_url=origin+'/'+quote(meta['Pico验证页'])
    report={'日期':'2026-11-14','说明':'资源归档与隔离验证；没有改动Migo网站或品牌项目。','构建':{'结果':'通过','Node':run(['node','--version']).strip(),'npm':run(['npm','--version']).strip(),'直接依赖版本':versions,'锁文件SHA256':digest(ROOT/meta['依赖锁文件']),'生成页面':['/','/markdown-page/','/components/'],'安装方式':'npm install --ignore-scripts首次生成锁；复查或重现使用npm ci --ignore-scripts，依赖未入库','构建日志':build},'验证页面SHA256':{key:digest(ROOT/meta[key]) for key in ['组件验证页','Pico验证页']},'截图':[],'交互检查':{},'人工查看':{'状态':'待查看'}}
    executable=os.environ.get('MIGO_CHROMIUM_EXECUTABLE') or shutil.which('chromium') or shutil.which('chromium-browser')
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(**({'executable_path':executable} if executable else {}),headless=True,args=['--no-sandbox']);report['浏览器']=browser.version
            page=browser.new_page(viewport={'width':1440,'height':1000},device_scale_factor=1)
            errors=[];external=[];http_errors=[]
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.on('requestfailed',lambda r:errors.append(r.url+' '+str(r.failure)))
            page.on('response',lambda r:http_errors.append(r.url+' '+str(r.status)) if r.status>=400 else None)
            page.on('request',lambda r:external.append(r.url) if r.url.startswith(('http:','https:')) and not any(r.url.startswith(o+'/') for o in [origin,astro]) else None)
            layout=[]
            for pack,url in [(template,astro+'/'),(components,astro+'/components/'),(pico,pico_url)]:
                for device,width,height,key in [('桌面',1440,1000,'桌面预览'),('手机',390,844,'手机预览')]:
                    page.set_viewport_size({'width':width,'height':height});response=page.goto(url,wait_until='networkidle');assert response.ok
                    assert page.evaluate('document.documentElement.scrollWidth')<=width,(pack['名称'],device,'横向溢出')
                    if pack==template:
                        assert page.get_by_role('button',name='Tailwind Button in Astro!').is_visible()
                        assert page.get_by_role('button').evaluate('(e)=>getComputedStyle(e).backgroundColor')!='rgba(0, 0, 0, 0)'
                    if pack==components:
                        proof=page.evaluate('''()=>({默认列数:getComputedStyle(document.querySelector('#default ul')).gridTemplateColumns.split(' ').length,错位首项:getComputedStyle(document.querySelector('#offset li')).transform,紧凑布局:getComputedStyle(document.querySelector('#small ul')).display,紧凑末项起列:getComputedStyle(document.querySelector('#small li:last-child')).gridColumnStart,紧凑末项终列:getComputedStyle(document.querySelector('#small li:last-child')).gridColumnEnd,标题字号:getComputedStyle(document.querySelector('.title')).fontSize})''')
                        assert proof['默认列数']==(2 if device=='桌面' else 1)
                        assert (proof['错位首项']!='none')==(device=='桌面')
                        assert proof['紧凑布局']==('flex' if device=='桌面' else 'grid')
                        if device=='手机':assert (proof['紧凑末项起列'],proof['紧凑末项终列'])==('1','3')
                        layout.append({'设备':device,**proof})
                    page.screenshot(path=str(ROOT/pack[key]),full_page=True)
                    report['截图'].append({'套装':pack['名称'],'设备':device,'文件':pack[key],'SHA256':digest(ROOT/pack[key]),'宽度':width,'高度':height,'无横向溢出':True,'类型':'实际构建页面' if pack!=pico else '本库语义HTML＋官方CSS验证页'})
            page.set_viewport_size({'width':1440,'height':1000})
            page.goto(astro+'/',wait_until='networkidle');page.keyboard.press('Tab');assert page.get_by_role('button').evaluate('(e)=>e===document.activeElement');page.keyboard.press('Enter');page.wait_for_selector('canvas')
            await_canvas=page.locator('canvas').count();assert await_canvas>0
            page.get_by_role('link',name='Markdown is also supported...').click();page.wait_for_url(astro+'/markdown-page/');assert page.get_by_text('Tailwind classes also work in Markdown!').is_visible()
            page.get_by_role('link',name='Go home').click();page.wait_for_url(astro+'/')
            page.emulate_media(reduced_motion='reduce');page.get_by_role('button').click();page.wait_for_selector('canvas');reduced_canvas=page.locator('canvas').count()>0;page.emulate_media(reduced_motion='no-preference')
            report['交互检查']['Astro示例']={'首页与Markdown互返':'通过','Tab与Enter触发源按钮':'通过，实际生成canvas','减少动态效果时仍生成彩纸canvas':reduced_canvas,'限制':'源按钮用全局首个button且confetti()未传减少动效参数，不能直接视为适合多实例或生产动效的组件'}
            report['交互检查']['作品集组件']=layout
            page.goto(pico_url,wait_until='networkidle')
            before=page.evaluate('getComputedStyle(document.documentElement).backgroundColor');page.locator('#theme').click();assert page.locator('html').get_attribute('data-theme')=='dark';after=page.evaluate('getComputedStyle(document.documentElement).backgroundColor');assert before!=after;page.locator('#theme').click()
            page.locator('#feedback').focus();page.keyboard.press('Enter');assert '已触发' in page.locator('#status').inner_text()
            page.locator('#details summary').click();assert page.locator('#details').get_attribute('open') is not None
            assert not page.locator('#form').evaluate('(e)=>e.checkValidity()')
            page.locator('[name="sample-name"]').fill('组件验证');page.locator('[name="sample-email"]').fill('invalid');page.locator('[name="sample-confirm"]').check();assert not page.locator('#form').evaluate('(e)=>e.checkValidity()')
            page.locator('[name="sample-email"]').fill('example@example.com');page.locator('#form button').click();assert '没有发送' in page.locator('#form-status').inner_text()
            page.locator('#open-dialog').click();assert page.locator('#dialog').evaluate('(e)=>e.open');page.keyboard.press('Escape');assert not page.locator('#dialog').evaluate('(e)=>e.open');assert page.locator('#open-dialog').evaluate('(e)=>e===document.activeElement')
            page.locator('#open-dialog').click();page.locator('#confirm-dialog').click();assert not page.locator('#dialog').evaluate('(e)=>e.open')
            report['交互检查']['Pico验证页']={'主题切换':'通过，实际根背景变化','按钮键盘反馈':'通过','原生折叠':'通过','无效邮箱拒绝／有效输入反馈':'通过；无发送与保存','原生对话框Escape／按钮关闭与焦点返回':'通过','行为来源':'Pico负责样式；折叠与验证依赖浏览器，开关和反馈脚本为本库编写'}
            # Overview uses actual local screenshots; it is not another website template.
            overview=ROOT/meta['HTML'];cards=[]
            for pack in packs:
                desktop=os.path.relpath(ROOT/pack['桌面预览'],overview.parent).replace(os.sep,'/');mobile=os.path.relpath(ROOT/pack['手机预览'],overview.parent).replace(os.sep,'/')
                cards.append(f'<article><h2>{html.escape(pack["名称"])}</h2><p>{html.escape(pack["类型"])} · MIT · 候选／未采用</p><div class="shots"><img src="{quote(desktop,safe="/")}" alt="桌面实际预览"><img src="{quote(mobile,safe="/")}" alt="手机实际预览"></div></article>')
            overview.write_text('''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>网页模板与UI资源总览</title><style>*{box-sizing:border-box}body{margin:0;background:#eeeee9;color:#222;font:15px/1.6 system-ui,sans-serif}main{padding:28px;max-width:1800px;margin:auto}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}article{min-width:0;background:white;padding:16px;border:1px solid #ccc}h1{font-size:30px}h2{font-size:20px}p,footer{font-size:13px;color:#555}.shots{display:grid;grid-template-columns:2fr 1fr;gap:10px;align-items:start}img{width:100%;height:570px;object-fit:contain;object-position:top;background:#fafafa;border:1px solid #ddd}footer{margin-top:20px}@media(max-width:800px){.grid{grid-template-columns:1fr}img{height:auto}}</style><main><h1>网页模板与UI组件 · 实际运行预览</h1><p>2026-11-14 · 三套来源、14个官方源码文件。每组左为1440px桌面，右为390px手机。仅为资源学习与验证，不是Migo作品集UI或已采用方案。</p><div class="grid">'''+''.join(cards)+'''</div><footer>Astro官方Tailwind示例、官方作品集组件及Pico CSS按各自MIT许可保留。Astro示例保持原画面；组件组合页与Pico语义HTML由本库编写并标明临时参数。原件未改；源码／浏览器验证不代表完整产品、所有设备或整套无障碍认证。</footer></main></html>''')
            page.goto(origin+'/'+quote(meta['HTML']),wait_until='networkidle');page.set_viewport_size({'width':1600,'height':1000});page.evaluate('Promise.all([...document.images].map(i=>i.decode()))');assert page.locator('img').count()==6
            assert page.evaluate('document.documentElement.scrollWidth')<=1600
            page.locator('main').screenshot(path=str(ROOT/meta['总览PNG']))
            report['截图'].append({'套装':'全部','设备':'总览','文件':meta['总览PNG'],'SHA256':digest(ROOT/meta['总览PNG']),'六张本地截图读取':True})
            assert not errors and not external and not http_errors,(errors,external,http_errors)
            report['脚本或加载错误']=errors;report['外部网络请求数']=len(external);report['HTTP错误']=http_errors
            browser.close()
    finally:
        for server in servers:server.shutdown();server.server_close()
    (ROOT/meta['检查记录']).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Astro构建通过，三类页面桌面／手机共六张实际截图与一张总览；基础操作、布局与原件检查完成。')

if __name__=='__main__':main()
