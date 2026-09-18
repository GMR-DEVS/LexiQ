# ─────────────────────────────────────────────────────────────────────────────
# STEP 0 — SETUP
# import stuffs
# Config stuffs
# Get some words from nltk
# ─────────────────────────────────────────────────────────────────────────────
# # This is namade import section, we are importing stuffs like Regular expression for word parsing, requests for making HTTP requests, nltk fro NLP stuffs, FastAPI for API stuffs and Basemodel from pydantic to define what we expect from the API response
import re
import requests
import nltk
from symspellpy import SymSpell, Verbosity
import pkg_resources
import logging
from fastapi import FastAPI
from pydantic import BaseModel

# We are downloading some pre defined words from nltk library. Evide we are using quiet=True to ensure tht our terminal doesnt get clustered by laoding, dowloading blah blah stuffs from nltk
# Corpus is like a dictioanry of this so called nltk library, namal athile "words" tag ola elam idth ENGLISH_WORDS enna set il add cheyth idum
nltk.download("words", quiet=True)
from nltk.corpus import words as nltk_words # evide output is a python list of strings
ENGLISH_WORDS = set(w.lower() for w in nltk_words.words())  # Set is used because it gives us a faster lookup! for words

# Setting up some configuration so tht our code doesnt go south!
DICTIONARY_API_URL  = "https://api.dictionaryapi.dev/api/v2/entries/en"
MAX_EDIT_DISTANCE   = 2   # max Levenshtein distance to accept a suggestion
MAX_SUGGESTIONS     = 5   # how many suggestions to return per error

# FastAPI setup
app = FastAPI()

try:
    sym_spell = SymSpell(max_dictionary_edit_distance=MAX_EDIT_DISTANCE, prefix_length=7)
    dictionary_path = pkg_resources.resource_filename(
        "symspellpy", "frequency_dictionary_en_82_765.txt"
    )
    loaded_ok = sym_spell.load_dictionary(dictionary_path, term_index=0, count_index=1)
    if not loaded_ok:
        logging.warning("SymSpell dictionary failed to load.")
        sym_spell = None
except Exception as e:
    logging.warning(f"SymSpell initialization failed: {e}")
    sym_spell = None

# BaseModel class from Pydantic library to check the format of stuffs
class SpellCheckRequest(BaseModel):
    text: str

class SpellCheckResponse(BaseModel):
    original_text: str
    errors: list



# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — PREPROCESSING
# Normalize the sentence - collapse extra spaces, keep punctuation intact
# ─────────────────────────────────────────────────────────────────────────────
def preprocess(text: str) -> str:
    text = text.strip() # Remove trailing spaces
    text = re.sub(r"\s+", " ", text)   # collapse multiple spaces into one
    return text



# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 — TOKENIZATION
# Split sentence into individual word tokens(Namal ignoring numbers and shiii).
# We record each token's position so we can report it later.
# ─────────────────────────────────────────────────────────────────────────────
def tokenize(text: str) -> list:
    tokens = []
    for index, match in enumerate(re.finditer(r"[A-Za-z']+", text)): # Evide namal enumertae use cheyum, for giving index(int) to each token we are generating
        tokens.append({
            "raw"        : match.group(),           # original casing
            "clean"      : match.group().lower(),   # lowercased for lookup
            "token_index": index,                   # position among all tokens (0-based start)
            "char_start" : match.start(),           # character offset in the sentence
        })
    return tokens



# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 — DICTIONARY API CHECK
# Call the Free Dictionary API for the given word.
# Returns:
#   True  → word is valid (API returned 200 with entries)
#   False → word not found (API returned 404)
#   None  → network/timeout error (we skip the word to avoid false positives)
# ─────────────────────────────────────────────────────────────────────────────
def check_word_in_api(word: str):
    url = f"{DICTIONARY_API_URL}/{word}" # Ithu use cheyth we will rqst to API to send shii
    try: # We check for timeout and connection error specifically and a generic stuff for rest
        response = requests.get(url, timeout=5)
    except requests.exceptions.Timeout:
        print(f"[API] Timeout for word: {word}")
        return None
    except requests.exceptions.ConnectionError:
        print(f"[API] Connection error for word: {word}")
        return None
    # STATUS CODE 200
    if response.status_code == 200: # 200 is for okie dokie
        data = response.json() # convert json data to python dict/list :::: If respones is in dict fromat, we get a python dict...else if its in list format, we get a python list
        # The API returns a list of entries — if it's non-empty, word is valid
        if isinstance(data, list) and len(data) > 0:
            return True # Evide if list length is greater than 0, means word exists in Dictionary
        return False # else if list length is 0, means word doesnt exist in Dictionary
    # STATUS CODE 404
    if response.status_code == 404: # 404 is for not found
        # 404 means the word was not found in the dictionary
        return False
    # STATUS CODE 5xx & others
    # Any other status (5xx, rate limit, etc.) → treat as uncertain, skip
    print(f"[API] Unexpected status {response.status_code} for word: {word}")
    return None # None means we are skipping the word to avoid false positives



