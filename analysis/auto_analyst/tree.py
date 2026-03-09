"""
Analysis tree: stores nodes as JSON, generates summaries for the agent.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

DECISION_LABELS = {
    "a": "深挖 (drill-down)",
    "b": "側探 (explore related variable)",
    "c": "回溯 (backtrack)",
    "d": "停止 (stop — sufficient conclusion)",
}


@dataclass
class AnalysisNode:
    node_id: int
    parent_id: int | None
    hypothesis: str
    code: str = ""
    stdout: str = ""
    png_paths: list[str] = field(default_factory=list)
    insight: str = ""
    decision: str = ""          # a / b / c / d
    decision_rationale: str = ""
    next_hypothesis: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class AnalysisTree:
    def __init__(self, topic: str, output_dir: Path):
        self.topic = topic
        self.output_dir = output_dir
        self.nodes: list[AnalysisNode] = []
        self._next_id = 0
        self.json_path = output_dir / "tree.json"

    # ------------------------------------------------------------------ #
    # Node management
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
        decision_rationale: str,
        next_hypothesis: str = "",
    ) -> AnalysisNode:
        node = AnalysisNode(
            node_id=self._next_id,
            parent_id=parent_id,
            hypothesis=hypothesis,
            code=code,
            stdout=stdout,
            png_paths=png_paths,
            insight=insight,
            decision=decision,
            decision_rationale=decision_rationale,
            next_hypothesis=next_hypothesis,
        )
        self.nodes.append(node)
        self._next_id += 1
        self.save()
        return node

    def backtrack(self) -> tuple[int | None, str]:
        """Return (parent_id, parent_hypothesis) of last non-dead-end node."""
        for node in reversed(self.nodes):
            if node.decision in ("a", "b", ""):  # not yet exhausted
                return node.node_id, node.hypothesis
        return None, self.topic

    def current_node(self) -> AnalysisNode | None:
        return self.nodes[-1] if self.nodes else None

    # ------------------------------------------------------------------ #
    # Summary for agent context
    # ------------------------------------------------------------------ #

    def summary(self, max_nodes: int = 12) -> str:
        """Compact text summary of the tree to fit in agent context."""
        if not self.nodes:
            return "(尚無分析節點)"

        lines = [f"主題: {self.topic}", ""]
        recent = self.nodes[-max_nodes:]
        for n in recent:
            indent = "  " * self._depth(n.node_id)
            decision_str = DECISION_LABELS.get(n.decision, n.decision)
            lines.append(
                f"{indent}[節點 {n.node_id}] 假設: {n.hypothesis}"
            )
            if n.insight:
                lines.append(f"{indent}  → 發現: {n.insight}")
            if n.decision:
                lines.append(f"{indent}  → 決策: {decision_str}")
            lines.append("")

        return "\n".join(lines)

    def _depth(self, node_id: int) -> int:
        node = self.nodes[node_id]
        if node.parent_id is None:
            return 0
        return 1 + self._depth(node.parent_id)

    # ------------------------------------------------------------------ #
    # Persistence
    # ------------------------------------------------------------------ #

    def save(self):
        data = {
            "topic": self.topic,
            "nodes": [asdict(n) for n in self.nodes],
        }
        self.json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    @classmethod
    def load(cls, json_path: Path) -> AnalysisTree:
        data = json.loads(json_path.read_text())
        tree = cls(topic=data["topic"], output_dir=json_path.parent)
        for nd in data["nodes"]:
            tree.nodes.append(AnalysisNode(**nd))
        tree._next_id = len(tree.nodes)
        return tree

    # ------------------------------------------------------------------ #
    # Final story (Markdown)
    # ------------------------------------------------------------------ #

    def to_markdown(self) -> str:
        lines = ["# 數據分析故事線\n", f"**主題**: {self.topic}\n"]
        lines.append(f"**分析節點數**: {len(self.nodes)}\n")
        lines.append("---\n")

        def _render(node_id: int, depth: int):
            n = self.nodes[node_id]
            prefix = "#" * min(depth + 2, 6)
            decision_str = DECISION_LABELS.get(n.decision, "")
            lines.append(f"{prefix} 節點 {n.node_id}: {n.hypothesis}\n")
            if n.insight:
                lines.append(f"**發現**: {n.insight}\n")
            if n.decision:
                lines.append(f"**決策**: {decision_str}")
                if n.decision_rationale:
                    lines.append(f" — {n.decision_rationale}")
                lines.append("\n")
            lines.append("")

        for n in self.nodes:
            _render(n.node_id, self._depth(n.node_id))

        return "\n".join(lines)
