#!/usr/bin/env python3
"""只读检索本库统一素材清单；不下载、不复制、不修改采用状态。"""
import argparse
import collections
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--清单', type=Path, default=Path(__file__).resolve().parents[2] / '素材清单.json')
    parser.add_argument('--分类', default='', help='精确分类名称')
    parser.add_argument('--格式', default='', help='例如 SVG、TTF、OGG')
    parser.add_argument('--关键词', default='', help='空格分隔，所有词均须匹配')
    parser.add_argument('--编号', default='')
    parser.add_argument('--上限', type=int, default=20)
    parser.add_argument('--统计', action='store_true')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    if args.上限 < 1:
        parser.error('上限必须大于零')
    try:
        data = json.loads(args.清单.read_text(encoding='utf-8'))
        items = [x for x in data['素材'] if
                 (not args.分类 or x['分类'] == args.分类) and
                 (not args.格式 or x['格式'].casefold() == args.格式.casefold()) and
                 (not args.编号 or x['编号'] == args.编号) and
                 all(word in json.dumps(x, ensure_ascii=False).casefold() for word in args.关键词.casefold().split())]
    except (OSError, ValueError, KeyError) as exc:
        parser.exit(1, f'读取清单失败：{exc}\n')
    if args.统计:
        result = {'匹配数': len(items), '原件总字节数': sum(x['文件字节数'] for x in items),
                  '分类': dict(sorted(collections.Counter(x['分类'] for x in items).items()))}
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.json:
        print(json.dumps({'匹配数': len(items), '显示数': min(len(items), args.上限), '素材': items[:args.上限]}, ensure_ascii=False, indent=2))
    else:
        print(f'匹配 {len(items)} 项，显示前 {args.上限} 项；状态以清单为准。')
        for x in items[:args.上限]:
            print(f"{x['编号']} | {x['名称']} | {x['格式']} | {x['许可证']} | {x['状态']}／{x['项目采用情况']}\n  {x['文件']}")


if __name__ == '__main__':
    main()
