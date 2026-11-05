#!/usr/bin/env python3
"""Regenerate aggregate metrics from JSONL; does not import an API client or spend credits."""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.benchmark import summarize_records

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input',type=Path);parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    try:
        records=[json.loads(line) for line in args.input.read_text(encoding='utf-8').splitlines() if line.strip()]
        result=summarize_records(records)
    except (ValueError,OSError,KeyError,TypeError) as exc: parser.error(str(exc))
    data=json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n'
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(data,encoding='utf-8')
    else:print(data)
if __name__=='__main__':main()
