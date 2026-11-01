# Minimal ZX Spectrum 48K harness (no ROM needed) to test the port headlessly
import sys
import z80
from PIL import Image

ROWS = {0xFE: 'CZXCV', 0xFD: 'ASDFG', 0xFB: 'QWERT', 0xF7: '12345',
        0xEF: '09876', 0xDF: 'POIUY', 0xBF: 'eLKJH', 0x7F: ' sMNB'}   # C=caps, e=enter, s=symshift, ' '=space
# key name -> (row, bit)
KEYS = {}
for row, chars in ROWS.items():
    for bit, ch in enumerate(chars):
        KEYS.setdefault(ch, (row, bit))
KEYS['CAPS'] = (0xFE, 0); KEYS['ENTER'] = (0xBF, 0); KEYS['SPACE'] = (0x7F, 0)

PAL = [(0, 0, 0), (0, 0, 205), (205, 0, 0), (205, 0, 205), (0, 205, 0), (0, 205, 205), (205, 205, 0), (205, 205, 205)]
PALB = [(0, 0, 0), (0, 0, 255), (255, 0, 0), (255, 0, 255), (0, 255, 0), (0, 255, 255), (255, 255, 0), (255, 255, 255)]

class ZX:
    def __init__(self, img, base, entry):
        self.m = z80.Z80Machine()
        self.m.set_memory_block(base, bytes(img))
        self.m.pc = entry
        self.pressed = set()
        self.frame = 0
        self.kempston = 0
        self.m.set_input_callback(self.inp)
        self.m.set_output_callback(lambda port, val: None)
    def inp(self, port):
        if port & 0xFF == 0x1F:
            return self.kempston
        if port & 1 == 0:
            hi = port >> 8
            v = 0x1F
            for k in self.pressed:
                row, bit = KEYS[k]
                if hi & (~row & 0xFF) == 0 or (~hi & 0xFF) & (~row & 0xFF):
                    pass
                if (~hi & 0xFF) & (~row & 0xFF):
                    v &= ~(1 << bit)
            return v | 0xE0
        return 0xFF
    def run_frames(self, n):
        for _ in range(n):
            self.m.ticks_to_stop = 69888
            while True:
                ev = self.m.run()
                if ev & 4: break
            self.m.on_handle_active_int()
            self.frame += 1
    def peek(self, a): return self.m.memory[a]
    def screenshot(self, path, scale=2):
        mem = self.m.memory
        im = Image.new('RGB', (256 + 32, 192 + 32), (0, 0, 0))
        px = im.load()
        for y in range(192):
            row = 0x4000 | ((y & 0xC0) << 5) | ((y & 7) << 8) | ((y & 0x38) << 2)
            for cx in range(32):
                b = mem[row + cx]; at = mem[0x5800 + (y >> 3) * 32 + cx]
                p = PALB if at & 0x40 else PAL
                ink, paper = p[at & 7], p[(at >> 3) & 7]
                for x in range(8):
                    px[16 + cx * 8 + x, 16 + y] = ink if b & (0x80 >> x) else paper
        im.resize((im.width * scale, im.height * scale), Image.NEAREST).save(path)
