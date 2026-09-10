#!/usr/bin/env python3
"""
谱面 JSON 校验器
  python audit_score.py score.json                  # 校验字数/音符数
  python audit_score.py A.json --compare B.json     # 比较两个来源的音符差异
"""
import argparse
import json
import re
import sys


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def iter_rows(data):
    for sect in data["sections"]:
        for row in sect["rows"]:
            yield sect["name"], row


def audit(data, path=""):
    bad = 0
    warned = []
    total = 0
    print(f"{'行数':<6}{'字数/音符':<12}{'歌词'}")
    print("-" * 72)
    for i, (sect, row) in enumerate(iter_rows(data), 1):
        lyric, notes = row["lyric"], row["notes"]
        n_chars, n_toks = len(list(lyric)), len(notes.split())
        total += 1
        flag = "OK " if n_chars == n_toks else "BAD"
        if flag == "BAD":
            bad += 1
        print(f"{i:<6}{f'{n_chars}/{n_toks}':<12}{lyric}   [{flag}]")
        # 非法音符记号
        for tok in notes.split():
            core = tok.lstrip("_").rstrip("^")
            if not core.isdigit() or not (1 <= int(core) <= 7):
                warned.append(f"第{i}行 {lyric}：非法音符 {tok!r}（应为 1-7，^表高八度，_表低八度）")
    print("-" * 72)
    for w in warned:
        print("WARN", w)
    print(f"共 {total} 行，{bad} 行字数与音符数不符，{len(warned)} 处记号告警")
    return bad + len(warned)


def compare(A, B):
    """按歌词对齐，打印两个来源的音符差异。"""
    def index(d):
        out = {}
        for _, row in iter_rows(d):
            out[row["lyric"]] = row["notes"]
        return out

    ia, ib = index(A), index(B)
    keys = [k for k in ia if k in ib]
    print(f"共同行 {len(keys)} 条；"
          f"A独有 {len(set(ia)-set(ib))} 条；B独有 {len(set(ib)-set(ia))} 条\n")
    diff = 0
    for k in keys:
        if ia[k].replace(" ", "") != ib[k].replace(" ", ""):
            if len(ia[k].split()) != len(ib[k].split()):
                tag = "⚠ 音符数不同"
            else:
                tag = "· 音符有出入"
            diff += 1
            print(f"{tag}  {k}")
            print(f"    A: {ia[k]}")
            print(f"    B: {ib[k]}")
    print(f"\n共 {diff} 行存在差异 —— 逐条用第三个来源或直接听原曲来判定")
    return diff


def main():
    ap = argparse.ArgumentParser(description="校验 / 比对简谱 JSON")
    ap.add_argument("json_path")
    ap.add_argument("--compare", metavar="OTHER", help="与另一份 JSON 做逐句比对")
    args = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    data = load(args.json_path)
    rc = audit(data, args.json_path)
    if args.compare:
        print()
        rc += compare(data, load(args.compare))
    sys.exit(1 if rc else 0)


if __name__ == "__main__":
    main()
