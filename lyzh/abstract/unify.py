import dataclasses

import lyzh.abstract.data as ast
import lyzh.core as core
import lyzh.abstract.normalize as normalize


@dataclasses.dataclass
class Unifier:
    ids: core.IDs
    globals: ast.Globals

    def unify(self, lhs: ast.Term, rhs: ast.Term) -> bool:
        match lhs, rhs:
            case ast.Ref(x), ast.Ref(y):
                return x.text == y.text and x.id == y.id
            case ast.App(f, x), ast.App(g, y):
                return self.unify(f, g) and self.unify(x, y)
            case ast.Fn(p, b), ast.Fn(q, c):
                return self.unify(b, self.nf().subst((q.name, ast.Ref(p.name)), c))
            case ast.FnType(p, b), ast.FnType(q, c):
                if not self.unify(p.type, q.type):
                    return False
                return self.unify(b, self.nf().subst((q.name, ast.Ref(p.name)), c))
            case ast.Univ(), ast.Univ():
                return True
        return False

    def nf(self) -> normalize.Normalizer:
        return normalize.Normalizer(self.ids, self.globals)
