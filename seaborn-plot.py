#!/usr/bin/env python3
"""
Plot the number of 'translate-out-of-memory' errors per domain,
broken down by translator setting, from a Lab properties file.

Usage:
    python plot_oom.py properties [output.png]
"""

import json
import sys
import collections

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns
import pandas as pd


TARGET_ERROR = "translate-out-of-memory"


def load_properties(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


def extract_translator_setting(algorithm: str) -> str:
    """
    Pull the eliminate-disjunctions value out of the algorithm nick.
    E.g. '0f0b7b4cb-lama-all'  -> 'all'
         'cc6ee384e-astar-blind-none' -> 'none'
    Falls back to the full algorithm string if no known keyword is found.
    """
    for keyword in ("none", "all", "extreme"):
        if f"-{keyword}" in algorithm:
            return keyword
    # Fallback: strip revision prefix and return remainder
    parts = algorithm.split("-", 1)
    return parts[1] if len(parts) == 2 else algorithm


def build_dataframe(props: dict) -> pd.DataFrame:
    counts: dict[tuple[str, str], int] = collections.defaultdict(int)

    for run in props.values():
        if run.get("error") != TARGET_ERROR:
            continue
        domain = run.get("domain", "unknown")
        setting = extract_translator_setting(run.get("algorithm", ""))
        counts[(domain, setting)] += 1

    if not counts:
        return pd.DataFrame(columns=["domain", "translator_setting", "oom_tasks"])

    rows = [
        {"domain": d, "translator_setting": s, "oom_tasks": n}
        for (d, s), n in counts.items()
    ]
    return pd.DataFrame(rows)


def plot(df: pd.DataFrame, out_path: str) -> None:
    if df.empty:
        print(f"No '{TARGET_ERROR}' errors found — nothing to plot.")
        return

    all_domains = sorted(df["domain"].unique())
    all_settings = sorted(df["translator_setting"].unique())

    # Fill every (domain × setting) combination so bars are always grouped evenly
    full_index = pd.MultiIndex.from_product(
        [all_domains, all_settings], names=["domain", "translator_setting"]
    )
    df = (
        df.set_index(["domain", "translator_setting"])
        .reindex(full_index, fill_value=0)
        .reset_index()
    )

    sns.set_theme(style="ticks", font_scale=1.15)
    palette = sns.color_palette("colorblind", n_colors=len(all_settings))

    fig_w = max(9, len(all_domains) * 1.4 + 2)
    fig, ax = plt.subplots(figsize=(fig_w, 5))

    sns.barplot(
        data=df,
        x="domain",
        y="oom_tasks",
        hue="translator_setting",
        hue_order=all_settings,
        palette=palette,
        ax=ax,
        edgecolor="white",
        linewidth=0.7,
        width=0.65,
    )

    sns.despine(ax=ax)
    ax.set_title(
        "Translate-out-of-memory errors per domain",
        fontsize=14,
        fontweight="medium",
        pad=14,
    )
    ax.set_xlabel("Domain", fontsize=12, labelpad=8)
    ax.set_ylabel("Number of OOM tasks", fontsize=12)
    ax.tick_params(axis="x", rotation=35)
    ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    ax.grid(axis="y", linewidth=0.5, alpha=0.6)

    legend = ax.legend(
        title="--eliminate-disjunctions",
        bbox_to_anchor=(1.02, 1),
        loc="upper left",
        borderaxespad=0,
        frameon=False,
    )
    legend.get_title().set_fontsize(11)

    plt.tight_layout()
    fig.savefig(out_path, dpi=180, bbox_inches="tight")
    print(f"Saved plot to {out_path}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    props_path = sys.argv[1]
    out_path = sys.argv[2] if len(sys.argv) > 2 else "oom_errors.png"

    props = load_properties(props_path)
    df = build_dataframe(props)
    print(df.to_string(index=False) if not df.empty else "No OOM runs found.")
    plot(df, out_path)


if __name__ == "__main__":
    main()
