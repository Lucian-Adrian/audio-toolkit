# Requirements Document (EARS Notation)

> **EARS** = Easy Approach to Requirements Syntax
> Format: `When [trigger], the [system] shall [response].`

---

## 1. Ubiquitous Requirements (Always Apply)

### 1.1 Architectural Constraints (Min-Max Philosophy)
| ID | Requirement |
|----|-------------|
| U-001 | The system shall limit all source files to a maximum of 100 lines of code. |
| U-002 | The system shall enforce strict Python type hints on all function signatures. |
| U-003 | The system shall implement each feature as an isolated processor/plugin. |
| U-004 | The system shall provide both CLI (Typer) and Python API access for all features. |
| U-005 | The system shall process batch operations without requiring code modifications. |
| U-006 | The system shall store all runtime output in `data/output/` and logs in `data/logs/`. |

### 1.2 Performance Requirements
| ID | Requirement |
|----|-------------|
| U-007 | The system shall process 1 hour of audio in less than 1 minute (excluding transcription). |
| U-008 | The system shall support processing 1 to 10,000+ files in a single command. |

---

## 2. Core Module Requirements

### 2.1 Smart Splitter

#### Event-Driven Requirements
| ID | Trigger | Response |
|----|---------|----------|
| SPLIT-001 | When the user specifies `--mode fixed --duration N`, the Splitter shall chunk audio into exact N-second segments. |
| SPLIT-002 | When the user specifies `--mode silence`, the Splitter shall detect silence based on configurable decibel threshold and minimum duration. |
| SPLIT-003 | When the user specifies `--mode timestamp --file <path>`, the Splitter shall split audio at timestamps provided in JSON, CSV, or TXT format. |
| SPLIT-004 | When the last segment is shorter than the specified duration, the Splitter shall apply cleanup logic to prevent abrupt cutoffs. |
| SPLIT-005 | When processing a directory, the Splitter shall recursively scan and process all supported audio files. |
| SPLIT-006 | When silence is detected, the Splitter shall optionally remove silent segments or use them as split points. |

#### Acceptance Criteria: Smart Splitter
| Criterion | Description |
|-----------|-------------|
| AC-SPLIT-1 | Given a 10-minute audio file and `--duration 60`, the system produces exactly 10 segments of 60 seconds each. |
| AC-SPLIT-2 | Given a 10-minute audio file and `--duration 180`, the system produces 3 segments of 180s and 1 segment of 60s (with cleanup applied). |
| AC-SPLIT-3 | Given `--mode silence --threshold -40dB --min-duration 0.5s`, the system correctly identifies pauses ≥0.5s at ≤-40dB. |
| AC-SPLIT-4 | Given a CSV with timestamps `[0:00, 2:30, 5:00]`, the system produces 3 segments: 0:00-2:30, 2:30-5:00, 5:00-end. |
| AC-SPLIT-5 | Output filenames follow pattern: `{original_name}_segment_{NNN}.{ext}` |

#### Edge Cases: Smart Splitter
| ID | Scenario | Expected Behavior |
|----|----------|-------------------|
| EC-SPLIT-1 | Audio file shorter than specified duration | Output single segment with original length, log warning. |
| EC-SPLIT-2 | Timestamp file contains out-of-bounds values | Skip invalid timestamps, log error, continue processing valid ones. |
| EC-SPLIT-3 | Audio file is entirely silence | Output empty result set, log warning "No speech detected". |
| EC-SPLIT-4 | Corrupted audio file in batch | Skip file, log error with filename, continue batch processing. |
| EC-SPLIT-5 | Zero-byte audio file | Skip file, log error "Empty file: {filename}". |

### 2.2 Format Converter

#### Event-Driven Requirements
| ID | Trigger | Response |
|----|---------|----------|
| CONV-001 | When the user specifies `--format <target>`, the Converter shall transform audio to the target format (WAV, MP3, FLAC, OGG, AAC, M4A). |
| CONV-002 | When the user specifies `--normalize`, the Converter shall normalize audio to -14 LUFS during conversion. |
| CONV-003 | When processing a directory with `--recursive`, the Converter shall scan and convert all supported files in subdirectories. |
| CONV-004 | When the source format matches the target format, the Converter shall skip the file and log "Already in target format". |

