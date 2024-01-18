import typing

import lyzh.conc.data as conc
import lyzh.core as core
import lyzh.parsing as parsing


def parse_file(f: str) -> typing.List[core.Def[conc.Expr]]:
    with open(f) as f:
        return parse_text(f.read())


def parse_text(text: str) -> typing.List[core.Def[conc.Expr]]:
    defs = []
    prog(defs)(parsing.Source(text))
    return defs


DEF = parsing.word("fn")
TYPE = parsing.word("type")
LPAREN = parsing.word("(")
RPAREN = parsing.word(")")
COLON = parsing.word(":")
ARROW = parsing.word("->")
PIPE = parsing.word("|")
LBRACE = parsing.word("{")
RBRACE = parsing.word("}")


def prog(ds: typing.List[core.Def[conc.Expr]]) -> parsing.Parser:
    def parse(s: parsing.Source) -> parsing.Source:
        return parsing.seq(parsing.soi, parsing.many(defn(ds)), parsing.eoi)(s)

    return parse


def defn(ds: typing.List[core.Def[conc.Expr]]) -> parsing.Parser:
    def parse(s: parsing.Source) -> parsing.Source:
        loc = s.cur()
        name = core.Var()
        ps = []
        ret = ExprParser()
        body = ExprParser()
        s = parsing.seq(
            DEF,
            parsing.ident(name),
            parsing.many(param(ps)),
            ARROW,
            ret.expr(),
            LBRACE,
            body.expr(),
            RBRACE,
        )(s)
        ds.append(core.Def(loc, name, ps, ret.e, body.e))
        return s

    return parse


def param(ps: core.Params) -> parsing.Parser:
    def parse(s: parsing.Source) -> parsing.Source:
        v = core.Var()
        typ = ExprParser()
        s = parsing.seq(LPAREN, parsing.ident(v), COLON, typ.expr(), RPAREN)(s)
        ps.append(core.Param(v, typ.e))
        return s

    return parse


class ExprParser:
    e: typing.Optional[conc.Expr] = None

    def expr(self) -> parsing.Parser:
        def parse(s: parsing.Source) -> parsing.Source:
            return parsing.choice(
                self.fn(),
                self.fn_type(),
                self.univ(),
                self.app(),
                self.ref(),
                self.paren_expr(),
            )(s)

        return parse

    def primary_expr(self) -> parsing.Parser:
        def parse(s: parsing.Source) -> parsing.Source:
            return parsing.choice(self.fn(), self.ref(), self.paren_expr())(s)

        return parse

    def fn(self) -> parsing.Parser:
        def parse(s: parsing.Source) -> parsing.Source:
            """fn"""
            loc = s.cur()
            x = core.Var()
            body = ExprParser()
            s = parsing.seq(
                PIPE,
                parsing.ident(x),
                PIPE,
                LBRACE,
                body.expr(),
                RBRACE,
            )(s)
            self.e = conc.Fn(loc, x, body.e)
            return s

        return parse

    def app(self) -> parsing.Parser:
        def parse(s: parsing.Source) -> parsing.Source:
            """app"""
            loc = s.cur()
            f = ExprParser()
            x = ExprParser()
            s = parsing.seq(f.primary_expr(), x.expr())(s)
            self.e = conc.App(loc, f.e, x.e)
            return s

        return parse

    def fn_type(self) -> parsing.Parser:
        def parse(s: parsing.Source) -> parsing.Source:
            """fn_type"""
            loc = s.cur()
            ps = []
            body = ExprParser()
            s = parsing.seq(param(ps), ARROW, body.expr())(s)
            self.e = conc.FnType(loc, ps[0], body.e)
            return s

        return parse

    def univ(self) -> parsing.Parser:
        def parse(s: parsing.Source) -> parsing.Source:
            """univ"""
            loc = s.cur()
            s = TYPE(s)
            self.e = conc.Univ(loc)
            return s

        return parse

    def ref(self) -> parsing.Parser:
        def parse(s: parsing.Source) -> parsing.Source:
            """ref"""
            loc = s.cur()
            v = core.Var()
            s = parsing.ident(v)(s)
            self.e = conc.Unresolved(loc, v)
            return s

        return parse

    def paren_expr(self) -> parsing.Parser:
        def parse(s: parsing.Source) -> parsing.Source:
            """paren_expr"""
            return parsing.seq(LPAREN, self.expr(), RPAREN)(s)

        return parse
