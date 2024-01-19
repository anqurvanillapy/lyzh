import dataclasses
import typing

import lyzh.core as core


class Error(Exception):
    pass


@dataclasses.dataclass
class Source:
    src: str
    ids: core.IDs
    loc: core.Loc = dataclasses.field(default_factory=core.Loc)
    last_err: typing.Optional[Error] = None

    def cur(self) -> core.Loc:
        return core.Loc(self.loc.pos, self.loc.ln, self.loc.col)

    def text(self, start: core.Loc) -> str:
        return self.src[start.pos : self.loc.pos]

    def peek(self) -> typing.Optional[str]:
        if self.loc.pos >= len(self.src):
            return None
        return self.src[self.loc.pos]

    def next(self) -> typing.Optional[str]:
        c = self.peek()
        if not c:
            return None
        if c == "\n":
            self.loc.next_line()
        else:
            self.loc.next_column()
        return c

    def eat(self, c: str) -> typing.Self:
        loc = self.cur()
        n = self.next()
        if n != c:
            raise Error(f"{loc}: expected '{c}', got '{n}'")
        return self

    def skip_spaces(self) -> typing.Self:
        while True:
            c = self.peek()
            if not c or not c.isspace():
                break
            self.eat(c)
        return self

    def back(self, loc: core.Loc, e: Error) -> typing.Self:
        self.loc = core.Loc(loc.pos, loc.ln, loc.col)
        self.last_err = e
        return self


type Parser = typing.Callable[[Source], Source]


def soi(s: Source) -> Source:
    if s.loc.pos != 0:
        raise Error(f"{s.loc}: expected start of input")
    return s


def eoi(s: Source) -> Source:
    if s.loc.pos != len(s.src):
        if s.last_err:
            raise s.last_err
        raise Error(f"{s.loc}: expected end of input")
    return s


def word(w: str) -> Parser:
    def parse(s: Source) -> Source:
        for c in w:
            s = s.eat(c)
        return s

    return parse


def ident(v: core.Var) -> Parser:
    def parse(s: Source) -> Source:
        start = s.cur()

        first = s.peek()
        if not first or not first.islower() or not first.isalpha():
            raise Error(f"{s.loc}: expected identifier")
        s = s.eat(first)

        while True:
            c = s.peek()
            if not c:
                break
            if not (c.islower() or c.isalnum()) and c != "_":
                break
            s = s.eat(c)

        v.text = s.text(start)
        v.id = s.ids.next()
        return s

    return parse


def seq(*parsers: Parser) -> Parser:
    def parse(s: Source) -> Source:
        for i, p in enumerate(parsers):
            s = p(s)
            if i != len(parsers) - 1:
                s = s.skip_spaces()
        return s

    return parse


def choice(*parsers: Parser) -> Parser:
    def parse(s: Source) -> Source:
        loc = s.cur()
        for p in parsers:
            try:
                s = p(s)
                return s
            except Error as e:
                s = s.back(loc, e)
        msg = ", ".join([r.__doc__ for r in parsers])
        raise Error(f"{s.loc}: expected {msg}")

    return parse


def many(p: Parser) -> Parser:
    def parse(s: Source) -> Source:
        while True:
            loc = s.cur()
            try:
                s = p(s)
            except Error as e:
                return s.back(loc, e)
            s = s.skip_spaces()

    return parse
