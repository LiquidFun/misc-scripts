#!/usr/bin/python
# This is a simple command line script to roll dice. Supports multiple rolls per call as well
# as advantage and disadvantage. See the test function on how to use.

import re
import random
import sys
from collections import defaultdict


DEBUG = False

def test():
    expect("d20", 4)
    expect("adv 100d20", 20)
    expect("adv 3d20", 9)
    expect("2d12+10", 23)
    expect("+6d27+100-123", 44)
    expect("dis 2d20+6", 7)
    expect("adv 2d20+4", 8)
    expect("adv 2d20+4; 4-2d21 +18; sum 26d6", [8, 5, 92])

prefix_to_func = defaultdict(
    lambda: sum,
    adv=max,
    advantage=max,
    dis=min,
    disadv=min,
    disadvantage=min,
    sum=sum,
)

def debug(*args, **kwargs):
    if DEBUG:
        print(*args, **kwargs)

def d(sides: int, *, dice: int = 1):
    return [random.randint(1, sides) for _ in range(dice)]

def roll(text: str, noprint=False) -> int | list[int]:
    if not noprint:
        print()
    subrolls = text.replace(" ", "").split(";")
    result = []
    prefixes = '|'.join(list(prefix_to_func.keys() - {None}))
    debug(text)
    for subroll in subrolls:
        debug("  ", subroll)
        result.append(0)
        for subsum in re.findall(r"[-+]?[0-9a-zA-Z]+", subroll):
            debug("    ", subsum)

            if matches := re.fullmatch(rf"([-+])?({prefixes})?(\d+)?[dD](\d+)", subsum):
                sign, prefix, dice, sides = matches.groups()
                sign = -1 if sign == "-" else 1
                func = prefix_to_func[prefix]
                dice = int(dice or 1)
                sides = int(sides)
                rolls = d(sides, dice=dice)
                if not noprint:
                    print("  •", f"{dice}d{sides}=", rolls, f"--{func.__name__}-->", func(rolls))
                result[-1] += sign * func(rolls)
                debug("      ", matches.groups())

            elif re.fullmatch(r"[-+]?\d+", subsum):
                result[-1] += int(subsum)
                if not noprint:
                    print("  •", subsum)

            else:
                debug(f"Ignoring {subroll}")

        if not noprint:
            print(" ", subroll, "=", result[-1])

    if not noprint:
        print(result, "rolled from", text)
    return result[0] if len(result) == 1 else result

def expect(text: str, expected: int | list[int]):
    random.seed(42)
    assert (rolled := roll(text, noprint=True)) == expected, \
        f"Rolled: {rolled}, but expected: {expected}"

def main():
    roll(' '.join(sys.argv[1:]) or "d20")

if __name__ == "__main__":
    main()
    test()
