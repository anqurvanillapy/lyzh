import dataclasses
import typing

import lyzh.abstract.data as ast
import lyzh.core as core
import lyzh.abstract.rename as rename


@dataclasses.dataclass
class Normalizer:
    ids: core.IDs
    globals: ast.Globals
    env: typing.Dict[core.ID, ast.Term] = dataclasses.field(default_factory=dict)

    def term(self, tm: ast.Term) -> ast.Term:
        match tm:
            case ast.Ref(v):
                try:
                    return self.term(rename.Renamer(self.ids).rename(self.env[v.id]))
                except KeyError:
                    return tm
            case ast.App(f, x):
                f = self.term(f)
                x = self.term(x)
                match f:
                    case ast.Fn(p, b):
                        return self.subst((p.name, x), b)
                    case _:
                        return ast.App(f, x)
            case ast.Fn(p, b):
                return ast.Fn(self.param(p), self.term(b))
            case ast.FnType(p, b):
                return ast.FnType(self.param(p), self.term(b))
            case ast.Univ():
                return tm
        raise AssertionError("impossible")

    def param(self, p: core.Param[ast.Term]) -> core.Param[ast.Term]:
        return core.Param[ast.Term](p.name, self.term(p.type))

    def subst(self, m: typing.Tuple[core.Var, ast.Term], tm: ast.Term) -> ast.Term:
        (v, x) = m
        self.env[v.id] = x
        return self.term(tm)

    def apply(self, f: ast.Term, *args: ast.Term) -> ast.Term:
        ret = f
        for x in args:
            match f:
                case ast.Fn(p, b):
                    ret = self.subst((p.name, x), b)
                case _:
                    ret = ast.App(ret, x)
        return ret


def to_value(d: core.Def[ast.Term]) -> ast.Term:
    ret = d.body
    for p in reversed(d.params):
        ret = ast.Fn(p, ret)
    return ret


def to_type(d: core.Def[ast.Term]) -> ast.Term:
    ret = d.ret
    for p in reversed(d.params):
        ret = ast.FnType(p, ret)
    return ret
