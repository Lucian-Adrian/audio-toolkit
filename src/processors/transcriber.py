"""Audio transcriber using Whisper."""

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.exceptions import ProcessingError, ValidationError
from ..core.interfaces import AudioProcessor
from ..core.types import ParameterSpec, ProcessorCategory, ProcessResult
from ..utils.file_ops import ensure_directory
from ..utils.logger import get_logger
from ..utils.validators import validate_input_file

logger = get_logger(__name__)

# Optional Whisper import
try:
    import whisper
    HAS_WHISPER = True
except ImportError:
    HAS_WHISPER = False


class AudioTranscriber(AudioProcessor):
    """
    Audio transcriber using OpenAI Whisper.
    
    Features:
    - Multiple model sizes (tiny, base, small, medium, large)
    - Language detection and forced language
    - Word-level timestamps (optional)
    - Multiple output formats (txt, json, srt, vtt)
    """
    
    # Model sizes and their approximate VRAM requirements
    MODEL_INFO = {
        "tiny": {"params": "39M", "vram": "~1GB", "speed": "~32x"},
        "base": {"params": "74M", "vram": "~1GB", "speed": "~16x"},
        "small": {"params": "244M", "vram": "~2GB", "speed": "~6x"},
        "medium": {"params": "769M", "vram": "~5GB", "speed": "~2x"},
        "large": {"params": "1550M", "vram": "~10GB", "speed": "1x"},
    }
    
    _loaded_model = None
    _loaded_model_name = None
    
    @property
    def name(self) -> str:
        return "transcriber"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "Transcribe audio using OpenAI Whisper"
    
    @property
    def category(self) -> ProcessorCategory:
        return ProcessorCategory.ANALYSIS
    
    @property
    def parameters(self) -> List[ParameterSpec]:
        return [
            ParameterSpec(
                name="model",
                type="string",
                description="Whisper model size",
                required=False,
                default="base",
                choices=["tiny", "base", "small", "medium", "large"],
            ),
            ParameterSpec(
                name="language",
                type="string",
                description="Language code (e.g., 'en', 'es', 'fr') or 'auto' for detection",
                required=False,
                default="auto",
            ),
            ParameterSpec(
                name="output_format",
                type="string",
                description="Output format for transcription",
                required=False,
                default="txt",
                choices=["txt", "json", "srt", "vtt"],
            ),
            ParameterSpec(
                name="word_timestamps",
                type="boolean",
                description="Include word-level timestamps (slower)",
                required=False,
                default=False,
            ),
            ParameterSpec(
                name="task",
                type="string",
                description="Task: 'transcribe' or 'translate' (to English)",
                required=False,
                default="transcribe",
                choices=["transcribe", "translate"],
            ),
        ]
    
    def _check_dependencies(self) -> None:
        """Check if required dependencies are available."""
        if not HAS_WHISPER:
            raise ProcessingError(
                "Missing required dependency: openai-whisper. "
                "Install with: pip install openai-whisper"
            )
    
    def _load_model(self, model_name: str) -> "whisper.Whisper":
        """Load Whisper model (cached)."""
        if self._loaded_model is not None and self._loaded_model_name == model_name:
            logger.debug(f"Using cached model: {model_name}")
            return self._loaded_model
        
        logger.info(f"Loading Whisper model: {model_name}")
        model = whisper.load_model(model_name)
        
        # Cache the model
        AudioTranscriber._loaded_model = model
        AudioTranscriber._loaded_model_name = model_name
        
        return model
    
    def _format_timestamp(self, seconds: float) -> str:
        """Format seconds as HH:MM:SS,mmm for SRT."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    def _format_vtt_timestamp(self, seconds: float) -> str:
        """Format seconds as HH:MM:SS.mmm for VTT."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"
    
    def _format_txt(self, result: Dict[str, Any]) -> str:
        """Format transcription as plain text."""
        return result["text"].strip()
    
    def _format_json(self, result: Dict[str, Any], input_path: Path) -> str:
        """Format transcription as JSON."""
        output = {
            "file": str(input_path.name),
            "language": result.get("language", "unknown"),
            "text": result["text"].strip(),
            "segments": [
                {
                    "id": seg["id"],
                    "start": seg["start"],
                    "end": seg["end"],
                    "text": seg["text"].strip(),
                }
                for seg in result.get("segments", [])
            ],
        }
        
        # Add word timestamps if available
        if "words" in result:
            output["words"] = result["words"]
        
        return json.dumps(output, indent=2, ensure_ascii=False)
    
    def _format_srt(self, result: Dict[str, Any]) -> str:
        """Format transcription as SRT subtitles."""
        lines = []
        for i, seg in enumerate(result.get("segments", []), 1):
            start = self._format_timestamp(seg["start"])
            end = self._format_timestamp(seg["end"])
            text = seg["text"].strip()
            lines.append(f"{i}")
            lines.append(f"{start} --> {end}")
            lines.append(text)
            lines.append("")
        return "\n".join(lines)
    
    def _format_vtt(self, result: Dict[str, Any]) -> str:
        """Format transcription as WebVTT subtitles."""
        lines = ["WEBVTT", ""]
        for seg in result.get("segments", []):
            start = self._format_vtt_timestamp(seg["start"])
            end = self._format_vtt_timestamp(seg["end"])
            text = seg["text"].strip()
            lines.append(f"{start} --> {end}")
            lines.append(text)
            lines.append("")
        return "\n".join(lines)
    
    def process(
        self,
        input_path: Path,
        output_dir: Path,
        model: str = "base",
        language: str = "auto",
        output_format: str = "txt",
        word_timestamps: bool = False,
        task: str = "transcribe",
        **kwargs
    ) -> ProcessResult:
        """
        Transcribe audio file using Whisper.
        
        Args:
            input_path: Path to input audio file
            output_dir: Directory for output file
            model: Whisper model size
            language: Language code or 'auto'
            output_format: Output format (txt, json, srt, vtt)
            word_timestamps: Include word-level timestamps
            task: 'transcribe' or 'translate'
            
        Returns:
            ProcessResult with success status and output path
        """
        start_time = time.time()
        
        try:
            # Check dependencies
            self._check_dependencies()
            
            # Validate inputs
            validate_input_file(input_path)
            ensure_directory(output_dir)
            
            # Load model
            whisper_model = self._load_model(model)
            
            logger.info(
                f"Transcribing: {input_path.name} "
                f"(model={model}, language={language}, task={task})"
            )
            
            # Prepare options
            options = {
                "task": task,
                "word_timestamps": word_timestamps,
            }
            
            if language != "auto":
                options["language"] = language
            
            # Transcribe
            result = whisper_model.transcribe(str(input_path), **options)
            
            # Format output
            if output_format == "txt":
                output_content = self._format_txt(result)
            elif output_format == "json":
                output_content = self._format_json(result, input_path)
            elif output_format == "srt":
                output_content = self._format_srt(result)
            elif output_format == "vtt":
                output_content = self._format_vtt(result)
            else:
                output_content = self._format_txt(result)
            
            # Write output
            output_path = output_dir / f"{input_path.stem}.{output_format}"
            output_path.write_text(output_content, encoding="utf-8")
            
            logger.info(f"Transcription saved to: {output_path}")
            
            elapsed_ms = (time.time() - start_time) * 1000
            
            # Build metadata
            metadata = {
                "model": model,
                "model_info": self.MODEL_INFO.get(model, {}),
                "language_detected": result.get("language", "unknown"),
                "language_requested": language,
                "task": task,
                "word_timestamps": word_timestamps,
                "output_format": output_format,
                "text_length": len(result["text"]),
                "segment_count": len(result.get("segments", [])),
            }
            
            return ProcessResult(
                success=True,
                input_path=input_path,
                output_paths=[output_path],
                metadata=metadata,
                processing_time_ms=elapsed_ms,
            )
            
        except (ValidationError, ProcessingError) as e:
            logger.error(f"Transcription failed: {e}")
            return ProcessResult(
                success=False,
                input_path=input_path,
                error_message=str(e),
                processing_time_ms=(time.time() - start_time) * 1000,
            )
        except Exception as e:
            logger.exception(f"Unexpected error during transcription: {e}")
            return ProcessResult(
                success=False,
                input_path=input_path,
                error_message=f"Unexpected error: {e}",
                processing_time_ms=(time.time() - start_time) * 1000,
            )
