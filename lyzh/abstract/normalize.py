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
                        self.env[p.name.id] = x
                        return self.term(b)
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
