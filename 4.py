#! /usr/bin/env python3

import os
import custom_parser
from lab.environments import BaselSlurmEnvironment
import common_setup
from common_setup import OptionsConfig, TranslatorExperiment

DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.environ["DOWNWARD_REPO"]
BENCHMARKS_DIR = os.environ["DISJUNCTIVE_BENCHMARKS"]
REVISIONS = ["9cee9542ab43cb5c420237011414f127353b4535"]
BUILDS = ["release"]
CONFIG_NICKS = [
    ("astar-hmax-none", ["--translate-options", "--eliminate-disjunctions=none", "--search-options", "--search", "astar(blind())"]),
    ("astar-hmax-all", ["--translate-options", "--eliminate-disjunctions=all", "--search-options", "--search", "astar(blind())"]),
    ("astar-hmax-extreme", ["--translate-options", "--eliminate-disjunctions=extreme", "--search-options", "--search", "astar(blind())"]),
    #("astar-hmax", ["--search", "astar(hmax())"]),
]
CONFIGS = [
    OptionsConfig(
        nick=config_nick,
        component_options=config,
        build_options=[build],
        driver_options=['--search-time-limit', '10m', "--build", build])
    for build in BUILDS
    for config_nick, config in CONFIG_NICKS
]

SUITE = list(set(['muddy-children', 'blocker', 'psr-middle', 'sum', 'word-rooms', 'spanning-tree', 'collab-and-comm']))
ENVIRONMENT = BaselSlurmEnvironment(
    partition="infai_2",
    email="ben.heuser@unibas.ch",
    export=["PATH"],
)

# if common_setup.is_test_run():
#    SUITE = IssueExperiment.DEFAULT_TEST_SUITE
#    ENVIRONMENT = LocalEnvironment(processes=4)

exp = TranslatorExperiment(repo_path=REPO_DIR, revisions=REVISIONS, configs=CONFIGS, path=None, environment=ENVIRONMENT)

exp.add_suite(BENCHMARKS_DIR, SUITE)

exp.add_parser(exp.EXITCODE_PARSER)
exp.add_parser(exp.TRANSLATOR_PARSER)
exp.add_parser(exp.SINGLE_SEARCH_PARSER)
exp.add_parser(exp.PLANNER_PARSER)
# exp.add_parser(custom_parser.get_parser())

exp.add_step('build', exp.build)
exp.add_step('start', exp.start_runs)
exp.add_step('parse', exp.parse)
exp.add_fetcher(name='fetch')

exp.add_absolute_report_step(attributes=["translator_task_size", "memory", "expansions", "generated", "planner_memory", "planner_time"])
# exp.add_comparison_table_step(attributes=exp.DEFAULT_TABLE_ATTRIBUTES + ["search_start_time"])
# exp.add_scatter_plot_step(relative=False, attributes=["total_time", "memory", "translator_task_size"])
exp.run_steps()
