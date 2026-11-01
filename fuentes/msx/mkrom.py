# Cartridge (32K ROM) version of ANUBIS for MSX1: the loader in page 1 copies the game to RAM
# (C000-F310 from page 2, then page 2 is switched to RAM and 8500-BFFF is copied from page 1)
import subprocess
B = 0x8500
d = open('anubis_new.bin', 'rb').read()
p1, p2 = d[:0xC000 - B], d[0xC000 - B:]
ASM = r'''
        org 4000h
        db 'AB'
        dw INIT
        dw 0,0,0
        ds 6
INIT:   di
        ld sp,0F37Eh
        call 0138h              ; RSLREG: our slot (page 1) -> also page 2
        rrca
        rrca
        and 3
        ld c,a
        ld b,0
        ld hl,0FCC1h            ; EXPTBL
        add hl,bc
        ld a,(hl)
        and 80h
        or c
        ld c,a
        inc hl
        inc hl
        inc hl
        inc hl                  ; SLTTBL
        ld a,(hl)
        and 0Ch
        or c
        ld h,80h
        call 0024h              ; ENASLT
        ld hl,8000h             ; page 2 (ROM) -> C000..
        ld de,0C000h
        ld bc,{LEN2}
        ldir
        call 0138h              ; page 2 := the RAM slot of page 3
        rlca
        rlca
        and 3
        ld c,a
        ld b,0
        ld hl,0FCC1h
        add hl,bc
        ld a,(hl)
        and 80h
        jr z,NOEXP
        or c
        ld c,a
        ld a,(0FFFFh)
        cpl
        rrca
        rrca
        rrca
        rrca
        and 0Ch
        or c
        ld c,a
NOEXP:  ld a,c
        ld h,80h
        call 0024h
        ld hl,DATA1
        ld de,8500h
        ld bc,{LEN1}
        ldir
        ei
        jp 8500h
DATA1:
'''
open('rom.asm', 'w').write(ASM.format(LEN1=len(p1), LEN2=len(p2)))
subprocess.run(['pasmo', '--bin', 'rom.asm', 'rom_loader.bin'], check=True)
ld = open('rom_loader.bin', 'rb').read()
page1 = ld + p1
assert len(page1) <= 0x4000, len(page1)
rom = page1 + bytes(0x4000 - len(page1)) + p2 + bytes(0x4000 - len(p2))
open('ANUBIS_EGIPTO.rom', 'wb').write(rom)
print('ROM 32K: loader %d bytes, page1 free %d, page2 free %d' % (len(ld), 0x4000 - len(page1), 0x4000 - len(p2)))
