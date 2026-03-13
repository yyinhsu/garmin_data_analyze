"""
Session management for Claude-driven analysis.

Wraps AnalysisTree with session lifecycle helpers:
  Session.latest_unfinished() — resume an unfinished session
  Session.new(topic)          — start a fresh session
  session.add_node(...)       — record one analysis round
  session.save_story(story)   — write story.md with embedded charts + workflow.ipynb
  session.summary()           — compact tree text for Claude to read
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from .tree import AnalysisTree

OUTPUTS_DIR = Path(__file__).parent / "outputs"

DECISION_LABELS = {"a": "深挖↓", "b": "側探→", "c": "回溯↑", "d": "結論✓"}


class Session:
    def __init__(self, tree: AnalysisTree):
        self.tree = tree

    # ------------------------------------------------------------------ #
    # Properties
    # ------------------------------------------------------------------ #

    @property
    def session_dir(self) -> Path:
        return self.tree.output_dir

    @property
    def topic(self) -> str:
        return self.tree.topic

    @property
    def next_node_id(self) -> int:
        return self.tree._next_id

    @property
    def node_count(self) -> int:
        return len(self.tree.nodes)

    def is_finished(self) -> bool:
        return (self.session_dir / "story.md").exists()

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #

    @classmethod
    def new(cls, topic: str) -> Session:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_dir = OUTPUTS_DIR / ts
        session_dir.mkdir(parents=True, exist_ok=True)
        tree = AnalysisTree(topic=topic, output_dir=session_dir)
        tree.save()  # write empty tree.json immediately so latest_unfinished() can find it
        print(f"[Session] 新建 session: {session_dir}")
        return cls(tree)

    @classmethod
    def latest_unfinished(cls) -> Session | None:
        """Return the most recent session that has tree.json but no story.md."""
        if not OUTPUTS_DIR.exists():
            return None
        dirs = sorted(
            (d for d in OUTPUTS_DIR.iterdir() if d.is_dir()),
            reverse=True,
        )
        for d in dirs:
            if (d / "tree.json").exists() and not (d / "story.md").exists():
                tree = AnalysisTree.load(d / "tree.json")
                print(f"[Session] 找到未完成 session: {d}（{len(tree.nodes)} 個節點）")
                return cls(tree)
        return None

    @classmethod
    def load_latest(cls) -> Session | None:
        """Load the most recent session regardless of completion status."""
        if not OUTPUTS_DIR.exists():
            return None
        dirs = sorted(
            (d for d in OUTPUTS_DIR.iterdir() if d.is_dir()),
            reverse=True,
        )
        for d in dirs:
            if (d / "tree.json").exists():
                tree = AnalysisTree.load(d / "tree.json")
                return cls(tree)
        return None

    # ------------------------------------------------------------------ #
    # Recording
    # ------------------------------------------------------------------ #

    def add_node(
        self,
        hypothesis: str,
        parent_id: int | None,
        code: str,
        stdout: str,
        png_paths: list[str],
        insight: str,
        decision: str,
        next_hypothesis: str = "",
    ):
        return self.tree.add_node(
            hypothesis=hypothesis,
            parent_id=parent_id,
            code=code,
            stdout=stdout,
            png_paths=png_paths,
            insight=insight,
            decision=decision,
            decision_rationale="",
            next_hypothesis=next_hypothesis,
        )

    # ------------------------------------------------------------------ #
    # Finalisation: story.md (with charts) + workflow.ipynb
    # ------------------------------------------------------------------ #

    def save_story(self, story: str):
        """Save story.md with embedded chart images, tree.md, and workflow.ipynb."""
        story_with_charts = self._inject_charts_into_story(story)
        (self.session_dir / "story.md").write_text(story_with_charts, encoding="utf-8")
        (self.session_dir / "tree.md").write_text(
            self.tree.to_markdown(), encoding="utf-8"
        )
        self._generate_notebook()
        print(f"[Session] 故事線已儲存: {self.session_dir / 'story.md'}")
        print(f"[Session] 分析筆記本已儲存: {self.session_dir / 'workflow.ipynb'}")

    def _inject_charts_into_story(self, story: str) -> str:
        """Append a Charts section at the end of story.md with all node charts."""
        charts_section = ["\n\n---\n\n## 分析圖表\n"]
        for node in self.tree.nodes:
            node_pngs = [p for p in node.png_paths if Path(p).exists()]
            if not node_pngs:
                continue
            label = DECISION_LABELS.get(node.decision, node.decision)
            charts_section.append(
                f"\n### 節點 {node.node_id} {label} — {node.hypothesis}\n"
            )
            for png_path in node_pngs:
                fname = Path(png_path).name
                charts_section.append(f"\n![{fname}](./{fname})\n")
        return story + "".join(charts_section)

    def _generate_notebook(self):
        """Generate workflow.ipynb — a Jupyter notebook recording the full analysis."""
        cells = []

        # Title cell
        cells.append(_md_cell([
            f"# 分析工作流程：{self.topic}\n",
            "\n",
            f"**Session**: `{self.session_dir.name}`  \n",
            f"**節點數**: {len(self.tree.nodes)}  \n",
            f"**生成時間**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n",
            "\n",
            "---\n",
            "\n",
            "本筆記本記錄 Claude 自主分析的完整過程，包含每輪的假設、代碼、輸出與解讀。\n",
        ]))

        # Setup cell (preamble explanation)
        cells.append(_md_cell([
            "## 環境設定\n",
            "\n",
            "以下所有代碼假設執行環境已預載：\n",
            "- `runs`, `daily`, `df_sleep`, `runs_daily`, `runs_sleep` DataFrames\n",
            "- `pd`, `np`, `plt`, `sns`, `stats`, `spearmanr`, `pearsonr`, `mannwhitneyu`, `lowess`\n",
        ]))

        # One section per node
        for node in self.tree.nodes:
            label = DECISION_LABELS.get(node.decision, node.decision)
            parent_str = f"父節點: {node.parent_id}" if node.parent_id is not None else "根節點"

            # Node header
            cells.append(_md_cell([
                "---\n",
                f"\n## 節點 {node.node_id} — {node.hypothesis}\n",
                f"\n**決策**: {label}　｜　**{parent_str}**\n",
            ]))

            # Code cell
            cells.append(_code_cell(node.code or "# (無代碼記錄)"))

            # Output cell (stdout)
            if node.stdout:
                cells.append(_code_cell(
                    f"# === 執行輸出 ===",
                    outputs=[{
                        "output_type": "stream",
                        "name": "stdout",
                        "text": node.stdout.splitlines(keepends=True),
                    }],
                ))

            # Charts
            node_pngs = [p for p in node.png_paths if Path(p).exists()]
            if node_pngs:
                img_lines = ["**圖表**\n\n"]
                for png_path in node_pngs:
                    fname = Path(png_path).name
                    img_lines.append(f"![{fname}](./{fname})\n\n")
                cells.append(_md_cell(img_lines))

            # Insight
            cells.append(_md_cell([
                f"**🔍 發現**：{node.insight}\n",
                "\n",
                f"**決策理由**：{node.decision_rationale or '—'}\n",
            ]))
            if node.next_hypothesis:
                cells.append(_md_cell([
                    f"**⬇ 下一個假設**：{node.next_hypothesis}\n",
                ]))

        # Final story summary cell
        story_path = self.session_dir / "story.md"
        if story_path.exists():
            cells.append(_md_cell([
                "---\n\n## 最終報告\n\n",
                "完整故事線請見 [`story.md`](./story.md)\n",
            ]))

        nb = {
            "nbformat": 4,
            "nbformat_minor": 5,
            "metadata": {
                "kernelspec": {
                    "display_name": "Python 3",
                    "language": "python",
                    "name": "python3",
                },
                "language_info": {
                    "name": "python",
                    "version": "3.12.0",
                },
            },
            "cells": cells,
        }
        nb_path = self.session_dir / "workflow.ipynb"
        nb_path.write_text(json.dumps(nb, ensure_ascii=False, indent=1))

    # ------------------------------------------------------------------ #
    # State for Claude
    # ------------------------------------------------------------------ #

    def summary(self, max_nodes: int = 15) -> str:
        return self.tree.summary(max_nodes=max_nodes)

    def last_node(self):
        return self.tree.current_node()


# ------------------------------------------------------------------ #
# Notebook cell helpers
# ------------------------------------------------------------------ #

def _md_cell(source: list[str]) -> dict:
    return {
        "cell_type": "markdown",
        "id": _cell_id(),
        "metadata": {},
        "source": source,
    }


def _code_cell(source: str, outputs: list | None = None) -> dict:
    return {
        "cell_type": "code",
        "id": _cell_id(),
        "execution_count": None,
        "metadata": {},
        "outputs": outputs or [],
        "source": source.splitlines(keepends=True),
    }


_CELL_COUNTER = [0]


def _cell_id() -> str:
    _CELL_COUNTER[0] += 1
    return f"cell-{_CELL_COUNTER[0]:04d}"
