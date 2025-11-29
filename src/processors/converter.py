"""Audio converter implementation."""

from pathlib import Path
import pydub
from ...core.types import AudioFile, ProcessingConfig, ConversionResult
from ...core.interfaces import AudioProcessor
from ...core.exceptions import AudioProcessingError
from ...utils.logger import logger


class AudioConverter(AudioProcessor):
    """Audio format converter using pydub."""

    def process(self, audio_file: AudioFile, config: ProcessingConfig) -> ConversionResult:
        """Convert audio file to specified format."""
        try:
            # Load audio
            audio = pydub.AudioSegment.from_file(str(audio_file.path))

            # Apply processing options
            if config.normalize:
                audio = audio.normalize()

            if config.remove_silence:
                audio = self._remove_silence(audio)

            # Generate output path
            output_path = self._get_output_path(audio_file.path, config.output_format)

            # Export with specified quality
            export_params = {}
            if config.output_format.lower() == 'mp3':
                export_params['bitrate'] = f"{config.quality}k"
            elif config.output_format.lower() in ['wav', 'flac']:
                # For lossless formats, quality doesn't apply
                pass

            audio.export(str(output_path), format=config.output_format, **export_params)

            # Create output AudioFile
            output_audio = AudioFile(
                path=output_path,
                format=config.output_format,
                duration=len(audio) / 1000.0,
                sample_rate=audio.frame_rate,
                channels=audio.channels,
                bitrate=config.quality if config.output_format == 'mp3' else None
            )

            logger.info(f"Converted {audio_file.path} to {output_path}")

            return ConversionResult(
                input_file=audio_file,
                output_file=output_audio,
                success=True,
                processing_time=0.0  # TODO: measure time
            )

        except Exception as e:
            logger.error(f"Failed to convert {audio_file.path}: {e}")
            return ConversionResult(
                input_file=audio_file,
                output_file=audio_file,  # dummy
                success=False,
                error_message=str(e),
                processing_time=0.0
            )

    def _remove_silence(self, audio: pydub.AudioSegment, threshold: int = -50) -> pydub.AudioSegment:
        """Remove silence from audio."""
        return pydub.effects.strip_silence(audio, threshold=threshold)

    def _get_output_path(self, input_path: Path, output_format: str) -> Path:
        """Generate output path for converted file."""
        stem = input_path.stem
        return input_path.parent / f"{stem}_converted.{output_format}"
