# Workflow Detail — 子Agent调用与错误处理

> **Read this before executing any phase that involves sub-agents.**
> Contains exact tool call formats, wait/sync logic, and error recovery paths.

---

## Sub-Agent Launch Pattern

Every sub-agent is launched via the `Agent` tool. Use `run_in_background: true` so the
main session is not blocked.

### Standard Launch

```json
{
  "subagent_type": "general-purpose",
  "description": "Red Team adversarial code audit",
  "prompt": "<full role definition + code + attack vectors>",
  "run_in_background": true
}
```

### Wait for Completion

After launching a background agent, write its output file path to a known location and
wait for the task notification. The notification arrives automatically — do NOT poll.

When the notification arrives, use `TaskOutput` to retrieve the agent's output:

```json
{
  "task_id": "<task_id_from_notification>"
}
```

Then read the output file the agent wrote (e.g., `.workbuddy/review/01_red.md`).

### Foreground Alternative

If `run_in_background` is omitted, the agent runs in the foreground and returns results
directly. This is simpler but blocks the main session. Use background for all phases
except Phase 0 (preflight, which is fast and done by the main agent itself).

---

## Phase 0: Preflight — Exact Steps

```
1. Read <target_file> with the Read tool.
   If file not found → abort with "File not found: <path>"

2. Detect project type:
   - package.json → JavaScript/TypeScript project
   - pyproject.toml / setup.py → Python project
   - Neither → skip toolchain detection

3. Run linter (if applicable):
   JS/TS: Bash("npx eslint <file> 2>&1 || true")
   Python: Bash("ruff check <file> 2>&1 || true")
   If command fails because tool not installed → note "Not installed" in preflight

4. Run type-checker (if TS):
   Bash("npx tsc --noEmit 2>&1 || true")

5. Write results to .workbuddy/review/00_preflight.md:
   mkdir -p .workbuddy/review/
   Write output with sections:
   [File Info] — MUST include: Target file path, Detected language, Project type (if any)
   [Lint Results]
   [Type Check]
   [Build Status]
```

---

## Phase 1: Red Team Attack — Exact Launch

```
Prompt structure for the sub-agent:

"""
## Role
<role definition from SKILL.md Phase 1>

## Target File
<full content of the target file, read with Read tool>

## Preflight Results
<full content of 00_preflight.md, or "No preflight available" if Phase 0 had no tools>

## Applicable Attack Vectors
<load references/attack_vectors.md, extract sections matching the detected language.
 For JS/TS: include Universal + JavaScript/TypeScript Specific + React sections.
 For Python: include Universal + Python Specific sections.
 Always include General Architecture Smells.>

## Output Requirements
Write your complete attack report to .workbuddy/review/01_red.md.
Use the format: [DEFECT-ID] Severity: X | Location: file:line | Type: X | Trigger Path | Impact | Fix Direction
Only report defects you are CONFIDENT exist.
"""
```

### Error Handling

- If sub-agent returns without writing 01_red.md → retry once with simplified prompt (see below).
- If sub-agent claims 0 defects → verify by spot-checking 3 random code sections before accepting.

### Simplified Prompt Definition (Retry Fallback)

If Phase 1 sub-agent fails, retry with this stripped prompt that drops attack vectors and preflight:

"""
You are a code auditor. Find real defects in the target file below.
For each defect: give exact line range, what is wrong, and severity (Critical/High/Medium/Low).
Only report defects you are 100% confident exist.
Write output to .workbuddy/review/01_red.md

## Target File
<full target file content>
"""

---

## Phase 2: Blue Team Defense — Exact Launch

```
START ONLY AFTER: 01_red.md exists and has been read by the main agent.

Prompt structure:

"""
## Role
<role definition from SKILL.md Phase 2>

## Target File
<full content of the target file, from same Read used in Phase 1>

## Red Team Accusations (Respond to EVERY ONE)
<full content of 01_red.md>

## Instructions
For each [DEFECT-ID] in the Red Team report:
1. State your verdict: CONFIRMED / DISPUTED / NEEDS_CONTEXT
2. If DISPUTED: cite specific code lines that prove your defense
3. If CONFIRMED: acknowledge honestly, rate severity, explain root cause
4. If NEEDS_CONTEXT: explain what additional context would resolve ambiguity

## Output
Write to .workbuddy/review/02_blue.md
"""
```

### Error Handling

- If Blue claims CONFIRMED on a defect Red didn't find → flag as NEW_FINDING in Phase 3.
- If Blue's response is too brief (under 50 words per accusation) → re-invoke with stronger emphasis on detail.

---

## Phase 3: Cross-Adjudication — Decision Rules

