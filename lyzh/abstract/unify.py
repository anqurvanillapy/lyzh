"""\
# Unifier

相等检查器, 即执行 unification 算法, 又叫做 conversion checking.
"""

import dataclasses

import lyzh.abstract.data as ast
import lyzh.abstract.normalize as normalize


@dataclasses.dataclass
class Unifier:
    """相等检查器."""

    globals: ast.Globals

    def unify(self, lhs: ast.Term, rhs: ast.Term) -> bool:
        match lhs, rhs:
            case ast.Ref(x), ast.Ref(y):
                return x.text == y.text and x.id == y.id
            case ast.App(f, x), ast.App(g, y):
                return self.unify(f, g) and self.unify(x, y)
            case ast.Fn(p, b), ast.Fn(q, c):
                # 将 c 内部的 q 替换成 p 后和 b 检查是否相等.
                return self.unify(
                    b, normalize.Normalizer().subst((q.name, ast.Ref(p.name)), c)
                )
            case ast.FnType(p, b), ast.FnType(q, c):
                if not self.unify(p.type, q.type):
                    return False
                # 将 c 内部的 q 替换成 p 后和 b 检查是否相等.
                return self.unify(
                    b, normalize.Normalizer().subst((q.name, ast.Ref(p.name)), c)
                )
            case ast.Univ(), ast.Univ():
                return True
        return False
