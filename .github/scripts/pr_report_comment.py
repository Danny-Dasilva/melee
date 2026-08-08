#!/usr/bin/env python3
"""Render a decomp.dev-style PR report comment from objdiff report/changes JSON.

Usage: pr_report_comment.py BASELINE.json CURRENT.json CHANGES.json BASE_SHA HEAD_SHA
Writes markdown to stdout; the workflow posts it as (or patches into) a PR comment.
"""
import json
import sys


def load(path):
    with open(path) as f:
        return json.load(f)


def main():
    baseline, current, changes, base_sha, head_sha = sys.argv[1:6]
    b, c, ch = load(baseline), load(current), load(changes)
    bm, cm = b["measures"], c["measures"]
    pct = cm["matched_code_percent"]
    dpct = pct - bm["matched_code_percent"]
    dbytes = int(cm["matched_code"]) - int(bm["matched_code"])

    broken, regressed, improved = [], [], []
    for unit in ch.get("units", []):
        for fn in unit.get("functions") or []:
            if fn is None:
                continue
            fr = (fn.get("from") or {}).get("fuzzy_match_percent") or 0
            to = (fn.get("to") or {}).get("fuzzy_match_percent") or 0
            if to == fr:
                continue
            row = (unit.get("name"), fn.get("name"), fr, to)
            if fr == 100 and to < 100:
                broken.append(row)
            elif to < fr:
                regressed.append(row)
            else:
                improved.append(row)
    improved.sort(key=lambda r: r[3] - r[2], reverse=True)

    print("<!-- fork-pr-report -->")
    print(f"## Report for GALE01 (`{base_sha[:7]}` → `{head_sha[:7]}`)\n")
    print(f"**Matched code**: {pct:.2f}% ({dpct:+.2f}%, {dbytes:+,} bytes)\n")

    def table(title, rows):
        if not rows:
            return
        print(f"### {title} ({len(rows)})\n")
        print("| Unit | Function | Before | After |")
        print("|---|---|---:|---:|")
        for u, f, fr, to in rows[:30]:
            print(f"| `{u}` | `{f}` | {fr:.2f}% | {to:.2f}% |")
        if len(rows) > 30:
            print(f"\n…and {len(rows) - 30} more")
        print()

    table("💔 Broken matches", broken)
    table("📉 Regressions in unmatched items", regressed)
    table("📈 Improvements", improved)
    if not (broken or regressed or improved):
        print("No function-level changes.")


if __name__ == "__main__":
    main()
