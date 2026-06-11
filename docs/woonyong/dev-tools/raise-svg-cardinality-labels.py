#!/usr/bin/env python3
"""Move cardinality labels to the top SVG layer.

Graphviz renders edge labels inside each edge group. Later edges can cross over
earlier labels, so relation cardinalities such as "1 -> 0..*" may look buried
under lines. This script moves those text elements to the end of the graph group
and adds a small background-colored stroke for readability.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


LABEL_LAYER_RE = re.compile(
    r'\n<g id="cardinality-label-layer" class="cardinality-labels">\n'
    r"(?P<body>.*?)\n</g>",
    re.DOTALL,
)
CARDINALITY_TEXT_RE = re.compile(
    r'<text\b(?=[^>]*fill="#d19a66")[^>]*>'
    r"1 (?:&#45;&gt;|-&gt;|->) 0\.\.[^<]+</text>"
)


def prepare_label(label: str) -> str:
    label = re.sub(r'\s+paint-order="[^"]*"', "", label)
    label = re.sub(r'\s+stroke="[^"]*"', "", label)
    label = re.sub(r'\s+stroke-width="[^"]*"', "", label)
    label = re.sub(r'\s+stroke-linejoin="[^"]*"', "", label)
    return label.replace(
        "<text ",
        '<text paint-order="stroke fill" stroke="#282c34" '
        'stroke-width="3" stroke-linejoin="round" ',
        1,
    )


def raise_labels(svg: str) -> tuple[str, int]:
    existing_labels: list[str] = []

    def remove_existing_layer(match: re.Match[str]) -> str:
        existing_labels.extend(CARDINALITY_TEXT_RE.findall(match.group("body")))
        return ""

    svg = LABEL_LAYER_RE.sub(remove_existing_layer, svg)
    labels = CARDINALITY_TEXT_RE.findall(svg)
    svg = CARDINALITY_TEXT_RE.sub("", svg)

    if not labels:
        labels = existing_labels
    if not labels:
        return svg, 0

    label_layer = "\n".join(prepare_label(label) for label in labels)
    layer = (
        '\n<g id="cardinality-label-layer" class="cardinality-labels">\n'
        f"{label_layer}\n"
        "</g>"
    )

    marker = "\n</g>\n</svg>"
    if marker not in svg:
        raise ValueError("Could not find the closing graph group")

    head, tail = svg.rsplit(marker, 1)
    return f"{head}{layer}{marker}{tail}", len(labels)


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: raise-svg-cardinality-labels.py <svg> [<svg> ...]", file=sys.stderr)
        return 2

    for arg in sys.argv[1:]:
        path = Path(arg)
        svg = path.read_text()
        updated, count = raise_labels(svg)
        path.write_text(updated)
        print(f"{path}: raised {count} cardinality labels")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
