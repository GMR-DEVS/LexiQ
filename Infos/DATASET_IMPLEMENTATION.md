# Dataset Role in your project

W&I + LOCNESS + FCE → preprocessing → M2 error extraction → DistilBERT → contextual error detection → evaluation

## W&I + LOCNESS

Primary dataset — train DistilBERT to detect contextual grammatical errors in learner writing.

- Full name: Write & Improve + LOCNESS
- Type: English learner writing + native English writing
- Content: Essays written by learners at different proficiency levels, along with native-speaker essays.
- Annotations: Grammatical errors are annotated and corrected in M2 format, with ERRANT error categories in the BEA-2019 standardized version.
- Purpose: This is your main dataset for training DistilBERT to recognize grammatical errors based on sentence context.

- Example:

She go to school every day.
→ go is identified as an error
→ correction: goes

- Use in your project:
  Primary training dataset for contextual grammatical error detection.

## FCE

Secondary dataset — provides additional learner English examples and helps improve/generalize the model.

- Full name: First Certificate in English (FCE) corpus
- Source: Cambridge English examination writing.
- Type: English learner writing.
- Content: Essays written by students taking the FCE exam.
- Annotations: Learner errors are annotated with their corresponding corrections. The BEA-2019 version is standardized in M2 format with ERRANT-style error types.
- Purpose: Provides a different collection of learner writing, allowing your model to learn from additional error patterns and reducing dependence on one dataset.

- Use in your project:
  Secondary dataset for additional training/evaluation and improving generalization.
