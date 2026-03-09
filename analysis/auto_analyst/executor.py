"""
Code executor: runs Python code in a subprocess within the analysis/ directory,
captures stdout/stderr, detects newly created PNG files.
"""
from __future__ import annotations

import subprocess
import textwrap
from pathlib import Path

# Where the analysis modules live (sys.path entry)
ANALYSIS_DIR = Path(__file__).parent.parent.resolve()
VENV_PYTHON = ANALYSIS_DIR.parent / ".venv" / "bin" / "python"


class ExecutionResult:
    def __init__(self, stdout: str, stderr: str, png_paths: list[Path], success: bool):
        self.stdout = stdout
        self.stderr = stderr
        self.png_paths = png_paths
        self.success = success

    def __repr__(self):
        return (
            f"ExecutionResult(success={self.success}, "
            f"stdout_lines={len(self.stdout.splitlines())}, "
            f"pngs={len(self.png_paths)})"
        )


def run(code: str, output_dir: Path, node_id: int, timeout: int = 120) -> ExecutionResult:
    """
    Execute `code` as a Python script.
    - Prepends sys.path setup so `from customized.xxx import ...` works.
    - Redirects plt.savefig to output_dir/node_{node_id}_chart_{n}.png.
    - Returns stdout, stderr, list of saved PNG paths.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Boilerplate prepended to every generated script
    preamble = textwrap.dedent(f"""
        import sys, os
        sys.path.insert(0, {str(ANALYSIS_DIR)!r})
        os.chdir({str(ANALYSIS_DIR)!r})

        import warnings
        warnings.filterwarnings("ignore")

        import matplotlib
        matplotlib.use("Agg")   # non-interactive backend
        import matplotlib.pyplot as plt
        import numpy as np
        import pandas as pd
        from scipy import stats
        from statsmodels.nonparametric.smoothers_lowess import lowess

        from customized.sleep_feature_builder import build_sleep_features

        # --- Chart save helper ---
        _CHART_DIR = {str(output_dir)!r}
        _NODE_ID   = {node_id}
        _chart_counter = [0]

        def save_chart(title=""):
            idx = _chart_counter[0]
            _chart_counter[0] += 1
            fname = f"node_{{_NODE_ID}}_chart_{{idx}}.png"
            path  = os.path.join(_CHART_DIR, fname)
            plt.tight_layout()
            plt.savefig(path, dpi=110, bbox_inches="tight")
            plt.close("all")
            print(f"CHART_SAVED: {{path}}")
            return path

        # Monkey-patch plt.show → save_chart so agent code works unchanged
        plt.show = save_chart

    """)

    full_code = preamble + "\n" + code

    # Write to temp file
    script_path = output_dir / f"node_{node_id}_script.py"
    script_path.write_text(full_code)

    try:
        proc = subprocess.run(
            [str(VENV_PYTHON), str(script_path)],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(ANALYSIS_DIR),
        )
        stdout = proc.stdout
        stderr = proc.stderr
        success = proc.returncode == 0
    except subprocess.TimeoutExpired:
        stdout = ""
        stderr = f"[TIMEOUT after {timeout}s]"
        success = False

    # Collect PNGs referenced in stdout
    png_paths: list[Path] = []
    for line in stdout.splitlines():
        if line.startswith("CHART_SAVED:"):
            p = Path(line.split("CHART_SAVED:", 1)[1].strip())
            if p.exists():
                png_paths.append(p)

    # Trim stdout to ~6000 chars to stay within context budget
    if len(stdout) > 6000:
        stdout = stdout[:5800] + "\n... [truncated]"

    if not success and stderr:
        stdout += f"\n[STDERR]\n{stderr[:1000]}"

    return ExecutionResult(stdout=stdout, stderr=stderr, png_paths=png_paths, success=success)
