---
name: "Analyze: Run Autonomous Analysis"
description: Launch the autonomous data analysis agent for a given topic
category: Analysis
tags: [analysis, autonomous, gemini]
---

Launch the autonomous analysis agent (`auto_analyst`) for a given topic.

**Input**: The argument after `/analyze:run` is the topic. If none, ask.

## Steps

### 1. Get topic

If no argument provided, use **AskUserQuestion** to ask:
> "要分析什麼主題？例如：「睡眠品質惡化的原因」、「運動對睡眠的影響」"

### 2. Check API key

Read `.env` at the project root. If `GEMINI_API_KEY` is missing or still placeholder:
> "請先在 `.env` 填入你的 Gemini API Key：`GEMINI_API_KEY=你的金鑰`"

Stop here if key is missing.

### 3. Parse options

From the argument string, extract:
- `--max-iter N` → use N (default: 12, max: 20)
- `--hypothesis "..."` → pass as initial hypothesis

### 4. Run the agent

```bash
cd analysis
../.venv/bin/python auto_analyst/run.py "<topic>" --max-iter <N>
```

Show output as it streams. Each iteration prints:
- 當前假設
- 執行結果摘要
- Agent 決策 (a深挖 / b側探 / c回溯 / d停止)

### 5. Report results

When done:
- Output directory: `analysis/auto_analyst/outputs/<timestamp>/`
- Number of iterations completed
- First 50 lines of `story.md`
- Paths to generated charts

## Guardrails
- Do NOT modify analysis code before running
- If execution fails, show stderr and suggest checking `.env`
- Refuse if `--max-iter` > 20
