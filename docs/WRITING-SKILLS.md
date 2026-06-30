# 写 skill 的尺子

> 借鉴 [mattpocock/skills](https://github.com/mattpocock/skills) 的 `productivity/writing-great-skills`（MIT）。
> 本文是精简改写 + 本 harness（bio-* skills / agents）适配，非逐字搬运。
>
> **根本目的：predictability**——让 agent 每次走同一个**流程**（不是产出同一个输出）。下面每条都服务于此。

## 1. 触发方式：两种，各花一种成本

| | model-invoked（留 description） | user-invoked（`disable-model-invocation: true`） |
|---|---|---|
| 谁能触发 | agent 自己 + 别的 skill + 你手敲 | 只有你手敲 |
| 代价 | description 每轮占窗口（**context load**） | 零 context load，但花你的**记忆成本**：你得记得它在 |

- 只靠手动触发的 → 设 user-invoked，别白占窗口。
- user-invoked 多到记不住 → 建一个**路由 skill**（一个 user-invoked，列出其余的 + 何时用哪个）。本仓 `ask-matt` 式。

## 2. description 怎么写

- 把 skill 的**主导词**放最前——它在这儿干"触发"的活。
- **一个 branch 一个触发词**；同义改写 = 重复，合并掉。
- 别把正文已有的身份信息重复进 description；只留触发词 + "当别的 skill 需要…"的可达子句。

## 3. 信息阶梯（把料放对层）

1. **in-skill step**：`SKILL.md` 里有序的动作。每步以**完成判据**收尾，判据要**可核验**（能分辨做完没）、必要处**穷尽**（"每个改过的对象都交代了"，不是"产出一个清单"）——判据含糊 → 抢跑（见 §7）。
2. **in-skill reference**：`SKILL.md` 里按需查的定义/规则（一组平级规则放同一层很正常，不是坏味道）。
3. **external reference**：推到单独文件，靠**上下文指针**触发才加载。

- **渐进披露**：只有部分 branch 用到的料推到链接文件，顶层保持清爽。**branch 是最好的拆分判据**：每个 branch 都要的 inline，只有部分要的放指针后。
- **co-location**：一个概念的定义/规则/坑放同一标题下，别散落——读一处就把邻居带出来。

## 4. 何时拆 skill（每拆一刀都花一种成本，值才拆）

- **按触发拆**：有独立"主导词"该单独触发、或别的 skill 必须调它。
- **按序列拆**：后续步骤诱使 agent 草草了事前一步（抢跑）时，把后续步骤藏起来，逼它把当前这步做扎实。

## 5. 剪枝（对抗 sediment）

- **single source of truth**：每个意思只在一处权威，改行为 = 改一处。
- **relevance**：逐行问"还跟这 skill 干的事相关吗"。
- **no-op 测试**：逐**句**问"这句相对默认行为改变了什么吗"，没改变就**整句删**（别改写）。要狠——大多数没过测的散文该删不该修。

## 6. 主导词（leading words）

用一个模型预训练里已有的紧凑概念锚住一片行为（如 _tight_ / _red_ / _tracer bullet_）。它两头省：正文里锚**执行**（同一个词 = 同一种行为），description 里锚**触发**（同一个词同时出现在你 prompt/文档/代码里，agent 更稳地认出该 skill）。把"快、确定、低开销"塌缩成"_tight_ loop"这种——更少 token + 更利落的挂钩。

## 7. 失败模式（诊断清单）

- **premature completion（抢跑）**：步骤没真做完就奔向"做完了"。先磨完成判据（便宜、就地）；实在含糊又观察到抢跑，才按序列拆。
- **duplication**：同一意思多处 → 维护和 token 双亏，还虚抬它在阶梯上的层级。
- **sediment（陈渣）**：只敢加不敢删积出的旧层 → 没有剪枝纪律的默认归宿。
- **sprawl**：就是太长（哪怕每行都活）→ 用阶梯治：reference 推指针后、按 branch/序列拆。
- **no-op**：模型默认就会做的话 → 白占 load。弱主导词（该 thorough 时写"be thorough"）也是 no-op；治法是换更强的词（_relentless_），不是换技术。

## 套到本 harness

- 这套词汇正好给 CLAUDE.md 的"文档单一真源 / 别堆多版本"配上精确语言：**single source of truth** + **sediment** + **no-op**。
- `bio-result-auditor` 的承重 claim 复算：完成判据要"**每条 claim 都对过账**"（可核验 + 穷尽），不是"列个清单"——否则抢跑。
- 决定哪些 `bio-*` skill 该自动触发（model-invoked）、哪些只手敲（user-invoked）：按 **context load vs cognitive load** 权衡，别让草稿/低频 skill 白占窗口。
