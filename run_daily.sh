#!/bin/bash
# Runs the crawl on any computer with Python 3: bash run_daily.sh   (on Windows: python mercor_crawl.py etc. in PowerShell)
cd "$(dirname "$0")"
python3 mercor_crawl.py && python3 micro1_crawl.py && python3 hot_tracker.py
