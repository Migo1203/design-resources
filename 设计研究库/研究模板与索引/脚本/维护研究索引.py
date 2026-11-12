#!/usr/bin/env python3
"""从 YAML 生成 Markdown 索引并检查研究库；不改变研究状态。"""
import argparse
import datetime as dt
import re
import sys
from collections import defaultdict
from pathlib import Path
from urllib.parse import unquote, urlsplit
try:
    import yaml
except ImportError:
    sys.exit('缺少 PyYAML，请运行 python -m pip install PyYAML')

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / '设计研究库'
INDEX = BASE / '研究模板与索引'
CATEGORIES = {
    '01_设计师档案': '设计师档案', '02_品牌设计案例': '品牌案例',
    '03_角色与IP设计案例': '角色与IP案例', '04_网站与数字体验案例': '网站案例',
    '05_平面与视觉设计案例': '平面视觉案例', '设计方法专题': '设计方法专题',
    '教程与学习资源': '教程与学习资源',
    '06_电商设计案例': '电商案例',
}
STATUSES = ['待研究', '研究中', '待补充', '已完成', '已应用验证', '已搁置']
INDEX_TYPES = {'设计师索引.md': '设计师档案', '品牌案例索引.md': '品牌案例',
               'IP案例索引.md': '角色与IP案例', '网站案例索引.md': '网站案例',
               '视觉案例索引.md': '平面视觉案例', '电商案例索引.md': '电商案例'}
REQUIRED = {'标题', '研究类型', '研究状态', '创建日期', '更新日期', '标签', '关联项目'}

# 拒绝重复键，避免 YAML 看起来一个状态、程序实际读到另一个状态。
class StrictLoader(yaml.SafeLoader):
    pass

def unique_mapping(loader, node, deep=False):
    result = {}
    for k, v in node.value:
        key = loader.construct_object(k, deep=deep)
        if key in result:
            raise ValueError('YAML 重复字段：' + str(key))
        result[key] = loader.construct_object(v, deep=deep)
    return result

StrictLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)

def day(value):
    return value.isoformat() if isinstance(value, dt.date) else str(value)

def metadata(path, vocabulary):
    text = path.read_text()
    match = re.match(r'\A---\n(.*?)\n---\n', text, re.S)
    if not match:
        raise ValueError(f'{path.relative_to(ROOT)}：缺少 YAML Front Matter')
    data = yaml.load(match[1], Loader=StrictLoader)
    if not isinstance(data, dict) or not REQUIRED <= data.keys():
        raise ValueError(f'{path.name}：YAML 缺必填字段')
    if not isinstance(data['标题'], str) or not data['标题'].strip():
        raise ValueError(f'{path.name}：标题无效')
    if data['研究类型'] not in CATEGORIES.values() or data['研究状态'] not in STATUSES:
        raise ValueError(f'{path.name}：研究类型或状态无效')
    for key in ['创建日期', '更新日期']:
        data[key] = day(data[key])
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', data[key]):
            raise ValueError(f'{path.name}：日期必须为 YYYY-MM-DD')
        dt.date.fromisoformat(data[key])
    if data['更新日期'] < data['创建日期']:
        raise ValueError(f'{path.name}：更新早于创建')
    tags = data['标签']
    if not isinstance(tags, list) or not all(isinstance(t, str) for t in tags):
        raise ValueError(f'{path.name}：标签必须为字符串列表')
    if not 3 <= len(tags) <= 8 or len(tags) != len(set(tags)) or set(tags) - vocabulary:
        raise ValueError(f'{path.name}：标签须为词典中3–8个不重复项：{set(tags)-vocabulary}')
    projects = data['关联项目']
    if not isinstance(projects, list) or not projects or not all(isinstance(p, str) and p.strip() for p in projects):
        raise ValueError(f'{path.name}：关联项目须为非空字符串列表')
    return data, text[match.end():]

