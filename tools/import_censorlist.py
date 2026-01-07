#!/usr/bin/env python3
"""Import words from a CensorList JSON into src/cleanvid/swears.txt.

Usage: python tools/import_censorlist.py /path/to/CensorList.json

The script will:
 - parse the JSON (single object, list, or newline-delimited JSON objects)
 - extract the `Word` and optional `Replacement` fields
 - back up the existing `src/cleanvid/swears.txt` to a timestamped .bak
 - append any new (deduplicated) entries to `src/cleanvid/swears.txt`
"""
import sys
import os
import json
from datetime import datetime


def load_input(path):
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    # Try to parse as a single JSON value
    try:
        data = json.loads(text)
        return data
    except Exception:
        pass
    # Try newline-delimited JSON objects
    items = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            items.append(json.loads(line))
        except Exception:
            # ignore unparsable lines
            continue
    return items


def extract_items(parsed):
    results = []
    if isinstance(parsed, dict):
        # Could be a single object or a dict-of-things
        # If it looks like a record with 'Word', use it; otherwise, iterate values
        if 'Word' in parsed:
            results.append(parsed)
        else:
            for v in parsed.values():
                if isinstance(v, dict) and 'Word' in v:
                    results.append(v)
    elif isinstance(parsed, list):
        for it in parsed:
            if isinstance(it, dict) and 'Word' in it:
                results.append(it)
    return results


def main():
    if len(sys.argv) < 2:
        print('Usage: import_censorlist.py /path/to/CensorList.json')
        sys.exit(2)
    src = sys.argv[1]
    if not os.path.isfile(src):
        print('Input file not found:', src)
        sys.exit(2)

    parsed = load_input(src)
    items = extract_items(parsed)
    if not items:
        print('No items with a "Word" field found in input.')
        sys.exit(0)

    swear_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src', 'cleanvid', 'swears.txt')
    swear_path = os.path.normpath(swear_path)
    if not os.path.isfile(swear_path):
        print('swears.txt not found at expected location:', swear_path)
        sys.exit(2)

    # Read existing entries
    with open(swear_path, 'r', encoding='utf-8') as f:
        existing_lines = [l.rstrip('\n') for l in f.readlines()]

    existing_keys = set()
    for ln in existing_lines:
        if not ln.strip():
            continue
        if '|' in ln:
            k = ln.split('|', 1)[0].strip().lower()
        else:
            k = ln.strip().lower()
        existing_keys.add(k)

    # Build new entries
    to_add = []
    for rec in items:
        word = rec.get('Word') or rec.get('word')
        if not word:
            continue
        word = str(word).strip()
        if not word:
            continue
        rep = rec.get('Replacement') if 'Replacement' in rec else rec.get('replacement') if 'replacement' in rec else None
        if rep is not None:
            rep = str(rep).strip()
            if rep == '' or rep.lower() == 'null':
                rep = None
        key = word.lower()
        if key in existing_keys:
            continue
        if rep:
            to_add.append(f"{word}|{rep}")
        else:
            to_add.append(word)
        existing_keys.add(key)

    if not to_add:
        print('No new words to add (all entries already present).')
        sys.exit(0)

    # Backup
    bak = swear_path + '.bak.' + datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    with open(bak, 'w', encoding='utf-8') as f:
        f.write('\n'.join(existing_lines) + '\n')
    # Append
    with open(swear_path, 'a', encoding='utf-8') as f:
        for ln in to_add:
            f.write(ln + '\n')

    print(f'Added {len(to_add)} new entries to {swear_path}. Backup saved as {bak}')


if __name__ == '__main__':
    main()
