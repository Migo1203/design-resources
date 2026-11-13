#!/usr/bin/env python3
"""只读校验入库清单与文件完整性；不修改采用或认可状态。"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def inside(name):
    path = (ROOT/name).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError('素材路径超出目录：'+name)
    if not path.is_file():
        raise ValueError('文件不存在：'+name)
    return path

def check():
    data = json.loads((ROOT/'素材清单.json').read_text())
    seen, paths = set(), set()
    notices = {x['文件'] for x in data['许可证原文']}
    for item in data['素材']:
        ident = item['编号']
        if ident in seen:
            raise ValueError('重复编号：'+ident)
        seen.add(ident)
        path = inside(item['文件'])
        if item['文件'] in paths:
            raise ValueError('原件重复登记：'+item['文件'])
        paths.add(item['文件'])
        raw = path.read_bytes()
        if len(raw) != item['文件字节数'] or hashlib.sha256(raw).hexdigest() != item['SHA256']:
            raise ValueError('原件与清单不一致：'+item['文件'])
        if item.get('源GitBlobSHA1') and hashlib.sha1(f'blob {len(raw)}\0'.encode()+raw).hexdigest() != item['源GitBlobSHA1']:
            raise ValueError('原件与官方Git blob不一致：'+item['文件'])
        if item['许可证文件'] not in notices:
            raise ValueError('未登记许可证：'+ident)
        inside(item['许可证文件'])
        if not all(item.get(k) for k in ['原始文件名','来源页面','下载链接','下载日期','读取情况','项目采用情况']) or not (item.get('来源提交') or item.get('来源版本')):
            raise ValueError('缺少记录：'+ident)
    for item in data['许可证原文']:
        if hashlib.sha256(inside(item['文件']).read_bytes()).hexdigest() != item['SHA256']:
            raise ValueError('许可证原文有变化：'+item['文件'])
    actual = {str(p.relative_to(ROOT)) for folder in ['字体','图标','样机'] for p in (ROOT/folder).rglob('*') if p.suffix.lower() in {'.ttf','.otf','.woff','.woff2','.svg','.css','.psd','.psb'}}
    actual |= {str(p.relative_to(ROOT)) for p in (ROOT/'插画与矢量图').glob('*/原件/*') if p.is_file()}
    if actual != paths:
        raise ValueError('清单未覆盖实际原件：'+str(actual ^ paths))
    for item in data['既有工具引用']:
        for name in item['文件']:
            path = (ROOT/name).resolve()
            if not path.is_relative_to(ROOT.parent) or not path.is_file():
                raise ValueError('既有工具引用无效：'+name)
    for name in ['预览/素材样张.html','预览/首批素材样张.png']:
        inside(name)
    families = data.get('字体家族清单', [])
    for family in families:
        for key in ['元数据文件','说明文件','样张图','样张HTML']:
            inside(family[key])
        if hashlib.sha256(inside(family['元数据文件']).read_bytes()).hexdigest() != family['元数据SHA256']:
            raise ValueError('官方字体元数据有变化：'+family['名称'])
        members = [x for x in data['素材'] if x.get('字体家族目录') == family['目录']]
        if {x['原始文件名'] for x in members} != set(family['目标原始文件名']):
            raise ValueError('目标字体下载范围不完整：'+family['名称'])
    if families:
        checks = json.loads(inside('字体/管理资料/字体样张检查记录.json').read_text())
        expected = {x['样张图'] for x in families} | {'字体/全部字体预览.png'}
        if {x['PNG'] for x in checks['检查']} != expected:
            raise ValueError('字体样张检查未覆盖全部家族和总览')
        for check in checks['检查']:
            if hashlib.sha256(inside(check['PNG']).read_bytes()).hexdigest() != check['截图SHA256']:
                raise ValueError('字体截图与检查记录不一致：'+check['PNG'])
            inside(check['HTML'])
    packs = data.get('图标套装清单', [])
    for pack in packs:
        members = sorted([x for x in data['素材'] if x.get('套装') == pack['名称']],key=lambda x:x['原始文件名'])
        names = {x['原始文件名'] for x in members}
        if len(members) != pack['SVG原件数'] or len(names) != len(members):
            raise ValueError('图标套装数量或唯一名称不一致')
        if sum(x['文件字节数'] for x in members) != pack['原件总字节数']:
            raise ValueError('图标套装原件大小不一致')
        listing = '\n'.join(x['原始文件名']+'\t'+x['源GitBlobSHA1'] for x in members)
        if hashlib.sha256(listing.encode()).hexdigest() != pack['目标SVG集合SHA256']:
            raise ValueError('图标套装与官方完整SVG集合不一致')
        inside(pack['许可文件']); inside(pack['HTML'])
        report = json.loads(inside(pack['检查记录']).read_text())
        rendered = []
        for check in report['检查']:
            if hashlib.sha256(inside(check['PNG']).read_bytes()).hexdigest() != check['截图SHA256']:
                raise ValueError('图标截图与检查记录不一致：'+check['PNG'])
            if not check['实际结果']['图片读取'] or check['脚本或加载错误'] or check['外部请求数']:
                raise ValueError('图标预览存在读取错误')
            if check['名称'] != '常用': rendered.extend(check['实际结果']['当前名称'])
        if len(rendered) != len(members) or set(rendered) != {x[:-4] for x in names}:
            raise ValueError('图标总览未逐页覆盖完整套装')
    mockups = data.get('样机套装清单', [])
    for pack in mockups:
        source = next(x for x in data['素材'] if x['编号'] == pack['原件编号'])
        if source['分类'] != '样机':
            raise ValueError('样机原件分类不一致')
        inside(pack['HTML'])
        report = json.loads(inside(pack['检查记录']).read_text())
        if len(report['设备']) != len(pack['展示模板']) or not all(x['图片可读'] for x in report['设备']):
            raise ValueError('样机展示验证不完整')
        for item in report['截图']:
            if hashlib.sha256(inside(item['文件']).read_bytes()).hexdigest() != item['SHA256']:
                raise ValueError('样机PNG与检查记录不一致')
        if report['交互检查']['脚本或加载错误'] or report['交互检查']['外部请求数']:
            raise ValueError('样机读取存在错误或外部请求')
    illustrations = data.get('插画套装清单', [])
    for pack in illustrations:
        members = sorted([x for x in data['素材'] if x.get('套装') == pack['名称']], key=lambda x: x['文件'])
        listing = '\n'.join(x['文件']+'\t'+x['SHA256'] for x in members)
        if len(members) != pack['原件数'] or sum(x['文件字节数'] for x in members) != pack['原件总字节数'] or hashlib.sha256(listing.encode()).hexdigest() != pack['原件集合SHA256']:
            raise ValueError('插画套装数量、大小或原件集合不一致：'+pack['名称'])
        for key in ['许可证文件','预览图','说明文件']:
            inside(pack[key])
    if illustrations:
        management = data['插画管理资料']
        inside(management['HTML'])
        report = json.loads(inside(management['检查记录']).read_text())
        expected_images = {p['预览图'] for p in illustrations} | {management['总览PNG']}
        if {x['文件'] for x in report['截图']} != expected_images:
            raise ValueError('插画预览未覆盖三套及总览')
        for shot in report['截图']:
            if hashlib.sha256(inside(shot['文件']).read_bytes()).hexdigest() != shot['SHA256']:
                raise ValueError('插画截图与检查记录不一致：'+shot['文件'])
            expected_ids = {x['编号'] for x in data['素材'] if x['分类'] == '插画与矢量图' and (shot['名称'] == '全部' or x.get('套装') == shot['名称'])}
            proof = shot['实际结果']
            if set(proof['编号']) != expected_ids or proof['原件数'] != len(expected_ids) or len(proof['编号']) != len(expected_ids) or not proof['图片读取']:
                raise ValueError('插画截图的原件读取证明不完整：'+shot['名称'])
        interaction = report['交互检查']
        if interaction['脚本或加载错误'] or interaction['外部请求数'] or interaction['390px横向溢出']:
            raise ValueError('插画预览存在加载或布局错误')
    print(f'通过：{len(seen)}项素材、{len(notices)}份许可证、{len(families)}个字体家族、{len(packs)}套图标、{len(mockups)}套样机、{len(illustrations)}套插画及全部预览；未修改任何状态。')

if __name__ == '__main__':
    check()
