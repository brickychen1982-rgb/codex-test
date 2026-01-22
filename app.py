#!/usr/bin/env python3
"""Select high-value consultation questions from a CSV export.

Expected input CSV columns (case-insensitive):
- id
- title
- content
- category
- budget
- urgency
- location
- created_at

The script scores each question using configurable heuristics and outputs
selected rows with their score and reasons.
"""
from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


@dataclass
class Question:
    qid: str
    title: str
    content: str
    category: str
    budget: float
    urgency: str
    location: str
    created_at: str


@dataclass
class ScoreResult:
    score: float
    reasons: List[str]


def normalize_header(header: str) -> str:
    return header.strip().lower().replace(" ", "_")


def parse_budget(raw: str) -> float:
    try:
        return float(raw)
    except (TypeError, ValueError):
        return 0.0


def load_questions(path: Path) -> Iterable[Question]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            return []
        header_map = {normalize_header(name): name for name in reader.fieldnames}
        for row in reader:
            def get(key: str) -> str:
                return row.get(header_map.get(key, key), "")

            yield Question(
                qid=get("id"),
                title=get("title"),
                content=get("content"),
                category=get("category"),
                budget=parse_budget(get("budget")),
                urgency=get("urgency"),
                location=get("location"),
                created_at=get("created_at"),
            )


def score_question(question: Question, config: Dict) -> ScoreResult:
    score = 0.0
    reasons: List[str] = []

    content = f"{question.title} {question.content}".strip()
    length = len(content)

    length_rules = config.get("length_score", {})
    for threshold, points in length_rules.items():
        if length >= int(threshold):
            score += float(points)
    if length >= config.get("length_bonus_threshold", 200):
        reasons.append("详情描述充分")

    if question.budget >= config.get("budget", {}).get("high", 500):
        score += config.get("budget", {}).get("high_points", 20)
        reasons.append("预算较高")
    elif question.budget >= config.get("budget", {}).get("medium", 100):
        score += config.get("budget", {}).get("medium_points", 10)
        reasons.append("预算适中")

    urgency_keywords = config.get("urgency_keywords", [])
    if any(keyword in question.urgency for keyword in urgency_keywords):
        score += config.get("urgency_points", 10)
        reasons.append("紧急咨询")

    category_weights = config.get("category_weights", {})
    for category, points in category_weights.items():
        if category and category in question.category:
            score += float(points)
            reasons.append(f"重点领域: {category}")

    quality_keywords = config.get("quality_keywords", [])
    hits = [kw for kw in quality_keywords if kw in content]
    if hits:
        score += min(len(hits) * config.get("quality_points_per_hit", 2), 10)
        reasons.append("包含关键事实信息")

    if not reasons:
        reasons.append("基础筛选")

    return ScoreResult(score=score, reasons=reasons)


def write_output(
    output_path: Path,
    rows: Iterable[Tuple[Question, ScoreResult]],
    min_score: float,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        fieldnames = [
            "id",
            "title",
            "content",
            "category",
            "budget",
            "urgency",
            "location",
            "created_at",
            "score",
            "reasons",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for question, result in rows:
            if result.score < min_score:
                continue
            writer.writerow(
                {
                    "id": question.qid,
                    "title": question.title,
                    "content": question.content,
                    "category": question.category,
                    "budget": question.budget,
                    "urgency": question.urgency,
                    "location": question.location,
                    "created_at": question.created_at,
                    "score": f"{result.score:.1f}",
                    "reasons": "、".join(result.reasons),
                }
            )


def load_config(path: Path) -> Dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Select high-value questions from a consultation CSV export.")
    parser.add_argument("--input", required=True, help="Path to input CSV")
    parser.add_argument("--output", required=True, help="Path to output CSV")
    parser.add_argument(
        "--config",
        default="config.json",
        help="Path to scoring config JSON",
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=60,
        help="Minimum score to keep",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config(Path(args.config))
    questions = list(load_questions(Path(args.input)))
    scored = [(question, score_question(question, config)) for question in questions]
    write_output(Path(args.output), scored, args.min_score)


if __name__ == "__main__":
    main()