def read_research(vocabulary):
    records = []
    titles = set()
    for folder, typ in CATEGORIES.items():
        if not (BASE / folder / 'README.md').is_file():
            raise ValueError('分类缺少 README：'+folder)
        for path in sorted((BASE / folder).rglob('*.md')):
            if path.name == 'README.md':
                continue
            data, body = metadata(path, vocabulary)
            if data['研究类型'] != typ:
                raise ValueError(f'{path.name}：目录与研究类型不一致')
            if data['标题'] in titles:
                raise ValueError('重复研究标题：'+data['标题'])
            titles.add(data['标题'])
            for heading in ['研究目的', '核心结论', '学习价值', '资料来源', '关联项目', '研究记录']:
                if heading not in body:
                    raise ValueError(f'{path.name}：缺少{heading}')
            if data['研究状态'] not in ['待研究', '已搁置']:
                conclusions = re.search(r'## 核心结论\n(.*?)(?=\n## |\Z)', body, re.S)
                if not conclusions or not 3 <= len(re.findall(r'^\d+\. ', conclusions[1], re.M)) <= 5:
                    raise ValueError(f'{path.name}：须3–5条核心结论')
                rows = [line for line in body.splitlines() if re.match(r'^\| [A-Z][A-Z0-9]*\d+ \|', line)]
                if not rows:
                    raise ValueError(f'{path.name}：来源表至少一条记录，编号采用H1、R1等字母数字')
                ids = set()
                for row in rows:
                    cols = [c.strip() for c in row.strip('|').split('|')]
                    if len(cols) != 5 or not all(cols):
                        raise ValueError(f'{path.name}：来源须编号、名称及链接、日期、可信度、范围五列')
                    if cols[0] in ids:
                        raise ValueError(f'{path.name}：来源编号重复')
                    ids.add(cols[0])
                    if not re.search(r'\[[^]]+\]\(https?://[^)]+\)', cols[1]):
                        raise ValueError(f'{path.name}：来源缺名称或原始HTTP链接')
                    dt.date.fromisoformat(cols[2])
                    if not re.match(r'^[ABC]类', cols[3]):
                        raise ValueError(f'{path.name}：来源可信度须A类、B类或C类')
                if typ == '设计师档案':
                    for n, name in enumerate(['基本信息','设计理念','代表作品','设计特点','值得学习的地方','资料来源'],1):
                        if f'## {n:02d} {name}' not in body:
                            raise ValueError(f'{path.name}：缺设计师六维章节{name}')
                    if len(re.findall(r'^### [A-Z]\. ', body, re.M)) < 2 or '深入拆解' not in body:
                        raise ValueError(f'{path.name}：须两个作品且一个深入拆解')
            if data['研究状态'] in ['已完成', '已应用验证'] and '## 完成检查记录' not in body:
                raise ValueError(f'{path.name}：完成状态须有完成检查记录，脚本不代替事实检查')
            if data['研究状态'] == '已应用验证' and '## 实际应用证据' not in body:
                raise ValueError(f'{path.name}：应用验证须有实际应用证据，内容仍需人工核实')
            data['_path'], data['_body'] = path, body
            records.append(data)
    for path in sorted((INDEX/'模板').glob('*.md')):
        metadata(path, vocabulary)
    return sorted(records, key=lambda d: (d['研究类型'], d['标题']))

def link(data):
    rel = data['_path'].relative_to(BASE).as_posix()
    return f"[{data['标题']}](../{rel})"

def cell(value):
    return str(value).replace('|', '\\|').replace('\n', ' ')

def table(records):
    out = ['| 名称 | 研究类型 | 研究状态 | 主要标签 | 关联项目 | 文档链接 | 最近更新时间 |',
           '| --- | --- | --- | --- | --- | --- | --- |']
    for d in records:
        values = [d['标题'], d['研究类型'], d['研究状态'], '、'.join(d['标签']), '、'.join(d['关联项目']), link(d), d['更新日期']]
        out.append('| '+' | '.join(cell(v) for v in values)+' |')
    if not records:
        out += ['\n当前没有独立研究文档。相关作品可能在设计师档案内，先查总索引；不得将分类说明或模板算成案例。']
    return '\n'.join(out)

