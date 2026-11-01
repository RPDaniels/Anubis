proc st {tag} { puts stderr "ST $tag room=[debug read memory 0xf304] lives=[debug read memory 0x8af1] pc=[format %x [reg pc]]" }
after time 30 {press 0 0x20 0.3}
after time 32 {type "6\r"}
after time 34 {debug write memory 0x8af1 1; st a}
after time 36 {st b; dump d1}
after time 37 {st c; dump d2}
after time 38 {st c2; dump d3}
after time 42 {st d; dump go}
after time 43 {press 8 0x01 0.3}
after time 46 {st e; dump after}
after time 47 exit
