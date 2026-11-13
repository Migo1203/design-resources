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
        if item['许可证文件'] not in notices:
            raise ValueError('未登记许可证：'+ident)
        inside(item['许可证文件'])
        if not all(item.get(k) for k in ['原始文件名','来源页面','下载链接','来源提交','下载日期','读取情况','项目采用情况']):
            raise ValueError('缺少记录：'+ident)
    for item in data['许可证原文']:
        if hashlib.sha256(inside(item['文件']).read_bytes()).hexdigest() != item['SHA256']:
            raise ValueError('许可证原文有变化：'+item['文件'])
    actual = {str(p.relative_to(ROOT)) for folder in ['字体','图标'] for p in (ROOT/folder).rglob('*') if p.suffix.lower() in {'.ttf','.otf','.woff','.woff2','.svg'}}
    if actual != paths:
        raise ValueError('清单未覆盖实际原件：'+str(actual ^ paths))
    for item in data['既有工具引用']:
        for name in item['文件']:
            path = (ROOT/name).resolve()
            if not path.is_relative_to(ROOT.parent) or not path.is_file():
                raise ValueError('既有工具引用无效：'+name)
    for name in ['预览/素材样张.html','预览/首批素材样张.png']:
        inside(name)
    print(f'通过：{len(seen)}项素材、{len(notices)}份许可证、既有工具引用与预览文件；未修改任何状态。')

if __name__ == '__main__':
    check()
