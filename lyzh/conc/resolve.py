import dataclasses
import typing

import lyzh.core as core
import lyzh.conc.data as conc


class Error(Exception):
    pass


@dataclasses.dataclass
class Resolver:
    ctx: typing.Dict[str, core.Var] = dataclasses.field(default_factory=dict)
    names: typing.Set[str] = dataclasses.field(default_factory=set)

    def resolve(self, defs: core.Defs[conc.Expr]) -> core.Defs[conc.Expr]:
        return [self.resolve_def(d) for d in defs]

    def resolve_def(self, d: core.Def[conc.Expr]) -> core.Def[conc.Expr]:
        recoverable = []
        removable = []

        params = []
        for p in d.params:
            old = self.insert(p.name)
            if old:
                recoverable.append(old)
            else:
                removable.append(p.name)
            params.append(core.Param[conc.Expr](p.name, self.resolve_expr(p.type)))

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

        return core.Def[conc.Expr](d.loc, d.name, params, ret, body)

    def resolve_expr(self, e: conc.Expr) -> conc.Expr:
        match e:
            case conc.Unresolved(loc, v):
                try:
                    return conc.Resolved(loc, self.ctx[v.text])
                except KeyError:
                    raise Error(f"{loc.ln}:{loc.col}: unresolved variable '{v.text}'")
            case conc.Fn(loc, v, body):
                b = self.guard(v, body)
                return conc.Fn(loc, v, b)
            case conc.App(loc, f, x):
                return conc.App(loc, self.resolve_expr(f), self.resolve_expr(x))
            case conc.FnType(loc, p, body):
                typ = self.resolve_expr(p.type)
                b = self.guard(p.name, body)
                return conc.FnType(loc, core.Param(p.name, typ), b)
            case conc.Univ(_):
                return e
            case conc.Resolved:
                raise AssertionError("impossible")

    def guard(self, v: core.Var, e: conc.Expr) -> conc.Expr:
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
