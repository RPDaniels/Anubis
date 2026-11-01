# Extrae game.bin (binario original &H8500-&HF310) del CAS original del juego.
# Uso: copia el CAS original como orig.cas en esta carpeta y ejecuta: python3 extract.py
import struct
d = open('orig.cas', 'rb').read()
b = d[32:]                                  # 2.º bloque: cabecera binaria + datos
start, end, exe = struct.unpack('<HHH', b[:6])
open('game.bin', 'wb').write(b[6:6 + end - start + 1])
print('game.bin %04X-%04X, exec %04X' % (start, end, exe))
