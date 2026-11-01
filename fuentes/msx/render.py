import sys
from PIL import Image
PAL=[(0,0,0),(0,0,0),(33,200,66),(94,220,120),(84,85,237),(125,118,252),(212,82,77),(66,235,245),(252,85,84),(255,121,120),(212,193,84),(230,206,128),(33,176,59),(201,91,186),(204,204,204),(255,255,255)]
def render(vram,regs,out,sprites=True,scale=2):
    m1=(regs[1]>>4)&1; m3=(regs[0]>>1)&1
    nt=(regs[2]&0x0f)*0x400; bd=regs[7]&15
    img=Image.new('RGB',(256,192),PAL[bd])
    px=img.load()
    if m3:
        ct=0x2000 if regs[3]&0x80 else 0; pg=0x2000 if regs[4]&4 else 0
        cm=((regs[3]&0x7f)<<3)|7; pm=((regs[4]&3)<<8)|0xff
        for r in range(24):
          for c in range(32):
            ch=vram[nt+r*32+c]+(r//8)*256
            for y in range(8):
              p=vram[pg+((ch&pm)*8)+y]; col=vram[ct+((ch&cm)*8)+y]
              fg,bg=col>>4,col&15
              for x in range(8):
                v=fg if p&(0x80>>x) else bg
                if v==0: v=bd
                px[c*8+x,r*8+y]=PAL[v]
    else:
        ct=regs[3]*0x40; pg=(regs[4]&7)*0x800
        for r in range(24):
          for c in range(32):
            ch=vram[nt+r*32+c]; col=vram[ct+ch//8]; fg,bg=col>>4,col&15
            for y in range(8):
              p=vram[pg+ch*8+y]
              for x in range(8):
                v=fg if p&(0x80>>x) else bg
                if v==0: v=bd
                px[c*8+x,r*8+y]=PAL[v]
    if sprites:
        sat=(regs[5]&0x7f)*0x80; spg=(regs[6]&7)*0x800; big=regs[1]&2; mag=regs[1]&1
        sz=16 if big else 8
        for i in range(32):
            y,x,n,c=vram[sat+i*4:sat+i*4+4]
            if y==208: break
            y=(y+1)&255
            if y>192: y-=256
            if c&0x80: x-=32
            if big: n&=0xfc
            col=c&15
            if col==0: continue
            for yy in range(sz):
              for xx in range(sz):
                if big: b=vram[spg+n*8+(xx//8)*16+yy]
                else: b=vram[spg+n*8+yy]
                if b&(0x80>>(xx%8)):
                    X,Y=x+xx,y+yy
                    if 0<=X<256 and 0<=Y<192: px[X,Y]=PAL[col]
    img=img.resize((256*scale,192*scale),Image.NEAREST)
    img.save(out)
if __name__=='__main__':
    vram=open(sys.argv[1],'rb').read(); regs=list(open(sys.argv[2],'rb').read())
    render(vram,regs,sys.argv[3])
