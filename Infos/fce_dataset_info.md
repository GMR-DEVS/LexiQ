# First Certificate in English (FCE) Dataset Guide

## 1. Overview

The **FCE (First Certificate in English)** corpus is one of the most widely cited benchmark datasets for **Automated Essay Scoring (AES)**, **Grammatical Error Detection (GED)**, and **Grammatical Error Correction (GEC)**.

- **Origin**: Part of the Cambridge Learner Corpus (CLC), developed by Cambridge Assessment and Cambridge University Press.
- **Content**: Authentic examination scripts written by non-native English learners sitting for the Cambridge ESOL First Certificate in English (CEFR level **B2** upper-intermediate) examination between December 2000 and December 2001.
- **BEA-2019 Release (v2.1)**: Released as part of the BEA-2019 Shared Task on Grammatical Error Correction with standard train/dev/test splits, normalised punctuation, and dual formats (JSON Lines and ERRANT M2).

---

## 2. Directory Structure

Inside `data/raw/fce/fce/`:

```
fce/
├── json/                           # Raw essay-level annotations (JSON Lines / NDJSON)
│   ├── fce.train.json              # Training set (~2,141 essays / 1,061 candidates)
│   ├── fce.dev.json                # Development/Validation set (~160 essays)
│   └── fce.test.json               # Evaluation/Test set (~154 essays)
│
├── m2/                             # Processed sentence-level files (M2 format for ERRANT)
│   ├── fce.train.gold.bea19.m2     # Golden sentence-level training annotations
│   ├── fce.dev.gold.bea19.m2       # Golden sentence-level dev annotations
│   └── fce.test.gold.bea19.m2      # Golden sentence-level test annotations
│
├── json_to_m2.py                   # Script converting character JSON to sentence M2 using ERRANT
├── licence.txt                     # Research and educational use licence
└── readme.txt                      # Official release notes and citations
```

---

## 3. Dataset Splits & Statistics

Each examination candidate answered **2 separate prompt questions** (`q`), meaning most candidates have two essay entries in the corpus.

| Split | Number of Essays | Annotations Available | Purpose |
| :--- | :--- | :--- | :--- |
| **Train** (`fce.train.*`) | ~2,141 | Metadata, Scores, Character edits, M2 tags | Model training |
| **Dev** (`fce.dev.*`) | 160 | Metadata, Scores, Character edits, M2 tags | Hyperparameter tuning & validation |
| **Test** (`fce.test.*`) | 154 | Metadata, Scores, Character edits, M2 tags | Final model benchmarking |
| **Total** | **2,455 essays** | ~1,241 candidates | Upper-Intermediate (CEFR B2) |

---

## 4. File Formats & Schemas

### A. Raw JSON Format (`json/*.json`)

The files in `json/` are **JSON Lines (NDJSON)**: each row is an independent, valid JSON object containing an essay submission along with student metadata and grading scores.

#### Example Record:
```json
{
  "id": "TR27*0100*2000*01",
  "l1": "ja",
  "age": "26-30",
  "q": "1",
  "script-s": "27",
  "answer-s": "4.3",
  "text": "13th June 2000\n\nDear Ms Helen Ryan\n\nCompetition Organiser\n\nI have just recieved the letter...",
  "edits": [
    [
      0,
      [
        [71, 79, "received", "S"],
        [195, 203, "grateful", "RJ"],
        [333, 340, "This is because", "M"],
        [358, 358, "an", "MD"],
        [374, 383, "September", "S"],
        [1001, 1010, null, "DJ"]
      ]
    ]
  ]
}
```

