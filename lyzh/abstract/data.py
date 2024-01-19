import dataclasses
import typing

import lyzh.core as core


@dataclasses.dataclass
class Term:
    pass


@dataclasses.dataclass
class Ref(Term):
    v: core.Var


@dataclasses.dataclass
class Univ(Term):
    pass


@dataclasses.dataclass
class FnType(Term):
    p: core.Param[Term]
    body: Term


@dataclasses.dataclass
class Fn(Term):
    p: core.Param[Term]
    body: Term


@dataclasses.dataclass
class App(Term):
    f: Term
    x: Term


type Globals = typing.Dict[core.ID, core.Def[Term]]
