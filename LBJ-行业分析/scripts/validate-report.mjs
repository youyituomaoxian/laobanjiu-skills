#!/usr/bin/env node
/**
 * LBJ-行业分析 · 报告结构校验器
 * ------------------------------------------------------------------
 * 用法：
 *   node scripts/validate-report.mjs <报告路径> [选项]
 *
 * 选项：
 *   --framework      框架版模式：允许出现「待采集」（无联网降级时使用）
 *   --strict         把 WARN 提升为 FAIL（交付前建议开启）
 *   --out <文件>     把报告写入文本文件（stdout 静默的终端用这个 + 读文件）
 *   --json <文件>    额外输出机器可读 JSON
 *   --quiet          只输出 FAIL/WARN 明细，不输出通过项
 *
 * 退出码：0 = 全部通过；1 = 存在 FAIL；2 = 用法错误/文件不可读
 *
 * 零依赖，Node 18+。
 */

import fs from 'node:fs';
import path from 'node:path';

/* ── 参数解析 ──────────────────────────────────────────────────── */
const argv = process.argv.slice(2);
const opts = { framework: false, strict: false, quiet: false, out: null, json: null };
const files = [];
for (let i = 0; i < argv.length; i++) {
  const a = argv[i];
  if (a === '--framework' || a === '--allow-framework') opts.framework = true;
  else if (a === '--strict') opts.strict = true;
  else if (a === '--quiet') opts.quiet = true;
  else if (a === '--out') opts.out = argv[++i];
  else if (a === '--json') opts.json = argv[++i];
  else if (a.startsWith('--')) { console.error(`未知选项：${a}`); process.exit(2); }
  else files.push(a);
}

if (files.length !== 1) {
  console.error('用法：node scripts/validate-report.mjs <报告路径> [--framework] [--strict] [--out <file>] [--json <file>] [--quiet]');
  process.exit(2);
}

const target = path.resolve(files[0]);
if (!fs.existsSync(target) || !fs.statSync(target).isFile()) {
  console.error(`找不到文件：${target}`);
  process.exit(2);
}

let html;
try {
  html = fs.readFileSync(target, 'utf8');
} catch (e) {
  console.error(`读取失败：${e.message}`);
  process.exit(2);
}

/* ── 结果收集 ──────────────────────────────────────────────────── */
const FAIL = [], WARN = [], PASS = [];
const fail = (m) => FAIL.push(m);
const warn = (m) => WARN.push(m);
const pass = (m) => PASS.push(m);
const lineOf = (pats) => {
  for (const p of pats) {
    const i = html.indexOf(p);
    if (i >= 0) return html.slice(0, i).split('\n').length;
  }
  return null;
};
const at = (n) => (n ? ` (约第 ${n} 行)` : '');

/* ═════════ 1. 占位符残留 ═══════════════════════════════════════ */
{
  // 先剥离 script/style：JS 对象字面量嵌套会产生 `}}`，直接统计花括号会误判
  const proseText = html
    .replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi, '')
    .replace(/<style\b[^>]*>[\s\S]*?<\/style>/gi, '')
    .replace(/<!--[\s\S]*?-->/g, '');

  const hits = [];
  const tokenRe = /\{\{[^{}\n]{0,80}\}\}/g;
  let m;
  while ((m = tokenRe.exec(proseText))) {
    hits.push({ line: html.slice(0, m.index).split('\n').length, text: m[0].trim() });
    if (hits.length >= 25) break;
  }
  const leftoverBraces = (proseText.match(/\{\{|\}\}/g) || []).length;
  const todoHits = [];
  for (const kw of ['TODO', 'FIXME', 'XXX占位', '待填', '待补充', 'Lorem', '此处填写']) {
    if (proseText.includes(kw)) todoHits.push(kw);
  }
  const placeholderCount = (proseText.match(/待采集/g) || []).length;

  if (hits.length) {
    fail(`残留 {{...}} 占位符 ${hits.length}${hits.length >= 25 ? '+' : ''} 处：` +
      hits.slice(0, 8).map(h => `第${h.line}行「${h.text}」`).join('；') +
      (hits.length > 8 ? ` …等 ${hits.length} 处` : ''));
  } else if (leftoverBraces) {
    fail(`存在未配对的 {{ 或 }} 共 ${leftoverBraces} 处（约第 ${lineOf(['{{', '}}'])} 行）`);
  } else {
    pass('无 {{...}} 占位符残留');
  }

  if (todoHits.length) fail(`残留待填标记：${todoHits.join('、')}`);
  else pass('无 TODO/待填 类标记');

  if (placeholderCount > 0) {
    if (opts.framework) pass(`框架版模式：${placeholderCount} 处「待采集」已按约定放行`);
    else fail(`出现 ${placeholderCount} 处「待采集」，但未声明框架版。若本次为无联网降级，请加 --framework`);
  }
}

