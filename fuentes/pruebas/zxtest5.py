import sys
sys.path.insert(0,'.')
from zxsim import ZX
exec(open('zxtest3.py').read().split('# jetpack')[0])
zx=boot(); goto(zx,58); zx.run_frames(20); zx.screenshot('zxshots/jar0.png')
print('room',zx.peek(0xF304),'CANON',zx.peek(0xDE95),'sat3',bytes(zx.m.memory[0x6B0C:0x6B10]).hex())
zx.pressed={'P'}; zx.run_frames(100); zx.pressed=set(); zx.run_frames(20)
zx.screenshot('zxshots/jar1.png'); print('CANF',zx.peek(0xDE94),'room',zx.peek(0xF304))
zx=boot(); goto(zx,240); zx.run_frames(30); zx.screenshot('zxshots/gate.png'); print('CANMSG',zx.peek(0xDE96),'pc',hex(zx.m.pc))
zx.m.memory[0xDE94]=15
zx.pressed={'P'}; zx.run_frames(60); zx.pressed={'O'}; zx.run_frames(80); zx.pressed=set(); zx.run_frames(200)
zx.screenshot('zxshots/gate_end.png'); print('pc',hex(zx.m.pc))
