#!/usr/bin/env python3

import sys


def sequences(spec):
    return [
        f"\x1b]4;0;{spec}\x1b\\"
        f"\x1b]10;{spec}\x1b\\"
        f"\x1b]11;{spec}\x1b\\"
        f"\x1b]12;{spec}\x1b\\"
        f"\x1b]13;{spec}\x1b\\"
        f"\x1b]14;{spec}\x1b\\"
        f"\x1b]15;{spec}\x1b\\"
        f"\x1b]16;{spec}\x1b\\"
        f"\x1b]17;{spec}\x1b\\"
        f"\x1b]18;{spec}\x1b\\"
        f"\x1b]19;{spec}\x1b\\"
    ]


def test(specs):
    print(f"\nTesting with {specs}", end="")
    for spec in specs:
        for seq in sequences(spec):
            print(seq, end="")

    sys.stdout.flush()
    print(", press Ctrl+C to continue...")
    try:
        sys.stdin.read()
    except KeyboardInterrupt:
        pass


test(["?"])
test(["+?", "-?"])
