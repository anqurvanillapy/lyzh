import dataclasses
import typing

import lyzh.abstract.data as ast
import lyzh.core as core


@dataclasses.dataclass
class Renamer:
    ids: core.IDs
    m: typing.Dict[core.ID, core.ID] = dataclasses.field(default_factory=dict)

    def rename(self, tm: ast.Term) -> ast.Term:
        match tm:
            case ast.Ref(v):
                try:
                    return ast.Ref(core.Var(v.text, self.m[v.id]))
                except KeyError:
                    return tm
            case ast.App(f, x):
                return ast.App(self.rename(f), self.rename(x))
            case ast.Fn(p, b):
                return ast.Fn(self.param(p), self.rename(b))
            case ast.FnType(p, b):
                return ast.FnType(self.param(p), self.rename(b))
            case ast.Univ():
                return tm
        raise AssertionError("impossible")

    def param(self, p: core.Param[ast.Term]) -> core.Param[ast.Term]:
        name = self.ids.rename(p.name)
        self.m[p.name.id] = name.id
        return core.Param[ast.Term](name, self.rename(p.type))
