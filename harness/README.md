# Bioinformatics Delivery Harness

这个目录是 `bio-*` skills 的确定性执行层。设计原则：

- **harness = engine**：所有会影响交付质量的硬规则、检查、证明、打包逻辑放在这里。
- **skills = adapter**：skills 负责识别用户意图、解释结果、编排 agent，不重复实现质量规则。
- **goal loop 只看 proof**：`/goal` 持续推进时，必须通过 harness 命令退出码、`delivery/proof.json`、`goal_proof.md` 证明完成，而不是让模型主观判断。

推荐主流程：

```bash
bash harness/specs/preflight_check.sh .
bash harness/quality/validate.sh --strict .
bash harness/quality/run_audit.sh .
bash harness/delivery/ai_scan.sh .
bash harness/delivery/package.sh pack delivery 项目名
python3 harness/delivery/proof.py status .
```

在 Claude Code 中建议用 `bio-goal` skill 或 `/bio-goal` command 生成 `/goal` 完成条件。

## 输出约定

项目最终建议包含：

```text
delivery/
  proof.json
  goal_proof.md
  delivery_manifest.tsv
  *.zip
  *.zip.md5
audit/
  audit.json
report_claims.tsv
numeric_reference.tsv
reference.lock          # 建议(版本/注释锁)；缺=P3 建议、不阻断
contract.yaml           # 可选；不强制那层。仅在采用后才校验字段(给 sample_sheet/contrast lint 当基准)
data_manifest.yaml      # 可选；同上。真源仍是 plan.md
```

## 严重度

- `P0`：禁止继续；需求/计划/隐私/证据链存在硬缺口。
- `P1`：禁止交付；数值、来源、样本表、审计、报告存在高风险缺口。
- `P2`：严格模式禁止交付；普通模式允许继续但必须记录 warning。
- `P3`：提示性建议。
