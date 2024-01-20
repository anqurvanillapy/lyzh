"""求值器, 将一个值转换为它的 normal form, 所谓 NbE (normalized by evaluation)
就是在编译期间将可以计算的表达式通过求值 (evaluation) 转换为 normal form, 以供后续类型检查使用的算法理念.

有趣的是, 如果你将 ast.Univ 和 ast.FnType 抛去, 仅仅留下 ast.App, ast.Ref 和 ast.Fn,
那么这个求值器可以看作是 UTLC (untyped lambda calculus) 的求值器! 这也侧面说明了, 到达了
abstract syntax 层面之后, 这些数值已经失去了相应的类型信息, 进行无类型的单纯的变量替换与求值."""

import dataclasses
import typing

import lyzh.abstract.data as ast
import lyzh.core as core
import lyzh.abstract.rename as rename


@dataclasses.dataclass
class Normalizer:
    ids: core.IDs
    globals: ast.Globals
    # env 在学术里又叫做 rho, ρ, evaluation context, evaluation environment 等等,
    # 要时刻注意这里的映射值的结构是 ast.Term, 和 ast.Locals 不同, 它可以是类型 (type term),
    # 也可以是值 (value term), 因为这里要做的事情无非就是变量替换 (substitution).
    #
    # 所以, 根据惯例, 变量到变量类型的映射 (也就是 locals, Gamma, Γ) 我们习惯叫 context,
    # 变量到值的映射 (也就是 env, pho, ρ) 我们叫 environment.
    env: typing.Dict[core.ID, ast.Term] = dataclasses.field(default_factory=dict)

    def term(self, tm: ast.Term) -> ast.Term:
        """对单个值进行求值."""
        match tm:
            case ast.Ref(v):
                try:
                    # 进行变量替换, 并且刷新内部变量的引用.
                    return self.term(rename.Renamer(self.ids).rename(self.env[v.id]))
                except KeyError:
                    return tm
            case ast.App(f, x):
                f = self.term(f)
                x = self.term(x)
                match f:
                    case ast.Fn(p, b):
                        # 将 b 里面 p.name 出现的地方替换为 x.
                        return self.subst((p.name, x), b)
                    case _:
                        return ast.App(f, x)
            case ast.Fn(p, b):
                # 对参数类型和函数体求值, 并保持原样.
                return ast.Fn(self.param(p), self.term(b))
            case ast.FnType(p, b):
                # 对参数类型和函数类型体求值, 并保持原样.
                return ast.FnType(self.param(p), self.term(b))
            case ast.Univ():
                return tm
        raise AssertionError("impossible")

    def param(self, p: core.Param[ast.Term]) -> core.Param[ast.Term]:
        """对参数类型求值."""
        return core.Param[ast.Term](p.name, self.term(p.type))

    def subst(self, m: typing.Tuple[core.Var, ast.Term], tm: ast.Term) -> ast.Term:
        """提供一组映射, 并对 tm 进行求值."""
        (v, x) = m
        self.env[v.id] = x
        return self.term(tm)

    def apply(self, f: ast.Term, *args: ast.Term) -> ast.Term:
        """模拟函数调用, 如果 f 是函数, 则不断用它的函数体进行变量替换."""
        ret = f
        for x in args:
            match f:
                case ast.Fn(p, b):
                    ret = self.subst((p.name, x), b)
                case _:
                    ret = ast.App(ret, x)
        return ret


def to_value(d: core.Def[ast.Term]) -> ast.Term:
    """将一个定义转换为它的值形式."""
    ret = d.body
    for p in reversed(d.params):
        ret = ast.Fn(p, ret)  # 参数不为空, 转成函数
    return ret


def to_type(d: core.Def[ast.Term]) -> ast.Term:
    """将一个定义转换为它的类型形式."""
    ret = d.ret
    for p in reversed(d.params):
        ret = ast.FnType(p, ret)  # 参数不为空, 转成函数类型
    return ret
