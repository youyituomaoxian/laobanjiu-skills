---
name: adversarial-review
description: |
  Adversarial code review pipeline — Red Team attacks, Blue Team defends, main agent arbitrates.
  This skill should be used when the user asks to review, audit, or security-check a specific source file
  with adversarial rigor. Triggers on: 对抗审查, 对抗性审查, 攻击性审查, /adversarial-review,
  "adversarial code review", "review FILE adversarial", "security audit FILE".
  Supports all languages and frameworks — auto-detects project toolchain.
agent_created: true
---

# Adversarial Review

Six-phase adversarial code review in WorkBuddy GUI.
The main agent is the pipeline — sub-agents provide opposing perspectives, main agent arbitrates and fixes.

## Quick Start

```
User: 对抗审查 src/App.jsx
User: /adversarial-review src/components/Hero.jsx
```

---

## Pipeline Overview

```
Phase 0: Preflight        → linter + build results (main agent)
Phase 1: Red Team Attack  → adversarial audit (sub-agent, background)
Phase 2: Blue Team Defense → response to every accusation (sub-agent, background)
Phase 3: Cross-Adjudication → main agent reads both, rules on each defect
Phase 4: Fix              → main agent applies confirmed fixes
Phase 5: Verification     → QA sub-agent checks for regressions (sub-agent, background)
```

Output directory: `<workspace>/.workbuddy/review/`

| File | Phase | Description |
|------|-------|-------------|
| `00_preflight.md` | 0 | Lint/build results |
| `01_red.md` | 1 | Red Team attack report |
| `02_blue.md` | 2 | Blue Team defense report |
| `03_verdict.md` | 3 | Main agent's adjudication |
| `04_changes.md` | 4 | Diff summary of fixes |
| `05_final.md` | 5 | QA verification + GO/NO-GO |

---

## Phase 0: Preflight

**Main agent only. No sub-agent needed.**

1. Read the target file (Read tool).
   - **If file not found → abort:** "File not found: `<path>`. Please check the path."
2. Ensure `.workbuddy/review/` exists: `mkdir -p .workbuddy/review/`
3. Detect toolchain: check for `package.json`, `pyproject.toml`, etc.
4. Run available linters and type-checkers via Bash. Capture all output.
   - If a tool is not installed, note "Not installed" — do NOT attempt to install it.
5. Write results to `00_preflight.md`.

---

## Phase 1: Red Team Attack

**Launch as sub-agent, background mode.** See `references/workflow_detail.md` for exact Agent tool call format.

### Role Definition (embed in sub-agent prompt)

```
You are a malicious auditor. Your ONLY goal is to find real defects.
Every line is guilty until proven innocent. Assume:

- Every input may be null, undefined, or malicious.
- Every async operation may have a race condition.
- Every boundary condition has already been triggered.
- Every useEffect/side-effect may leak or fire incorrectly.

Attack dimensions (priority order):
1. SECURITY: injection, XSS, auth bypass, secret leakage, unsafe eval
2. CORRECTNESS: off-by-one, state inconsistency, race conditions, missing cleanup
3. ROBUSTNESS: null/undefined, error propagation, timeout handling, empty states
4. PERFORMANCE: O(n²) traps, missing memoization, unnecessary re-renders, memory leaks

Rules:
- Only report defects you are CONFIDENT exist. No "maybe."
- For every defect: exact line range, trigger path, CVSS-style severity.
- For code files: Use Grep to trace imports and cross-references to find hidden dependencies.

Output: .workbuddy/review/01_red.md
Format:
  ## [DEFECT-ID] Severity: Critical/High/Medium/Low
  **Location:** <file>:<line range>
  **Type:** Security/Correctness/Robustness/Performance
  **Trigger Path:** step-by-step
  **Impact:** what happens
  **Fix Direction:** one-line suggestion
```

Inject into prompt:
- Full target file content
- Full `00_preflight.md` content
- Relevant sections from `references/attack_vectors.md` (match language/framework)

### Wait & Verify

Wait for background task notification. Use `TaskOutput` to retrieve output.
Then verify `01_red.md` was written. If not → retry once with simplified prompt.

---

## Phase 2: Blue Team Defense

**Launch as sub-agent, background mode. ONLY after Phase 1 completes.**

### Role Definition (embed in sub-agent prompt)

```
You are the author defending your code in adversarial review.
Respond to EVERY accusation in the Red Team report below.

For each [DEFECT-ID]:
1. Verdict: CONFIRMED / DISPUTED / NEEDS_CONTEXT
2. If DISPUTED: cite specific code lines that prove your defense
3. If CONFIRMED: acknowledge honestly, rate severity, explain root cause
4. If NEEDS_CONTEXT: explain what additional info would resolve it

Your incentive: maximize successfully defended accusations with concrete evidence.
Do NOT make excuses — only defend with facts.

Output: .workbuddy/review/02_blue.md

Format:
  ## Response to [DEFECT-ID]
  **Verdict:** CONFIRMED / DISPUTED / NEEDS_CONTEXT
  **Evidence:** <code reference or reasoning>
  **Proposed Fix:** (if CONFIRMED) specific code change
```

Inject into prompt:
- Full target file content
- Full `01_red.md` content

### Wait & Verify

