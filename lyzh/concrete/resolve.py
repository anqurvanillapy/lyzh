"""Resolving, 即 scope checking, 作用域检查."""

import dataclasses
import typing

import lyzh.concrete.data as cst
import lyzh.core as core


class Error(Exception):
    """作用域检查错误."""

    pass


@dataclasses.dataclass
class Resolver:
    """作用域检查器."""

    # 名字到 ID 的映射.
    m: typing.Dict[str, core.Var] = dataclasses.field(default_factory=dict)
    # 简单的防止定义重名的集合, 给全局定义使用.
    names: typing.Set[str] = dataclasses.field(default_factory=set)

    def resolve(self, defs: core.Defs[cst.Expr]) -> core.Defs[cst.Expr]:
        """检查所有定义的作用域."""
        return [self.resolve_def(d) for d in defs]

    def resolve_def(self, d: core.Def[cst.Expr]) -> core.Def[cst.Expr]:
        """检查单个定义的作用域."""
        shadowed = []  # 被覆盖 (shadowed) 的变量, 需要在检查作用域后恢复
        fresh = []  # 没有被覆盖的全新的变量, 需要在检查作用域后删除

        params = []  # 检查完毕的参数列表
        for p in d.params:
            old = self.insert(p.name)
            if old:
                shadowed.append(old)
            else:
                fresh.append(p.name)
            params.append(core.Param[cst.Expr](p.name, self.resolve_expr(p.type)))

        ret = self.resolve_expr(d.ret)
        body = self.resolve_expr(d.body)

        for v in fresh:  # 删除没有被覆盖的全新变量
            del self.m[v.text]
        for v in shadowed:  # 重新插入被覆盖的变量
            self.insert(v)

        # 简单检查定义是否重名.
        if d.name.text in self.names:
            raise Error(f"{d.loc}: duplicate name '{d.name.text}'")
        self.names.add(d.name.text)

        # 插入新的定义, 后续定义可以引用这个全局定义.
        self.insert(d.name)

        return core.Def[cst.Expr](d.loc, d.name, params, ret, body)

    def resolve_expr(self, e: cst.Expr) -> cst.Expr:
        """检查单个表达式的作用域."""
        match e:
            case cst.Unresolved(loc, v):
                try:
                    # 检查在上下文中是否有 v 这个变量定义.
                    return cst.Resolved(loc, self.m[v.text])
                except KeyError:
                    raise Error(f"{loc}: unresolved variable '{v.text}'")
            case cst.Fn(loc, v, body):
                # body 中能够引用变量 v.
                b = self.guard(v, body)
                return cst.Fn(loc, v, b)
            case cst.App(loc, f, x):
                return cst.App(loc, self.resolve_expr(f), self.resolve_expr(x))
            case cst.FnType(loc, p, body):
                typ = self.resolve_expr(p.type)
                # body 中能够引用变量 p.name.
                b = self.guard(p.name, body)
                return cst.FnType(loc, core.Param(p.name, typ), b)
            case cst.Univ(_):
                return e
        raise AssertionError("impossible")

    def guard(self, v: core.Var, e: cst.Expr) -> cst.Expr:
        """在 v 的保护下 (即插入 v 到上下文中, 检查完毕后删除), 检查表达式 e 的作用域."""
        old = self.insert(v)
        ret = self.resolve_expr(e)
        if old:
            self.insert(old)
        else:
            del self.m[v.text]
        return ret

    def insert(self, v: core.Var) -> typing.Optional[core.Var]:
        """插入一个新的变量到上下文中. 返回旧的变量 (如果有的话)."""
        old = None
        try:
            old = self.m[v.text]
        except KeyError:
            pass
        self.m[v.text] = v
        return old
