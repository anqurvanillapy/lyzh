import dataclasses
import typing

import lyzh.core as core


@dataclasses.dataclass
class Term:
    pass


@dataclasses.dataclass
class Ref(Term):
    v: core.Var

    def __str__(self):
        return str(self.v)


@dataclasses.dataclass
class Univ(Term):
    pass

    def __str__(self):
        return "type"


@dataclasses.dataclass
class FnType(Term):
    p: core.Param[Term]
    body: Term

    def __str__(self):
        return f"{self.p} -> {self.body}"


@dataclasses.dataclass
class Fn(Term):
    p: core.Param[Term]
    body: Term

    def __str__(self):
        return f"|{self.p}| {{ {self.body} }}"


@dataclasses.dataclass
class App(Term):
    f: Term
    x: Term

    def __str__(self):
        return f"({self.f} {self.x})"


type Globals = typing.Dict[core.ID, core.Def[Term]]

type Locals = typing.Dict[core.ID, Term]
