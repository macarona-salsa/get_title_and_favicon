#!/usr/bin/env python3
"""Test get_favicon_and_title.py"""
import sys
import argparse

import get_favicon_and_title

parser = argparse.ArgumentParser(description="Test get_favicon_and_title.py")
parser.add_argument("url", help="url to get favicon and title from")
args = parser.parse_args()

favicon, title = get_favicon_and_title.get_favicon_and_title(args.url)
get_favicon_and_title.save_favicon(favicon)
print(f"title: {title}\nicon saved to disk")
