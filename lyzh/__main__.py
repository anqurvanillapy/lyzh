import sys
import typing

import lyzh.concrete.resolve as resolve
import lyzh.core as core
import lyzh.surface.grammar as grammar
import lyzh.surface.parsec as parsec


def fatal(m: str | Exception) -> typing.Never:
    print(m)
    sys.exit(1)


ids = core.IDs()
defs = []

try:
    _, file, *_ = sys.argv
except ValueError:
    fatal("usage: lyzh FILE")

try:
    with open(file) as f:
        grammar.prog(defs)(parsec.Source(f.read(), ids))
except FileNotFoundError as e:
    fatal(e)
except parsec.Error as e:
    fatal(f"{file}:{e}")

try:
    print(resolve.Resolver().resolve(defs))
except resolve.Error as e:
    fatal(f"{file}:{e}")
