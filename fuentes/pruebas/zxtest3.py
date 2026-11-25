import sys
sys.path.insert(0,'.')
from zxsim import ZX
img=open('anubis_zx.bin','rb').read()
def boot():
    zx=ZX(img,0x7600,0xF400); zx.run_frames(1100); return zx
def tap(zx,k,n=6,gap=6):
    zx.pressed={k}; zx.run_frames(n); zx.pressed=set(); zx.run_frames(gap)
def goto(zx,room):
    tap(zx,'5'); zx.run_frames(10)
    for ch in str(room): tap(zx,ch)
    tap(zx,'ENTER'); zx.run_frames(80)
# jetpack
zx=boot(); goto(zx,105); print('start',zx.peek(0xF304))
zx.pressed={'Q'}; zx.run_frames(150); print('holding up room',zx.peek(0xF304),'y',zx.peek(0x6B00)); zx.screenshot('zxshots/jet.png')
zx.pressed={'O','Q'}; zx.run_frames(60); zx.pressed=set(); zx.run_frames(50); print('after left room',zx.peek(0xF304),'x',zx.peek(0x6B01),'y',zx.peek(0x6B00))
# lotus ending
zx=boot(); goto(zx,240); zx.screenshot('zxshots/lotus.png')
zx.pressed={'P'}; zx.run_frames(120); zx.pressed=set(); zx.run_frames(100)
zx.screenshot('zxshots/ending.png'); print('pc',hex(zx.m.pc))
zx.run_frames(1000); tap(zx,'SPACE',20); zx.run_frames(50); print('after space pc',hex(zx.m.pc))
