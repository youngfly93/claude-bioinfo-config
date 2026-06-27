export const meta = {
  name: 'bio-audit-fanout',
  description:
    '对生信交付包做并行多代理审计：扫模块 → 每模块一个 bio-result-auditor 子代理只读审计(发现落盘) → 对每条 P0/P1 做对抗式复核 → 汇总确认清单。把你"4-6 个并行审计子代理"的习惯固化成可复用、可重跑、结果不占上下文的 workflow。',
  phases: [
    { title: 'Scan', detail: '读 plan.md，列出要审的模块' },
    { title: 'Audit', detail: '每模块一个 bio-result-auditor 子代理，只读审计、发现落盘' },
    { title: 'Verify', detail: '对每条 P0/P1 承重发现做对抗式复核' },
    { title: 'Synthesize', detail: '汇总确认的 P0/P1' },
  ],
}

// 用法：Workflow({ scriptPath:'~/.claude/workflows/bio-audit-fanout.js',
//   args:{ projectPath:'/path/to/项目', planPath:'/path/to/plan.md' } })
const proj = (args && args.projectPath) || '.'
const planHint = (args && args.planPath) || `${proj}/plan.md`

const MODULES = {
  type: 'object',
  properties: {
    modules: {
      type: 'array',
      items: {
        type: 'object',
        properties: { name: { type: 'string' }, path: { type: 'string' }, note: { type: 'string' } },
        required: ['name', 'path'],
      },
    },
  },
  required: ['modules'],
}
const FINDINGS = {
  type: 'object',
  properties: {
    findings: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          severity: { type: 'string', enum: ['P0', 'P1', 'P2', 'P3'] },
          title: { type: 'string' },
          evidence: { type: 'string' },
          file: { type: 'string' },
        },
        required: ['severity', 'title'],
      },
    },
  },
  required: ['findings'],
}
const VERDICT = {
  type: 'object',
  properties: { isReal: { type: 'boolean' }, reason: { type: 'string' } },
  required: ['isReal'],
}

phase('Scan')
const scan = await agent(
  `读取 ${planHint} 与项目 ${proj} 的 results/figures/reports/scripts 目录，列出需要审计的「模块」` +
  `（如 质控 / 差异表达 / 富集 / 生存 / 报告 等），每个给 name + 主要结果路径 path。只读，不改文件。`,
  { schema: MODULES, label: 'scan', phase: 'Scan' }
)
const modules = (scan && scan.modules) || []
log(`待审模块 ${modules.length} 个`)

const audited = await pipeline(
  modules,
  // 阶段 1：每模块一个只读审计子代理（bio-result-auditor），发现落盘
  (m) => agent(
    `按 bio-result-audit 规则，对项目 ${proj} 的「${m.name}」模块做只读审计：对照 ${planHint}，` +
    `检查完整性 / 数据准确性 / 分析准确性 / 方法合理性 / 图表-数据一致性 / 参考版本；` +
    `对承重数字做针对性复算（数字台账）。把完整发现写进 ${proj}/audit/${m.name}.md，本回只返回结构化发现清单。` +
    `严格只读，不改/删文件。结果路径：${m.path}`,
    { schema: FINDINGS, agentType: 'bio-result-auditor', label: `audit:${m.name}`, phase: 'Audit' }
  ),
  // 阶段 2：对每条 P0/P1 发现做对抗式复核（默认倾向"证伪"，第二种独立方法核实）
  (res, m) => parallel(
    ((res && res.findings) || [])
      .filter((f) => f.severity === 'P0' || f.severity === 'P1')
      .map((f) => () =>
        agent(
          `对抗式复核这条审计发现，默认倾向「不成立」除非证据确凿：\n` +
          `模块 ${m.name} · ${f.severity} · ${f.title}\n依据：${f.evidence || '(无)'}\n文件：${f.file || m.path}\n` +
          `用第二种独立方法核实（别只信原审计的单次读取/正则）。只读。`,
          { schema: VERDICT, label: `verify:${m.name}`, phase: 'Verify' }
        ).then((v) => ({ ...f, module: m.name, verdict: v }))
      )
  )
)

phase('Synthesize')
const confirmed = audited.flat().filter(Boolean).filter((x) => x.verdict && x.verdict.isReal)
const bySev = (s) => confirmed.filter((x) => x.severity === s)
const report = {
  project: proj,
  modules: modules.length,
  P0: bySev('P0'),
  P1: bySev('P1'),
  note: 'P2/P3 见各模块 audit/*.md（未对抗复核）；本表只列经对抗复核确认的 P0/P1',
  summary: `确认 P0 ${bySev('P0').length} 条 · P1 ${bySev('P1').length} 条（已对抗复核）`,
}
log(report.summary)
return report