def generated(records):
    note = '> 本文件由脚本从研究文档 YAML 生成，请修改研究正文后重新生成，不手抄索引。\n\n'
    summary = '# 研究总索引\n\n'+note+f'当前实际研究文档：{len(records)} 份。研究状态不代表用户审美认可或实际采用。\n\n'+table(records)+'\n\n'
    summary += '## 按研究状态检索\n\n'
    for status in STATUSES:
        matches = [link(d) for d in records if d['研究状态'] == status]
        summary += f'- **{status}**：'+('；'.join(matches) or '暂无记录')+'\n'
    summary += '\n## 按五类标签检索\n\n只列当前实际使用的标签，全部可选标签见[标签词典](标签词典.md)。\n\n'
    for prefix in ['领域','风格','方法','行业','项目']:
        summary += f'### {prefix}\n\n'
        by_tag = defaultdict(list)
        for d in records:
            for tag in d['标签']:
                if tag.startswith(prefix+'/'):
                    by_tag[tag].append(link(d))
        summary += '\n'.join(f'- **{tag}**：'+ '；'.join(values) for tag, values in sorted(by_tag.items())) or '暂无已使用标签。'
        summary += '\n\n'
    summary += '## 按关联项目检索\n\n'
    by_project = defaultdict(list)
    for d in records:
        for project in d['关联项目']:
            by_project[project].append(link(d))
    summary += '\n'.join(f'- **{project}**：'+ '；'.join(values) for project, values in sorted(by_project.items()))
    summary += '\n\n按姓名可搜索中文标题；英文名保留在标题或正文，如 Paul Rand、Michael Bierut、Kenya Hara。\n\n[维护规则](README.md) · [返回研究库](../README.md)\n'
    outputs = {'研究总索引.md': summary}
    for name, typ in INDEX_TYPES.items():
        outputs[name] = '# '+name[:-3]+'\n\n'+note+table([d for d in records if d['研究类型'] == typ])+'\n\n[研究总索引](研究总索引.md) · [维护规则](README.md)\n'
    # 从全部研究档案的来源表提取，不维护第二份手工来源数据库。
    sources = '# 资料来源清单\n\n'+note+'本清单从实际研究来源表提取；访问状态和可信度必须一起看。外部链接不提供素材授权，原始作品图不复制到仓库。\n\n| 研究档案 | 来源编号 | 来源与原始链接 | 访问日期 | 可信度 | 核验范围与限制 |\n| --- | --- | --- | --- | --- | --- |\n'
    for d in records:
        for row in d['_body'].splitlines():
            if re.match(r'^\| [A-Z][A-Z0-9]*\d+ \|', row):
                sources += '| '+link(d)+' '+row+'\n'
    sources += '\n[来源与核验规范](来源与核验规范.md) · [研究总索引](研究总索引.md)\n'
    outputs['资料来源清单.md'] = sources
    return outputs

def anchors(path):
    text = re.sub(r'```.*?```', '', path.read_text(), flags=re.S)
    found = set(re.findall(r'<(?:a|h\d)\b[^>]*id=[\"\']([^\"\']+)', text))
    counts = defaultdict(int)
    for heading in re.findall(r'^#{1,6}\s+(.+?)(?:\s+#+)?$', text, re.M):
        slug = re.sub(r'[^\w\- ]', '', heading.lower()).replace(' ', '-')
        count = counts[slug]
        found.add(slug+(f'-{count}' if count else '')); counts[slug] += 1
    return found

def check_links():
    count = 0
    # 检查整个仓库的 Markdown 本地链接。外部站点逐个研究访问，不批量抓取原目录1249资源。
    for path in sorted(ROOT.rglob('*.md')):
        if '.git' in path.parts:
            continue
        text = re.sub(r'```.*?```', '', path.read_text(), flags=re.S)
        for raw in re.findall(r'!?\[[^\]\n]*\]\(([^\s)]+)(?:\s+[^)]*)?\)', text):
            raw = raw.strip('<>')
            url = urlsplit(raw)
            if url.scheme or raw.startswith('//'):
                continue
            dest = (path.parent / unquote(url.path)).resolve() if url.path else path
            if not dest.exists():
                raise ValueError(f'{path.relative_to(ROOT)}：本地链接不存在 {raw}')
            if url.fragment and dest.suffix == '.md' and unquote(url.fragment) not in anchors(dest):
                raise ValueError(f'{path.relative_to(ROOT)}：Markdown 锚点不存在 {raw}')
            count += 1
    return count

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true', help='生成索引和来源清单')
    parser.add_argument('--check', action='store_true', help='检查元数据、索引与本地链接')
    args = parser.parse_args()
    if not args.write and not args.check:
        parser.error('请使用 --write 或 --check')
    try:
        vocabulary = set(re.findall(r'^\| ((?:领域|风格|方法|行业|项目)/[^|\n]+?) \|', (INDEX/'标签词典.md').read_text(), re.M))
        records = read_research(vocabulary)
        outputs = generated(records)
        for name, text in outputs.items():
            path = INDEX/name
            if args.write:
                path.write_text(text)
            elif not path.exists() or path.read_text() != text:
                raise ValueError('索引过期或缺失：'+name+'；请先运行 --write')
        links = check_links()
        print(f'通过：{len(records)}份研究、{len(vocabulary)}个定义标签、{len(list((INDEX/'模板').glob('*.md')))}类模板、{len(outputs)}份生成文件、{links}个本地Markdown链接。')
        print('检查不自动确认事实、图像已查看、审美认可或项目应用。')
    except (ValueError, OSError, yaml.YAMLError) as error:
        print('检查失败：'+str(error), file=sys.stderr)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())