#### Field Explanations:
| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | `string` | Unique candidate & question script identifier. |
| `l1` | `string` | First language (native language) code of the candidate (e.g. `ja` for Japanese, `es` for Spanish, `fr` for French, `zh` for Chinese). |
| `age` | `string` | Age bracket of author (e.g., `"26-30"`, `"16-20"`). |
| `q` | `string` | Question/Prompt index (usually `1` or `2` out of the exam's questions). |
| `script-s` | `string` / `float` | Overall score awarded to the student across the entire exam paper. |
| `answer-s` | `string` / `float` | Specific score awarded to this individual essay response. |
| `text` | `string` | Original uncorrected text written by the student. |
| `edits` | `list` | Nested list of character-level annotations: `[[annotator_id, [[start, end, correction, clc_error_code], ...]]]`. |

#### FCE Character Edit Fields:
Unlike generic W&I JSON, FCE character edits also include **CLC Error Codes** as a 4th element:
- `start` *(int)*: Starting character index in `text`.
- `end` *(int)*: Ending character index in `text`.
- `correction` *(str / null)*: Proposed replacement string (`""` means delete; `null` means flagged error without suggested correction).
- `clc_error_code` *(str)*: CLC error tag (e.g., `S` = Spelling, `M` = Missing word, `RJ` = Replace Adjective, `RT` = Replace Preposition, `FV` = Wrong Verb Form, `MD` = Missing Determiner).

---

### B. Processed M2 Format (`m2/*.m2`)

M2 files contain sentence-tokenized data mapped to standard **ERRANT** grammatical error categories.

#### Example:
```
S Dear Kim ,
A -1 -1|||noop|||-NONE-|||REQUIRED|||-NONE-|||0

S You might not believe but actually I helped at a pop concert last month .
A 4 4|||M:PRON|||it|||REQUIRED|||-NONE-|||0
A 10 11|||R:PREP|||with|||REQUIRED|||-NONE-|||0
```

- **`S ...`**: Tokenized original sentence.
- **`A <start> <end>|||<error_tag>|||<correction>|||<required>|||<comment>|||<annotator_id>`**:
  - Token offsets are `[start, end)`.
  - `noop`: Indicates a clean, error-free sentence.

---

## 5. Python Quickstart

### Loading with Python (JSON Lines)
```python
import json

def load_fce(file_path):
    records = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records

dev_data = load_fce("data/raw/fce/fce/json/fce.dev.json")
print(f"Dev Essays: {len(dev_data)}")
print(f"Sample Candidate L1: {dev_data[0]['l1']}, Score: {dev_data[0]['answer-s']}")
```

### Loading with Pandas
```python
import pandas as pd

df = pd.read_json("data/raw/fce/fce/json/fce.train.json", lines=True)
print(df[["id", "l1", "age", "answer-s", "script-s"]].describe())
```

### Reconstructing Golden Corrected Sentences (From Character Edits)
```python
def get_corrected_essay(text: str, edits: list) -> str:
    """Replaces character spans in reverse order to produce the corrected text."""
    if not edits or not edits[0] or len(edits[0]) < 2:
        return text
    # Sort backwards by character start to maintain valid indices
    char_edits = sorted(edits[0][1], key=lambda x: (x[0], x[1]), reverse=True)
    corrected = text
    for start, end, repl, *extra in char_edits:
        if repl is not None:
            corrected = corrected[:start] + repl + corrected[end:]
    return corrected
```

---

## 6. Applications in LexiQ

1. **Grammatical Error Correction (GEC):** Train and benchmark sequence-to-sequence or edit-based models on learner writing.
2. **Automated Essay Scoring (AES):** Predict `answer-s` or `script-s` based on linguistic and syntactic essay quality.
3. **L1 Transfer Analysis:** Study frequent error patterns correlated with learner native languages (`l1`).

---

## 7. Citations & References

- **FCE Dataset Paper:**
  > Helen Yannakoudakis, Ted Briscoe, and Ben Medlock. 2011. *A new dataset and method for automatically grading ESOL texts.* In Proceedings of the 49th Annual Meeting of the Association for Computational Linguistics: Human Language Technologies, pages 180–189.
- **BEA-2019 Shared Task:**
  > Christopher Bryant, Mariano Felice, Øistein E. Andersen, and Ted Briscoe. 2019. *The BEA-2019 Shared Task on Grammatical Error Correction.* In Proceedings of the Fourteenth Workshop on Innovative Use of NLP for Building Educational Applications (BEA 2019).
- **Dataset Repository:** [iLexIR FCE Datasets](https://ilexir.co.uk/datasets/index.html)
