import sys; sys.path.insert(0,'.')
import zxsim, spectrum
img, hs = spectrum.build()
sym={}
for line in open('mons.sym'):
    p=line.split()
    if len(p)>=3 and p[1]=='EQU': sym[p[0]]=int(p[2].rstrip('H'),16)
room=sys.argv[1]; tag=sys.argv[2]
zx = zxsim.ZX(img, 0x8500, hs['INIT'])
zx.run_frames(850)
zx.screenshot('./zx_menu.png')
def key(k,n=6):
    zx.pressed.add(k); zx.run_frames(n); zx.pressed.discard(k); zx.run_frames(6)
key('5')
for ch in room: key(ch)
key('ENTER')
zx.run_frames(100)
zx.screenshot('./zx_%s_a.png'%tag)
print('room', zx.peek(0xF304))
if tag=='death':
    zx.m.memory[sym['LIVES']]=1
    for i in range(12):
        zx.run_frames(50); zx.screenshot('./zx_death_%02d.png'%i)
        print(i, 'lives', zx.peek(sym['LIVES']), 'pc %x'%zx.m.pc)
