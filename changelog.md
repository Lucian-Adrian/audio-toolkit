# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project structure
- Basic documentation
- **Phase 4: Pipeline Engine** (PIPE-001 to PIPE-004)
  - `src/orchestration/pipeline_config.py` - Pydantic models for pipeline configuration (PipelineStep, PipelineInput, PipelineSettings, PipelineConfig)
  - `src/orchestration/pipeline.py` - PipelineEngine with validate, dry_run, and execute methods
  - `src/presentation/cli/pipeline_cmd.py` - CLI commands for pipeline operations (run, validate, processors)
  - Unit tests for pipeline configuration parsing (22 tests)
  - Unit tests for pipeline engine (14 tests)
  - Integration tests for full pipeline execution (7 tests)
- YAML-based pipeline definitions supporting multi-step workflows
- Pipeline validation before execution (checks processor existence and required params)
- Dry-run mode showing execution plan without processing
- Step chaining - each step's output becomes next step's input
- Error handling with `continue_on_error` option
- Checkpointing support during pipeline execution

### Changed

### Deprecated

### Removed

### Fixed

### Security
