# CLI Module Specifications

## Overview
The CLI module provides command-line interface for the audio toolkit using Click.

## Main CLI

### cli
Main CLI group with global options.

**Options:**
- `--log-level` - Set logging level (INFO, DEBUG, WARNING, ERROR)
- `--log-file` - Optional log file path

**Commands:**
- `convert` - Convert audio files
- `split` - Split audio files

## Convert Command

### convert
Convert audio files to different formats.

**Arguments:**
- `input_file` - Path to input audio file

**Options:**
- `--output-dir, -o` - Output directory (default: same as input)
- `--format, -f` - Output format (default: mp3)
- `--quality, -q` - Quality/bitrate (default: 128)
- `--normalize` - Normalize audio levels
- `--remove-silence` - Remove silent sections
- `--quiet` - Suppress progress output

**Example:**
```bash
audio-toolkit convert input.wav --format mp3 --quality 192 --normalize
```

## Split Command

### split
Split audio files into segments.

**Arguments:**
- `input_file` - Path to input audio file

**Options:**
- `--output-dir, -o` - Output directory (default: same as input)
- `--method, -m` - Split method (default: fixed)
- `--duration, -d` - Duration per segment (seconds)
- `--prefix, -p` - Output file prefix (default: segment)
- `--quiet` - Suppress progress output

**Example:**
```bash
audio-toolkit split input.mp3 --duration 30 --prefix chapter
```

## Error Handling
- Invalid files: Display validation errors
- Processing failures: Display error messages
- Keyboard interrupt: Graceful exit

## Progress Reporting
- Console progress bar for long operations
- Can be suppressed with --quiet flag
- Shows operation status and completion