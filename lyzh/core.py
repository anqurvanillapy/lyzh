"""\
# Core

核心定义, 一些所有语法层级都使用得到的实用类.
"""

import dataclasses
import typing


@dataclasses.dataclass
class Loc:
    """Source location, 源代码位置, 用于定位错误."""

    pos: int = 0  # position
    ln: int = 1  # line
    col: int = 1  # column

    def __str__(self):
        return f"{self.ln}:{self.col}"

    def next_line(self):
        """前进新的一行."""
        self.pos += 1
        self.ln += 1
        self.col = 1

    def next_column(self):
        """前进新的一列."""
        self.pos += 1
        self.col += 1


type ID = int
"""变量的 ID. 后续用到的技术叫做 capture-avoiding substitution. 和 de Bruijn index 与
de Bruijn level 不同的是, 这两个概念实际上是 local context (存放本地变量) 和 global
context (存放全局变量) 的变量索引. 那么我们可以使用一个全局唯一的 ID, 这样我们不需要在 local
和 global context 发生变动的时候 (如新增了一个变量定义) 去修改表达式内所有变量的引用."""


@dataclasses.dataclass
class Var:
    """变量, 包含变量的原文以及它的 ID."""

    text: str = ""
    id: ID = 0

    def __str__(self):
        return self.text


_NEXT_ID = 0


def fresh() -> ID:
    global _NEXT_ID
    _NEXT_ID += 1
    return _NEXT_ID


@dataclasses.dataclass
class Param[T]:
    """参数定义, 即变量和它的类型."""

    name: Var
    type: T

    def __str__(self):
        return f"({self.name}: {self.type})"


type Params[T] = typing.List[Param[T]]
"""参数列表, 学术里又叫做 telescope, context 等, 有趣的是, telescope 就是中文里面说的
"裂项", 至于为什么英文是 telescope, 可以假设你想看到天空中的某颗星星, 你手头有足量的 100
倍镜, 10 倍镜, 和 1 倍镜, 你凑合了这几类倍镜之后, 最终在 114 倍的情况下看到这颗星星最为清晰,
所以你可以认为观察天空中的星星是这么一个函数:

```
stargaze : (x : Scope100) -> (y : Scope10) -> (z : Scope1) -> Star
stargaze = ...

myStar : Star
myStar = stargaze 1 1 4
```

输入一系列参数的函数, 就像是把弄一个天文望远镜上的各种不同的焦距旋钮, 故此得名.
"""


@dataclasses.dataclass
class Def[T]:
    """即 definition, 一个函数定义.

    当 T 是 Expr 时, 它是个尚未通过类型检查的定义, 如果是 Term, 则是个类型安全 (well-typed)
    的定义."""

    loc: Loc
    name: Var
    params: Params[T]
    ret: T  # return type
    body: T

    def __str__(self):
        params = " ".join(str(p) for p in self.params)
        return f"fn {self.name}{params} -> {self.ret} {{\n\t{self.body}\n}}"


type Defs[T] = typing.List[Def[T]]
"""函数定义列表, 即一个文件."""
