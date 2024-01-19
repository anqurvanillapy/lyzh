import dataclasses
import typing

import lyzh.core as core
import lyzh.concrete.data as cst
import lyzh.abstract.data as ast
import lyzh.abstract.normalize as normalize
import lyzh.abstract.unify as unify
import lyzh.abstract.rename as rename


class Error(Exception):
    pass


@dataclasses.dataclass
class Elaborator:
    ids: core.IDs
    globals: ast.Globals = dataclasses.field(default_factory=dict)
    locals: ast.Locals = dataclasses.field(default_factory=dict)

    def elaborate(self, ds: core.Defs[cst.Expr]) -> core.Defs[ast.Term]:
        return [self.elaborate_def(d) for d in ds]

    def elaborate_def(self, d: core.Def[cst.Expr]) -> core.Def[ast.Term]:
        checked = []
        ps = []
        for p in d.params:
            typ = self.check(p.type, ast.Univ())
            ps.append(core.Param[ast.Term](p.name, typ))
            self.locals[p.name.id] = typ
            checked.append(p.name.id)
        ret = self.check(d.ret, ast.Univ())
        body = self.check(d.body, ret)
        for v in checked:
            del self.locals[v]
        checked_def = core.Def[ast.Term](d.loc, d.name, ps, ret, body)
        self.globals[d.name.id] = checked_def
        return checked_def

    def check(self, e: cst.Expr, typ: ast.Term) -> ast.Term:
        match e:
            case cst.Fn(loc, v, body):
                match self.nf().term(typ):
                    case ast.FnType(p, b):
                        body_type = self.nf().subst((p.name, ast.Ref(v)), b)
                        param = core.Param[ast.Term](v, p.type)
                        return ast.Fn(param, self.guarded_check(param, body, body_type))
                    case typ:
                        raise Error(f"{loc}: expected '{typ}', got function type")
            case _:
                tm, got = self.infer(e)
                got = self.nf().term(got)
                typ = self.nf().term(typ)
                if self.unify(got, typ):
                    return tm
                raise Error(f"{e.loc}: expected '{typ}', got '{got}'")

    def infer(self, e: cst.Expr) -> typing.Tuple[ast.Term, ast.Term]:
        match e:
            case cst.Resolved(_, v):
                try:
                    return ast.Ref(v), self.locals[v.id]
                except KeyError:
                    pass
                try:
                    d = self.globals[v.id]
                    return (
                        self.rename(normalize.to_value(d)),
                        self.rename(normalize.to_type(d)),
                    )
                except KeyError:
                    raise AssertionError("impossible")
            case cst.FnType(_, p, b):
                p_typ, _ = self.infer(p.type)
                checked_p = core.Param[ast.Term](p.name, p_typ)
                b_tm, b_ty = self.guarded_infer(checked_p, b)
                return ast.FnType(checked_p, b_tm), b_ty
            case cst.App(_, f, x):
                f_tm, f_typ = self.infer(f)
                match f_typ:
                    case ast.FnType(p, b):
                        x_tm = self.guarded_check(p, x, p.type)
                        typ = self.nf().subst((p.name, x_tm), b)
                        tm = self.nf().apply(f_tm, x_tm)
                        return tm, typ
                    case typ:
                        raise Error(f"{f.loc}: expected function type, got '{typ}'")
            case cst.Univ(_):
                return ast.Univ(), ast.Univ()
        raise AssertionError("impossible")

    def guarded_check(
        self, p: core.Param[ast.Term], e: cst.Expr, typ: ast.Term
    ) -> ast.Term:
        self.locals[p.name.id] = p.type
        ret = self.check(e, typ)
        del self.locals[p.name.id]
        return ret

    def guarded_infer(
        self, p: core.Param[ast.Term], e: cst.Expr
    ) -> typing.Tuple[ast.Term, ast.Term]:
        self.locals[p.name.id] = p.type
        ret = self.infer(e)
        del self.locals[p.name.id]
        return ret

    def nf(self) -> normalize.Normalizer:
        return normalize.Normalizer(self.ids, self.globals)

    def unify(self, lhs: ast.Term, rhs: ast.Term) -> bool:
        return unify.Unifier(self.ids, self.globals).unify(lhs, rhs)

    def rename(self, tm: ast.Term) -> ast.Term:
        return rename.Renamer(self.ids).rename(tm)
