"""
Session management for Claude-driven analysis.

Wraps AnalysisTree with session lifecycle helpers:
  Session.latest_unfinished() — resume an unfinished session
  Session.new(topic)          — start a fresh session
  session.add_node(...)       — record one analysis round
  session.save_story(story)   — write story.md and finalize
  session.summary()           — compact tree text for Claude to read
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .tree import AnalysisTree

OUTPUTS_DIR = Path(__file__).parent / "outputs"


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

    def save_story(self, story: str):
        (self.session_dir / "story.md").write_text(story, encoding="utf-8")
        (self.session_dir / "tree.md").write_text(
            self.tree.to_markdown(), encoding="utf-8"
        )
        print(f"[Session] 故事線已儲存: {self.session_dir / 'story.md'}")

    # ------------------------------------------------------------------ #
    # State for Claude
    # ------------------------------------------------------------------ #

    def summary(self, max_nodes: int = 15) -> str:
        return self.tree.summary(max_nodes=max_nodes)

    def last_node(self):
        return self.tree.current_node()