### 2.3 Metadata Manager

#### Event-Driven Requirements
| ID | Trigger | Response |
|----|---------|----------|
| META-001 | When the user specifies `--read`, the Metadata Manager shall display all ID3 tags for the specified file(s). |
| META-002 | When the user specifies `--edit --tag <key>=<value>`, the Metadata Manager shall update the specified tag. |
| META-003 | When the user specifies `--template <file>`, the Metadata Manager shall batch-apply metadata from a JSON/YAML template. |
| META-004 | When the user specifies `--export`, the Metadata Manager shall output all tags to a JSON file. |

---

## 3. Analysis Module Requirements

### 3.1 Visualizer

#### Event-Driven Requirements
| ID | Trigger | Response |
|----|---------|----------|
| VIS-001 | When the user specifies `--type mel`, the Visualizer shall generate Mel-spectrogram images (PNG/SVG). |
| VIS-002 | When the user specifies `--type waveform`, the Visualizer shall generate waveform images (PNG/SVG). |
| VIS-003 | When processing batch files, the Visualizer shall output images with filenames matching source audio. |

### 3.2 Audio Statistics

#### Event-Driven Requirements
| ID | Trigger | Response |
|----|---------|----------|
| STAT-001 | When the user specifies `--stats`, the system shall calculate and display RMS, Peak Amplitude, and Silence Ratio. |
| STAT-002 | When the user specifies `--vad`, the system shall extract audio chunks containing only speech (Voice Activity Detection). |
| STAT-003 | When the user specifies `--output json`, the system shall export statistics to a structured JSON file. |

---

## 4. Voice Module Requirements

### 4.1 Noise Reduction

#### Event-Driven Requirements
| ID | Trigger | Response |
|----|---------|----------|
| NOISE-001 | When the user specifies `--denoise`, the system shall apply Wiener filtering or spectral subtraction to reduce background noise. |
| NOISE-002 | When the user specifies `--denoise-strength <level>`, the system shall adjust noise reduction intensity (low/medium/high). |

### 4.2 Dynamics Processing

#### Event-Driven Requirements
| ID | Trigger | Response |
|----|---------|----------|
| DYN-001 | When the user specifies `--compress`, the system shall apply Dynamic Range Compression with configurable ratio. |
| DYN-002 | When the user specifies `--eq <preset>`, the system shall apply 3-band equalization based on preset (voice/music/podcast). |

### 4.3 Trimming

#### Event-Driven Requirements
| ID | Trigger | Response |
|----|---------|----------|
| TRIM-001 | When the user specifies `--trim`, the system shall auto-detect and remove silence from start and end of audio. |
| TRIM-002 | When the user specifies `--trim-threshold <dB>`, the system shall use the specified decibel level for silence detection. |

---

## 5. Automation Module Requirements

### 5.1 Pipeline System

#### Event-Driven Requirements
| ID | Trigger | Response |
|----|---------|----------|
| PIPE-001 | When the user specifies `--pipeline <config.yaml>`, the system shall execute operations in the defined sequence. |
| PIPE-002 | When a pipeline step fails, the system shall halt execution and log the failure point with details. |
| PIPE-003 | When the user specifies `--pipeline --dry-run`, the system shall validate the config and display planned operations without executing. |
| PIPE-004 | When the user specifies `--pipeline --resume`, the system shall continue from the last successful step. |

#### Acceptance Criteria: Pipeline System
| Criterion | Description |
|-----------|-------------|
| AC-PIPE-1 | Given a YAML config with `[normalize, denoise, split, transcribe]`, the system executes steps in exact order. |
| AC-PIPE-2 | Given `--dry-run`, the system outputs "Step 1: normalize, Step 2: denoise..." without modifying files. |
| AC-PIPE-3 | Given a pipeline failure at step 3, the system logs "Pipeline halted at step 3: {error}" and preserves steps 1-2 output. |
| AC-PIPE-4 | Given `--resume` after failure, the system reads checkpoint and continues from step 3. |
| AC-PIPE-5 | Pipeline config files are shareable and produce identical results across environments. |

