"""
GroundReport: counts 'translate-out-of-memory' errors per domain and algorithm,
then produces a seaborn bar plot per revision.
"""

import collections
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

from lab.reports import Report


ERROR = "translate-out-of-memory"


class GroundReport(Report):
    """
    For each revision, produce a bar plot showing how many tasks per domain
    hit a 'translate-out-of-memory' error, with one bar per algorithm.

    The report writes one PNG per revision into the directory given as *outfile*
    (treated as a directory, not a file).  If *outfile* ends in ".html" or
    similar the parent directory is used instead.
    """

    def __init__(self, **kwargs):
        # We don't need any particular attribute; we read 'error' from each run.
        kwargs.setdefault("attributes", ["error"])
        super().__init__(**kwargs)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _parse_algorithm(self, algo_string):
        """
        Algorithm strings are typically '<revision>-<config_nick>'.
        Return (revision, config_nick).
        """
        parts = algo_string.split("-", 1)
        if len(parts) == 2:
            return parts[0], parts[1]
        return algo_string, algo_string

    def _collect_oom_counts(self):
        """
        Walk self.props and build a nested dict:
            counts[revision][domain][algorithm] = number_of_oom_tasks
        where 'algorithm' is the config nick (revision stripped).
        """
        counts = collections.defaultdict(
            lambda: collections.defaultdict(
                lambda: collections.defaultdict(int)
            )
        )

        for run in self.props.values():
            if run.get("error") != ERROR:
                continue
            algo_string = run.get("algorithm", "")
            domain = run.get("domain", "unknown")
            revision, config_nick = self._parse_algorithm(algo_string)
            counts[revision][domain][config_nick] += 1

        return counts

    # ------------------------------------------------------------------
    # Plotting
    # ------------------------------------------------------------------

    def _plot_revision(self, revision, domain_data, out_dir):
        """
        Draw a grouped bar chart for one revision.

        domain_data: dict  domain -> {config_nick: count}
        """
        # Build a tidy DataFrame
        rows = []
        for domain, algo_counts in domain_data.items():
            for algo, count in algo_counts.items():
                rows.append({"domain": domain, "algorithm": algo, "oom_tasks": count})

        if not rows:
            return

        df = pd.DataFrame(rows)

        # Ensure every (domain, algorithm) combination exists (fill missing with 0)
        all_algos = sorted(df["algorithm"].unique())
        all_domains = sorted(df["domain"].unique())
        full_index = pd.MultiIndex.from_product(
            [all_domains, all_algos], names=["domain", "algorithm"]
        )
        df = (
            df.set_index(["domain", "algorithm"])
            .reindex(full_index, fill_value=0)
            .reset_index()
        )

        n_domains = len(all_domains)
        fig_width = max(10, n_domains * 1.2)

        fig, ax = plt.subplots(figsize=(fig_width, 5))

        sns.set_theme(style="whitegrid", font_scale=1.1)
        palette = sns.color_palette("colorblind", n_colors=len(all_algos))

        sns.barplot(
            data=df,
            x="domain",
            y="oom_tasks",
            hue="algorithm",
            palette=palette,
            ax=ax,
            edgecolor="white",
            linewidth=0.6,
        )

        ax.set_title(
            f"Translate-out-of-memory errors — revision {revision}",
            fontsize=13,
            pad=12,
        )
        ax.set_xlabel("Domain", fontsize=11)
        ax.set_ylabel("Number of OOM tasks", fontsize=11)
        ax.tick_params(axis="x", rotation=40)
        ax.legend(title="Algorithm", bbox_to_anchor=(1.01, 1), loc="upper left", borderaxespad=0)
        ax.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))

        plt.tight_layout()

        out_path = os.path.join(out_dir, f"oom_{revision}.png")
        fig.savefig(out_path, dpi=150)
        plt.close(fig)
        print(f"Wrote {out_path}")

    # ------------------------------------------------------------------
    # Report entry point
    # ------------------------------------------------------------------

    def write(self):
        counts = self._collect_oom_counts()

        # Determine output directory
        if os.path.splitext(self.outfile)[1]:
            out_dir = os.path.dirname(self.outfile) or "."
        else:
            out_dir = self.outfile

        os.makedirs(out_dir, exist_ok=True)

        if not counts:
            print(
                f"GroundReport: no runs with error='{ERROR}' found; "
                "no plots produced."
            )
            return

        for revision, domain_data in sorted(counts.items()):
            self._plot_revision(revision, domain_data, out_dir)
