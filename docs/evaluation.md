# Evaluation Framework Design

This document outlines the design for the evaluation framework of the speech transformation platform.

## 1. Metrics

The following metrics will be used to evaluate the performance of the `anonymize` (SAS) and `convert` (VC) tasks.

### 1.1. Anonymization (SAS) Metrics

*   **Intelligibility**:
    *   **Metric**: Word Error Rate (WER).
    *   **Method**: An Automatic Speech Recognition (ASR) model will transcribe both the original and anonymized audio. The WER will be calculated between the two transcriptions. A lower WER indicates higher intelligibility.
    *   **Implementation**: This will be implemented in `evaluation/metrics.py` and will require an external ASR library.

*   **Privacy**:
    *   **Metric**: Speaker Verification Equal Error Rate (EER).
    *   **Method**: A speaker recognition model will be used to determine if the speaker in the anonymized audio is the same as the original speaker. A higher EER indicates better privacy, as it's harder for the model to distinguish the speakers.
    *   **Implementation**: This will be implemented in `evaluation/metrics.py` and will require a speaker verification library.

### 1.2. Voice Conversion (VC) Metrics

*   **Speaker Similarity**:
    *   **Metric**: Cosine Similarity.
    *   **Method**: A speaker embedding model will extract embeddings from the target voice and the converted voice. The cosine similarity between the embeddings will be calculated. A higher similarity score indicates a more successful conversion.
    *   **Implementation**: This will be implemented in `evaluation/metrics.py`.

*   **Audio Naturalness**:
    *   **Metric**: Mean Opinion Score (MOS) prediction.
    *   **Method**: A pre-trained model (e.g., MOSNet) will be used to predict the naturalness of the converted audio on a scale of 1 to 5.
    *   **Implementation**: This will be implemented in `evaluation/metrics.py`.

### 1.3. Common Metrics

*   **Latency**: End-to-end processing time.
*   **Real-Time Factor (RTF)**: For streaming mode, this is `processing_time / audio_duration`.
*   **Resource Usage**: CPU and memory consumption, measured using `psutil`.

## 2. Evaluation Runner (`evaluation/runner.py`)

The evaluation runner will be a command-line tool responsible for executing evaluation runs.

### 2.1. High-Level Design

The runner will be configuration-driven. A `evaluation.yaml` file will define the evaluation runs.

```yaml
datasets:
  - name: librispeech-test-clean-short
    version: v1.0
providers:
  - cpu
  - remote
modes:
  - non-streaming
  - streaming
tasks:
  - anonymize:
      - strength: 1.0
      - strength: 2.0
  - convert:
      - target_voice_profile: "p225"
```

### 2.2. Workflow

1.  **Load Configuration**: The runner will parse the `evaluation.yaml` file.
2.  **Initialize Providers**: It will initialize the specified providers (`cpu`, `remote`).
3.  **Load Datasets**: It will load the specified datasets using a new `evaluation/datasets.py` module.
4.  **Execute Runs**: For each combination of provider, mode, task, and parameters, the runner will:
    a.  Process each audio file in the dataset.
    b.  Calculate the relevant metrics using `evaluation/metrics.py`.
    c.  Store the results.
5.  **Store and Present Results**:
    *   Results will be saved to a timestamped JSON or CSV file (e.g., `results-20261014T131029.json`).
    *   A summary report will be generated in markdown format.

## 3. Fixture and Dataset Strategy

### 3.1. Versioning

*   **DVC (Data Version Control)** will be used to manage large audio datasets. This will keep the git repository small while ensuring reproducibility.
*   Dataset versions will be referenced in the `evaluation.yaml` file.

### 3.2. Structure

*   `tests/fixtures/`: Small audio files for unit and integration tests. These will be checked into git.
*   `evaluation/datasets/`: Larger datasets for evaluation. This directory will be managed by DVC.
    *   Each dataset will have a `metadata.csv` file with columns like `file_path`, `transcript`, `speaker_id`.

### 3.3. Datasets

Publicly available and licensed datasets will be used, such as:

*   **LibriSpeech**: For ASR and intelligibility testing.
*   **VCTK**: For multi-speaker VC evaluation.
