after time 30 {press 0 0x20 0.08}
after time 31 {type "105\r"}
after time 33 {record start -audioonly /tmp/claude-0/jet/jet.wav}
after time 33.5 {keymatrixdown 8 0x20}
after time 34.2 {puts stderr "DUMP up psg=[debug read_block {PSG regs} 0 11] y=[debug read VRAM 0x1B00]"; dump j0}
after time 35.5 {keymatrixup 8 0x20}
after time 36.5 {puts stderr "DUMP rel psg=[debug read_block {PSG regs} 0 11] y=[debug read VRAM 0x1B00]"}
after time 37 {record stop}
after time 37.2 exit
