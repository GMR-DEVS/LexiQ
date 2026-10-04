# coding: utf-8
import sys
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from preprocessing.clean_dataset import (
    m2_to_pairs,
    clean_dataset,
    save_cleaned,
    load_cleaned,
)


def extract_and_clean_all():
    base = Path(__file__).resolve().parents[2]  # LexiQ
    raw_wi = base / "data" / "raw" / "wi+locness" / "m2"
    raw_fce = base / "data" / "raw" / "fce" / "fce" / "m2"
    proc = base / "data" / "processed"
    proc.mkdir(parents=True, exist_ok=True)

    all_recs = []
    for p in sorted(raw_wi.glob("*.m2")):
        pairs = m2_to_pairs(p)
        split = "train" if "train" in p.name else ("dev" if "dev" in p.name else ("test" if "test" in p.name else "other"))
        for o, c in pairs:
            all_recs.append({"original": o, "corrected": c, "source": "wi+locness", "split": split})
    for p in sorted(raw_fce.glob("*.m2")):
        pairs = m2_to_pairs(p)
        split = "train" if "train" in p.name else ("dev" if "dev" in p.name else ("test" if "test" in p.name else "other"))
        for o, c in pairs:
            all_recs.append({"original": o, "corrected": c, "source": "fce", "split": split})

    cleaned, stats = clean_dataset(all_recs)
    save_cleaned(cleaned, proc / "combined_cleaned.jsonl")
    cleaned_noid, stats_noid = clean_dataset(all_recs, drop_identical=True)
    save_cleaned(cleaned_noid, proc / "combined_cleaned_no_identical.jsonl")

    # split out
    recs_wi = [r for r in all_recs if r["source"] == "wi+locness"]
    recs_fce = [r for r in all_recs if r["source"] == "fce"]
    cw, sw = clean_dataset(recs_wi)
    cf, sf = clean_dataset(recs_fce)
    cnw, snw = clean_dataset(recs_wi, drop_identical=True)
    cnf, snf = clean_dataset(recs_fce, drop_identical=True)
    save_cleaned(cw, proc / "wi_locness_cleaned.jsonl")
    save_cleaned(cf, proc / "fce_cleaned.jsonl")
    save_cleaned(cnw, proc / "wi_locness_cleaned_no_identical.jsonl")
    save_cleaned(cnf, proc / "fce_cleaned_no_identical.jsonl")

    print("STATS:", stats)
    print("STATS_NO_ID:", stats_noid)
    print("COUNTS_BY_SPLIT:", Counter((r["source"], r["split"]) for r in cleaned))
    return stats


if __name__ == "__main__":
    extract_and_clean_all()
