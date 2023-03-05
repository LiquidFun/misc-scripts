#!/usr/bin/python
# This is a simple command line script to roll dice. Supports multiple rolls per call as well
# as advantage and disadvantage. See the test function on how to use.

import re
import random
import sys
from collections import defaultdict
import operator


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


operators = {
    "<": operator.lt,
    "<=": operator.le,
    ">": operator.gt,
    ">=": operator.ge,
    "==": operator.eq,
    "!=": operator.ne,
}

prefix_to_func = defaultdict(
    lambda: sum,
    adv=max,
    advantage=max,
    dis=min,
    disadv=min,
    disadvantage=min,
    sum=sum,
)

_prefixes = '|'.join(list(prefix_to_func.keys() - {None}))
roll_pattern = re.compile(rf"([-+])?({_prefixes})?(\d+)?[dD](\d+)")

def debug(*args, **kwargs):
    if DEBUG:
        print(*args, **kwargs)

def d(sides: int, *, dice: int = 1):
    return [random.randint(1, sides) for _ in range(dice)]

def basic_roll(subroll: str, noprint=False):
    result = 0

    for subsum in re.findall(r"[-+]?[0-9a-zA-Z]+", subroll):
        debug("    ", subsum)
        if matches := roll_pattern.fullmatch(subsum):
            sign, prefix, dice, sides = matches.groups()
            sign = -1 if sign == "-" else 1
            func = prefix_to_func[prefix]
            dice = int(dice or 1)
            sides = int(sides)
            rolls = d(sides, dice=dice)
            if not noprint:
                print("  •", f"{dice}d{sides}=", rolls, f"--{func.__name__}-->", func(rolls))
            result += sign * func(rolls)
            debug("      ", matches.groups())

        elif re.fullmatch(r"[-+]?\d+", subsum):
            result += int(subsum)
            if not noprint:
                print("  •", subsum)

        else:
            debug(f"Ignoring {subroll}")
    return result

def roll(text: str, noprint=False) -> int | list[int]:
    if not noprint:
        print()
    subrolls = text.replace(" ", "").split(";")
    result = []
    debug(text)
    for subroll in subrolls:
        matches = re.fullmatch(r"(?:(\d+)x)?(.*?)([<>=!]+\d+)?(-->x?.*?)?", subroll)
        times = int(matches.group(1) or 1)
        subroll = matches.group(2)
        DC = matches.group(3)
        damage = matches.group(4)

        debug("  ", subroll)
        subresult = []
        for _ in range(times):
            subresult.append(basic_roll(subroll))

            if not noprint:
                print(" ", subroll, "=", subresult[-1])
        if DC:
            op, dc = re.fullmatch(r"([<>=!]+)(\d+)", DC).groups()
            subresult = [len([num for num in subresult if operators[op](num, int(dc))])]

        if damage:
            assert len(subresult) == 1
            subresult = [roll(str(subresult[0])+damage[3:])]

        result.extend(subresult)

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
    # test()
