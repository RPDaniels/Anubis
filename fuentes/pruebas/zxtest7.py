import sys
sys.path.insert(0,'.')
from zxsim import ZX
from PIL import Image
exec(open('zxtest3.py').read().split('# jetpack')[0])
ims=[]
for room in (14,132,202,230):
    zx=boot(); goto(zx,room); zx.run_frames(60)
    print(room, 'room',zx.peek(0xF304),'CANON',zx.peek(0xDE95), 'SAT', bytes(zx.m.memory[0x6B00:0x6B10]).hex())
    zx.screenshot('zxshots/v%d.png'%room); ims.append(Image.open('zxshots/v%d.png'%room))
w,h=ims[0].size; o=Image.new('RGB',(w*2+10,h*2+10))
for i,im in enumerate(ims): o.paste(im,((i%2)*(w+10),(i//2)*(h+10)))
o.save('/tmp/claude-0/vasos_zx.png')
