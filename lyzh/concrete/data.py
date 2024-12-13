"""Concrete syntax, 这里的定义携带了位置信息, 并且可以用于深入求值计算."""

import dataclasses

import lyzh.core as core


@dataclasses.dataclass
class Expr:
    """表达式父类."""

    loc: core.Loc


@dataclasses.dataclass
class Fn(Expr):
    """Function, 函数表达式, 也就是 lambda 表达式."""

    v: core.Var  # 只有名字, 不需要标明类型
    body: Expr


@dataclasses.dataclass
class App(Expr):
    """Function application, 函数应用表达式."""

    f: Expr
    x: Expr


@dataclasses.dataclass
class FnType(Expr):
    """Function type, 函数类型表达式, 也就是学术里的 Pi type 和 dependent function type."""

    p: core.Param
    body: Expr


# Universe, 类型宇宙表达式, 也就是学术里的 type of type, 类型的类型.
@dataclasses.dataclass
class Univ(Expr): ...


@dataclasses.dataclass
class Unresolved(Expr):
    """未进行作用域检查的变量引用表达式."""

    v: core.Var


@dataclasses.dataclass
class Resolved(Expr):
    """通过作用域检查后的变量引用表达式."""

    v: core.Var
