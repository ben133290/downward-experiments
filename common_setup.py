# -*- coding: utf-8 -*-

# Last edited on May 14, 2025 to add IPC 2023 domains.

import itertools
import os
import platform
import re
import sys

from lab.experiment import ARGPARSER
from lab import tools

from downward.experiment import FastDownwardExperiment
from downward.reports.absolute import AbsoluteReport
from downward.reports.compare import ComparativeReport
from downward.reports.scatter import ScatterPlotReport


def parse_args():
    ARGPARSER.add_argument(
        "--test",
        choices=["yes", "no", "auto"],
        default="auto",
        dest="test_run",
        help="test experiment locally on a small suite if --test=yes or "
             "--test=auto and we are not on a cluster")
    return ARGPARSER.parse_args()

ARGS = parse_args()
DEBUG_SUITE = ['explode-5']
DISJUNCTION_SUITE = ['assembly', 'miconic-fulladl', 'recharging-robots-sat23-adl', 'explode-5']
DISJUNCTION_DERIVED_SUITE = ['philosophers', 'psr-middle', 'optical-telegraphs',]

def get_script():
    """Get file name of main script."""
    return tools.get_script_path()


def get_script_dir():
    """Get directory of main script.

    Usually a relative directory (depends on how it was called by the user.)"""
    return os.path.dirname(get_script())


def get_experiment_name():
    """Get name for experiment.

    Derived from the absolute filename of the main script, e.g.
    "/ham/spam/eggs.py" => "spam-eggs"."""
    script = os.path.abspath(get_script())
    script_base = os.path.splitext(os.path.basename(script))[0]
    return "%s" % (script_base)


def get_data_dir():
    """Get data dir for the experiment.

    This is the subdirectory "data" of the directory containing
    the main script."""
    return os.path.join(get_script_dir(), "data", get_experiment_name())


def get_repo_base():
    """Get base directory of the repository, as an absolute path.

    Search upwards in the directory tree from the main script until a
    directory with a subdirectory named ".git" is found.

    Abort if the repo base cannot be found."""
    path = os.path.abspath(get_script_dir())
    while os.path.dirname(path) != path:
        if os.path.exists(os.path.join(path, ".git")):
            return path
        path = os.path.dirname(path)
    sys.exit("repo base could not be found")


def is_running_on_cluster():
    return re.fullmatch(r"login12|ic[ab]\d\d", platform.node())


def is_test_run():
    return ARGS.test_run == "yes" or (
        ARGS.test_run == "auto" and not is_running_on_cluster())


def get_algo_nick(revision, config_nick):
    return f"{revision}-{config_nick}"


class OptionsConfig(object):
    def __init__(self, nick, component_options,
                 build_options=None, driver_options=None):
        self.nick = nick
        self.component_options = component_options
        self.build_options = build_options
        self.driver_options = driver_options


