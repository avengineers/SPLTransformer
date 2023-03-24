#!/usr/bin/env python
from pathlib import Path

"""
Utility functions needed by all test scripts.
"""


def get_test_data(filename=""):
    return (Path(__file__).parent / "data" / filename).resolve()


def get_output_folder():
    return (Path(__file__).parent.parent / "output").resolve()


def read_file(path):
    with open(path) as f:
        lines = "".join(f.readlines())
    return lines