#### Edge Cases: Pipeline System
| ID | Scenario | Expected Behavior |
|----|----------|-------------------|
| EC-PIPE-1 | Invalid YAML syntax in config | Fail fast with "Invalid config: {parse_error}" before any processing. |
| EC-PIPE-2 | Unknown processor name in pipeline | Fail with "Unknown processor: {name}. Available: [list]". |
| EC-PIPE-3 | Circular dependency in config | Detect and reject with "Circular dependency detected in pipeline". |
| EC-PIPE-4 | Missing required parameter for a step | Fail with "Missing required parameter '{param}' for step '{step}'". |
| EC-PIPE-5 | Input directory empty | Log warning "No files to process", exit gracefully with code 0. |

### 5.2 Transcriber (Dataset Prep)

#### Event-Driven Requirements
| ID | Trigger | Response |
|----|---------|----------|
| TRANS-001 | When the user specifies `--transcribe --model whisper`, the system shall generate transcripts using OpenAI Whisper. |
| TRANS-002 | When the user specifies `--transcribe --model gemini`, the system shall generate transcripts using Google Gemini. |
| TRANS-003 | When the user specifies `--output-format srt`, the system shall generate `.srt` subtitle files. |
| TRANS-004 | When the user specifies `--output-format txt`, the system shall generate plain text transcripts. |
| TRANS-005 | When transcription completes for a split segment, the system shall name the transcript to match the segment filename. |

---

## 6. Unwanted Behaviors (Shall NOT)

| ID | Condition | Prohibited Behavior |
|----|-----------|---------------------|
| NOT-001 | If a file is read-only | The system shall NOT attempt to modify it; log error instead. |
| NOT-002 | If processing fails | The system shall NOT delete or corrupt source files. |
| NOT-003 | If credentials are missing for transcription | The system shall NOT send data to external APIs; fail with clear auth error. |
| NOT-004 | If output directory is not writable | The system shall NOT silently fail; raise explicit permission error. |
| NOT-005 | If batch processing | The system shall NOT stop entirely on single-file failure; log and continue. |

---

## 7. Optional Features (WHERE included)

| ID | Feature Condition | Behavior |
|----|-------------------|----------|
| OPT-001 | Where `--verbose` is specified | The system shall output detailed progress logs for each operation. |
| OPT-002 | Where `--quiet` is specified | The system shall suppress all output except errors. |
| OPT-003 | Where `--config <file>` is specified | The system shall load default parameters from the specified config file. |
| OPT-004 | Where plugin system is enabled | The system shall allow third-party processors to register via entry points. |

---

## 8. Traceability Matrix

| Feature | Requirements | Acceptance Criteria | Edge Cases |
|---------|--------------|---------------------|------------|
| Smart Splitter | SPLIT-001 to SPLIT-006 | AC-SPLIT-1 to AC-SPLIT-5 | EC-SPLIT-1 to EC-SPLIT-5 |
| Format Converter | CONV-001 to CONV-004 | — | — |
| Metadata Manager | META-001 to META-004 | — | — |
| Visualizer | VIS-001 to VIS-003 | — | — |
| Audio Statistics | STAT-001 to STAT-003 | — | — |
| Noise Reduction | NOISE-001 to NOISE-002 | — | — |
| Dynamics | DYN-001 to DYN-002 | — | — |
| Trimming | TRIM-001 to TRIM-002 | — | — |
| Pipeline System | PIPE-001 to PIPE-004 | AC-PIPE-1 to AC-PIPE-5 | EC-PIPE-1 to EC-PIPE-5 |
| Transcriber | TRANS-001 to TRANS-005 | — | — |
