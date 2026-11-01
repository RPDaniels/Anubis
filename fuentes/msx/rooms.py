import sys
from PIL import Image
from render import render, PAL
B=0x8500
class Mem:
    def __init__(s,d): s.d=bytearray(d)
    def __getitem__(s,a): return s.d[a-B]
    def w(s,a): return s.d[a-B]|(s.d[a-B+1]<<8)
def run(m,vram,addr,depth=0):
    A=BC=DE=HL=0
    pc=addr
    while True:
        op=m[pc]
        if op==0x00: pc+=1
        elif op==0x01: BC=m.w(pc+1); pc+=3
        elif op==0x11: DE=m.w(pc+1); pc+=3
        elif op==0x21: HL=m.w(pc+1); pc+=3
        elif op==0x3e: A=m[pc+1]; pc+=2
        elif op==0xc9: return
        elif op==0xcd:
            t=m.w(pc+1); pc+=3
            if t==0x5c:
                for i in range(BC): vram[DE+i]=m[HL+i]
            elif t==0x56:
                for i in range(BC): vram[HL+i]=A
            elif t==0x4d: vram[HL]=A
            elif t==0xa800:
                w,h=BC>>8,BC&255; src=DE
                for y in range(h):
                    for x in range(w): vram[HL+y*32+x]=m[src]; src+=1
            else: run(m,vram,t,depth+1)
        else: raise Exception('op %02x at %04x'%(op,pc))
def compose(m,room):
    vram=bytearray(16384)
    for i in range(0x800): vram[i]=m[0xcda0+i]
    for i in range(32): vram[0x2000+i]=m[0xd5a0+i]
    for i in range(0x300): vram[0x1800+i]=0x20
    vram[0x1b00]=208
    run(m,vram,0xb18f)
    t=m[0xcb00+room]
    run(m,vram,0xb000+13*t)
    run(m,vram,0xd5c0+16*room)
    return vram
REGS=[0,0xe2,6,0x80,0,0x36,7,0]
if __name__=='__main__':
    m=Mem(open(sys.argv[1],'rb').read())
    out=sys.argv[2]; rooms=[int(x) for x in sys.argv[3:]]
    imgs=[]
    for r in rooms:
        v=compose(m,r); render(v,REGS,'_tmp_render.png',sprites=False,scale=1)
        imgs.append(Image.open('_tmp_render.png').copy())
    cols=min(4,len(imgs)); rows=(len(imgs)+cols-1)//cols
    sheet=Image.new('RGB',(cols*260,rows*196),(80,80,80))
    for i,im in enumerate(imgs): sheet.paste(im,((i%cols)*260+2,(i//cols)*196+2))
    sheet.save(out)
