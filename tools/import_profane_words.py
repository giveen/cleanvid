#!/usr/bin/env python3
"""Fetch profane-words JSON and merge unique entries into src/cleanvid/swears.txt.
Backup original file before writing.
Prints the number of words added and the backup path.
"""
import json
import urllib.request
import os
import sys
from datetime import datetime

RAW_URL = 'https://raw.githubusercontent.com/zautumnz/profane-words/master/words.json'
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SWEARS_PATH = os.path.join(HERE, 'src', 'cleanvid', 'swears.txt')


def fetch_json(url):
    with urllib.request.urlopen(url) as r:
        data = r.read()
    return json.loads(data.decode('utf-8'))


def load_current_keys(path):
    keys = set()
    if not os.path.isfile(path):
        return keys
    with open(path, 'r', encoding='utf-8') as f:
        for ln in f:
            ln = ln.strip()
            if not ln:
                continue
            if '|' in ln:
                key = ln.split('|', 1)[0].strip().lower()
            else:
                key = ln.strip().lower()
            keys.add(key)
    return keys


def main():
    try:
        words = fetch_json(RAW_URL)
    except Exception as e:
        print(f"Failed to fetch JSON: {e}", file=sys.stderr)
        sys.exit(2)
    words_norm = []
    for w in words:
        if not isinstance(w, str):
            continue
        w2 = w.strip()
        if not w2:
            continue
        words_norm.append(w2)

    current_keys = load_current_keys(SWEARS_PATH)
    added = []
    for w in words_norm:
        k = w.split('|',1)[0].strip().lower()
        if k not in current_keys:
            added.append(w)
            current_keys.add(k)

    if not added:
        print("No new words to add.")
        return

    # Backup
    bak_path = SWEARS_PATH + '.bak.' + datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    try:
        if os.path.isfile(SWEARS_PATH):
            os.rename(SWEARS_PATH, bak_path)
        else:
            # ensure dir exists
            os.makedirs(os.path.dirname(SWEARS_PATH), exist_ok=True)
            open(SWEARS_PATH, 'w', encoding='utf-8').close()
    except Exception as e:
        print(f"Failed to create backup: {e}", file=sys.stderr)
        sys.exit(3)

    # Write merged file: preserve original lines from backup order, then append new entries
    try:
        orig_lines = []
        if os.path.isfile(bak_path):
            with open(bak_path, 'r', encoding='utf-8') as f:
                orig_lines = [ln.rstrip('\n') for ln in f]
        with open(SWEARS_PATH, 'w', encoding='utf-8') as out:
            # write original content first
            for ln in orig_lines:
                out.write(ln + '\n')
            # append new words in lowercase
            for w in added:
                out.write(w.lower() + '\n')
    except Exception as e:
        print(f"Failed to write merged file: {e}", file=sys.stderr)
        # Attempt to restore backup
        try:
            if os.path.isfile(bak_path):
                os.replace(bak_path, SWEARS_PATH)
        except Exception:
            pass
        sys.exit(4)

    print(f"Added {len(added)} new entries to {SWEARS_PATH}")
    print(f"Backup saved as {bak_path}")


if __name__ == '__main__':
    main()
