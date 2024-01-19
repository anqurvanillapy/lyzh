import typing

import lyzh.conc.data as conc
import lyzh.core as core
import lyzh.surf.parsec as parsec


def parse_file(f: str) -> typing.List[core.Def[conc.Expr]]:
    with open(f) as f:
        return parse_text(f.read())


def parse_text(text: str) -> typing.List[core.Def[conc.Expr]]:
    defs = []
    prog(defs)(parsec.Source(text))
    return defs


DEF = parsec.word("fn")
TYPE = parsec.word("type")
LPAREN = parsec.word("(")
RPAREN = parsec.word(")")
COLON = parsec.word(":")
ARROW = parsec.word("->")
PIPE = parsec.word("|")
LBRACE = parsec.word("{")
RBRACE = parsec.word("}")


def prog(ds: typing.List[core.Def[conc.Expr]]) -> parsec.Parser:
    def parse(s: parsec.Source) -> parsec.Source:
        return parsec.seq(parsec.soi, parsec.many(defn(ds)), parsec.eoi)(s)

    return parse


def defn(ds: typing.List[core.Def[conc.Expr]]) -> parsec.Parser:
    def parse(s: parsec.Source) -> parsec.Source:
        loc = s.cur()
        name = core.Var()
        ps = []
        ret = ExprParser()
        body = ExprParser()
        s = parsec.seq(
            DEF,
            parsec.ident(name),
            parsec.many(param(ps)),
            ARROW,
            ret.expr(),
            LBRACE,
            body.expr(),
            RBRACE,
        )(s)
        ds.append(core.Def(loc, name, ps, ret.e, body.e))
        return s

    return parse


def param(ps: core.Params) -> parsec.Parser:
    def parse(s: parsec.Source) -> parsec.Source:
        v = core.Var()
        typ = ExprParser()
        s = parsec.seq(LPAREN, parsec.ident(v), COLON, typ.expr(), RPAREN)(s)
        ps.append(core.Param(v, typ.e))
        return s

    return parse


class ExprParser:
    e: typing.Optional[conc.Expr] = None

    def expr(self) -> parsec.Parser:
        def parse(s: parsec.Source) -> parsec.Source:
            return parsec.choice(
                self.fn(),
                self.fn_type(),
                self.univ(),
                self.app(),
                self.ref(),
                self.paren_expr(),
            )(s)

        return parse

    def primary_expr(self) -> parsec.Parser:
        def parse(s: parsec.Source) -> parsec.Source:
            return parsec.choice(self.fn(), self.ref(), self.paren_expr())(s)

        return parse

    def fn(self) -> parsec.Parser:
        def parse(s: parsec.Source) -> parsec.Source:
            """fn"""
            loc = s.cur()
            x = core.Var()
            body = ExprParser()
            s = parsec.seq(
                PIPE,
                parsec.ident(x),
                PIPE,
                LBRACE,
                body.expr(),
                RBRACE,
            )(s)
            self.e = conc.Fn(loc, x, body.e)
            return s

        return parse

    def app(self) -> parsec.Parser:
        def parse(s: parsec.Source) -> parsec.Source:
            """app"""
            loc = s.cur()
            f = ExprParser()
            x = ExprParser()
            s = parsec.seq(f.primary_expr(), x.expr())(s)
            self.e = conc.App(loc, f.e, x.e)
            return s

        return parse

    def fn_type(self) -> parsec.Parser:
        def parse(s: parsec.Source) -> parsec.Source:
            """fn_type"""
            loc = s.cur()
            ps = []
            body = ExprParser()
            s = parsec.seq(param(ps), ARROW, body.expr())(s)
            self.e = conc.FnType(loc, ps[0], body.e)
            return s

        return parse

    def univ(self) -> parsec.Parser:
        def parse(s: parsec.Source) -> parsec.Source:
            """univ"""
            loc = s.cur()
            s = TYPE(s)
            self.e = conc.Univ(loc)
            return s

        return parse

    def ref(self) -> parsec.Parser:
        def parse(s: parsec.Source) -> parsec.Source:
            """ref"""
            loc = s.cur()
            v = core.Var()
            s = parsec.ident(v)(s)
            self.e = conc.Unresolved(loc, v)
            return s

        return parse

    def paren_expr(self) -> parsec.Parser:
        def parse(s: parsec.Source) -> parsec.Source:
            """paren_expr"""
            return parsec.seq(LPAREN, self.expr(), RPAREN)(s)

        return parse
