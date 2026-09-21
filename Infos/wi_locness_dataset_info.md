# W&I+LOCNESS v2.1 Dataset Guide

## 1. Overview

The **W&I+LOCNESS** dataset (Release 2.1, BEA-2019 Shared Task) is an industry-standard benchmark for **Grammatical Error Correction (GEC)** and automated essay placement/evaluation.

It consists of two complementary sources:
1. **Write & Improve (W&I):** Essays written by non-native (ESL/EFL) English learners submitted to the Cambridge English [Write & Improve](https://writeandimprove.com/) platform. Annotated by Cambridge English annotators and mapped to CEFR proficiency levels.
2. **LOCNESS (Louvain Corpus of Native English Essays):** Essays written by native English students compiled by the Centre for English Corpus Linguistics at the University of Louvain. A subset was annotated by W&I annotators to evaluate GEC models across native-speaker error distributions as well.

---

## 2. Directory Structure

Inside `data/raw/wi+locness/`:

```
wi+locness/
├── json/               # Raw essay-level annotations in JSON Lines (NDJSON) format
│   ├── A.train.json    # CEFR Level A (Beginner) training set
│   ├── A.dev.json      # CEFR Level A validation set
│   ├── B.train.json    # CEFR Level B (Intermediate) training set
│   ├── B.dev.json      # CEFR Level B validation set
│   ├── C.train.json    # CEFR Level C (Advanced) training set
│   ├── C.dev.json      # CEFR Level C validation set
│   └── N.dev.json      # Native English validation set (from LOCNESS)
│
├── m2/                 # Processed sentence-level files in standard M2 format
│   ├── A.train.gold.bea19.m2
│   ├── A.dev.gold.bea19.m2
│   ├── B.train.gold.bea19.m2
│   ├── B.dev.gold.bea19.m2
│   ├── C.train.gold.bea19.m2
│   ├── C.dev.gold.bea19.m2
│   ├── N.dev.gold.bea19.m2
│   ├── ABC.train.gold.bea19.m2  # Merged train set (A + B + C)
│   └── ABCN.dev.gold.bea19.m2   # Merged dev set (A + B + C + N)
│
├── test/               # Tokenized test inputs for BEA-2019 evaluation
├── json_to_m2.py       # Conversion script from character JSON to sentence M2 (requires ERRANT)
├── licence.wi.txt      # Cambridge W&I license (research/educational only)
├── license.locness.txt  # LOCNESS license
└── readme.txt          # Original corpus documentation & citations
```

---

## 3. Data Splits & Statistics

| Split | Metric | Level A (Beginner) | Level B (Intermediate) | Level C (Advanced) | Level N (Native) | Total |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Train** | Essays | 1,300 | 1,000 | 700 | 0 | **3,000** |
| | Sentences | 10,493 | 13,032 | 10,783 | 0 | **34,308** |
| | Tokens | 183,684 | 238,112 | 206,924 | 0 | **628,720** |
| **Dev** | Essays | 130 | 100 | 70 | 50 | **350** |
| | Sentences | 1,037 | 1,290 | 1,069 | 988 | **4,384** |
| | Tokens | 18,691 | 23,725 | 21,440 | 23,117 | **86,973** |
| **Test** | Essays | 130 | 100 | 70 | 50 | **350** |
| | Sentences | 1,107 | 1,330 | 1,010 | 1,030 | **4,477** |
| | Tokens | 18,905 | 23,667 | 19,953 | 23,143 | **85,668** |
| **Total** | Essays | **1,560** | **1,200** | **840** | **100** | **3,700** |

> **Note:** There is **no training set for Native (N)** due to time constraints during the shared task. Level N is only present in Dev and Test sets.

---

## 4. File Formats & Schemas

### A. Raw JSON Format (`json/*.json`)
Files in `json/` are **JSON Lines (NDJSON)**: every line in the file is a separate, valid JSON object containing one complete essay.

> **Important IDE Note:** In VS Code, you might see `End of file expected` on line 2 because the file extension is `.json` instead of `.jsonl`. This does not mean the file is corrupted.

#### Schema:
```json
{
  "id": "1-352420",
  "userid": "21658",
  "cefr": "A2.ii",
  "text": "It's difficult answer at the question...",
  "edits": [
    [
      0,
      [
        [14, 14, " to"],
        [21, 24, ""],
        [328, 334, "clinic"],
        [466, 472, "more easily"]
      ]
    ]
  ]
}
```

#### Field Explanations:
- `id` *(string)*: Unique identifier for the essay.
- `userid` *(string)*: Anonymized ID of the student.
- `cefr` *(string)*: Sub-level CEFR proficiency score (e.g. `A1.i`, `A1.ii`, `A2.i`, `A2.ii`, `B1.i`, `B2.ii`, `C1`, `C2`).
- `text` *(string)*: The uncorrected, original essay as submitted by the student.
- `edits` *(list)*: Character-level edits:
  `[[annotator_id, [[char_start, char_end, correction], ...]], ...]`
  - `char_start` to `char_end`: Zero-indexed character slice in `text`.
  - `correction`: Replacement string (`""` means deletion, `null` indicates an uncorrected/flagged segment).

---

### B. Standard M2 Format (`m2/*.m2`)
M2 is the standard sentence-level format used by GEC evaluation tools like **ERRANT** and **M2Scorer**.

#### Schema:
```
S It 's difficult answer at the question " what are you going to do in the future ? " if the only one who has to know it is in two minds .
A 3 3|||M:VERB:FORM|||to|||REQUIRED|||-NONE-|||0
A 4 5|||U:PREP||||||REQUIRED|||-NONE-|||0

S Maybe I 'll change my mind , maybe not .
A -1 -1|||noop|||-NONE-|||REQUIRED|||-NONE-|||0
```

#### Meaning:
- **`S <tokenized sentence>`**: Original tokenized sentence.
- **`A <start_token> <end_token>|||<error_type>|||<correction>|||<required>|||<comment>|||<annotator_id>`**:
  - `A 3 3|||M:VERB:FORM|||to...`: Missing verb form at index 3; insert `"to"`.
  - `A 4 5|||U:PREP|||||...`: Unnecessary preposition at indices [4, 5); delete it.
  - `A -1 -1|||noop...`: Sentence has no grammatical errors.

#### Common Error Types in ERRANT:
- `R:<CAT>`: Replacement (e.g. `R:VERB`, `R:NOUN`, `R:PREP`, `R:SPELL`)
- `M:<CAT>`: Missing token (e.g. `M:DET`, `M:PUNCT`, `M:VERB:FORM`)
- `U:<CAT>`: Unnecessary token (e.g. `U:PREP`, `U:DET`)
- `noop`: No error

---

## 5. Python Quickstart

### Reading the JSON Files
```python
import json
from pathlib import Path

def load_essays(file_path):
    essays = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                essays.append(json.loads(line))
    return essays

data = load_essays("data/raw/wi+locness/json/A.dev.json")
print(f"Loaded {len(data)} essays. First essay ID: {data[0]['id']}")
```

### Loading with Pandas
```python
import pandas as pd

df = pd.read_json("data/raw/wi+locness/json/A.dev.json", lines=True)
print(df[["id", "cefr", "text"]].head())
```

### Reconstructing the Corrected Text (Character Edits)
```python
def apply_edits(text: str, edits: list) -> str:
    """Applies character-level edits from annotator 0 to text."""
    if not edits or not edits[0] or len(edits[0]) < 2:
        return text
    # Sort edits in reverse order so offsets remain valid
    annotator_edits = sorted(edits[0][1], key=lambda e: (e[0], e[1]), reverse=True)
    corrected = text
    for start, end, repl in annotator_edits:
        if repl is None:
            continue
        corrected = corrected[:start] + repl + corrected[end:]
    return corrected
```

---

## 6. Citations & References

- **Write & Improve (W&I):**
  > Helen Yannakoudakis, Øistein E. Andersen, Ardeshir Geranpayeh, Ted Briscoe, and Diane Nicholls. 2018. *Developing an automated writing placement system for ESL learners.* Applied Measurement in Education, 31:3, pages 251-267.
- **BEA-2019 Shared Task:**
  > Christopher Bryant, Mariano Felice, Øistein E. Andersen, and Ted Briscoe. 2019. *The BEA-2019 Shared Task on Grammatical Error Correction.* In Proceedings of the Fourteenth Workshop on Innovative Use of NLP for Building Educational Applications (BEA 2019).
- **LOCNESS:**
  > Centre for English Corpus Linguistics, Université catholique de Louvain: [LOCNESS Corpus](https://uclouvain.be/en/research-institutes/ilc/cecl/locness.html).