class TranslatorExperiment(FastDownwardExperiment):

    DEFAULT_TEST_SUITE = ["depot:p01.pddl", "gripper:prob01.pddl"]

    DEFAULT_TABLE_ATTRIBUTES = [
        "cost",
        "coverage",
        "error",
        "evaluations",
        "expansions",
        "expansions_until_last_jump",
        "initial_h_value",
        "generated",
        "memory",
        "planner_memory",
        "planner_time",
        "quality",
        "run_dir",
        "score_evaluations",
        "score_expansions",
        "score_generated",
        "score_memory",
        "score_search_time",
        "score_total_time",
        "search_time",
        "total_time",
        ]

    DEFAULT_SCATTER_PLOT_ATTRIBUTES = [
        "evaluations",
        "expansions",
        "expansions_until_last_jump",
        "initial_h_value",
        "memory",
        "search_time",
        "total_time",
        ]

    PORTFOLIO_ATTRIBUTES = [
        "cost",
        "coverage",
        "error",
        "plan_length",
        "run_dir",
        ]

    def __init__(self, repo_path=None, revisions=None, configs=None, path=None, **kwargs):
        path = path or get_data_dir()

        FastDownwardExperiment.__init__(self, path=path, **kwargs)

        # input checking
        if repo_path is None:
            repo_path = get_repo_base()

        if (revisions and not configs) or (not revisions and configs):
            raise ValueError(
                "please provide either both or none of revisions and configs")

        if revisions is None:
            revisions = []
        if configs is None:
            configs = []

        if all(isinstance(rev, tuple) for rev in revisions):
            pass
        else:
            revisions = [(rev, rev) for rev in revisions]

        for rev, rev_nick in revisions:
            for config in configs:
                self.add_algorithm(
                    get_algo_nick(rev_nick, config.nick),
                    repo_path,
                    rev,
                    config.component_options,
                    build_options=config.build_options,
                    driver_options=config.driver_options)

        self._revisions = [rev[0] for rev in revisions]
        self._configs = configs

    @classmethod
    def _is_portfolio(cls, config_nick):
        return "fdss" in config_nick

    @classmethod
    def get_supported_attributes(cls, config_nick, attributes):
        if cls._is_portfolio(config_nick):
            return [attr for attr in attributes
                    if attr in cls.PORTFOLIO_ATTRIBUTES]
        return attributes

    def add_absolute_report_step(self, **kwargs):
        """Add step that makes an absolute report.

        Absolute reports are useful for experiments that don't compare
        revisions.

        The report is written to the experiment evaluation directory.

        All *kwargs* will be passed to the AbsoluteReport class. If the
        keyword argument *attributes* is not specified, a default list
        of attributes is used. ::

            exp.add_absolute_report_step(attributes=["coverage"])

        """
        kwargs.setdefault("attributes", self.DEFAULT_TABLE_ATTRIBUTES)
        report = AbsoluteReport(**kwargs)
        outfile = os.path.join(
            self.eval_dir,
            get_experiment_name() + "." + report.output_format)
        self.add_report(report, outfile=outfile)

    def add_comparison_table_step(self, revision_pairs=[], **kwargs):
        """Add a step that makes pairwise revision comparisons.

        Create comparative reports for all pairs of Fast Downward
        revisions. Each report pairs up the runs of the same config and
        lists the two absolute attribute values and their difference
        for all attributes in kwargs["attributes"].

        All *kwargs* will be passed to the CompareConfigsReport class.
        If the keyword argument *attributes* is not specified, a
        default list of attributes is used. ::

            exp.add_comparison_table_step(attributes=["coverage"])

        """
        kwargs.setdefault("attributes", self.DEFAULT_TABLE_ATTRIBUTES)

        if not revision_pairs:
            revision_pairs = [(rev1, rev2) for rev1, rev2 in itertools.combinations(self._revisions, 2)]
        def make_comparison_tables():
            for rev1, rev2 in revision_pairs:
                compared_configs = []
                for config in self._configs:
                    config_nick = config.nick
                    compared_configs.append(
                        ("%s-%s" % (rev1, config_nick),
                         "%s-%s" % (rev2, config_nick),
                         "Diff (%s)" % config_nick))
                report = ComparativeReport(compared_configs, **kwargs)
                outfile = os.path.join(
                    self.eval_dir,
                    "%s-%s-%s-compare.%s" % (
                        self.name, rev1, rev2, report.output_format))
                report(self.eval_dir, outfile)

        self.add_step("make-comparison-tables", make_comparison_tables)

    def add_scatter_plot_step(self, relative=False, attributes=None, additional=[]):
        if relative:
            scatter_dir = os.path.join(self.eval_dir, "scatter-relative")
            step_name = "make-relative-scatter-plots"
        else:
            scatter_dir = os.path.join(self.eval_dir, "scatter-absolute")
            step_name = "make-absolute-scatter-plots"
        if attributes is None:
            attributes = self.DEFAULT_SCATTER_PLOT_ATTRIBUTES

        def make_scatter_plot(config1, config2, rev, attribute):
            name = "-".join([self.name, config1, config2])
            print("Make scatter plot for", name)
            algo1 = get_algo_nick(rev, config1)
            algo2 = get_algo_nick(rev, config2)

            print(f"{attribute}")
            report = ScatterPlotReport(
                format="pdf",
                filter_algorithm=[algo1, algo2],
                attributes=[attribute],
                relative=relative,
                get_category=lambda run1, run2: run1["domain"])
            report(
                self.eval_dir,
                os.path.join(scatter_dir, config1 + "-" + config2, name))

        def make_scatter_plots():
            for config1, config2 in itertools.combinations(self._configs, 2):
                for rev in self._revisions:
                    for attribute in self.get_supported_attributes(config1.nick, attributes):
                        make_scatter_plot(config1.nick, config2.nick, rev, attribute)

        self.add_step(step_name, make_scatter_plots)


def average(values):
    return sum(values) / len(values) if values else None
