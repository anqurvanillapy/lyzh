import dataclasses

import lyzh.core as core


@dataclasses.dataclass
class Expr:
    loc: core.Loc


@dataclasses.dataclass
class Fn(Expr):
    v: core.Var
    body: Expr


@dataclasses.dataclass
class App(Expr):
    f: Expr
    x: Expr


@dataclasses.dataclass
class FnType(Expr):
    p: core.Param
    body: Expr


@dataclasses.dataclass
class Univ(Expr):
    pass


@dataclasses.dataclass
class Unresolved(Expr):
    v: core.Var


@dataclasses.dataclass
class Resolved(Expr):
    v: core.Var