# ─────────────────────────────────────────────────────────────────────────────
# STEP 4 — LEVENSHTEIN DISTANCE
# Calculates the minimum number of insertions, deletions, or substitutions
# ─────────────────────────────────────────────────────────────────────────────
def levenshtein_distance(word1: str, word2: str) -> int:
    # Make word1 the shorter one to save memory
    if len(word1) > len(word2):
        word1, word2 = word2, word1

    prev_row = list(range(len(word2) + 1))

    for i, char1 in enumerate(word1, start=1):
        curr_row = [i] + [0] * len(word2)
        for j, char2 in enumerate(word2, start=1):
            if char1 == char2:
                curr_row[j] = prev_row[j - 1]          # characters match — no edit needed
            else:
                curr_row[j] = 1 + min(
                    prev_row[j],        # deletion
                    curr_row[j - 1],    # insertion
                    prev_row[j - 1],    # substitution
                )
        prev_row = curr_row

    return prev_row[len(word2)]



# ─────────────────────────────────────────────────────────────────────────────
# STEP 5 — CANDIDATE GENERATION
# Compare the misspelled word against every word in the NLTK word list.
# Keep only words whose Levenshtein distance is within MAX_EDIT_DISTANCE. A quick length filter avoids computing distance for obviously far words.
# ─────────────────────────────────────────────────────────────────────────────
# Namal are gonna go through each word in ENGLISH_WORDS and then comapre it with each word in our sentence
# We gonna check leveveve shiii and decide if its wrong or not
def symspell_candidates(misspelled: str) -> list:
    """
    Use SymSpell to quickly get a small pool of candidate corrections.
    
    SymSpell pre-builds a deletion index at startup so this lookup is very fast.
    It returns only words within MAX_EDIT_DISTANCE — no full word list scan needed.
    
    Returns a list of (word, distance) tuples, same format as generate_candidates().
    Returns empty list if SymSpell is unavailable.
    """
    if sym_spell is None:
        return []
    try:
        suggestions = sym_spell.lookup(
            misspelled, Verbosity.CLOSEST, max_edit_distance=MAX_EDIT_DISTANCE
        )
        return [{"word": s.term, "distance": s.distance} for s in suggestions]
    except Exception as e:
        logging.warning(f"SymSpell lookup failed for {misspelled}: {e}")
        return []

def generate_candidates(misspelled: str) -> list:
    candidates = [] # To store things tht we r gonna send back in return statement
    target_len = len(misspelled)

    for word in ENGLISH_WORDS:
        # Skip words that are too different in length to be within MAX_EDIT_DISTANCE
        if abs(len(word) - target_len) > MAX_EDIT_DISTANCE:
            continue

        dist = levenshtein_distance(misspelled, word)
        if dist <= MAX_EDIT_DISTANCE:
            candidates.append({"word": word, "distance": dist})

    return candidates



# ─────────────────────────────────────────────────────────────────────────────
# STEP 6 — CANDIDATE RANKING
# Sort candidates by:
#   1. Levenshtein distance (lower = better)
#   2. Length similarity    (closer length = better, as a tie-breaker)
#   3. Alphabetical order   (final deterministic tie-breaker)
# Return only the top MAX_SUGGESTIONS results.
# ─────────────────────────────────────────────────────────────────────────────
def rank_candidates(misspelled: str, candidates: list) -> list:
    target_len = len(misspelled)
    ranked = sorted(
        candidates,
        key=lambda c: (c["distance"], abs(len(c["word"]) - target_len), c["word"])
    )
    return ranked[:MAX_SUGGESTIONS]



# ─────────────────────────────────────────────────────────────────────────────
# STEP 7 — ERROR RECORDING
# Bundle everything about a detected error into one dict.
# The original word is never changed — this step only records the finding.
# ─────────────────────────────────────────────────────────────────────────────
def record_error(token: dict, suggestions: list) -> dict:
    return {
        "word"        : token["raw"],
        "position"    : token["token_index"],
        "char_position": token["char_start"],
        "error_type"  : "spelling",
        "suggestions" : suggestions,
    }



# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINT — POST /check-spelling
# Runs all 7 steps above and returns the original text + list of errors.
# ─────────────────────────────────────────────────────────────────────────────
@app.post("/check-spelling")
def check_spelling(request: SpellCheckRequest):
    # ---------- Step 1 — Preprocess ----------
    text = preprocess(request.text)
    # ---------- Step 2 — Tokenize ----------
    tokens = tokenize(text)
    
    errors = []
    for token in tokens:
        word = token["clean"]
        # Skip single-character words like "I" or "a", usually valid ale 
        if len(word) < 2:
            continue

        # ---------- Step 3 — Dictionary API check ----------
        result = check_word_in_api(word)

        if result is True:
            continue   # word is valid, move on

        if result is None:
            continue   # API failed, skip word to avoid false positives

        # Word not found in dictionary — treat as possible spelling error
        # ---------- Step 4 + 5 — Levenshtein distance + Candidate generation ----------
        
        # Try SymSpell first — it's fast because it uses a pre-built index
        candidates = symspell_candidates(word)
        
        # If SymSpell returned nothing (unavailable or no results), fall back
        # to the original generate_candidates which scans the full word list
        if not candidates:
            candidates = generate_candidates(word)

        # ---------- Step 6 — Rank candidates ----------
        suggestions = rank_candidates(word, candidates)

        # ---------- Step 7 — Record the error ----------
        errors.append(record_error(token, suggestions))

    return SpellCheckResponse(original_text=request.text, errors=errors)
