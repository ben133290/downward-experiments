#! /usr/bin/env python3

import os
import custom_parser
from lab.environments import BaselSlurmEnvironment
from lab.reports import Attribute
import common_setup
from common_setup import OptionsConfig, TranslatorExperiment, average
from downward.reports.scatter import ScatterPlotReport

DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.environ["DOWNWARD_REPO"]
BENCHMARKS_DIR = os.environ["DISJUNCTIVE_BENCHMARKS"]
REVISIONS = ["409982b293", "80929ba016"]
BUILDS = ["release"]
CONFIG_NICKS = [
    ("1-none", ["--translate-options", "--eliminate-disjunctions=none", "--search-options", "--search", "astar(blind())"]),
    ("2-all", ["--translate-options", "--eliminate-disjunctions=all", "--search-options", "--search", "astar(blind())"]),
    ("3-extreme", ["--translate-options", "--eliminate-disjunctions=extreme", "--search-options", "--search", "astar(blind())"]),
]
CONFIGS = [
    OptionsConfig(
        nick=config_nick,
        component_options=config,
        build_options=[build],
        driver_options=['--search-time-limit', '20m', '--search-memory-limit', '4000', "--build", build])
    for build in BUILDS
    for config_nick, config in CONFIG_NICKS
]

SUITE = list(set(['muddy-children', 'muddy-child', 'blocker', 'psr-middle', 'sum', 'word-rooms', 'collab-and-comm', 'psr-large', 'miconic-fulladl', 'optical-telegraphs', 'social-planning', 'ghosh-etal-JAR-acc-cc2', 'ged1-ds2nd', 'ged1-ds1', 'assembly', 'miconic-axioms', 'explode',]))
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
exp.add_parser(custom_parser.get_parser())

exp.add_step('build', exp.build)
exp.add_step('start', exp.start_runs)
exp.add_step('parse', exp.parse)
exp.add_fetcher(name='fetch')

REPORT_ATTRIBUTES = [
    "cost",
    "coverage",
    Attribute("expansions", function=sum, min_wins=True),
    "expansions_until_last_jump",
    Attribute("generated", function=sum, min_wins=True),
    "generated_until_last_jump",
    "memory",
    "planner_memory",
    "planner_time",
    "ratio_in_precond",
    "reused_axioms",
    "sccs",
    "sccs_max",
    "search_bytes_per_state",
    Attribute("search_time", function=sum, min_wins=True),
    "task_size",
    "total_time",
    "translator_axioms",
    "translator_derived_variables",
    "translator_der_effcond",
    "translator_der_goalcond",
    "translator_der_precond",
    "translator_exit_code",
    Attribute("translator_peak_memory", function=average, min_wins=True),
    Attribute("translator_ratio_effcond", function=average, min_wins=True),
    Attribute("translator_ratio_goalcond", function=average, min_wins=True),
    Attribute("translator_ratio_precond", function=average, min_wins=True),
    Attribute("translator_success", function=average, min_wins=True),
    "translator_task_size",
    Attribute("translator_tot_ratio_precond", function=average, min_wins=True),
    "translator_tot_der_precond",
    "variables",
]

exp.add_absolute_report_step(attributes=REPORT_ATTRIBUTES)

exp.run_steps()
