"""Elaborator, 类型检查器, 之所以叫这个名字, 是因为更高级的类型检查器是可以给用户提示更多的信息的,
后续高级的功能包括 holes (也叫 goals), implicit arguments (隐式参数, 即自动填写类型等),
pruning 和 first-class polymorphism (总之就是猜类型猜的更智能) 等, 另见著名的动物园项目
AndrasKovacs/elaboration-zoo."""

import dataclasses
import typing

import lyzh.core as core
import lyzh.concrete.data as cst
import lyzh.abstract.data as ast
import lyzh.abstract.normalize as normalize
import lyzh.abstract.unify as unify
import lyzh.abstract.rename as rename


class Error(Exception):
    """类型检查错误."""

    pass


@dataclasses.dataclass
class Elaborator:
    """类型检查器."""

    ids: core.IDs
    globals: ast.Globals = dataclasses.field(default_factory=dict)
    locals: ast.Locals = dataclasses.field(default_factory=dict)

    def elaborate(self, ds: core.Defs[cst.Expr]) -> core.Defs[ast.Term]:
        """检查所有定义的类型."""
        return [self.elaborate_def(d) for d in ds]

    def elaborate_def(self, d: core.Def[cst.Expr]) -> core.Def[ast.Term]:
        """检查单个定义的类型."""
        checked = []  # 已经检查过的局部变量
        ps = []  # 已经检查过的函数参数
        for p in d.params:
            typ = self.check(p.type, ast.Univ())
            ps.append(core.Param[ast.Term](p.name, typ))
            self.locals[p.name.id] = typ  # 加入到局部变量中
            checked.append(p.name.id)
        ret = self.check(d.ret, ast.Univ())  # 返回类型一定是 type 类型
        body = self.check(d.body, ret)  # 函数体的表达式是 ret 类型
        for v in checked:  # 清空局部变量, 下一个定义的检查用不到了
            del self.locals[v]
        checked_def = core.Def[ast.Term](d.loc, d.name, ps, ret, body)
        self.globals[d.name.id] = checked_def  # 将此定义加入到全局中
        return checked_def

    def check(self, e: cst.Expr, typ: ast.Term) -> ast.Term:
        """进行类型检查."""
        match e:
            # 只需要检查函数类型, 因为信息是足够的.
            case cst.Fn(loc, v, body):
                #        Γ , x : A ⊢ M : B
                # --------------------------------- function introduction rule
                # Γ ⊢ λ (x : A) → M : π (x : A) → B
                match self.nf().term(typ):
                    case ast.FnType(p, b):
                        body_type = self.nf().subst((p.name, ast.Ref(v)), b)
                        param = core.Param[ast.Term](v, p.type)
                        return ast.Fn(param, self.guarded_check(param, body, body_type))
                    case typ:
                        raise Error(f"{loc}: expected '{typ}', got function type")
            # 其余的表达式进行类型推导, 用推导的类型和期盼的类型判断是否一致.
            case _:
                tm, got = self.infer(e)
                got = self.nf().term(got)
                typ = self.nf().term(typ)
                if self.unify(got, typ):  # 一致性检查
                    return tm
                raise Error(f"{e.loc}: expected '{typ}', got '{got}'")

    def infer(self, e: cst.Expr) -> typing.Tuple[ast.Term, ast.Term]:
        """类型推导, 其中内部也会调用 check, 所以才叫做 bidirectional typechecking,
        双向类型检查, 类型检查和类型推导是一对 mutual recursion (互相调用)."""
        match e:
            case cst.Resolved(_, v):
                # Γ ⊢ v : A
                try:
                    # 尝试从本地变量中找对应的类型.
                    return ast.Ref(v), self.locals[v.id]
                except KeyError:
                    pass  # 找不到没关系
                try:
                    # 继续从全局中找.
                    d = self.globals[v.id]
                    return (
                        # 将全局定义转换成对应的值和类型, 并且刷新内部的变量引用.
                        self.rename(normalize.to_value(d)),
                        self.rename(normalize.to_type(d)),
                    )
                except KeyError:
                    # 由于提前做过作用域检查, 所以不可能在本地和全局都不存在.
                    raise AssertionError("impossible")
            case cst.FnType(_, p, b):
                #  Γ , A : type ⊢ M : type
                # -------------------------- function type introduction rule
                # Γ ⊢ π (A: type) → M : type
                p_typ, _ = self.infer(p.type)  # 参数类型的类型一定是 Univ, 所以忽略了
                inferred_p = core.Param[ast.Term](p.name, p_typ)
                # 在参数 p 的保护下, 推导 body 的类型.
                b_tm, b_ty = self.guarded_infer(inferred_p, b)
                # 重新拼回去组成一个 ast.FnType.
                return ast.FnType(inferred_p, b_tm), b_ty
            case cst.App(_, f, x):
                # Γ ⊢ f : π (x : A) → B    x : A
                # ------------------------------ function elimination rule
                #          Γ ⊢ f x : B
                f_tm, f_typ = self.infer(f)  # 先推导出 f 的类型
                match f_typ:
                    # f 的类型必须是 ast.FnType.
                    case ast.FnType(p, b):
                        # 在参数 p 的保护下检查参数 x 的类型必须是函数的参数 p 的类型.
                        x_tm = self.guarded_check(p, x, p.type)
                        # 表达式的类型即 b, 但是要将 b 内的 p 替换成 x.
                        typ = self.nf().subst((p.name, x_tm), b)
                        # 尝试对表达式进行计算.
                        tm = self.nf().apply(f_tm, x_tm)
                        return tm, typ
                    case typ:
                        raise Error(f"{f.loc}: expected function type, got '{typ}'")
            case cst.Univ(_):
                # Γ ⊢ U type
                # ---------- universe introduction rule
                # Γ ⊢ U : U
                return ast.Univ(), ast.Univ()
        raise AssertionError("impossible")

    def guarded_check(
        self, p: core.Param[ast.Term], e: cst.Expr, typ: ast.Term
    ) -> ast.Term:
        """在 p 的保护下 (即将 p 加入到本地变量中, 检查完毕后删除), 检查表达式 e 的类型是否为 typ."""
        self.locals[p.name.id] = p.type
        ret = self.check(e, typ)
        try:
            del self.locals[p.name.id]
        except KeyError:
            pass
        return ret

    def guarded_infer(
        self, p: core.Param[ast.Term], e: cst.Expr
    ) -> typing.Tuple[ast.Term, ast.Term]:
        """在 p 的保护下 (即将 p 加入到本地变量中, 推导完毕后删除), 推导表达式 e 的类型."""
        self.locals[p.name.id] = p.type
        ret = self.infer(e)
        try:
            del self.locals[p.name.id]
        except KeyError:
            pass
        return ret

    def nf(self) -> normalize.Normalizer:
        """获取求值器."""
        return normalize.Normalizer(self.ids)

    def unify(self, lhs: ast.Term, rhs: ast.Term) -> bool:
        """检查两个值是否相等."""
        return unify.Unifier(self.ids, self.globals).unify(lhs, rhs)

    def rename(self, tm: ast.Term) -> ast.Term:
        """刷新值内部的变量引用."""
        return rename.Renamer(self.ids).rename(tm)
