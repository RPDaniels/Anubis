# Build a 48K .z80 snapshot (version 1, uncompressed) that starts the Spectrum port
import struct, spectrum
img, hs = spectrum.build()
ram = bytearray(0xC000)                       # 0x4000-0xFFFF
ram[0x8500 - 0x4000:0x8500 - 0x4000 + len(img)] = img
hdr = bytearray(30)
pc, sp = hs['INIT'], 0x8000
struct.pack_into('<BBHHHHBB', hdr, 0, 0, 0, 0, 0, pc, sp, 0x3F, 0)
hdr[12] = 0x20                                # border black, data compressed (some emulators mishandle raw v1)
struct.pack_into('<HHHHBBHH', hdr, 13, 0, 0, 0, 0, 0, 0, 0x5C3A, 0)
hdr[27] = 0; hdr[28] = 0                      # interrupts disabled (INIT sets up IM 2)
hdr[29] = 1                                   # IM 1
def z80_compress(mem):
    out = bytearray(); i = 0; n = len(mem)
    while i < n:
        b = mem[i]; j = i
        while j < n and mem[j] == b and j - i < 255: j += 1
        run = j - i
        if run >= 5 or (b == 0xED and run >= 2):
            out += bytes([0xED, 0xED, run, b]); i = j
        else:
            out.append(b); i += 1
            if b == 0xED and i < n:          # a byte following a single ED is never the start of a block
                out.append(mem[i]); i += 1
    return bytes(out + b'\x00\xED\xED\x00')
def z80_expand(data, size):
    out = bytearray(); i = 0
    while len(out) < size:
        if data[i] == 0xED and data[i + 1] == 0xED:
            out += bytes([data[i + 3]]) * data[i + 2]; i += 4
        else:
            out.append(data[i]); i += 1
    return bytes(out)
packed = z80_compress(ram)
assert z80_expand(packed, len(ram)) == bytes(ram)
open('ANUBIS_ZX.z80', 'wb').write(bytes(hdr) + packed)
print('ANUBIS_ZX.z80', 30 + len(packed), 'bytes, PC=%04X' % pc)
