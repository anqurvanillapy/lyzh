import dataclasses
import typing


@dataclasses.dataclass
class Loc:
    pos: int = 0
    ln: int = 1
    col: int = 1

    def next_line(self):
        self.pos += 1
        self.ln += 1
        self.col = 1

    def next_column(self):
        self.pos += 1
        self.col += 1


type ID = int


@dataclasses.dataclass
class IDs:
    n: ID = 0

    def next(self) -> ID:
        self.n += 1
        return self.n


@dataclasses.dataclass
class Var:
    name: str = ""
    id: ID = 0


@dataclasses.dataclass
class Param[T]:
    name: Var
    type: T


type Params[T] = typing.List[Param[T]]


@dataclasses.dataclass
class Def[T]:
    name: Var
    params: Params[T]
    ret: T
    body: T


type Defs = typing.List[Def]
