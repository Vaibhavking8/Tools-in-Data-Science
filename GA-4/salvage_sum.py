#!/usr/bin/env python3
import sys
import json
import hashlib

path = sys.argv[1] if len(sys.argv) > 1 else 'corrupted_logs.json'

def find_metric(obj):
    total = 0
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == 'metric_2455':
                try:
                    total += int(v)
                except Exception:
                    pass
            total += find_metric(v)
    elif isinstance(obj, list):
        for item in obj:
            total += find_metric(item)
    return total

s = 0
try:
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            s += find_metric(obj)
except FileNotFoundError:
    # try path inside corrupted_logs folder
    try:
        with open('corrupted_logs/' + path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                s += find_metric(obj)
    except Exception:
        pass

h = hashlib.sha256(str(int(s)).encode('utf-8')).hexdigest()
sys.stdout.write(h)