/* ═════════ 2. 非法 / 异常字符 ═════════════════════════════════ */
{
  const bad = [];
  const add = (name, re) => {
    const c = (html.match(re) || []).length;
    if (c) bad.push(`${name}×${c}`);
  };
  add('U+FFFD 替换符', /\uFFFD/g);
  add('NUL', /\u0000/g);
  add('零宽字符', /[\u200B-\u200D\uFEFF]/g);
  add('私有区字符', /[\uE000-\uF8FF]/g);
  if (bad.length) fail(`存在非法字符：${bad.join('、')}（多为编码损坏，需重新生成该段）`);
  else pass('无非法 / 异常字符');
}

/* ═════════ 3. 图表计数一致性 ══════════════════════════════════ */
{
  const canvasTags = html.match(/<canvas\b[^>]*>/g) || [];
  const canvasIds = [...html.matchAll(/<canvas\b[^>]*\bid=["']([^"']+)["']/g)].map(m => m[1]);
  const noId = canvasTags.filter(t => !/\bid=/.test(t)).length;
  const chartCalls = (html.match(/new\s+Chart\s*\(/g) || []).length;
  const chartJsCdn = /chart(?:\.umd)?(?:\.min)?\.js/i.test(html) && /<script[^>]+src=/i.test(html);

  if (noId) fail(`${noId} 个 <canvas> 缺少 id 属性，chart 实例无法绑定`);
  if (canvasIds.length !== chartCalls) {
    fail(`canvas 数量（${canvasIds.length}）与 new Chart() 调用数（${chartCalls}）不一致——` +
      `删除图表时须把 <canvas> 与其 new Chart 调用成对删除`);
  } else if (canvasIds.length) {
    pass(`图表计数一致：${canvasIds.length} 个 canvas ↔ ${chartCalls} 个 Chart 实例`);
  } else {
    warn('报告中没有任何图表，请确认是否为刻意选择（行业报告通常至少含规模趋势图）');
  }

  const dangling = canvasIds.filter(id => !new RegExp(`getElementById\\(\\s*['"]${id.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}['"]\\s*\\)`).test(html));
  if (dangling.length) fail(`canvas 的 id 未被任何 Chart 绑定：${dangling.join('、')}`);
  else if (canvasIds.length) pass('全部 canvas id 均已被 Chart 实例引用');

  if (!chartJsCdn) fail('未检测到 Chart.js 的 <script src> 引入（图表将无法渲染）');
  else pass('Chart.js CDN 已引入');

  if (!/Chart\.defaults\.color/.test(html)) warn('未设置 Chart.defaults.color，暗色主题下刻度文字可能不可读');
  else pass('Chart.defaults 主题色已设置');
}

/* ═════════ 4. 导航与章节对应 ══════════════════════════════════ */
{
  const navLinks = [...html.matchAll(/<a\b[^>]*href=["']#([^"']+)["']/g)].map(m => m[1])
    .filter(id => id && id !== '');
  const ids = new Set([...html.matchAll(/\bid=["']([^"']+)["']/g)].map(m => m[1]));
  const sections = [...html.matchAll(/<section\b[^>]*\bid=["']([^"']*)["']/g)].map(m => m[1]);
  const navBlock = (html.match(/<nav\b[\s\S]*?<\/nav>/i) || [''])[0];
  const navCount = (navBlock.match(/<a\b[^>]*href=["']#/g) || []).length;

  if (!sections.length) fail('未找到任何 <section id="...">，章节锚点缺失');
  if (navCount !== sections.length) {
    fail(`导航链接数（${navCount}）与章节数（${sections.length}）不一致——增删章节时须同步导航`);
  } else if (navCount) {
    pass(`导航与章节对应：${navCount} 个锚点 ↔ ${sections.length} 个 section`);
  }

  const dangling = navLinks.filter(h => !ids.has(h));
  if (dangling.length) fail(`导航存在悬空锚点（无对应 id）：${dangling.join('、')}`);
  else if (navLinks.length) pass('全部导航锚点均可解析');

  const emptySec = sections.filter(s => !s).length;
  if (emptySec) fail(`${emptySec} 个 <section> 的 id 为空，锚点无法跳转`);

  /* 章节顺序号 01..N 连续 */
  const idxNums = [...html.matchAll(/<span class="idx"[^>]*>\s*(\d+)\s*<\/span>/g)].map(m => +m[1]);
  if (idxNums.length) {
    const expect = idxNums.map((_, i) => i + 1);
    const okSeq = idxNums.every((v, i) => v === expect[i]);
    if (!okSeq) fail(`章节编号不连续：实际 ${idxNums.join(',')}，应为 ${expect.join(',')}`);
    else pass(`章节编号连续：01–${String(idxNums.length).padStart(2, '0')}`);
    if (idxNums.length !== sections.length) {
      warn(`编号徽章数（${idxNums.length}）与 section 数（${sections.length}）不等，请确认无章节漏编号`);
    }
  } else {
    warn('未找到 .idx 编号徽章，章节缺少视觉编号');
  }
}

/* ═════════ 5. 标签配对 ════════════════════════════════════════ */
{
  // 移除注释与 script/style 内容后再扫描标签
  let scan = html
    .replace(/<!--[\s\S]*?-->/g, '')
    .replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi, '<script></script>')
    .replace(/<style\b[^>]*>[\s\S]*?<\/style>/gi, '<style></style>');

  const VOID = new Set(['area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
    'link', 'meta', 'param', 'source', 'track', 'wbr']);
  // HTML 允许省略闭合的标签：遇到不匹配时静默弹出
  const OPTIONAL = new Set(['li', 'p', 'td', 'th', 'tr', 'thead', 'tbody', 'tfoot',
    'option', 'dt', 'dd', 'optgroup', 'colgroup', 'caption', 'rp', 'rt']);

  const stack = [];
  const errors = [];
  const tagRe = /<(\/?)([a-zA-Z][a-zA-Z0-9-]*)\b([^>]*?)(\/?)>/g;
  let m;
  while ((m = tagRe.exec(scan))) {
    const isClose = m[1] === '/';
    const tag = m[2].toLowerCase();
    const selfClose = m[4] === '/';
    const line = scan.slice(0, m.index).split('\n').length;

    if (VOID.has(tag)) continue;

    if (!isClose) {
      if (selfClose) continue;
      stack.push({ tag, line });
    } else {
      if (!stack.length) { errors.push(`第 ${line} 行：多余的 </${tag}>（无对应开标签）`); continue; }
      if (stack[stack.length - 1].tag === tag) { stack.pop(); continue; }
      // 向上寻找匹配；途中仅允许跨越「可省略闭合」的标签
      let found = -1;
      for (let k = stack.length - 1; k >= 0; k--) {
        if (stack[k].tag === tag) { found = k; break; }
        if (!OPTIONAL.has(stack[k].tag)) break;
      }
      if (found >= 0) {
        const orphan = stack.splice(found + 1);   // 被跨过的省略闭合标签
        const bad = orphan.filter(d => !OPTIONAL.has(d.tag));
        if (bad.length) {
          errors.push(`第 ${line} 行：</${tag}> 之前有未闭合标签 ` +
            bad.map(b => `<${b.tag}>（第 ${b.line} 行）`).join('、'));
        }
        stack.pop();                              // 弹出匹配项
      } else {
        errors.push(`第 ${line} 行：</${tag}> 与栈顶 <${stack[stack.length - 1].tag}>（第 ${stack[stack.length - 1].line} 行）不匹配`);
      }
    }
  }

  const unclosed = stack.filter(s => !OPTIONAL.has(s.tag));
  if (unclosed.length) {
    fail(`未闭合标签 ${unclosed.length} 个：` +
      unclosed.slice(0, 8).map(u => `<${u.tag}> 第 ${u.line} 行`).join('、') +
      (unclosed.length > 8 ? ' …' : ''));
  }
  if (errors.length) {
    fail(`标签配对异常 ${errors.length} 处：` + errors.slice(0, 6).join('；') + (errors.length > 6 ? ' …' : ''));
  }
  if (!unclosed.length && !errors.length) pass('标签配对正常（div / section / table / canvas 等）');

  const divOpen = (scan.match(/<div\b/g) || []).length;
  const divClose = (scan.match(/<\/div>/g) || []).length;
  if (divOpen === divClose) pass(`<div> 开闭平衡：${divOpen} 对`);
}

/* ═════════ 6. 必备章节关键词 ══════════════════════════════════ */
{
  const REQUIRED = [
    ['执行摘要', /执行摘要|核心结论/],
    ['行业界定与口径', /行业界定|口径说明|口径基准/],
    ['市场规模与增长', /市场规模/],
    ['产业链与利润池', /产业链|利润池/],
    ['竞争格局', /竞争格局|市场份额/],
    ['供需与价格', /供需|价格走势/],
    ['驱动因素', /驱动因素|PESTEL/],
    ['情景预测', /情景预测|情景分析/],
    ['风险与免责', /风险提示|风险清单|免责声明/],
    ['附录', /附录/],
  ];
  const missing = REQUIRED.filter(([, re]) => !re.test(html)).map(([n]) => n);
  if (missing.length) fail(`缺少必备章节：${missing.join('、')}`);
  else pass(`必备章节齐全：10/10`);

  const APPX = [['附录 A 数据来源清单', /附录\s*[AＡ]/], ['附录 B 口径分歧矩阵', /附录\s*[BＢ]/],
                ['附录 C 未找到公开来源', /附录\s*[CＣ]/], ['附录 D 术语与缩写', /附录\s*[DＤ]/]];
  const missAppx = APPX.filter(([, re]) => !re.test(html)).map(([n]) => n);
  if (missAppx.length) {
    warn(`附录未按 A/B/C/D 分节编号（缺：${missAppx.join('、')}）——合并为单节时读者无法定位` +
      '。若确有取舍，请在报告中说明');
  } else pass('附录 A–D 齐全且已分节编号');
}

/* ═════════ 7. 报告头部元信息 ══════════════════════════════════ */
{
  const headerBlock = (html.match(/<header\b[\s\S]*?<\/header>/i) || [''])[0];
  if (!headerBlock) fail('未找到 <header> 区块，报告头部元信息无处承载');

  const META = [
    ['口径基准', /口径基准/],
    ['分析周期', /分析周期|周期/],
    ['数据截止日', /数据截止/],
    ['报告生成日', /报告生成/],
    ['主币种与汇率时点', /币种|汇率/],
    ['来源数', /来源数/],
  ];
  const missDoc = META.filter(([, re]) => !re.test(html)).map(([n]) => n);
  const missHeader = META.filter(([, re]) => re.test(html) && !re.test(headerBlock)).map(([n]) => n);

  if (missDoc.length) fail(`报告头部元信息缺失（全文均未出现）：${missDoc.join('、')}`);
  else if (missHeader.length) fail(`以下元信息存在但未置于 <header> 内：${missHeader.join('、')}——按规范须集中放在报告头部`);
  else pass('报告头部元信息齐全：口径基准 / 分析周期 / 数据截止 / 报告生成 / 主币种与汇率 / 来源数');

  if (!/不构成.*投资建议|投资建议/.test(html)) fail('缺少免责声明（不构成投资建议）');
  else pass('免责声明已包含');

  /* 数据截止 vs 报告生成 间隔 >90 天（尽力解析） */
  const grab = (label) => {
    const re = new RegExp(label + '[^0-9]{0,24}(\\d{4})[-/.年](\\d{1,2})[-/.月](\\d{1,2})');
    const m = html.match(re);
    if (!m) return null;
    const d = new Date(+m[1], +m[2] - 1, +m[3]);
    return isNaN(d) ? null : d;
  };
  const cutoff = grab('数据截止'), made = grab('报告生成');
  if (cutoff && made) {
    const days = Math.round((made - cutoff) / 86400000);
    if (days > 90) warn(`数据截止距报告生成 ${days} 天（>90 天），须在报告中说明原因`);
    else if (days >= 0) pass(`数据时效性正常：截止距生成 ${days} 天`);
    else warn('报告生成日早于数据截止日，请检查日期是否填反');
  }
}

/* ═════════ 8. 可信度标注与涨跌语义 ════════════════════════════ */
{
  const badge = (html.match(/class="b b-[123n]"/g) || []).length;
  if (badge === 0) fail('全文没有任何可信度徽章（★★★/★★/★/【估算】）—— 可信度逐项标注为强制要求');
  else pass(`可信度徽章出现 ${badge} 次`);

  const upDownVar = /--up\s*:\s*var\(--red\)/.test(html) && /--down\s*:\s*var\(--green\)/.test(html);
  if (!upDownVar) {
    warn('未检出「红涨绿跌」令牌（--up:var(--red) / --down:var(--green)），请确认未误用欧美惯例');
  } else pass('涨跌语义色符合中国市场惯例（红涨绿跌）');

  if (!/prefers-reduced-motion/.test(html)) fail('缺少 prefers-reduced-motion 动效降级（视觉规范强制项）');
  else pass('动效降级已包含');

  if (!/overflow-x\s*:\s*auto/.test(html)) warn('未见表格横向滚动（overflow-x:auto），小屏可能溢出');
  else pass('表格已设横向滚动容器');

  const idxCount = (html.match(/class="idx"/g) || []).length;
  const idxAria = (html.match(/class="idx"[^>]*aria-hidden/g) || []).length;
  if (idxCount && idxAria < idxCount) {
    warn(`${idxCount - idxAria} 个章节编号徽章缺少 aria-hidden="true"（徽章为装饰元素，不应进入无障碍树）`);
  } else if (idxCount) pass('章节编号徽章已作无障碍隐藏');
}

/* ═════════ 9. 令牌外裸色的出现 ════════════════════════════════ */
{
  const ALLOW = new Set([
    // 默认预设 · 弘讯暗色（tokens.json dark 节）
    // 表面层级
    '#121826', '#1e293b', '#243044', '#0f172a', '#0a2540', '#334155',
    // 文字阶梯
    '#f1f5f9', '#cbd5e1', '#94a3b8',
    // 主色 / 辅调 / 链接
    '#3b82f6', '#60a5fa', '#2563eb', '#38bdf8',
    // 功能色（dark.functional，Web 端）
    '#52c41a', '#ff4d4f', '#ffa940', '#22c55e',
    // 功能色柔底
    '#162312', '#2e2410', '#2a1414', '#0e2018',
    // 中性补充 / 图表网格
    '#475569', '#3e4c63',
    // 图表 8 色扩展板
    '#0066cc', '#00a3e0', '#00c7be', '#00d4a1',
    '#ff9500', '#ff4d4d', '#8a5cf5', '#ff66c2',
    // 弘讯其余令牌（品牌色 / 移动端图表色，规范文档中会提及）
    '#005eae', '#1d4ed8', '#059669',
    // 预设 B · hot-analysis 深藏蓝紫
    '#0b0f19', '#131a2b', '#1a2339', '#1e2d4a', '#16203a', '#e2e8f0',
    '#64748b', '#a78bfa', '#34d399', '#f87171', '#fb923c', '#fbbf24',
    '#243352',
    // 预设 C · shadcn Zinc
    '#09090b', '#18181b', '#141417', '#27272a', '#fafafa', '#a1a1aa', '#71717a',
    '#06b6d4', '#8b5cf6', '#f97316', '#eab308',
    // 中性 / 打印
    '#ffffff', '#fff', '#000000', '#000', '#111111', '#111',
  ]);
  const found = new Map();
  for (const m of html.matchAll(/#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b/g)) {
    const key = m[0].toLowerCase();
    if (ALLOW.has(key)) continue;
    if (!found.has(key)) found.set(key, html.slice(0, m.index).split('\n').length);
  }
  if (found.size) {
    const list = [...found.entries()].slice(0, 12)
      .map(([hex, line]) => `${hex}(第${line}行)`).join('、');
    warn(`发现 ${found.size} 个令牌外裸色：${list}` + (found.size > 12 ? ' …' : '') +
      '。颜色应取自 references/报告风格与组件规范.md 的令牌，或复用 JS 颜色常量');
  } else {
    pass('未发现令牌外裸色');
  }
}

/* ═════════ 10. 金额单位规范（金额「亿」必须带币种） ═══════════ */
{
  // 设计取舍：只抓「疑似金额但缺币种」，避免把「18亿用户」「9亿次」这类计数误报。
  // 判定：`亿` 后紧跟币种或量词 → 通过；否则再看前 24 字是否出现金额语境词。
  const CUR = /^(美元|欧元|人民币|日元|韩元|港元|元|台币|卢比)/;
  const COUNT = /^(次|人|户|用户|名|条|台|部|吨|个|份|张|种|家|集|期|播放|下载|安装|观看|粉丝|观众|GB|TB|参数|MAU|DAU|SKU)/;
  const MONEY_CUE = /(规模|收入|营收|产值|GMV|融资|投资|金额|成本|利润|估值|市值|费用|预算|交易额|流水|补贴|广告费|预算|ARPU)/;

  const bad = [];
  const re = /\d(?:[\d,.]*\d)?\s*亿/g;
  let m;
  while ((m = re.exec(html))) {
    const after = html.slice(m.index + m[0].length, m.index + m[0].length + 6);
    if (CUR.test(after) || COUNT.test(after)) continue;
    const before = html.slice(Math.max(0, m.index - 24), m.index).replace(/<[^>]*>/g, '');
    if (!MONEY_CUE.test(before)) continue;
    const line = html.slice(0, m.index).split('\n').length;
    const ctx = (before + m[0] + after).replace(/\s+/g, '');
    bad.push(`第${line}行「…${ctx}…」`);
    if (bad.length >= 10) break;
  }
  if (bad.length) {
    warn(`疑似金额但「亿」未带币种 ${bad.length}${bad.length >= 10 ? '+' : ''} 处：` +
      bad.slice(0, 5).join('；') + '。金额须写「亿元」/「亿美元」，否则读者无法判断币种');
  } else {
    pass('金额单位规范：未发现缺币种的裸「亿」');
  }
}

/* ═════════ 11. 附录一致性 / 结构体积 ═════════════════════════ */
{
  const size = Buffer.byteLength(html, 'utf8');
  if (size < 25 * 1024) warn(`报告仅 ${(size / 1024).toFixed(1)} KB，10 章内容可能过于单薄`);
  else pass(`报告体积 ${(size / 1024).toFixed(1)} KB`);

  const tables = (html.match(/<table\b/g) || []).length;
  const twWrapped = (html.match(/<div class="tw">[\s\S]{0,40}<table/g) || []).length;
  if (tables && twWrapped < tables) {
    warn(`${tables - twWrapped} 张表格未包在 .tw 容器内（缺横向滚动与边框圆角）`);
  } else if (tables) pass(`${tables} 张表格均置于 .tw 容器`);

  const rows = (html.match(/<tr\b/g) || []).length;
  pass(`表格行数：${rows}`);

  if (!/<meta\s+name=["']viewport["']/i.test(html)) fail('缺少 viewport meta，移动端将按桌面宽度渲染');
  else pass('viewport meta 已设置');
  if (!/<html[^>]*lang=/i.test(html)) warn('缺少 html lang 属性（影响中文排版与朗读）');
  if (!/<title>[^<]*[\u4e00-\u9fa5]/.test(html)) warn('<title> 未包含中文标题');
}

/* ── 输出 ─────────────────────────────────────────────────────── */
const strictPromoted = opts.strict ? WARN.splice(0).concat(FAIL) : null;
if (opts.strict && strictPromoted) { FAIL.length = 0; FAIL.push(...strictPromoted); }

const lines = [];
const bar = '─'.repeat(64);
lines.push(bar);
lines.push('LBJ-行业分析 · 报告结构校验');
lines.push(`目标：${target}`);
lines.push(`模式：${opts.framework ? '框架版（允许待采集）' : '正式版'}${opts.strict ? ' · 严格模式' : ''}`);
lines.push(bar);

if (FAIL.length) {
  lines.push('');
  lines.push(`✗ FAIL · ${FAIL.length} 项`);
  FAIL.forEach((f, i) => lines.push(`  ${i + 1}. ${f}`));
}
if (WARN.length) {
  lines.push('');
  lines.push(`! WARN · ${WARN.length} 项`);
  WARN.forEach((w, i) => lines.push(`  ${i + 1}. ${w}`));
}
if (!opts.quiet && PASS.length) {
  lines.push('');
  lines.push(`✓ PASS · ${PASS.length} 项`);
  PASS.forEach(p => lines.push(`  · ${p}`));
}

lines.push('');
lines.push(bar);
const verdict = FAIL.length === 0
  ? (WARN.length ? `结论：通过（${WARN.length} 项提醒待确认）` : '结论：全部通过 ✓')
  : `结论：不通过 — ${FAIL.length} 项 FAIL 必须修复后才能宣告完成`;
lines.push(verdict);
lines.push(bar);

const text = lines.join('\n') + '\n';
process.stdout.write(text);

if (opts.out) {
  try {
    fs.writeFileSync(path.resolve(opts.out), text, 'utf8');
  } catch (e) { console.error(`写 --out 失败：${e.message}`); }
}
if (opts.json) {
  try {
    fs.writeFileSync(path.resolve(opts.json), JSON.stringify({
      target, framework: opts.framework, strict: opts.strict,
      fail: FAIL, warn: WARN, pass: PASS,
      verdict: FAIL.length === 0 ? 'pass' : 'fail',
    }, null, 2), 'utf8');
  } catch (e) { console.error(`写 --json 失败：${e.message}`); }
}

process.exit(FAIL.length ? 1 : 0);
