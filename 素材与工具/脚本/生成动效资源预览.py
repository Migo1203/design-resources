#!/usr/bin/env python3
"""用本地CSS／JS实际验证交互、动效与减少动态效果；生成PNG与集中检查记录。

需要Playwright和Chromium；不下载、不安装、不改原件，不修改网站项目。
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

ROOT=Path(__file__).resolve().parents[1]

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    from playwright.sync_api import sync_playwright
    data=json.loads((ROOT/'素材清单.json').read_text());packs=data['动效套装清单'];meta=data['动效管理资料']
    class Handler(http.server.SimpleHTTPRequestHandler):
        def log_message(self,*args):pass
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(ROOT)))
    threading.Thread(target=server.serve_forever,daemon=True).start();origin=f'http://127.0.0.1:{server.server_port}';url=origin+'/'+quote(meta['HTML'])
    report={'日期':'2026-11-14','说明':'本地原件与本库验证页面；不是品牌采用、正式网站、完整无障碍或真实设备认证。','演示HTML_SHA256':sha(ROOT/meta['HTML']),'截图':[],'人工查看':{'状态':'待查看'}}
    executable=os.environ.get('MIGO_CHROMIUM_EXECUTABLE') or shutil.which('chromium') or shutil.which('chromium-browser')
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(**({'executable_path':executable} if executable else {}),headless=True,args=['--no-sandbox']);report['浏览器']=browser.version
            context=browser.new_context(viewport={'width':1440,'height':1000},reduced_motion='no-preference',device_scale_factor=1)
            page=context.new_page();errors=[];external=[];http_errors=[]
            def attach(page):
                page.on('pageerror',lambda e:errors.append(str(e)))
                page.on('requestfailed',lambda r:errors.append(r.url+' '+str(r.failure)))
                page.on('request',lambda r:external.append(r.url) if r.url.startswith(('http:','https:')) and not r.url.startswith(origin+'/') else None)
                page.on('response',lambda r:http_errors.append(r.url+' '+str(r.status)) if r.status>=400 else None)
            attach(page)
            def ready():page.wait_for_selector('html[data-ready="true"]',state='attached')
            def static_steps(state):return all(float(x['opacity'])==1 and x['transform'] in ['none','matrix(1, 0, 0, 1, 0, 0)'] for x in state['boxes'])
            def css_finished():page.evaluate("Promise.all(document.querySelector('#css-card').getAnimations().map(a=>a.finished.catch(()=>{})))")
            def modal_check():
                page.locator('#modal-open').focus();page.keyboard.press('Enter');assert page.locator('#sample-dialog').get_attribute('aria-hidden')=='false'
                assert page.evaluate('document.activeElement.id')=='modal-local'
                page.locator('#modal-close').focus()
                page.keyboard.press('Shift+Tab');assert page.evaluate('document.activeElement.id')=='modal-done'
                page.keyboard.press('Tab');assert page.evaluate('document.activeElement.id')=='modal-close'
                page.keyboard.press('Tab');assert page.evaluate('document.activeElement.id')=='modal-local'
                page.keyboard.press('Enter');assert '没有发送' in page.locator('#dialog-status').inner_text()
                page.keyboard.press('Escape');assert page.locator('#sample-dialog').get_attribute('aria-hidden')=='true';assert page.evaluate('document.activeElement.id')=='modal-open'
                for button in ['modal-close','modal-done']:
                    page.locator('#modal-open').click();page.locator('#'+button).click();assert page.locator('#sample-dialog').get_attribute('aria-hidden')=='true';assert page.evaluate('document.activeElement.id')=='modal-open'
                page.locator('#modal-open').click();page.locator('.modal-overlay').click(position={'x':4,'y':4});assert page.locator('#sample-dialog').get_attribute('aria-hidden')=='true'
                return {'Enter打开与首焦点':'通过；源库聚焦首个非关闭按钮modal-local','Tab与Shift+Tab双向循环':'通过','内部按钮本地反馈':'通过','Escape、关闭、完成与遮罩退出':'通过','Escape／按钮退出焦点返回':'通过','范围':'单个样例对话框，未测嵌套、读屏或Shadow DOM'}
            page.goto(url,wait_until='networkidle');ready();state=page.evaluate('demo.getState()');assert state['calls']==0 and not state['playing'] and static_steps(state)
            assert page.evaluate("typeof anime.createTimeline==='function'&&typeof MicroModal.init==='function'")
            easing=page.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--ease-out-3').trim()")
            assert easing.startswith('cubic-bezier(')
            page.locator('#demo-select').focus();page.keyboard.press('Tab');assert page.evaluate('document.activeElement.id')=='extra-reduce';page.keyboard.press('Tab');assert page.evaluate('document.activeElement.id')=='css-toggle'
            before=page.locator('#css-card').evaluate('(e)=>getComputedStyle(e).transform');page.keyboard.press('Enter')
            effects=page.locator('#css-card').evaluate('(e)=>e.getAnimations().map(a=>({duration:a.effect.getTiming().duration,easing:a.effect.getTiming().easing}))')
            assert effects and all(x['duration']==240 for x in effects)
            css_finished();after=page.locator('#css-card').evaluate('(e)=>getComputedStyle(e).transform');assert before!=after and page.locator('#css-toggle').get_attribute('aria-pressed')=='true'
            report['正常模式']={'初始无自动动画且静态内容可见':True,'CSS源缓动变量':easing,'CSS键盘路径':'select → Tab复选框 → Tab反馈按钮 → Enter通过','CSS真实过渡':effects,'CSS前后transform':[before,after]}
            page.locator('#anime-play').click();page.wait_for_function('demo.getState().time>90 && demo.getState().playing');moving=page.evaluate('demo.getState()');assert any(0<float(x['opacity'])<1 for x in moving['boxes'])
            page.locator('#anime-pause').focus();page.keyboard.press('Enter');paused=page.evaluate('demo.getState()');assert paused['paused'] is True and not paused['playing']
            page.evaluate('new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))');assert abs(page.evaluate('demo.getState().time')-paused['time'])<1
            page.locator('#anime-reset').click();assert static_steps(page.evaluate('demo.getState()'))
            report['正常模式']['时间线真实运动采样']=moving;report['正常模式']['暂停采样']=paused;report['正常模式']['重置恢复完整静态内容']=True
            page.locator('#anime-play').click();page.wait_for_function("document.getElementById('anime-status').textContent.includes('播放完成')");assert static_steps(page.evaluate('demo.getState()'))
            report['正常模式']['单次完成后全部内容可见']=True
            report['正常模式']['对话框']=modal_check()
            # Change the actual browser media preference while a source animation runs.
            page.locator('#anime-play').click();page.wait_for_function('demo.getState().playing');count=page.evaluate('demo.getState().calls')
            page.emulate_media(reduced_motion='reduce');page.wait_for_function("document.documentElement.dataset.reduce==='true'")
            reduced=page.evaluate('demo.getState()');assert not reduced['playing'] and reduced['time'] is None and static_steps(reduced)
            before_color=page.locator('#css-card').evaluate('(e)=>getComputedStyle(e).backgroundColor');page.locator('#css-toggle').click();after_color=page.locator('#css-card').evaluate('(e)=>getComputedStyle(e).backgroundColor')
            assert before_color!=after_color and page.locator('#css-card').evaluate('(e)=>e.getAnimations().length')==0
            assert page.locator('#css-card').evaluate('(e)=>getComputedStyle(e).transform')=='none'
            page.locator('#anime-play').click();assert page.evaluate('demo.getState().calls')==count and static_steps(page.evaluate('demo.getState()'))
            page.locator('#extra-reduce').check();page.locator('#extra-reduce').uncheck();assert page.evaluate('demo.getState().reduced')
            report['减少动效模式']={'运行中切换系统偏好会取消时间线并恢复内容':True,'CSS保留即时状态反馈且无动画':True,'减少模式点击播放未新增引擎调用':True,'页面开关不能覆盖系统减少偏好':True,'对话框':modal_check(),'实现归属':'减少动效判断、取消与回退逻辑由本库验证页编写，不是三个库自动完成'}
            # A user-controlled extra switch can also disable motion when the system does not.
            page.emulate_media(reduced_motion='no-preference');page.wait_for_function("document.documentElement.dataset.reduce==='false'");assert static_steps(page.evaluate('demo.getState()'))
            page.locator('#extra-reduce').check();assert page.evaluate('demo.getState().reduced');count=page.evaluate('demo.getState().calls');page.locator('#anime-play').click();assert page.evaluate('demo.getState().calls')==count;page.locator('#extra-reduce').uncheck()
            report['页面额外关闭开关']='通过；关闭／恢复均不自动播放'
            def snap(pack,device,width,height,key):
                page.set_viewport_size({'width':width,'height':height});page.goto(url+'?demo='+pack['标识'],wait_until='networkidle');ready()
                assert page.evaluate('document.documentElement.scrollWidth')<=width
                if pack['标识']=='css':page.locator('#css-toggle').click();css_finished()
                elif pack['标识']=='anime':page.evaluate('demo.freeze()');assert abs(page.evaluate('demo.getState().time')-200)<1;assert float(page.evaluate('demo.getState().boxes[2].opacity'))==0
                else:page.locator('#modal-open').click();assert page.locator('#sample-dialog').get_attribute('aria-hidden')=='false'
                assert page.evaluate('document.documentElement.scrollWidth')<=width
                page.screenshot(path=str(ROOT/pack[key]),full_page=True)
                report['截图'].append({'套装':pack['名称'],'设备':device,'文件':pack[key],'SHA256':sha(ROOT/pack[key]),'宽度':width,'高度':height,'无横向溢出':True,'状态':'时间线固定200ms' if pack['标识']=='anime' else ('对话框打开' if pack['标识']=='modal' else '选中反馈完成')})
            for pack in packs:
                snap(pack,'桌面',1440,1000,'桌面预览');snap(pack,'手机',390,844,'手机预览')
            page.set_viewport_size({'width':1440,'height':1000});page.goto(url,wait_until='networkidle');ready();page.locator('#css-toggle').click();css_finished();page.evaluate('demo.freeze()')
            page.screenshot(path=str(ROOT/meta['总览PNG']),full_page=True)
            report['截图'].append({'套装':'全部','设备':'总览','文件':meta['总览PNG'],'SHA256':sha(ROOT/meta['总览PNG']),'状态':'CSS选中、Anime.js固定200ms、对话框关闭'})
            page.emulate_media(reduced_motion='reduce');page.wait_for_function("document.documentElement.dataset.reduce==='true'");assert static_steps(page.evaluate('demo.getState()'))
            page.screenshot(path=str(ROOT/meta['减少动效PNG']),full_page=True)
            report['截图'].append({'套装':'全部','设备':'减少动效','文件':meta['减少动效PNG'],'SHA256':sha(ROOT/meta['减少动效PNG']),'状态':'系统reduce、所有内容静态可见'})
            # A separate touch-capable context tests tap without claiming a real device.
            touch=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True,reduced_motion='reduce');mobile=touch.new_page();attach(mobile)
            mobile.goto(url+'?demo=modal',wait_until='networkidle');mobile.wait_for_selector('html[data-ready="true"]',state='attached');mobile.locator('#modal-open').tap();assert mobile.locator('#sample-dialog').get_attribute('aria-hidden')=='false';mobile.locator('#modal-close').tap();assert mobile.locator('#sample-dialog').get_attribute('aria-hidden')=='true'
            report['触控模拟']='390px、reduce下触摸打开与关闭通过；不是实体设备测试';touch.close()
            assert not errors and not external and not http_errors,(errors,external,http_errors)
            report['脚本或加载错误']=errors;report['外部网络请求数']=len(external);report['HTTP错误']=http_errors
            context.close();browser.close()
    finally:server.shutdown();server.server_close()
    (ROOT/meta['检查记录']).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('三套本地资源读取通过；正常／系统reduce／页面关闭动效、键盘焦点、触控模拟通过；生成八张实际PNG。')

if __name__=='__main__':main()
