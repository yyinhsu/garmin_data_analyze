"""
Main orchestration loop for autonomous data analysis.

Usage:
    from auto_analyst.orchestrator import run
    run(topic="睡眠品質", max_iterations=15)
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .agent import AnalysisAgent
from .executor import run as exec_code
from .tree import AnalysisTree

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _log(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def _section(title: str):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


# ─────────────────────────────────────────────────────────────────────────────
# Core loop
# ─────────────────────────────────────────────────────────────────────────────

def run(
    topic: str,
    initial_hypothesis: str | None = None,
    max_iterations: int = 15,
    output_dir: Path | None = None,
    api_key: str | None = None,
) -> str:
    """
    Run the autonomous analysis loop.

    Parameters
    ----------
    topic               : High-level research question (e.g. "睡眠品質惡化的原因")
    initial_hypothesis  : Starting hypothesis; defaults to the topic itself
    max_iterations      : Safety cap on the number of analysis rounds
    output_dir          : Where to save PNGs, tree.json, story.md
    api_key             : Anthropic API key (falls back to ANTHROPIC_API_KEY env var)

    Returns
    -------
    Markdown story string (also saved to output_dir/story.md)
    """
    # --- Setup ---
    if output_dir is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path(__file__).parent / "outputs" / ts
    output_dir.mkdir(parents=True, exist_ok=True)

    _section(f"自主分析開始: {topic}")
    _log(f"輸出目錄: {output_dir}")

    agent = AnalysisAgent(api_key=api_key)
    tree = AnalysisTree(topic=topic, output_dir=output_dir)

    hypothesis = initial_hypothesis or topic
    parent_id: int | None = None

    # ------------------------------------------------------------------ #
    # Main loop
    # ------------------------------------------------------------------ #
    for iteration in range(max_iterations):
        _section(f"迭代 {iteration + 1}/{max_iterations}")
        _log(f"假設: {hypothesis}")

        # 1. Generate analysis code
        _log("Agent 正在生成分析代碼 ...")
        code = agent.generate_code(
            topic=topic,
            hypothesis=hypothesis,
            tree_summary=tree.summary(),
        )
        _log(f"代碼長度: {len(code)} 字元")

        # 2. Execute
        _log("執行代碼 ...")
        result = exec_code(code, output_dir=output_dir, node_id=tree._next_id)
        if result.success:
            _log(f"執行成功 — {len(result.png_paths)} 張圖表")
        else:
            _log(f"執行失敗 — stderr 前 200 字: {result.stderr[:200]}")

        # 3. Interpret
        _log("Agent 正在解讀結果 ...")
        interp = agent.interpret(
            topic=topic,
            hypothesis=hypothesis,
            stdout=result.stdout,
            png_paths=result.png_paths,
            tree_summary=tree.summary(),
        )

        decision = interp.get("decision", "b")
        _log(f"發現: {interp['insight'][:120]}")
        _log(f"決策: {decision} — {interp.get('rationale', '')}")

        # 4. Save node
        node = tree.add_node(
            hypothesis=hypothesis,
            parent_id=parent_id,
            code=code,
            stdout=result.stdout,
            png_paths=[str(p) for p in result.png_paths],
            insight=interp["insight"],
            decision=decision,
            decision_rationale=interp.get("rationale", ""),
            next_hypothesis=interp.get("next_hypothesis", ""),
        )
        parent_id = node.node_id

        # 5. Decide next step
        if decision == "d":
            _log("Agent 決定停止 — 已有足夠結論")
            break

        elif decision == "c":
            _log("Agent 回溯 ...")
            parent_id, hypothesis = tree.backtrack()
            if not hypothesis:
                _log("無法回溯，改為側探")
                hypothesis = f"從另一個角度探索主題: {topic}"

        else:  # a or b
            next_hyp = interp.get("next_hypothesis", "").strip()
            if not next_hyp:
                _log("未提供下一假設，回溯並重設")
                parent_id, hypothesis = tree.backtrack()
            else:
                hypothesis = next_hyp

    # ------------------------------------------------------------------ #
    # Final story
    # ------------------------------------------------------------------ #
    _section("生成分析故事線 ...")
    story = agent.generate_story(topic=topic, tree_summary=tree.summary(max_nodes=30))

    story_path = output_dir / "story.md"
    story_path.write_text(story, encoding="utf-8")
    _log(f"故事線已儲存: {story_path}")

    # Also save tree markdown
    (output_dir / "tree.md").write_text(tree.to_markdown(), encoding="utf-8")

    _section("分析完成")
    print(story)
    return story
