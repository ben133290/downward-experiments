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
    # The following two were used for v1.
    parser.add_pattern("search_start_time", r"\[t=(.+)s, \d+ KB\] g=0, 1 evaluated, 0 expanded", type=int)
    parser.add_pattern("search_start_memory", r"\[t=.+s, (\d+) KB\] g=0, 1 evaluated, 0 expanded", type=int)
    # The following two were used for the later experiments.
    parser.add_pattern("read_input_time", r"\[t=(.+)s, \d+ KB\] done reading input!", type=int)
    parser.add_pattern("read_input_memory", r"\[t=.+s, (\d+) KB\] done reading input!", type=int)
    return parser
