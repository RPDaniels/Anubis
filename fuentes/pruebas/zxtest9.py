import sys
sys.path.insert(0,'.')
from zxsim import ZX
from PIL import Image
exec(open('zxtest3.py').read().split('# jetpack')[0])
zx=boot(); goto(zx,240)
zx.m.memory[0xCD4B:0xCD4F]=b'1234'; zx.m.memory[0xDE94]=15
ims=[]
for i in range(6):
    zx.run_frames(30 if i else 12); zx.screenshot('zxshots/fd%d.png'%i); ims.append(Image.open('zxshots/fd%d.png'%i))
    print(i, 'LK',zx.peek(0xDE98), bytes(zx.m.memory[0xCD4B:0xCD4F]), hex(zx.m.pc))
zx.run_frames(60); zx.screenshot('zxshots/fd6.png'); ims.append(Image.open('zxshots/fd6.png'))
w,h=ims[0].size; o=Image.new('RGB',(w*4+30,h*2+10),(60,60,60))
for i,im in enumerate(ims): o.paste(im,((i%4)*(w+10),(i//4)*(h+10)))
o.save('/tmp/claude-0/fade_zx.png')
zx.run_frames(1000); tap(zx,"SPACE",20); zx.run_frames(1200); tap(zx,'0'); zx.run_frames(120)
print('new game room', zx.peek(0xF304), 'score', bytes(zx.m.memory[0xCD4B:0xCD4F]), 'CANF', zx.peek(0xDE94))
zx.screenshot('/tmp/claude-0/newgame_zx.png')
