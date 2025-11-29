This is the **Master Context File**. It consolidates your raw notes, feature lists, and architectural philosophy into a single "Source of Truth."

Save this content directly to `specs/00_context.md`.

***

# Project Context: Audio Toolkit

## 1. Executive Summary
**Audio Toolkit** is a comprehensive, modular, and "batch-first" Python utility designed to automate audio engineering tasks. It serves as a unified replacement for the fragmented ecosystem of one-off scripts currently used by Data Scientists, ML Engineers, Podcasters, and Musicians.

**The Core Value Proposition:**
* **Zero-Friction:** Accessible via a clean CLI (`Typer`) or Python API.
* **Batch-First:** Optimized to process 1 file or 10,000 files in a single command.
* **AI-Ready:** Specifically tuned for preparing training datasets for TTS (Text-to-Speech) and STT (Speech-to-Text) models.

## 2. Architectural Philosophy
The project adheres to a **"Min-Max"** operational strategy: *Minimum Complexity, Maximum Utility.*

* **Modular Design:** Features are implemented as isolated plugins/processors.
* **SOLID Principles:**
    * **Single Responsibility:** Each processor does one thing (e.g., `Splitter`, `Converter`).
    * **Open/Closed:** New features (plugins) can be added without modifying core logic.
* **Code Standards:**
    * **Micro-Files:** No source file shall exceed 100 lines of code to ensure readability.
    * **Type Safety:** Strict Python type hinting (`typing`) is required.
    * **Configuration:** Reproducible workflows via YAML config profiles.

## 3. Feature Specifications

### 3.1 Core Tools: Manipulation
* **Smart Splitter:**
    * **Fixed Duration:** Chunk files into exact $n$-second segments.
    * **Silence Detection:** Intelligently slice audio based on configurable decibel thresholds and duration (e.g., remove silence or split at natural pauses).
    * **Timestamp Mode:** Split based on input JSON/CSV/TXT timestamps.
    * **Cleanup:** Auto-adjust the last segment to prevent abrupt cutoffs.
* **Format Converter:**
    * **Universal Input/Output:** Supports WAV, MP3, FLAC, OGG, AAC, M4A.
    * **Batch Processing:** Recursive directory scanning to convert entire trees.
    * **Standardization:** Optional normalization (e.g., to -14 LUFS) during conversion.
* **Metadata Manager:**
    * Read, edit, and batch-update ID3 tags.
    * Import/Export metadata templates.

### 3.2 Analysis & ML Tools: Inspection
* **Visualizer:**
    * Batch export **Mel-spectrograms** and **Waveforms** (PNG/SVG) for visual dataset inspection.
* **Audio Statistics:**
    * Calculate RMS, Peak Amplitude, and Silence Ratio.
    * **Voice Activity Detection (VAD):** Extract chunks based purely on speech presence.
    * *Planned:* Speaker energy distribution and Diarization integration.

### 3.3 Voice Tools: Enhancement
* **Noise Reduction:** Implementation of Wiener filtering or spectral subtraction for cleaning background noise.
* **Dynamics:** Dynamic Range Compression and 3-band Equalization.
* **Trimming:** Auto-trim start/end silence.

### 3.4 The "Star Magnet": Transcriber (Dataset Prep)
* **LLM Wrapper:** A unified interface for Voice Models (OpenAI Whisper, Google Gemini, etc.).
* **Dataset Generator:** Automatically generate `.srt` or `.txt` transcripts for every audio segment created by the Splitter.
* **Goal:** Turn a raw audio folder into a fully labeled NLP/ML training dataset in one command.

### 3.5 Automation & Config
* **Pipeline System:** Users can define a "chain" of operations (e.g., `Normalize -> Noise Reduce -> Split -> Transcribe`) in a YAML profile.
* **Reproducibility:** Shareable config files for consistent team workflows.

## 4. Target Audience & Use Cases
1.  **ML Engineers:** Preparing 10,000 hours of audio for Llama 3/Whisper fine-tuning.
2.  **Podcasters:** Trimming silence and normalizing levels for an entire season of episodes.
3.  **Researchers:** Segmenting large datasets by timestamps.
4.  **Musicians:** Batch converting and normalizing sample libraries.

## 5. Success Metrics
* **Performance:** Process 1 hour of audio in <1 minute (excluding transcription).
* **Usability:** "pip install" ready with zero complex setup.
* **Community:** Clear `CONTRIBUTING.md` with a plugin system that allows developers to add custom pipelines easily.