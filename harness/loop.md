# 自主执行循环协议

> 从 Spec 检查到客户交付的完整自动化循环。

---

## 完整循环

```
Phase 1: 准备
  ├─ 读取 plan.md
  ├─ Spec 质量检查（→ harness/specs/plan_template.md）
  ├─ 长任务初始化 execution_log.md（→ harness/specs/execution_log_template.md）
  ├─ 选择分析类型 Harness（→ harness/types/{type}.md）
  └─ IF 检查不通过 → 停下，列出缺失项

Phase 1.5: 方法确认（仅高风险任务）
  ├─ 输出 3-5 点方法概要
  │  ├─ 使用什么工具 / 库
  │  ├─ macOS / bash 3.x 风险点
  │  └─ 如何验证输出
  ├─ IF 用户确认 → 立即进入 Phase 2 执行
  └─ IF 常规任务 → 跳过，不得只停留在规划阶段

Phase 2: 逐步执行
  LOOP for each Step in plan.md:
  │  ├─ 读取 Step 规格（输入/操作/输出/QC）
  │  ├─ 执行分析脚本
  │  ├─ 验证产出（QC 检查点）
  │  ├─ IF 失败 → 诊断 → 修复（最多3次）→ 再验证
  │  ├─ IF 3次后仍失败 → 停下，上报
  │  └─ 记录到 execution_log.md
  └─ 全部 Step 完成

Phase 3: 质量审计（→ harness/quality/audit.md）
  ├─ 3a. 机械化检查（脚本，无需 Agent）
  │  ├─ 完整性 → validate.sh（文件存在/非空/stale）
  │  ├─ 数据准确性 → validate.sh（QC 断言 + 数值比对）
  │  └─ 交付规范 → ai_scan.sh（AI 痕迹扫描）
  │
  ├─ 3b. 交叉验证（Codex / 第二 Agent，只读审查）
  │  ├─ 方法合理性 → /codex:rescue "审查分析方法是否合理"
  │  │  检查：统计检验选择、多重校正、归一化、DEG 阈值与 plan.md 一致性
  │  └─ 图表质量 → /codex:rescue "审查图表是否与数据一致"
  │     检查：阈值线、配色、标签、分辨率、legend 与实际内容匹配
  │  ⚠️ Codex 只做只读审查，不改任何文件，只输出 PASS/FAIL + 理由
  │
  ├─ 3c. 汇总与修复循环
  │  LOOP max 5 rounds:
  │  │  ├─ 汇总 3a + 3b 结果 → audit_result.json
  │  │  ├─ IF 全部 PASS → 进入 Phase 4
  │  │  ├─ IF 有 FAIL → 列出失败项 → 修复 → 下一轮
  │  │  └─ IF 超过 5 轮 → 停下，上报人工
  │  └─ 审计通过
  │
  └─ 注：若 Codex 不可用，方法和图表维度退化为 WARN（由 run_audit.sh 兜底）

Phase 4: 报告与校验
  ├─ 生成 Word 报告（→ harness/types/report.md）
  ├─ 数值交叉校验（→ harness/quality/validate.sh）
  └─ IF 校验不通过 → 修正报告 → 再校验

Phase 5: 交付打包（→ harness/delivery/standards.md）
  ├─ 组织目录结构
  ├─ AI 痕迹扫描（→ harness/delivery/ai_scan.sh）
  ├─ IF 发现 AI 痕迹 → 清理 → 再扫描
  ├─ ZIP 打包 + MD5 校验
  └─ Tailscale 传输（可选）

OUTPUT: 客户可直接使用的 ZIP 交付包
```

---

## 人工介入触发条件

### 必须停下（HALT）

- 生物学解释存在争议
- 数据质量问题可能影响结论（如一半样本 outlier）
- plan.md 中的参数与领域惯例明显不符
- 需要删除/修改客户提供的原始数据
- 审计循环超过 5 轮仍有维度未通过
- 任何涉及临床结论的判断

### 可以自主（PROCEED）

- 图表配色和排版调整
- 代码 bug 修复（不涉及方法学变更）
- 文件命名和目录组织
- 富集分析中的通路过滤（按 padj 阈值）
- 标准 QC 步骤的执行

---

## 并行编排

对于独立子任务，可使用并行 sub-agent：

```
可并行（无依赖）：
  ┌─ Claude sub-agent: Word 报告生成
  ├─ ai_scan.sh: AI 痕迹扫描
  ├─ Claude sub-agent: 文件夹结构组织
  ├─ validate.sh + run_audit.sh: 机械化审计（完整性/准确性/交付）
  └─ /codex:rescue: 交叉验证审计（方法/图表）← 与机械化审计并行

必须串行（有依赖）：
  数据准备 → 差异分析 → 富集分析 → 报告生成
```

---

## 上下文窗口交接

当会话接近上下文限制时，产出交接产物：

```markdown
# 交接摘要

## 已完成
- Step 1: ✅ 数据准备，产出 xxx (数值摘要)
- Step 2: ✅ DEG 分析，产出 xxx (关键数值)

## 当前状态
- Step 3: 🔄 进行中，完成了 XX，待做 YY

## 待处理
- Step 4-N: ⏳

## 关键数值（必须传递到下一个会话）
- 样本数、DEG数、阈值、方法选择

## 未解决的决策
- (需要人工判断的点)
```

优先把这些内容同步写入 `execution_log.md`，而不是只留在聊天上下文中。