Wait for background task notification. Verify `02_blue.md` was written.

---

## Phase 3: Cross-Adjudication

**Main agent. Read both reports, rule on every defect.**

### Verdict Classification

| Verdict | Condition | Action |
|---------|-----------|--------|
| CONFIRMED | Both agree, or independent verification confirms Red | Fix in Phase 4 |
| DISPUTED_VALID | Blue's evidence convincing, Red's claim false | Dismiss |
| NEEDS_CONTEXT | Blue cannot judge without more info | Independent verify → rule or escalate to UNDECIDABLE |
| UNDECIDABLE | Cannot determine from code + tools alone | Ask user |
| NEW_FINDING | Blue admitted defect Red missed | Treat as CONFIRMED |

### UNDECIDABLE Boundary

Mark UNDECIDABLE ONLY when:
- Dispute hinges on **design intent**, not code correctness
- Linter/tests cannot resolve the question
- Example: "useMemo here or not" — correct either way, depends on intent

Do NOT mark UNDECIDABLE to avoid making a call. If you can verify with Read + Bash + Grep, do it.

### Resolution Protocol

For each disputed defect:
1. Read the disputed code lines with Read tool.
2. Run linter: `npx eslint <file> 2>&1 || true`
3. Search for similar patterns: `Grep` across codebase
4. If evidence is clear → rule CONFIRMED or DISPUTED_VALID
5. If still ambiguous → mark UNDECIDABLE

### Output

Write `03_verdict.md`:
```markdown
# Adversarial Review Verdict — <file> — <date>

## Summary
| Total | Confirmed | Disputed | Undecidable | New Findings |
|-------|-----------|----------|-------------|--------------|
| N     | N         | N        | N           | N            |

## Confirmed (Will Fix)
[Each defect with full detail]

## Disputed (Dismissed with Reason)
[Each with evidence for dismissal]

## Requires Human Review
[Each UNDECIDABLE item with both sides' arguments]
```

### UNDECIDABLE Handling

If any UNDECIDABLE items exist:
- Use `AskUserQuestion` to present them one by one with Red/Blue positions.
- Wait for user response before proceeding to Phase 4.
- **Reclassify:** user-confirmed → CONFIRMED, user-dismissed → DISPUTED_VALID.
- **Update `03_verdict.md`** verdict table with resolved counts before checking the gate below.

If zero CONFIRMED + zero NEW_FINDING:
- Skip Phase 4 & 5. Write a clean bill of health to `05_final.md`. Done.

---

## Phase 4: Fix

**Main agent. Apply fixes for all CONFIRMED defects.**

1. Fix one defect at a time with the `Edit` tool.
2. After all fixes: run linter and type-checker again.
3. Write `04_changes.md` — each fix with before/after snippets and line ranges.

---

## Phase 5: Verification

**Launch as sub-agent, background mode. ONLY after Phase 4 linter passes.**

### Role Definition (embed in sub-agent prompt)

```
You are a QA engineer verifying code fixes. Do NOT re-audit the file.
Focus ONLY on verifying fixes resolved defects without regressions.

Context to read:
- .workbuddy/review/03_verdict.md (confirmed defects)
- .workbuddy/review/04_changes.md (what was changed)
- The modified source file directly

For each fix:
1. Verify the defect is actually resolved.
2. Check surrounding code (5 lines above/below) was not broken.
3. Look for NEW issues introduced by the change.

Run build + linter if available.
Optionally reference `assets/report_template.md` for output styling (scorecard, executive summary).

Output: .workbuddy/review/05_final.md

| DEFECT-ID | Status | Notes |
|-----------|--------|-------|
| ... | PASS / FAIL / NEW_ISSUE | ... |

Build: PASS / FAIL / N/A
Lint: PASS / FAIL / N/A
Final Verdict: GO / NO-GO
```

### Error Handling

- FAIL or NEW_ISSUE → final verdict NO-GO. Report to user with details. Do NOT auto-fix.
- Build/lint failure: check if pre-existing in `00_preflight.md`. Pre-existing → don't block. New → NO-GO.

---

## Final Presentation

After Phase 5:
1. Read `05_final.md`.
2. Present summary: file, defects found/fixed/disputed/undecidable, verdict.
3. Use `present_files` to show `05_final.md`.

---

## Resources

- `references/workflow_detail.md` — Exact Agent tool call formats, wait/sync logic, error recovery paths.
- `references/attack_vectors.md` — Vulnerability patterns by language/framework. Inject into Phase 1.
- `references/design.md` — Design rationale, UltraCode comparison, limitations. Read when user asks "why."
- `assets/report_template.md` — Final report markdown template for Phase 5 output styling.

---

## Limitations

1. **Single-model bias.** Sub-agents share the same model. Role-prompting creates divergent attention but deep blind spots may persist. Cannot assign different models per agent (GUI limitation).
2. **Static analysis only.** No runtime fuzzing, no exploit validation, no dynamic analysis.
3. **Two-round cap.** Red → Blue → Judge. No convergence loop. Sufficient for 80% of defects; deep multi-round review needs CLI Workflow.
4. **Semi-manual orchestration.** Phase transitions require the main agent to complete before launching the next. Fully automated chaining requires CLI Dynamic Workflow.
