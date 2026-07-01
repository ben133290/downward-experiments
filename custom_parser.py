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
    parser.add_function(translator_exit)
    return parser
