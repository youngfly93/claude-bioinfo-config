把当前生信项目转成 harness goal loop。请执行：

```bash
HARNESS_ROOT="$(sh harness/lib/resolve_harness.sh . 2>/dev/null || true)"
if [ -z "$HARNESS_ROOT" ] && [ -n "${CLAUDE_PLUGIN_ROOT:-}" ]; then
  HARNESS_ROOT="$(sh "${CLAUDE_PLUGIN_ROOT}/harness/lib/resolve_harness.sh" . 2>/dev/null || true)"
fi
if [ -n "$HARNESS_ROOT" ]; then
  sh "$HARNESS_ROOT/bin/bio_goal.sh" .
else
  echo "未找到 harness；请先安装 claude-bioinfo-config 或把 harness/ 放入项目根目录。"
fi
```

然后把输出内容作为 `/goal` 的完成条件执行。不要主观判断完成；必须用 `delivery/proof.json` 和 `delivery/goal_proof.md` 证明。
