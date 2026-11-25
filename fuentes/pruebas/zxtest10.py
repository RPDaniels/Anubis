import sys
sys.path.insert(0,'.')
from zxsim import ZX
from PIL import Image
exec(open('zxtest3.py').read().split('# jetpack')[0])
zx=boot(); zx.screenshot('zxshots/ht.png')
goto(zx,14); zx.run_frames(20); zx.screenshot('zxshots/h0.png')
zx.pressed={'P'}; zx.run_frames(60); zx.pressed=set(); zx.run_frames(10); zx.screenshot('zxshots/h1.png')
print('CANF',zx.peek(0xDE94))
ims=[Image.open('zxshots/%s.png'%n) for n in ('ht','h0','h1')]
w,h=ims[0].size; o=Image.new('RGB',(w*3+20,h),(60,60,60))
for i,im in enumerate(ims): o.paste(im,(i*(w+10),0))
o.save('/tmp/claude-0/hint_zx.png')
