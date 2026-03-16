"""
Analysis tree: stores nodes as JSON, generates summaries for the agent.

Each node can have multiple children (true branching tree).
- status "open"   : branch still active / children pending
- status "closed" : branch exhausted, mini_summary recorded
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

DECISION_LABELS = {
    "open":   "🔀 分支探索中",
    "closed": "✅ 此路已結",
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
    mini_summary: str = ""          # per-branch conclusion (filled when closed)
    status: str = "open"            # "open" | "closed"
    next_hypotheses: list[str] = field(default_factory=list)   # pending child branches
    decision_rationale: str = ""
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
        mini_summary: str = "",
        status: str = "open",
        next_hypotheses: list[str] | None = None,
        decision_rationale: str = "",
    ) -> AnalysisNode:
        node = AnalysisNode(
            node_id=self._next_id,
            parent_id=parent_id,
            hypothesis=hypothesis,
            code=code,
            stdout=stdout,
            png_paths=png_paths,
            insight=insight,
            mini_summary=mini_summary,
            status=status,
            next_hypotheses=next_hypotheses or [],
            decision_rationale=decision_rationale,
        )
        self.nodes.append(node)
        self._next_id += 1
        self.save()
        return node

    def close_node(self, node_id: int, mini_summary: str):
        """Mark a node as closed with a mini-summary."""
        self.nodes[node_id].status = "closed"
        self.nodes[node_id].mini_summary = mini_summary
        self.save()

    def children(self, node_id: int) -> list[AnalysisNode]:
        return [n for n in self.nodes if n.parent_id == node_id]

    def open_leaves(self) -> list[AnalysisNode]:
        """Nodes that are open and still have unexplored next_hypotheses."""
        children_count: dict[int, int] = {}
        for n in self.nodes:
            if n.parent_id is not None:
                children_count[n.parent_id] = children_count.get(n.parent_id, 0) + 1
        result = []
        for n in self.nodes:
            if n.status != "open":
                continue
            n_children = children_count.get(n.node_id, 0)
            n_pending = len(n.next_hypotheses) - n_children
            # open if: no children yet, or still has unexplored next_hypotheses
            if n_children == 0 or n_pending > 0:
                result.append(n)
        return result

    def all_closed(self) -> bool:
        return all(n.status == "closed" for n in self.nodes) if self.nodes else False

    def current_node(self) -> AnalysisNode | None:
        return self.nodes[-1] if self.nodes else None

    # ------------------------------------------------------------------ #
    # Summary for agent context
    # ------------------------------------------------------------------ #

    def summary(self, max_nodes: int = 20) -> str:
        """ASCII tree summary showing branch structure and open leaves."""
        if not self.nodes:
            return "(尚無分析節點)"

        lines = [f"主題: {self.topic}", ""]

        # Build child map
        children_map: dict[int | None, list[AnalysisNode]] = {}
        for n in self.nodes:
            children_map.setdefault(n.parent_id, []).append(n)

        def _render(node_id: int | None, prefix: str, is_last: bool):
            if node_id is None:
                for i, root in enumerate(children_map.get(None, [])):
                    _render(root.node_id, "", i == len(children_map.get(None, [])) - 1)
                return
            n = self.nodes[node_id]
            connector = "└─ " if is_last else "├─ "
            status_icon = "✅" if n.status == "closed" else "🔵"
            lines.append(f"{prefix}{connector}{status_icon} [{n.node_id}] {n.hypothesis}")
            if n.insight:
                child_prefix = prefix + ("   " if is_last else "│  ")
                lines.append(f"{child_prefix}   💡 {n.insight}")
            if n.mini_summary:
                child_prefix = prefix + ("   " if is_last else "│  ")
                lines.append(f"{child_prefix}   📝 小結: {n.mini_summary}")
            kids = children_map.get(n.node_id, [])
            child_prefix = prefix + ("   " if is_last else "│  ")
            for i, kid in enumerate(kids):
                _render(kid.node_id, child_prefix, i == len(kids) - 1)

        _render(None, "", True)
        lines.append("")

        # Show open leaves
        open_leaves = self.open_leaves()
        if open_leaves:
            # compute children counts for pending display
            children_count: dict[int, int] = {}
            for n in self.nodes:
                if n.parent_id is not None:
                    children_count[n.parent_id] = children_count.get(n.parent_id, 0) + 1
            lines.append("🔀 待探索分支：")
            for n in open_leaves:
                n_done = children_count.get(n.node_id, 0)
                pending = n.next_hypotheses[n_done:]
                lines.append(f"  → [{n.node_id}] (已探索 {n_done}/{len(n.next_hypotheses)})")
                for h in pending:
                    lines.append(f"       • {h}")
        else:
            lines.append("（所有分支已結束）")

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
            # backwards compat: old nodes have next_hypothesis (str) not next_hypotheses (list)
            if "next_hypothesis" in nd and "next_hypotheses" not in nd:
                nh = nd.pop("next_hypothesis")
                nd["next_hypotheses"] = [nh] if nh else []
            # old nodes have decision (a/b/c/d) not status
            if "decision" in nd and "status" not in nd:
                d = nd.pop("decision")
                nd["status"] = "closed" if d == "d" else "open"
            elif "decision" in nd:
                nd.pop("decision")
            nd.setdefault("mini_summary", "")
            nd.setdefault("status", "open")
            nd.setdefault("next_hypotheses", [])
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

        # Compact tree overview (no insight/summary, just structure)
        lines.append("## 樹狀結構總覽\n")
        lines.append("```")
        lines.append(self._compact_tree())
        lines.append("```\n")

        lines.append("---\n")

        # Detailed tree with full insight/summary using indentation
        lines.append("## 詳細節點\n")
        lines.append(self._detailed_tree())

        return "\n".join(lines)

    def _compact_tree(self) -> str:
        """Compact tree showing only node id, hypothesis, and status."""
        if not self.nodes:
            return "(尚無分析節點)"
        result: list[str] = [f"主題: {self.topic}"]
        children_map: dict[int | None, list[AnalysisNode]] = {}
        for n in self.nodes:
            children_map.setdefault(n.parent_id, []).append(n)

        def _walk(node_id: int, prefix: str, is_last: bool):
            n = self.nodes[node_id]
            connector = "└─ " if is_last else "├─ "
            icon = "✅" if n.status == "closed" else "🔵"
            result.append(f"{prefix}{connector}{icon} [{n.node_id}] {n.hypothesis}")
            kids = children_map.get(n.node_id, [])
            child_prefix = prefix + ("   " if is_last else "│  ")
            for i, kid in enumerate(kids):
                _walk(kid.node_id, child_prefix, i == len(kids) - 1)

        roots = children_map.get(None, [])
        for i, root in enumerate(roots):
            _walk(root.node_id, "", i == len(roots) - 1)
        return "\n".join(result)

    def _detailed_tree(self) -> str:
        """Detailed tree with insight and mini_summary, using indentation."""
        if not self.nodes:
            return ""
        result: list[str] = []
        children_map: dict[int | None, list[AnalysisNode]] = {}
        for n in self.nodes:
            children_map.setdefault(n.parent_id, []).append(n)

        def _walk(node_id: int, depth: int):
            n = self.nodes[node_id]
            indent = "  " * depth
            icon = "✅" if n.status == "closed" else "🔵"
            result.append(f"{indent}{icon} **[{n.node_id}] {n.hypothesis}**\n")
            detail_indent = indent + "> "
            if n.insight:
                result.append(f"{detail_indent}💡 {n.insight}\n")
            if n.mini_summary:
                result.append(f"{detail_indent}📝 {n.mini_summary}\n")
            kids = children_map.get(n.node_id, [])
            for kid in kids:
                _walk(kid.node_id, depth + 1)

        roots = children_map.get(None, [])
        for root in roots:
            _walk(root.node_id, 0)
        return "\n".join(result)
