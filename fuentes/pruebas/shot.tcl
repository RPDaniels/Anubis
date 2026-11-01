set throttle off
proc load_game {} {
  set f [open $::env(GAMEBIN) rb]; set data [read $f]; close $f
  debug write_block memory 0x8500 $data
  reg sp 0xF37E
  reg pc 0x8500
}
proc dump {name} {
  set d $::env(OUTDIR)
  set f [open $d/$name.vram wb]; puts -nonewline $f [debug read_block VRAM 0 16384]; close $f
  set f [open $d/$name.regs wb]; puts -nonewline $f [debug read_block {VDP regs} 0 8]; close $f
  set f [open $d/$name.ram wb]; puts -nonewline $f [debug read_block memory 0 65536]; close $f
  puts stderr "DUMP $name pc=[format %x [reg pc]]"
}
proc press {row mask t} { keymatrixdown $row $mask; after time $t "keymatrixup $row $mask" }
after time 6 load_game
source $::env(ACTIONS)
