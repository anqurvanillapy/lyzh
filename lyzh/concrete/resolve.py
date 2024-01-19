import dataclasses
import typing

import lyzh.concrete.data as cst
import lyzh.core as core


class Error(Exception):
    pass


@dataclasses.dataclass
class Resolver:
    ctx: typing.Dict[str, core.Var] = dataclasses.field(default_factory=dict)
    names: typing.Set[str] = dataclasses.field(default_factory=set)

    def resolve(self, defs: core.Defs[cst.Expr]) -> core.Defs[cst.Expr]:
        return [self.resolve_def(d) for d in defs]

    def resolve_def(self, d: core.Def[cst.Expr]) -> core.Def[cst.Expr]:
        recoverable = []
        removable = []

        params = []
        for p in d.params:
            old = self.insert(p.name)
            if old:
                recoverable.append(old)
            else:
                removable.append(p.name)
            params.append(core.Param[cst.Expr](p.name, self.resolve_expr(p.type)))

        ret = self.resolve_expr(d.ret)
        body = self.resolve_expr(d.body)

        for v in removable:
            del self.ctx[v.text]
        for v in recoverable:
            self.insert(v)

        if d.name.text in self.names:
            raise Error(f"{d.loc.ln}:{d.loc.col}: duplicate name '{d.name.text}'")
        self.names.add(d.name.text)
        self.insert(d.name)

        return core.Def[cst.Expr](d.loc, d.name, params, ret, body)

    def resolve_expr(self, e: cst.Expr) -> cst.Expr:
        match e:
            case cst.Unresolved(loc, v):
                try:
                    return cst.Resolved(loc, self.ctx[v.text])
                except KeyError:
                    raise Error(f"{loc.ln}:{loc.col}: unresolved variable '{v.text}'")
            case cst.Fn(loc, v, body):
                b = self.guard(v, body)
                return cst.Fn(loc, v, b)
            case cst.App(loc, f, x):
                return cst.App(loc, self.resolve_expr(f), self.resolve_expr(x))
            case cst.FnType(loc, p, body):
                typ = self.resolve_expr(p.type)
                b = self.guard(p.name, body)
                return cst.FnType(loc, core.Param(p.name, typ), b)
            case cst.Univ(_):
                return e
        raise AssertionError("impossible")

    def guard(self, v: core.Var, e: cst.Expr) -> cst.Expr:
        old = self.insert(v)
        ret = self.resolve_expr(e)
        if old:
            self.insert(old)
        else:
            del self.ctx[v.text]
        return ret

    def insert(self, v: core.Var) -> typing.Optional[core.Var]:
        old = None
        try:
            old = self.ctx[v.text]
        except KeyError:
            pass
        self.ctx[v.text] = v
        return old
