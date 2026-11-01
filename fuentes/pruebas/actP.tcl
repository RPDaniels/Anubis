proc st {tag} { puts stderr "ST $tag room=[debug read memory 0xf304] lives=[debug read memory 0x8af1] score=[debug read_block memory 0xcd4b 4] exfl=[debug read memory 0xde78]" }
after time 30 {press 0 0x20 0.3}
after time 32 {type "177\r"}
after time 35 {st a177; dump a177}
after time 35.2 {press 8 0x10 1.6}
after time 37.2 {st b177; dump b177}
after time 37.5 {press 0 0x20 0.3}
after time 38 exit
