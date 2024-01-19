"""数值内部引用刷新器, 这是因为, 我们使用了 capture-avoiding substitution 的技术,
所有的定义检查完毕类型之后, 它就像一个 "模板" 存在于 global context 当中, 如果后续有其他定义引用,
则我们应该把这个 "模板" 生成出来的数值内部的所有 ID 重新刷新, 不然的话, 引用会指向 "模板" 中去,
造成严重错误 (比如程序陷入死循环)."""

import dataclasses
import typing

import lyzh.abstract.data as ast
import lyzh.core as core


@dataclasses.dataclass
class Renamer:
    """数值内部引用刷新器."""

    ids: core.IDs
    m: typing.Dict[core.ID, core.ID] = dataclasses.field(default_factory=dict)

    def rename(self, tm: ast.Term) -> ast.Term:
        """刷新数值内部引用."""
        match tm:
            case ast.Ref(v):
                try:
                    # 用旧的 ID 替换成新的 ID.
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
        """将参数赋予新的 ID 放入映射, 并刷新参数类型."""
        name = self.ids.rename(p.name)
        self.m[p.name.id] = name.id  # 后续遇到旧的 ID 会被替换成新的 ID
        return core.Param[ast.Term](name, self.rename(p.type))
