#! /usr/bin/env python

import logging
import re
import sys

from lab.parser import Parser

class CustomParser(Parser):
    def __init__(self):
        Parser.__init__(self)

def get_parser():
    parser = CustomParser()
    parser.add_pattern("translator_exit_code", r"translate exit code: (.+)", type=int, file="run.log")
    return parser
