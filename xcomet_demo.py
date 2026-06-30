#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Xcomet translation quality evaluation — bundled with translation_eval_web.
Calls the remote xcomet-xl service at XCOMET_URL.
Usage (file mode):  python3 xcomet_demo.py -i input.txt
input.txt format:  <src>\t<translation>  (one pair per line, UTF-8)
Returns a Python dict: {"scores": [...], "mqm_scores": [...], "src_scores": [...]}
"""

import argparse
import codecs
import os
import requests

XCOMET_URL = os.getenv("XCOMET_BASE_URL", "http://10.255.124.15:8813/xcomet-xl")


def evaluate_file(file_path: str) -> dict:
    with codecs.open(file_path, "rb") as f:
        response = requests.post(f"{XCOMET_URL}/file", files={"file": f}, timeout=300)
    return response.json()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Xcomet translation quality evaluator")
    parser.add_argument("-i", required=True, type=str, help="Input file (src<TAB>translation, UTF-8)")
    args = parser.parse_args()
    result = evaluate_file(args.i)
    print(result)
