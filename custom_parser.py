#! /usr/bin/env python

import logging
import re
import sys

from lab.parser import Parser

def translator_exit(content, props):
    if "translator_exit_code" in props:
        if props["translator_exit_code"] == 0:
            props["translator_success"] = 1
        else:
            props["translator_success"] = 0
    else:
        props["translator_success"] = 0

class CustomParser(Parser):
    def __init__(self):
        Parser.__init__(self)

def get_parser():
    parser = CustomParser()
    parser.add_pattern("translator_exit_code", r"translate exit code: (.+)", type=int, file="run.log")
    parser.add_pattern("search_bytes_per_state", r"Bytes per state: (.+)", type=int, file="run.log")
    parser.add_pattern("blowup_potential", r"Translator total blow-up potential: (.+)", type=int, file="run.log")
    parser.add_pattern("refactored_disjunctions", r"Translator axiom refactored disjunctions: (.+)", type=int, file="run.log")
    parser.add_pattern("refactored_conditions", r"Translator axiom refactored conditions: (.+)", type=int, file="run.log")
    parser.add_pattern("reused_axioms", r"Number of reused Axioms: (.+)", type=int, file="run.log")
    parser.add_pattern("derived_in_precond", r"Number of derived variables in Preconditions: (.+)", type=int, file="run.log")
    parser.add_pattern("ratio_in_precond", r"Ratio of derived variables in Preconditions: (.+)", type=float, file="run.log")
    parser.add_pattern("sccs", r"Number of SCCs: (.+)", type=int, file="run.log")
    parser.add_pattern("sccs_max", r"Max size of SCCs: (.+)", type=int, file="run.log")

    parser.add_pattern(
        "translator_tot_der_precond",
        r"Translator total derived variables in precond: (.+)",
        type=int,
        file="run.log",
    )
    parser.add_pattern(
        "translator_der_precond",
        r"Translator derived variables in precond: (.+)",
        type=int,
        file="run.log",
    )
    parser.add_pattern(
        "translator_der_effcond",
        r"Translator derived variables in effcond: (.+)",
        type=int,
        file="run.log",
    )
    parser.add_pattern(
        "translator_der_goalcond",
        r"Translator derived variables in goalcond: (.+)",
        type=int,
        file="run.log",
    )

    # Ratios
    parser.add_pattern(
        "translator_tot_ratio_precond",
        r"Translator total ratio variables in precond: (.+)",
        type=float,
        file="run.log",
    )
    parser.add_pattern(
        "translator_ratio_precond",
        r"Translator ratio variables in precond: (.+)",
        type=float,
        file="run.log",
    )
    parser.add_pattern(
        "translator_ratio_effcond",
        r"Translator ratio variables in effcond: (.+)",
        type=float,
        file="run.log",
    )
    parser.add_pattern(
        "translator_ratio_goalcond",
        r"Translator ratio variables in goalcond: (.+)",
        type=float,
        file="run.log",
    )
    parser.add_function(translator_exit)
    return parser
