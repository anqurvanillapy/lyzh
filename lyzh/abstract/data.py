"""Abstract syntax, 这个层级的值能够被深度求值, 但也可能是没法继续求值的形式, 即 normal form."""

import dataclasses
import typing

import lyzh.core as core


@dataclasses.dataclass
class Term: ...


@dataclasses.dataclass
class Ref(Term):
    """变量引用."""

    v: core.Var

    def __str__(self):
        return str(self.v)


@dataclasses.dataclass
class Univ(Term):
    """类型宇宙."""

    def __str__(self):
        return "type"


@dataclasses.dataclass
class FnType(Term):
    """函数类型."""

    p: core.Param[Term]
    body: Term

    def __str__(self):
        return f"{self.p} -> {self.body}"


@dataclasses.dataclass
class Fn(Term):
    """函数."""

    p: core.Param[Term]  # 此时函数的参数类型确定
    body: Term

    def __str__(self):
        return f"|{self.p}| {{ {self.body} }}"


@dataclasses.dataclass
class App(Term):
    """函数应用."""

    f: Term
    x: Term

    def __str__(self):
        return f"({self.f} {self.x})"


type Globals = typing.Dict[core.ID, core.Def[Term]]
"""全局变量定义, 在学术中叫做 Sigma, ∑, 其实就是 global context."""

type Locals = typing.Dict[core.ID, Term]
"""本地变量定义, 在学术中叫做 Gamma, Γ (对, 论文里最常出现的那个), 其实就是 local context,
注意这里的映射值的结构是 Term, 但实际上它只能是该变量的类型 (type term), 不能是一个值 (value
term)."""
