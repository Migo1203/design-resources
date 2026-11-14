#!/usr/bin/env python3
"""将明确指定的RGB图片导出到全新目录，生成交付清单；不覆盖原件。需要Pillow。"""
import argparse
import hashlib
import io
import json
import shutil
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('输入', nargs='+', type=Path)
    parser.add_argument('--输出', required=True, type=Path, help='尚不存在的输出目录')
    parser.add_argument('--格式', choices=['webp', 'png', 'jpeg'], default='webp')
    parser.add_argument('--长边', type=int, default=1600, help='只缩小，不放大')
    parser.add_argument('--质量', type=int, default=85, help='WebP／JPEG的有损质量；PNG忽略')
    args = parser.parse_args()
    if args.长边 < 1 or not 1 <= args.质量 <= 100:
        parser.error('长边须大于零；质量范围1–100')
    try:
        import PIL
        from PIL import Image, ImageCms, ImageOps, features
    except ImportError as exc:
        parser.exit(1, f'缺少依赖：{exc}；请在自己的Python虚拟环境中安装Pillow。\n')
    try:
        if args.格式 == 'webp' and not features.check('webp'):
            raise ValueError('当前Pillow没有WebP编码支持')
        output = args.输出.expanduser().absolute()
        if output.exists() or output.is_symlink():
            raise ValueError('输出目录必须尚不存在，避免覆盖任何旧文件')
        extension = 'jpg' if args.格式 == 'jpeg' else args.格式
        inputs = [x.expanduser().resolve(strict=True) for x in args.输入]
        names = [x.stem + '.' + extension for x in inputs]
        if len({x.casefold() for x in names}) != len(names):
            raise ValueError('输入文件导出后重名，请分批处理或先整理名称')
        srgb = ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB'))
        srgb_bytes = srgb.tobytes()
        jobs = []
        # 全部预检通过才创建输出目录；排除多帧、CMYK及无法确认的模式。
        for source, name in zip(inputs, names):
            original_sha = digest(source)
            with Image.open(source) as opened:
                if getattr(opened, 'n_frames', 1) != 1:
                    raise ValueError(f'不支持动画或多页图片：{source.name}')
                if opened.mode not in ('RGB', 'RGBA', 'L', 'LA', 'P'):
                    raise ValueError(f'需独立管理的颜色模式 {opened.mode}：{source.name}')
                before = opened.size
                icc = opened.info.get('icc_profile')
                orientation = opened.getexif().get(274, 1)
                image = ImageOps.exif_transpose(opened).convert('RGBA')
                alpha = image.getchannel('A')
                rgb = image.convert('RGB')
                if icc:
                    profile = ImageCms.ImageCmsProfile(io.BytesIO(icc))
                    if profile.profile.xcolor_space.strip() != 'RGB':
                        raise ValueError(f'仅支持RGB ICC配置：{source.name}')
                    rgb = ImageCms.profileToProfile(rgb, profile, srgb, outputMode='RGB')
                    color = '嵌入RGB ICC转换到sRGB'
                else:
                    color = '无ICC：假定sRGB；不是色彩校准'
                rgb.putalpha(alpha)
                rgb.thumbnail((args.长边, args.长边), Image.Resampling.LANCZOS)
                flattened = args.格式 == 'jpeg'
                if flattened:
                    canvas = Image.new('RGB', rgb.size, 'white')
                    canvas.paste(rgb, mask=rgb.getchannel('A'))
                    rgb = canvas
                # PNG等编码器可能沿用info中的EXIF，必须显式清理；ICC在保存时统一写入sRGB。
                rgb.info.clear()
                jobs.append((source, name, rgb, {'输入文件': str(source), '输入SHA256': original_sha,
                    '输入尺寸': list(before), '输出文件': name, '输出尺寸': list(rgb.size), '色彩处理': color,
                    'EXIF方向值': orientation, 'EXIF已按方向纠正并移除': True,
                    '透明处理': '白底合成' if flattened else '保留透明通道',
                    '格式': args.格式, '质量': None if args.格式 == 'png' else args.质量}))
        output.mkdir(parents=True, exist_ok=False)
        records = []
        try:
            for source, name, image, record in jobs:
                if digest(source) != record['输入SHA256']:
                    raise ValueError('处理期间输入发生变化：' + source.name)
                destination = output / name
                options = {'icc_profile': srgb_bytes}
                if args.格式 != 'png':
                    options['quality'] = args.质量
                if args.格式 == 'webp':
                    options['method'] = 6
                with destination.open('xb') as handle:
                    image.save(handle, format={'jpeg': 'JPEG', 'webp': 'WEBP', 'png': 'PNG'}[args.格式], **options)
                record.update({'输出SHA256': digest(destination), '输出字节数': destination.stat().st_size})
                records.append(record)
            report = {'工具': '图片交付.py', 'Pillow版本': PIL.__version__, '处理数': len(records),
                      '说明': '派生文件；不授予输入图片许可，不自动标记项目采用；输出未保留EXIF定位等元数据。', '文件': records}
            (output / '交付清单.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        except Exception:
            # 仅清理本次创建的全新目录，永不清理输入或已有输出。
            shutil.rmtree(output)
            raise
        print(f'已导出 {len(records)} 张到 {output}，原件未改；详见交付清单.json。')
    except (OSError, ValueError, ImageCms.PyCMSError) as exc:
        parser.exit(1, f'未完成：{exc}\n')


if __name__ == '__main__':
    main()
