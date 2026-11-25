import sys
sys.path.insert(0,'.')
from zxsim import ZX
exec(open('zxtest3.py').read().split('# jetpack')[0])
sym={l.split()[0]:int(l.split()[2].rstrip('H'),16) for l in open('hal.sym') if 'EQU' in l}
H=sym['SFXH']; A=sym['SFXALT']
zx=boot(); goto(zx,58); zx.run_frames(20)
zx.pressed={'P'}
seen=[]
for i in range(140):
    zx.run_frames(1)
    v=(tuple(zx.m.memory[H:H+3]),zx.m.memory[A])
    if zx.peek(0xDE94): seen.append(v)
print('CANF',zx.peek(0xDE94))
for v in seen[:40]: print(v)
