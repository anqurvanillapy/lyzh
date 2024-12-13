"""Surface syntax, 语言的文本语法, 模仿的 Rust 风格. 这个文件可以只看以下 EBNF 规则, 其他跳过不看.

EBNF 规则:

    prog = defn*

    defn = 'fn' ident param* '->' expr '{' expr '}'

    param = '(' ident ':' expr ')'

    expr = '|' ident '|' '{' expr '}'   # fn
         | param '->' expr              # fn_type
         | 'type'                       # univ
         | primary_expr expr            # app
         | ident                        # ref
         | '(' expr ')'                 # paren_expr

    primary_expr = ref
                 | paren_expr
"""

import typing

import lyzh.concrete.data as cst
import lyzh.core as core
import lyzh.surface.parsec as parsec

FN = parsec.word("fn")
TYPE = parsec.word("type")
LPAREN = parsec.word("(")
RPAREN = parsec.word(")")
COLON = parsec.word(":")
ARROW = parsec.word("->")
PIPE = parsec.word("|")
LBRACE = parsec.word("{")
RBRACE = parsec.word("}")


def prog(ds: core.Defs[cst.Expr]) -> parsec.Parser:
    """即 program, 解析一个文件的所有定义到 ds."""

    def parse(s: parsec.Source) -> parsec.Source:
        return parsec.seq(parsec.soi, parsec.many(defn(ds)), parsec.eoi)(s)

    return parse


def defn(ds: core.Defs[cst.Expr]) -> parsec.Parser:
    """解析一个函数定义, 成功则加入到 ds 中."""

    def parse(s: parsec.Source) -> parsec.Source:
        loc = (
            s.cur()
        )  # 这里拿到的是 fn 关键词的位置, 我懒了, 拿到 name 的位置报错更友好
        name = core.Var()
        ps = []
        ret = ExprParser()
        body = ExprParser()
        s = parsec.seq(
            FN,
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
    """解析一对参数, 并加入到 ps 中."""

    def parse(s: parsec.Source) -> parsec.Source:
        v = core.Var()
        typ = ExprParser()
        s = parsec.seq(LPAREN, parsec.ident(v), COLON, typ.expr(), RPAREN)(s)
        ps.append(core.Param(v, typ.e))
        return s

    return parse


class ExprParser:
    """表达式解析器, 解析成功时设置到 e 中, 因为没法用以上类似的方法修改出参, 所以用这个方式代替."""

    e: typing.Optional[cst.Expr] = None

    def expr(self) -> parsec.Parser:
        """解析表达式."""

        def parse(s: parsec.Source) -> parsec.Source:
            return parsec.choice(
                self.fn(),
                self.fn_type(),
                self.univ(),  # 必须在 ref 的前面, 不然会被解析成 ref
                self.app(),  # 必须在 ref 的前面, 不然会被解析成 ref
                self.ref(),
                self.paren_expr(),
            )(s)

        return parse

    def primary_expr(self) -> parsec.Parser:
        """简单表达式, 主要给 app 使用."""

        def parse(s: parsec.Source) -> parsec.Source:
            return parsec.choice(
                self.ref(),
                self.paren_expr(),
            )(s)

        return parse

    def fn(self) -> parsec.Parser:
        """函数表达式, 即 lambda."""

        def parse(s: parsec.Source) -> parsec.Source:
            """fn"""
            loc = s.cur()
            x = core.Var()
            body = ExprParser()
            s = parsec.seq(
                PIPE,
                parsec.ident(x),  # 只支持一个参数
                PIPE,
                LBRACE,
                body.expr(),
                RBRACE,
            )(s)
            self.e = cst.Fn(loc, x, body.e)
            return s

        return parse

    def app(self) -> parsec.Parser:
        """函数应用表达式, 注意需要用括号来手动左结合, 如 ((a b) c), 而不是 a b c, 因为我懒了."""

        def parse(s: parsec.Source) -> parsec.Source:
            """app"""
            loc = s.cur()
            f = ExprParser()
            x = ExprParser()
            s = parsec.seq(f.primary_expr(), x.expr())(s)
            self.e = cst.App(loc, f.e, x.e)
            return s

        return parse

    def fn_type(self) -> parsec.Parser:
        """函数类型表达式, 即 Pi 类型."""

        def parse(s: parsec.Source) -> parsec.Source:
            """fn_type"""
            loc = s.cur()
            ps = []
            body = ExprParser()
            s = parsec.seq(param(ps), ARROW, body.expr())(s)
            self.e = cst.FnType(loc, ps[0], body.e)
            return s

        return parse

    def univ(self) -> parsec.Parser:
        """类型宇宙表达式, 即 type, 类型的类型."""

        def parse(s: parsec.Source) -> parsec.Source:
            """univ"""
            loc = s.cur()
            s = TYPE(s)
            self.e = cst.Univ(loc)
            return s

        return parse

    def ref(self) -> parsec.Parser:
        """变量引用表达式."""

        def parse(s: parsec.Source) -> parsec.Source:
            """ref"""
            loc = s.cur()
            v = core.Var()
            s = parsec.ident(v)(s)
            self.e = cst.Unresolved(loc, v)  # 该变量尚未进行作用域检查
            return s

        return parse

    def paren_expr(self) -> parsec.Parser:
        """带括号的表达式."""

        def parse(s: parsec.Source) -> parsec.Source:
            """paren_expr"""
            return parsec.seq(LPAREN, self.expr(), RPAREN)(s)

        return parse
