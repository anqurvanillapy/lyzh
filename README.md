# lyzh

```rs
fn f(t: type) -> type { t }
```

一款用于教学目的的依赖类型语言, 献给 [Lyzh].

需要使用 Python 3.12 版本. 执行以下命令运行一个文件:

```bash
python -m lyzh example.lyzh
```

整个代码仓库的代码量:

* 不包括注释: 650 行左右
* 不包括注释和文本解析部分: 420 行左右

由于整个类型系统里面能用的东西不多, 所以很难写一些真正有意义的事情, 所以这里建议大家把代码用自己喜欢的语言抄一遍,
然后阅读自己喜欢的纸, 往自己的语言里面添加 `string`, `number`, `i32`, tuple, enum, record, 这样那样好玩的类型吧!

当然了, 一些 functional pearls 还是可以玩的. :)

比如说 Church numerals:

```rs
fn nat -> type {
    (t : type) -> (s: (n: t) -> t) -> (z: t) -> t
}

fn add(a: nat) (b: nat) -> nat {
    |t| { |s| { |z| { ((a t) s) (((b t) s) z) } } }
}

fn mul(a: nat) (b: nat) -> nat {
    |t| { |s| { |z| { ((a t) ((b t) s)) z } } }
}
```

比如说 Leibniz equality:

```rs
fn eq(t: type) (a: t) (b: t) -> type {
    (p: (v: t) -> type) -> (pa: p a) -> p b
}

fn refl(t: type) (a: t) -> ((eq t) a) a {
    |p| { |pa| { pa } }
}

fn sym(t: type) (a: t) (b: t) (p: ((eq t) a) b) -> ((eq t) b) a {
    (p (|b| { ((eq t) b) a })) ((refl t) a)
}
```

用这几个定义来写点好玩的小证明吧! 哦对了, 有人说要我上传下习题的答案 (

* 用 `nat`、`add`、`mul` 写一些简单的计算:

<details>
<summary>答案</summary>

```rs
fn three -> nat {
    |t| { |s| { |z| { s (s (s z)) } } }
}

fn six -> nat {
    (add three) three
}

fn nine -> nat {
    (mul three) three
}
```

比如, 输出结果能看到 `six` 内部有 6 个 `f`, 说明计算成功.

</details>

* 用 `eq`、`refl`、`sym` 写一些简单的证明:

<details>
<summary>答案</summary>

```rs
fn a -> type {
    type
}

fn b -> type {
    type
}

fn lemma -> ((eq type) a) b {
    (refl type) a
}

fn theorem(p: ((eq type) a) b) -> ((eq type) b) a {
    (((sym type) a) b) lemma
}
```

</details>

[Lyzh]: https://github.com/imlyzh

## License

MIT
