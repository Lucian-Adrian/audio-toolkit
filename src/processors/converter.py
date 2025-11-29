"""Audio format converter."""

import time
from pathlib import Path
from typing import List, Optional

from pydub import AudioSegment
from pydub.effects import normalize

from ..core.exceptions import ProcessingError, ValidationError
from ..core.interfaces import AudioProcessor
from ..core.types import ParameterSpec, ProcessorCategory, ProcessResult
from ..utils.audio import export_audio, load_audio
from ..utils.file_ops import ensure_directory
from ..utils.logger import get_logger
from ..utils.validators import validate_format, validate_input_file

logger = get_logger(__name__)


class FormatConverter(AudioProcessor):
    """
    Audio format converter with optional processing.
    
    Pure function implementation - no side effects beyond file I/O.
    """
    
    @property
    def name(self) -> str:
        return "converter"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "Convert audio between formats with optional processing"
    
    @property
    def category(self) -> ProcessorCategory:
        return ProcessorCategory.MANIPULATION
    
    @property
    def parameters(self) -> List[ParameterSpec]:
        return [
            ParameterSpec(
                name="output_format",
                type="string",
                description="Target audio format",
                required=True,
                choices=["mp3", "wav", "flac", "ogg", "aac", "m4a"],
            ),
            ParameterSpec(
                name="bitrate",
                type="string",
                description="Bitrate for lossy formats (e.g., '192k')",
                required=False,
                default="192k",
            ),
            ParameterSpec(
                name="sample_rate",
                type="integer",
                description="Output sample rate in Hz (None = preserve original)",
                required=False,
                default=None,
                choices=[8000, 16000, 22050, 44100, 48000, 96000],
            ),
            ParameterSpec(
                name="channels",
                type="integer",
                description="Number of output channels (1=mono, 2=stereo, None=preserve)",
                required=False,
                default=None,
                choices=[1, 2],
            ),
            ParameterSpec(
                name="normalize_audio",
                type="boolean",
                description="Whether to normalize audio levels",
                required=False,
                default=False,
            ),
            ParameterSpec(
                name="remove_silence",
                type="boolean",
                description="Whether to remove leading/trailing silence",
                required=False,
                default=False,
            ),
            ParameterSpec(
                name="silence_threshold",
                type="float",
                description="Silence threshold in dBFS (for remove_silence)",
                required=False,
                default=-50.0,
            ),
        ]
    
    def _remove_silence(
        self,
        audio: AudioSegment,
        threshold_dbfs: float = -50.0,
        chunk_size: int = 10,
    ) -> AudioSegment:
        """Remove leading and trailing silence from audio."""
        def detect_leading_silence(sound: AudioSegment, thresh: float) -> int:
            trim_ms = 0
            while sound[trim_ms:trim_ms + chunk_size].dBFS < thresh:
                trim_ms += chunk_size
                if trim_ms >= len(sound):
                    return len(sound)
            return trim_ms
        
        start_trim = detect_leading_silence(audio, threshold_dbfs)
        end_trim = detect_leading_silence(audio.reverse(), threshold_dbfs)
        
        duration = len(audio)
        return audio[start_trim:duration - end_trim]
    
    def process(
        self,
        input_path: Path,
        output_dir: Path,
        output_format: str,
        bitrate: str = "192k",
        sample_rate: Optional[int] = None,
        channels: Optional[int] = None,
        normalize_audio: bool = False,
        remove_silence: bool = False,
        silence_threshold: float = -50.0,
        **kwargs
    ) -> ProcessResult:
        """
        Convert audio file to target format.
        
        Args:
            input_path: Path to input audio file
            output_dir: Directory for output file
            output_format: Target audio format
            bitrate: Bitrate for lossy formats
            sample_rate: Target sample rate (None = preserve)
            channels: Target channels (None = preserve)
            normalize_audio: Whether to normalize levels
            remove_silence: Whether to remove silence
            silence_threshold: Silence threshold in dBFS
            
        Returns:
            ProcessResult with success status and output path
        """
        start_time = time.time()
        
        try:
            # Validate inputs
            validate_input_file(input_path)
            validate_format(output_format)
            
            # Ensure output directory exists
            ensure_directory(output_dir)
            
            # Load audio
            logger.info(f"Loading audio: {input_path}")
            audio = load_audio(input_path)
            original_duration = len(audio)
            original_sample_rate = audio.frame_rate
            original_channels = audio.channels
            
            # Apply sample rate conversion if requested
            if sample_rate is not None and sample_rate != audio.frame_rate:
                logger.debug(f"Resampling from {audio.frame_rate}Hz to {sample_rate}Hz")
                audio = audio.set_frame_rate(sample_rate)
            
            # Apply channel conversion if requested
            if channels is not None and channels != audio.channels:
                logger.debug(f"Converting from {audio.channels} to {channels} channels")
                audio = audio.set_channels(channels)
            
            # Apply processing
            if normalize_audio:
                logger.debug("Normalizing audio")
                audio = normalize(audio)
            
            if remove_silence:
                logger.debug(f"Removing silence (threshold: {silence_threshold}dBFS)")
                audio = self._remove_silence(audio, silence_threshold)
            
            # Generate output path
            output_path = output_dir / f"{input_path.stem}.{output_format}"
            
            # Export
            logger.info(f"Exporting to: {output_path}")
            export_audio(audio, output_path, format=output_format, bitrate=bitrate)
            
            elapsed_ms = (time.time() - start_time) * 1000
            
            logger.info(f"Conversion complete in {elapsed_ms:.0f}ms")
            
            return ProcessResult(
                success=True,
                input_path=input_path,
                output_paths=[output_path],
                metadata={
                    "input_format": input_path.suffix.lstrip("."),
                    "output_format": output_format,
                    "input_sample_rate": original_sample_rate,
                    "output_sample_rate": audio.frame_rate,
                    "input_channels": original_channels,
                    "output_channels": audio.channels,
                    "normalized": normalize_audio,
                    "silence_removed": remove_silence,
                    "input_duration_ms": original_duration,
                    "output_duration_ms": len(audio),
                    "processor": self.name,
                    "version": self.version,
                },
                processing_time_ms=elapsed_ms,
            )
            
        except (ValidationError, ProcessingError) as e:
            logger.error(f"Conversion failed: {e}")
            return ProcessResult(
                success=False,
                input_path=input_path,
                error_message=str(e),
                processing_time_ms=(time.time() - start_time) * 1000,
            )
        except Exception as e:
            logger.exception(f"Unexpected error during conversion: {e}")
            return ProcessResult(
                success=False,
                input_path=input_path,
                error_message=f"Unexpected error: {e}",
                processing_time_ms=(time.time() - start_time) * 1000,
            )