```
1. Read 01_red.md and 02_blue.md using Read tool.

2. For each defect, classify:

   Both CONFIRMED → CONFIRMED (proceed to fix)
   Red says bug, Blue says DISPUTED:
     a. Read the disputed code lines directly
     b. Run linter/type-checker on those lines
     c. Search for similar patterns in codebase (Grep)
     d. If evidence supports Red → CONFIRMED
     e. If evidence supports Blue → DISPUTED_VALID
     f. If ambiguous even after verification → UNDECIDABLE

   Blue admits to defect Red missed → NEW_FINDING, treat as CONFIRMED

3. UNDECIDABLE boundary:
   Mark UNDECIDABLE ONLY when:
   - The dispute hinges on design intent (not code correctness)
   - The code is correct but the pattern is debatable (e.g., "useMemo here or not")
   - Running linter/tests cannot resolve the question
   Do NOT mark things UNDECIDABLE just to avoid making a call.

4. Write verdict to .workbuddy/review/03_verdict.md using format from SKILL.md Phase 3.

5. If any UNDECIDABLE items exist → present them to the user and ASK for ruling.
   Use AskUserQuestion tool with clear pros/cons for each undecidable item.
   Wait for user response before proceeding.

6. If zero CONFIRMED + zero NEW_FINDING → output clean bill of health to 05_final.md,
   skip Phase 4 & 5, done.
```

---

## Phase 4: Fix — Exact Steps

```
1. For each CONFIRMED defect in order:
   a. Use Edit tool on the target file to apply the fix.
   b. Fix ONE defect at a time to avoid merge conflicts.
   c. If two fixes overlap on the same line range → merge them manually.

2. After all fixes applied:
   a. Run linter again: Bash("npx eslint <file> 2>&1 || true")
   b. If new lint errors → fix them before proceeding.
   c. Run type-checker if applicable.

3. Record changes:
   Write .workbuddy/review/04_changes.md listing each fix:
   - DEFECT-ID
   - Before/After code snippets
   - Lines changed
```

---

## Phase 5: Verification — Exact Launch

```
START ONLY AFTER: Phase 4 completed, linter passes.

Prompt structure:

"""
## Role
You are a QA engineer verifying code fixes. Do NOT re-audit the entire file.
Focus ONLY on verifying that the fixes resolved the defects without introducing regressions.

## Context
- Read .workbuddy/review/00_preflight.md for project toolchain (detected language, linter used, build command)
- Read .workbuddy/review/03_verdict.md for the list of confirmed defects
- Read .workbuddy/review/04_changes.md for what was changed
- Read the modified source file directly

## For Each Fix
1. Verify the defect is actually resolved (the trigger path no longer works)
2. Check that surrounding code (5 lines above/below) was not broken
3. Look for any NEW issues introduced by the change

## Build & Lint
- Run the SAME linter command shown in 00_preflight.md (if any).
- Run the SAME build command shown in 00_preflight.md (if any).
- Compare results: pre-existing failures from 00_preflight.md → do not block. New failures → flag.

## Output
Write to .workbuddy/review/05_final.md

Format:
# Fix Verification
| DEFECT-ID | Status | Notes |
|-----------|--------|-------|
| ... | PASS / FAIL / NEW_ISSUE | ... |

# Build & Lint
PASS / FAIL / N/A

# Final Verdict
GO — all fixes verified, no regressions
NO-GO — <list of failing items, what needs attention>
"""
```

### Error Handling

- If any fix gets FAIL or NEW_ISSUE → mark final verdict as NO-GO.
  Do NOT attempt to re-fix. Report to user with exact failure details.
- If build/lint fails → check if the failure existed before the review (compare with 00_preflight.md).
  If pre-existing → note it but do not block GO verdict.
  If new → NO-GO.

---

## Final Presentation

After Phase 5 completes:
1. Read .workbuddy/review/05_final.md
2. Present a concise summary to the user:
   - File reviewed
   - Defects found / fixed / disputed / undecidable
   - Final verdict (GO / NO-GO)
   - Path to full report: .workbuddy/review/05_final.md

Use the `present_files` tool to show 05_final.md if it exists.

---

## Tool Availability Assumptions

All phases assume the following tools are available:
- `Read` — read files (always available)
- `Write` — write output files (always available)
- `Edit` — apply code fixes (always available)
- `Bash` — run linter, type-checker, build commands (always available)
- `Grep` — search codebase for patterns (always available)
- `Agent` — launch sub-agents (available in WorkBuddy with sub-agent support)
- `TaskOutput` — retrieve background agent results (available when Agent tool is)
- `AskUserQuestion` — ask user to resolve UNDECIDABLE items (always available)
