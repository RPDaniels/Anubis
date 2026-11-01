import sys
from PIL import Image, ImageDraw
from render import PAL
d=open(sys.argv[1],'rb').read();b=0x8500
pat=d[0xcda0-b:0xcda0-b+2048]; col=d[0xd5a0-b:0xd5a0-b+32]
S=3
img=Image.new('RGB',(16*10*S+40,16*10*S+40),(60,60,60))
dr=ImageDraw.Draw(img)
for ch in range(256):
  cx=40+(ch%16)*10*S; cy=40+(ch//16)*10*S
  c=col[ch//8]; fg,bg=c>>4,c&15
  for y in range(8):
    for x in range(8):
      v=fg if pat[ch*8+y]&(0x80>>x) else bg
      dr.rectangle([cx+x*S,cy+y*S,cx+x*S+S-1,cy+y*S+S-1],fill=PAL[v] if v else (0,0,0))
for i in range(16):
  dr.text((40+i*10*S,25),'%X'%i,fill=(255,255,0)); dr.text((10,40+i*10*S),'%X0'%i,fill=(255,255,0))
img.save(sys.argv[2])
print(' '.join('%02x'%c for c in col))
