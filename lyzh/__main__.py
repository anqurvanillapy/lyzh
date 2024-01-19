"""命令行入口."""

import sys
import typing

import lyzh.concrete.resolve as resolve
import lyzh.concrete.data as cst
import lyzh.concrete.elab as elab
import lyzh.core as core
import lyzh.surface.grammar as grammar
import lyzh.surface.parsec as parsec


def fatal(m: str | Exception) -> typing.Never:
    print(m)
    sys.exit(1)


ids = core.IDs()
defs: core.Defs[cst.Expr] = []  # 尚未检查类型的定义

# 获取文件名.
try:
    _, file, *_ = sys.argv
except ValueError:
    fatal("usage: lyzh FILE")

try:
    # 加载源文件, 并解析出所有定义.
    with open(file) as f:
        grammar.prog(defs)(parsec.Source(f.read(), ids))
    # 解析所有定义中的引用, 并开始类型检查.
    well_typed = elab.Elaborator(ids).elaborate(resolve.Resolver().resolve(defs))
    print("\n\n".join(str(d) for d in well_typed))
except FileNotFoundError as e:
    fatal(e)
except (parsec.Error, resolve.Error, elab.Error) as e:
    fatal(f"{file}:{e}")
