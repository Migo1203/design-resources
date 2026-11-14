#!/usr/bin/env python3
"""以临时合成图片检查交付工具，并只读查询素材清单；更新工具技术检查记录。"""
import tempfile,subprocess,json,hashlib
from pathlib import Path
from PIL import Image,ImageCms
root=Path(__file__).resolve().parents[1];scripts=root/'工具/交付与检索脚本'
temporary=tempfile.TemporaryDirectory(prefix='migo-image-tool-check-');tmp=Path(temporary.name)
alpha=Image.new('RGBA',(64,32),(12,34,56,0));alpha.paste((100,150,200,255),(32,0,64,32));alpha.save(tmp/'透明.png')
icc=ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
Image.new('RGB',(30,15),(200,100,20)).save(tmp/'配置.png',icc_profile=icc)
exif=Image.Exif();exif[274]=6;exif[315]='验证用作者';exif[270]='此项不得复制到交付图'
Image.new('RGB',(8,4),'red').save(tmp/'方向.jpg',exif=exif)
Image.new('CMYK',(10,10)).save(tmp/'印刷.jpg')
Image.new('RGB',(10,10)).save(tmp/'透明.jpg')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
inputs={str(p):sha(p) for p in tmp.glob('*') if p.is_file()}
proof=[]
def export(files,out,fmt='webp',edge=16,success=True):
 c=['python',str(scripts/'图片交付.py'),*[str(tmp/x) for x in files],'--输出',str(tmp/out),'--格式',fmt,'--长边',str(edge)]
 r=subprocess.run(c,text=True,capture_output=True);assert (r.returncode==0)==success,(c,r.stdout,r.stderr)
 proof.append({'参数':{'输入':files,'输出':out,'格式':fmt,'长边':edge},'预期成功':success,'退出码':r.returncode,'终端输出':(r.stdout+r.stderr).replace(str(tmp),'<临时合成测试目录>')})
 return tmp/out
out=export(['透明.png','配置.png'],'webp')
with Image.open(out/'透明.webp') as i:assert i.size==(16,8) and i.getpixel((0,0))[3]==0 and i.getpixel((15,0))[3]==255
out=export(['透明.png'],'jpeg','jpeg')
with Image.open(out/'透明.jpg') as i:assert i.size==(16,8) and min(i.getpixel((0,0)))>=245
out=export(['方向.jpg'],'direction','png',1600)
with Image.open(out/'方向.png') as i:assert i.size==(4,8) and not dict(i.getexif())
export(['透明.png'],'webp',success=False)
assert len(list((tmp/'webp').glob('*.webp')))==2
export(['透明.png','透明.jpg'],'collision',success=False);assert not (tmp/'collision').exists()
export(['印刷.jpg'],'cmyk',success=False);assert not (tmp/'cmyk').exists()
assert all(sha(Path(p))==v for p,v in inputs.items())
manifest=root/'素材清单.json';before=sha(manifest)
def find(args):
 r=subprocess.run(['python',str(scripts/'素材检索.py'),*args],capture_output=True,text=True);assert r.returncode==0,r.stderr;return r.stdout
x=json.loads(find(['--分类','音乐与音效','--统计']));assert x['匹配数']==7
x=json.loads(find(['--编号','字003','--json']));assert x['素材'][0]['编号']=='字003'
x=json.loads(find(['--格式','svg','--关键词','lucide','--统计']));assert x['匹配数']==2055
x=json.loads(find(['--关键词','不存在-验证专用','--json']));assert x['匹配数']==0
assert sha(manifest)==before
m=root/'工具/管理资料';m.mkdir(parents=True,exist_ok=True)
report={'验证输入':'仅Pillow生成的合成透明、RGB ICC、EXIF旋转及CMYK测试图；未处理用户照片或在库素材','图片交付':proof,'输入哈希未变':True,'透明与尺寸断言':True,'白底JPEG断言':True,'RGB_ICC处理断言':json.loads((tmp/'webp/交付清单.json').read_text())['文件'][1]['色彩处理']=='嵌入RGB ICC转换到sRGB','EXIF纠正与不放大':True,'重名拒绝与旧输出保护':True,'CMYK预检拒绝':True,'检索检查':{'音频数':7,'字003精确检索':True,'SVG_Lucide数量':2055,'无结果返回空集':True,'清单哈希未变':True},'本库脚本SHA256':{str(p.relative_to(root)):sha(p) for p in scripts.glob('*.py')}}
(m/'工具检查记录.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
temporary.cleanup()
print('通过：安全导出6组行为／透明／ICC／EXIF及4组只读检索检查。')
