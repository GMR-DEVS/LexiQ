# coding: utf-8
import json
import re
from pathlib import Path
from typing import List,Dict,Tuple,Union
import unicodedata

DEFAULT_MIN_TOKENS=2
DEFAULT_MAX_TOKENS=512

def normalize_text(s:str)->str:
    if s is None: return ""
    s=unicodedata.normalize("NFKC",s)
    s=re.sub(r"[\r\n\t]+"," ",s)
    s=re.sub(r"\s+"," ",s)
    return s.strip()

def count_tokens(s:str)->int:
    if not s: return 0
    return len(s.split())

def is_valid_record(orig:str,corr:str,min_tokens:int=DEFAULT_MIN_TOKENS,max_tokens:int=DEFAULT_MAX_TOKENS)->bool:
    on=normalize_text(orig); cn=normalize_text(corr)
    if not on or not cn: return False
    ot=count_tokens(on); ct=count_tokens(cn)
    if ot<min_tokens or ct<min_tokens: return False
    if ot>max_tokens or ct>max_tokens: return False
    return True

def is_identical_pair(orig:str,corr:str)->bool:
    return normalize_text(orig)==normalize_text(corr)

def m2_to_pairs(m2_path: Union[str, Path]) -> List[Tuple[str, str]]:
    m2_path = Path(m2_path)
    pairs = []
    try:
        with open(m2_path, encoding="utf-8", errors="replace") as fh:
            lines = fh.readlines()
    except Exception:
        return pairs
    j = 0; n = len(lines)
    while j < n:
        if lines[j].startswith("S "):
            orig = lines[j][2:].rstrip("\n\r")
            k = j + 1; edits = []
            while k < n and lines[k].strip() and not lines[k].startswith("S "):
                if lines[k].startswith("A "): edits.append(lines[k])
                k += 1
            real_edits = []
            for a in edits:
                parts = a.split("|||")
                if len(parts) >= 3 and parts[1] == "noop": continue
                real_edits.append(a)
            tokens = orig.split()
            tlist = list(tokens)
            for a in reversed(real_edits):
                try:
                    parts = a.split("|||"); span = parts[0].split()
                    if len(span) < 3: continue
                    s,e = int(span[1]), int(span[2]); cor = parts[2] if len(parts)>2 else ""; cortoks = cor.split() if cor else []
                    if cor == "" or cor == "-NONE-":
                        if s < len(tlist) and e <= len(tlist) and s <= e: del tlist[s:e]
                        elif s < len(tlist) and e > len(tlist): del tlist[s:]
                    else:
                        if s > len(tlist): s = len(tlist)
                        if e > len(tlist): e = len(tlist)
                        if s < 0: s = 0
                        if e < s: e = s
                        del tlist[s:e]
                        for ct in reversed(cortoks): tlist.insert(s, ct)
                except Exception: continue
            corr = " ".join(tlist)
            pairs.append((orig,corr))
            j=k; continue
        j+=1
    return pairs

def clean_dataset(records: List[Dict], min_tokens: int = DEFAULT_MIN_TOKENS, max_tokens: int = DEFAULT_MAX_TOKENS,
                  drop_identical: bool = False) -> Tuple[List[Dict], Dict[str, int]]:
    cleaned = []
    stats = {
        "total": len(records),
        "empty_removed": 0,
        "invalid_removed": 0,
        "identical_removed": 0,
        "duplicates_removed": 0,
        "short_removed": 0,
        "long_removed": 0,
        "kept": 0,
    }
    seen_pairs = set()
    for rec in records:
        orig = rec.get("original", rec.get("orig", ""))
        corr = rec.get("corrected", rec.get("corr", ""))
        orig_n = normalize_text(orig)
        corr_n = normalize_text(corr)
        if not orig_n or not corr_n:
            stats["empty_removed"] += 1
            continue
        ot = count_tokens(orig_n); ct = count_tokens(corr_n)
        if ot < min_tokens or ct < min_tokens:
            stats["short_removed"] += 1
            continue
        if ot > max_tokens or ct > max_tokens:
            stats["long_removed"] += 1
            continue
        if drop_identical and is_identical_pair(orig, corr):
            stats["identical_removed"] += 1
            continue
        pair_key = (orig_n, corr_n)
        if pair_key in seen_pairs:
            stats["duplicates_removed"] += 1
            continue
        seen_pairs.add(pair_key)
        cleaned_rec = dict(rec)
        cleaned_rec["original"] = orig_n
        cleaned_rec["corrected"] = corr_n
        cleaned.append(cleaned_rec)
        stats["kept"] += 1
    return cleaned, stats

def save_cleaned(records: List[Dict], path: Union[str, Path]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

def load_cleaned(path: Union[str, Path]) -> List[Dict]:
    path = Path(path)
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line: continue
            records.append(json.loads(line))
    return records

def sentence_to_token_labels(orig: str, corr: str) -> Tuple[List[str], List[str], List[int]]:
    """
    Compares original and corrected sentences and aligns them into token-level labels:
    - 'O': Correct token (binary 1)
    - 'ERROR': Contextually incorrect / modified / deleted token (binary 0)
    """
    import difflib
    orig_tokens = orig.split()
    corr_tokens = corr.split()

    matcher = difflib.SequenceMatcher(None, orig_tokens, corr_tokens)
    labels = ["O"] * len(orig_tokens)

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag in ("replace", "delete"):
            for idx in range(i1, i2):
                labels[idx] = "ERROR"
        elif tag == "insert":
            # Missing token in original sentence; mark adjacent anchor token as ERROR
            if i1 < len(labels):
                labels[i1] = "ERROR"
            elif i1 > 0:
                labels[i1 - 1] = "ERROR"

    binary_labels = [1 if lbl == "O" else 0 for lbl in labels]
    return orig_tokens, labels, binary_labels

