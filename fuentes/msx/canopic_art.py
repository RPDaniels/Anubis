# The four canopic jars: 16x16 sprite (in the room, gold) and 8x16 icon (status bar, blue faience)
BODY16 = ['....########....',
          '...##########...',
          '...##########...',
          '...#.#.##.#.#...',
          '...##########...',
          '....########....',
          '.....######.....',
          '....########....']
HEADS16 = {
 'Imsety':      ['.....######.....',
                 '....########....',
                 '...###....###...',
                 '...##.#..#.##...',
                 '...##......##...',
                 '...##..##..##...',
                 '...##..##..##...',
                 '.......##.......'],
 'Hapy':        ['................',
                 '..###.####.###..',
                 '..##.######.##..',
                 '..##.#.##.#.##..',
                 '...#.######.#...',
                 '.....##..##.....',
                 '......####......',
                 '.......##.......'],
 'Duamutef':    ['....#....#......',
                 '....##..##......',
                 '....######......',
                 '....#.#######...',
                 '....##########..',
                 '.....#####......',
                 '......####......',
                 '.......##.......'],
 'Qebehsenuef': ['......####......',
                 '.....######.....',
                 '....##.#####....',
                 '....#########...',
                 '....######.##...',
                 '.....#####..#...',
                 '......####......',
                 '.......##.......'],
}
NAMES = ['Imsety', 'Hapy', 'Duamutef', 'Qebehsenuef']
def sprite(name):
    return HEADS16[name] + BODY16
# status-bar icon: head char (8x8) per jar + one shared body char
HEADS8 = {
 'Imsety':      ['..###...', '.#####..', '.#.#.#..', '.#####..', '#.###.#.', '#..#..#.', '.#####..', '#######.'],
 'Hapy':        ['........', '#.###.#.', '#######.', '.#.#.#..', '.#####..', '..###...', '.#####..', '#######.'],
 'Duamutef':    ['.#...#..', '.##.##..', '.#####..', '.#.####.', '..#####.', '...##...', '.#####..', '#######.'],
 'Qebehsenuef': ['..###...', '.#####..', '.#.####.', '.######.', '..###.#.', '...#....', '.#####..', '#######.'],
}
BODY8 = ['#.#.#.#.', '#######.', '#######.', '.#####..', '.#####..', '..###...', '.#####..', '........']
HEAD_CHARS = [0x40, 0x46, 0x4A, 0x4B]   # letters @ F J K: no text of the game uses them (groups 0x40/0x48, white)
BODY_CHAR = 0x57                        # letter W, also unused (group 0x50, white)
# empty slot in the status bar until the jar is found: jar outline, cyan (free chars '.' and '/', group 0x28)
SLOT_HEAD, SLOT_BODY = 0x2E, 0x2F
SLOT8 = ['..###...', '.#...#..', '.#...#..', '..#.#...', '..#.#...', '.#...#..', '.#####..', '#.....#.']
SLOTB8 = ['#.....#.', '#.....#.', '.#...#..', '.#...#..', '..#.#...', '.#...#..', '.#####..', '........']
# title hint (no letter of it may be one of the icon letters, which the title copies from the game font)
HINT = 'ENCUENTRA LOS 4 VASOS CANOPOS'
# lotus message (it must not use the letters above)
MESSAGE = 'NECESITAS LOS CUATRO VASOS'
assert not (set(MESSAGE) | set(HINT)) & {chr(x) for x in HEAD_CHARS + [BODY_CHAR]}
