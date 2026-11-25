import sys
sys.path.insert(0,'.')
from zxsim import ZX
from PIL import Image
exec(open('zxtest3.py').read().split('# jetpack')[0])
zx=boot(); tap(zx,'0'); zx.run_frames(100)
tap(zx,'5',10); zx.run_frames(30); print('after 5 (left): room',zx.peek(0xF304))
tap(zx,'9',8); zx.run_frames(20); zx.screenshot('zxshots/w0.png')
tap(zx,'5'); tap(zx,'8'); zx.run_frames(5); zx.screenshot('zxshots/w1.png'); tap(zx,'ENTER'); zx.run_frames(60)
print('room',zx.peek(0xF304)); zx.screenshot('zxshots/w2.png')
ims=[Image.open('zxshots/w%d.png'%i) for i in range(3)]
w,h=ims[0].size; o=Image.new('RGB',(w*3+20,h),(60,60,60))
for i,im in enumerate(ims): o.paste(im,(i*(w+10),0))
o.save('/tmp/claude-0/warp_zx.png')
