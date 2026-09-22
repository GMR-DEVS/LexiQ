# what is distilbert
    DistilBERT is used to detect contextual errors in sentences through binary token classification. The input text is first converted into tokens using the DistilBERT tokenizer. These tokens are then passed to DistilBERT, which analyzes each word based on the context of the entire sentence.Here we are using distilbert-base-uncased.

# distilbert-base-uncased
    distilbert-base-uncased is a pretrained, smaller, and faster version of BERT used as the base model in our contextual error detection project. It understands each word by analyzing the surrounding sentence context. The model is fine-tuned for token classification, where 0 represents a contextual error and 1 represents a correct token. It only detects errors and does not correct or replace them.
    
# workflow of distilbert
Workflow:-
    The system receives the input sentence.

    The text is preprocessed and divided into words.

    The DistilBERT tokenizer converts the words into tokens, token IDs, and attention masks.

    Original word labels are aligned with DistilBERT subword tokens.

    The tokens are passed to the DistilBERT model.

    DistilBERT analyzes every token using the context of the complete sentence.

    A classification head predicts a label for each token:

    0 — contextually incorrect token

    1 — correct token

    Subword predictions are combined and mapped back to the original words.

    The system calculates the confidence score for each prediction.

    Post-processing extracts the incorrect word and its start and end positions.

    The results are returned through the inference function or FastAPI endpoint.
# working of distilbert
Working:-
    The model is fine-tuned using pairs of incorrect and corrected sentences.

    Differences between the two sentences are used to generate token-level labels.

    Contextually incorrect tokens receive the label 0.

    Correct tokens receive the label 1.

    During training, DistilBERT learns how surrounding words affect the meaning and correctness of each token.

    During inference, it checks every token in the input sentence and predicts whether it is correct or contextually incorrect.

    The model returns error details without correcting or replacing the word.

    Example:

    text
    Input:
    I goes to school.

    Tokens:
    I | goes | to | school

    Labels:
    1 |  0   | 1  | 1
    Here, goes is marked as a contextual error because it is incorrect in the sentence. The system can return the incorrect word, label, character position, and confidence score. Correction is not performed because it belongs to Phase 2.