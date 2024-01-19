import dataclasses
import typing


@dataclasses.dataclass
class Loc:
    pos: int = 0
    ln: int = 1
    col: int = 1

    def __str__(self):
        return f"{self.ln}:{self.col}"

    def next_line(self):
        self.pos += 1
        self.ln += 1
        self.col = 1

    def next_column(self):
        self.pos += 1
        self.col += 1


type ID = int


@dataclasses.dataclass
class Var:
    text: str = ""
    id: ID = 0

    def __str__(self):
        return self.text


@dataclasses.dataclass
class IDs:
    n: ID = 0

    def next(self) -> ID:
        self.n += 1
        return self.n

    def rename(self, v: Var) -> Var:
        return Var(v.text, self.next())


@dataclasses.dataclass
class Param[T]:
    name: Var
    type: T

    def __str__(self):
        return f"({self.name}: {self.type})"


type Params[T] = typing.List[Param[T]]


@dataclasses.dataclass
class Def[T]:
    loc: Loc
    name: Var
    params: Params[T]
    ret: T
    body: T

    def __str__(self):
        params = " ".join(str(p) for p in self.params)
        return f"fn {self.name}{params} -> {self.ret} {{\n\t{self.body}\n}}"


type Defs[T] = typing.List[Def[T]]
