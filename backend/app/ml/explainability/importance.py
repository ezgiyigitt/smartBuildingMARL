"""Feature importance and model explainability for TSV classifiers."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Sequence

import numpy as np
from sklearn.inspection import permutation_importance


@dataclass
class ImportanceResult:
    feature_names: list[str]
    mean_importance: dict[str, float]
    std_importance: dict[str, float]
    ranking: list[str]  # Ordered from most to least important
    method: str  # "permutation" or "tree_gini_gain"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def compute_tree_importance(
    model: Any,
    feature_names: Sequence[str],
) -> ImportanceResult | None:
    """Extract impurity-based (Gini/gain) feature importance from tree ensembles."""
    clf = model
    # Handle Pipeline
    if hasattr(model, "named_steps"):
        clf = list(model.named_steps.values())[-1]

    if not hasattr(clf, "feature_importances_"):
        return None

    importances = np.asarray(clf.feature_importances_, dtype=float)
    features = list(feature_names)

    sorted_indices = np.argsort(importances)[::-1]
    mean_imp = {features[i]: float(importances[i]) for i in sorted_indices}
    std_imp = {features[i]: 0.0 for i in sorted_indices}
    ranking = [features[i] for i in sorted_indices]

    return ImportanceResult(
        feature_names=features,
        mean_importance=mean_imp,
        std_importance=std_imp,
        ranking=ranking,
        method="tree_gini_gain",
    )


def compute_permutation_importance(
    model: Any,
    X: Any,
    y: Sequence[int] | np.ndarray,
    feature_names: Sequence[str],
    n_repeats: int = 10,
    random_state: int = 0,
    scoring: str = "f1_macro",
) -> ImportanceResult:
    """Compute permutation feature importance on held-out data.

    Measures drop in scoring metric (macro-F1) when each feature column is randomly shuffled.
    Higher value = feature is more critical to model performance.
    """
    perm = permutation_importance(
        model,
        X,
        y,
        n_repeats=n_repeats,
        random_state=random_state,
        scoring=scoring,
        n_jobs=-1,
    )

    means = np.asarray(perm.importances_mean, dtype=float)
    stds = np.asarray(perm.importances_std, dtype=float)
    features = list(feature_names)

    sorted_indices = np.argsort(means)[::-1]
    mean_imp = {features[i]: float(means[i]) for i in sorted_indices}
    std_imp = {features[i]: float(stds[i]) for i in sorted_indices}
    ranking = [features[i] for i in sorted_indices]

    return ImportanceResult(
        feature_names=features,
        mean_importance=mean_imp,
        std_importance=std_imp,
        ranking=ranking,
        method=f"permutation_{scoring}",
    )


def render_importance_svg(
    importance: ImportanceResult,
    title: str = "Feature Importance",
    out_path: Path | None = None,
) -> str:
    """Generate a clean SVG horizontal bar chart for feature importances."""
    items = [(f, importance.mean_importance[f], importance.std_importance[f]) for f in importance.ranking]
    max_val = max((val for _, val, _ in items), default=1.0)
    if max_val <= 0:
        max_val = 1.0

    width = 600
    row_height = 36
    margin_top = 60
    margin_left = 90
    bar_area_width = 440
    height = margin_top + len(items) * row_height + 40

    svg_lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" style="background-color:#ffffff; font-family:sans-serif;">',
        f'  <text x="{margin_left}" y="32" font-size="16" font-weight="bold" fill="#222222">{title}</text>',
        f'  <text x="{margin_left}" y="48" font-size="11" fill="#666666">Method: {importance.method}</text>',
    ]

    for idx, (feat, val, std) in enumerate(items):
        y = margin_top + idx * row_height
        bar_len = max(2, int((max(0.0, val) / max_val) * bar_area_width))
        color = "#2563eb" if idx == 0 else "#3b82f6"

        svg_lines.append(f'  <text x="{margin_left - 10}" y="{y + 20}" font-size="13" text-anchor="end" fill="#333333">{feat}</text>')
        svg_lines.append(f'  <rect x="{margin_left}" y="{y + 4}" width="{bar_len}" height="22" rx="3" fill="{color}" />')
        val_str = f"{val:.4f}" + (f" +/- {std:.4f}" if std > 0 else "")
        svg_lines.append(f'  <text x="{margin_left + bar_len + 8}" y="{y + 20}" font-size="11" fill="#444444">{val_str}</text>')

    svg_lines.append('</svg>')
    svg_content = "\n".join(svg_lines)

    if out_path is not None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(svg_content, encoding="utf-8")

    return svg_content
