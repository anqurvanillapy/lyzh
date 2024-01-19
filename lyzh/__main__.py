import sys
import typing

import lyzh.surf.parsec as parsec
import lyzh.surf.grammar as grammar
import lyzh.conc.resolve as resolve


def fatal(m: str | Exception) -> typing.Never:
    print(m)
    sys.exit(1)


try:
    _, file, *_ = sys.argv
except ValueError:
    fatal("usage: lyzh FILE")

try:
    defs = grammar.parse_file(file)
except parsec.Error as e:
    fatal(f"{file}:{e}")
except FileNotFoundError as e:
    fatal(e)

try:
    print(resolve.Resolver().resolve(defs))
except resolve.Error as e:
    fatal(f"{file}:{e}")
