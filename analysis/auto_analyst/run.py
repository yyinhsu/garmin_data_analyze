#!/usr/bin/env python
"""
CLI entry point for the autonomous analysis agent.

Usage:
    python run.py "睡眠品質惡化的原因" --max-iter 12
    python run.py "運動對睡眠的影響" --hypothesis "有氧運動讓深睡比例更高" --max-iter 10
"""
import argparse
import sys
from pathlib import Path

# Make sure the analysis/ dir is on sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from auto_analyst.orchestrator import run


def main():
    parser = argparse.ArgumentParser(description="Autonomous Garmin health data analyst")
    parser.add_argument("topic", help="分析主題，例如: 睡眠品質惡化的原因")
    parser.add_argument(
        "--hypothesis", "-H",
        default=None,
        help="初始假設（留空則使用主題本身）",
    )
    parser.add_argument(
        "--max-iter", "-n",
        type=int,
        default=12,
        help="最大迭代次數（預設 12）",
    )
    parser.add_argument(
        "--output-dir", "-o",
        type=Path,
        default=None,
        help="輸出目錄（預設: outputs/<timestamp>/）",
    )
    args = parser.parse_args()

    run(
        topic=args.topic,
        initial_hypothesis=args.hypothesis,
        max_iterations=args.max_iter,
        output_dir=args.output_dir,
    )


if __name__ == "__main__":
    main()
