# MSX .CAS -> .WAV (standard MSX tape format, 1200 baud FSK 1200/2400 Hz)
import sys, wave, array, math
RATE = 43200
HDR = bytes([0x1F, 0xA6, 0xDE, 0xBA, 0xCC, 0x13, 0x7D, 0x74])
def cycles(freq, n, out, amp=26000):
    spc = RATE // freq
    one = [int(amp * math.sin(2 * math.pi * i / spc)) for i in range(spc)]
    for _ in range(n): out.extend(one)
def bit(b, out):
    if b: cycles(2400, 2, out)
    else: cycles(1200, 1, out)
def byte(v, out):
    bit(0, out)
    for i in range(8): bit((v >> i) & 1, out)
    bit(1, out); bit(1, out)
def silence(sec, out): out.extend([0] * int(RATE * sec))
def convert(cas, wav):
    d = open(cas, 'rb').read()
    pos = []; i = 0
    while True:
        j = d.find(HDR, i)
        if j < 0: break
        if j % 8 == 0: pos.append(j)
        i = j + 1
    out = array.array('h')
    silence(1.0, out)
    for k, p in enumerate(pos):
        blk = d[p + 8:(pos[k + 1] if k + 1 < len(pos) else len(d))]
        is_file_header = len(blk) >= 10 and blk[:10] in (b'\xd0' * 10, b'\xd3' * 10, b'\xea' * 10)
        if is_file_header and k > 0: silence(2.0, out)
        elif k > 0: silence(1.0, out)
        cycles(2400, 16000 if is_file_header else 4000, out)   # long / short header
        for v in blk: byte(v, out)
    silence(1.0, out)
    w = wave.open(wav, 'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(RATE)
    w.writeframes(out.tobytes()); w.close()
    print('%s: %d blocks, %.1f s' % (wav, len(pos), len(out) / RATE))
if __name__ == '__main__':
    convert(sys.argv[1], sys.argv[2])
