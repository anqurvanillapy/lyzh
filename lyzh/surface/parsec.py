"""一个简单的解析器组合子, 其实就是一堆好用的文本解析实用类. 建议使用报错更友好的库和框架来替代,
这个文件可以跳过不看."""

import dataclasses
import typing

import lyzh.core as core


class Error(Exception): ...


@dataclasses.dataclass
class Source:
    """源码解析状态, 可以认为是个不严格的 monad."""

    src: str  # 源码文本
    ids: core.IDs
    loc: core.Loc = dataclasses.field(default_factory=core.Loc)
    last_err: typing.Optional[Error] = None  # 上一个发生的错误, 另见 back 方法

    def cur(self) -> core.Loc:
        """当前位置, 注意这里创建了新的 Loc."""
        return core.Loc(self.loc.pos, self.loc.ln, self.loc.col)

    def text(self, start: core.Loc) -> str:
        """返回起始位置到当前位置的文本."""
        return self.src[start.pos : self.loc.pos]

    def peek(self) -> typing.Optional[str]:
        """相当于 lookahead, 往前查看一个字符."""
        if self.loc.pos >= len(self.src):
            return None
        return self.src[self.loc.pos]

    def next(self) -> typing.Optional[str]:
        """获得下一个字符, 如果成功, 则让解析状态往前."""
        c = self.peek()
        if not c:
            return None
        if c == "\n":
            self.loc.next_line()
        else:
            self.loc.next_column()
        return c

    def eat(self, c: str) -> typing.Self:
        """期盼下一个字符是 c, 如果不是则报错."""
        loc = self.cur()
        n = self.next()
        if n != c:
            raise Error(f"{loc}: expected '{c}', got '{n}'")
        return self

    def skip_spaces(self) -> typing.Self:
        """跳过空白字符."""
        while True:
            c = self.peek()
            if not c or not c.isspace():
                break
            self.eat(c)
        return self

    def back(self, loc: core.Loc, e: Error) -> typing.Self:
        """在遇到错误 e 时, 恢复到指定的位置, 通常是上一个开始解析的位置, 这里 e 存入到
        last_err 中, 如果遇到了致命的无法恢复的错误, 则可以抛出 last_err."""
        self.loc = core.Loc(loc.pos, loc.ln, loc.col)
        self.last_err = e
        return self


type Parser = typing.Callable[[Source], Source]
"""解析方法类型, 串联起解析状态的扭转."""


def soi(s: Source) -> Source:
    """期盼当前解析状态为起始状态."""
    if s.loc.pos != 0:
        raise Error(f"{s.loc}: expected start of input")
    return s


def eoi(s: Source) -> Source:
    """期盼当前解析状态为结束状态."""
    if s.loc.pos != len(s.src):
        if s.last_err:  # 此时错误被认为是致命错误
            raise s.last_err
        raise Error(f"{s.loc}: expected end of input")
    return s


def word(w: str) -> Parser:
    """解析关键词 w."""

    def parse(s: Source) -> Source:
        try:
            for c in w:
                s = s.eat(c)
            return s
        except Error:
            raise Error(f"{s.loc}: expected '{w}'")

    return parse


def ident(v: core.Var) -> Parser:
    """解析一个标识符, 风格是 lower_case, 这里不允许第一个字符是下划线."""

    def parse(s: Source) -> Source:
        start = s.cur()

        # 第一个只能是小写字母.
        first = s.peek()
        if not first or not first.islower() or not first.isalpha():
            raise Error(f"{s.loc}: expected identifier")
        s = s.eat(first)

        # 后续可以是小写字母, 数字, 下划线.
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
    """Sequence, 运行一批解析方法, 类似 all, 需要保证所有解析方法都成功, 中间可跳过空格."""

    def parse(s: Source) -> Source:
        for i, p in enumerate(parsers):
            s = p(s)
            if i != len(parsers) - 1:
                s = s.skip_spaces()
        return s

    return parse


def choice(*parsers: Parser) -> Parser:
    """尝试运行一批解析方法, 类似 any, 任意解析方法成功则成功, 失败则回溯到上一个解析状态."""

    def parse(s: Source) -> Source:
        loc = s.cur()
        for p in parsers:
            try:
                s = p(s)
                return s
            except Error as e:
                s = s.back(loc, e)
        # 所有解析方法都失败, 用 docstring 作为解析方法的规则名, 拼接错误信息抛出.
        msg = ", ".join([p.__doc__ for p in parsers])
        raise Error(f"{s.loc}: expected {msg}")

    return parse


def many(p: Parser) -> Parser:
    """尝试运行 0 次或多次解析方法, 类似 `*` (闭包), 失败一次则停止并回到上一个解析状态."""

    def parse(s: Source) -> Source:
        while True:
            loc = s.cur()
            try:
                s = p(s)
            except Error as e:
                return s.back(loc, e)
            s = s.skip_spaces()

    return parse
