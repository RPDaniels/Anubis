import sys
sys.path.insert(0,'.')
from zxsim import ZX
from PIL import Image
exec(open('zxtest3.py').read().split('# jetpack')[0])
zx=boot(); goto(zx,14); zx.run_frames(30); zx.screenshot('zxshots/b0.png')
zx.pressed={'P'}; zx.run_frames(60); zx.pressed=set(); zx.run_frames(10); zx.screenshot('zxshots/b1.png')
print('CANF',zx.peek(0xDE94))
zx=boot(); goto(zx,240); zx.run_frames(30); zx.screenshot('zxshots/b2.png')
ims=[Image.open('zxshots/b%d.png'%i) for i in range(3)]
w,h=ims[0].size; o=Image.new('RGB',(w*3+20,h))
for i,im in enumerate(ims): o.paste(im,(i*(w+10),0))
o.save('/tmp/claude-0/blancos_zx.png')
