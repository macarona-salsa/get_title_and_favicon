#!/usr/bin/env python3
"""Test get_title_and_favicon.py"""
import sys
import argparse

import get_title_and_favicon

parser = argparse.ArgumentParser()
parser.add_argument("url", help="url to get title and favicon from")
args = parser.parse_args()

title, favicon = get_title_and_favicon.get_title_and_favicon(args.url)
get_title_and_favicon.save_favicon(favicon)
print(f"title: {title}\nicon saved to disk")
