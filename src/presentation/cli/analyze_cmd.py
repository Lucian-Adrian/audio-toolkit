"""CLI commands for audio analysis (visualizer, statistics)."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ...processors import get_processor
from ...utils.logger import get_logger

logger = get_logger(__name__)
console = Console()

app = typer.Typer(
    name="analyze",
    help="Audio analysis commands (visualize, statistics)",
    no_args_is_help=True,
)


@app.command("visualize")
def visualize_audio(
    input_file: Path = typer.Argument(
        ...,
        help="Input audio file",
        exists=True,
        dir_okay=False,
    ),
    output_dir: Path = typer.Option(
        Path("./output"),
        "--output", "-o",
        help="Output directory for visualization",
    ),
    viz_type: str = typer.Option(
        "combined",
        "--type", "-t",
        help="Visualization type: waveform, spectrogram, mel, combined",
    ),
    width: int = typer.Option(
        12,
        "--width", "-w",
        help="Figure width in inches",
    ),
    height: int = typer.Option(
        8,
        "--height", "-h",
        help="Figure height in inches",
    ),
    colormap: str = typer.Option(
        "viridis",
        "--colormap", "-c",
        help="Colormap for spectrograms",
    ),
    output_format: str = typer.Option(
        "png",
        "--format", "-f",
        help="Output image format: png, jpg, svg, pdf",
    ),
) -> None:
    """
    Generate audio visualizations (waveform, spectrogram).
    
    Examples:
        audio-toolkit analyze visualize audio.wav
        audio-toolkit analyze visualize audio.mp3 -t spectrogram
        audio-toolkit analyze visualize audio.wav -t combined -o ./viz
    """
    try:
        processor = get_processor("visualizer")
        
        console.print(f"\n[cyan]Generating visualization for:[/cyan] {input_file.name}")
        console.print(f"  Type: {viz_type}")
        console.print(f"  Output: {output_dir}")
        
        result = processor.process(
            input_path=input_file,
            output_dir=output_dir,
            visualization_type=viz_type,
            width=width,
            height=height,
            colormap=colormap,
            output_format=output_format,
        )
        
        if result.success:
            console.print(Panel(
                f"[green]✓[/green] Visualization saved to: {result.output_paths[0]}\n"
                f"Processing time: {result.processing_time_ms:.0f}ms",
                title="Visualization Complete",
                border_style="green",
            ))
        else:
            console.print(Panel(
                f"[red]✗[/red] {result.error_message}",
                title="Visualization Failed",
                border_style="red",
            ))
            raise typer.Exit(1)
            
    except Exception as e:
        logger.exception(f"Visualization error: {e}")
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command("stats")
def analyze_statistics(
    input_file: Path = typer.Argument(
        ...,
        help="Input audio file",
        exists=True,
        dir_okay=False,
    ),
    output_dir: Optional[Path] = typer.Option(
        None,
        "--output", "-o",
        help="Output directory for statistics file (optional)",
    ),
    silence_threshold: float = typer.Option(
        -40.0,
        "--silence-threshold", "-s",
        help="Silence threshold in dBFS",
    ),
    vad_threshold: float = typer.Option(
        -30.0,
        "--vad-threshold", "-v",
        help="Voice activity detection threshold in dBFS",
    ),
    output_format: str = typer.Option(
        "json",
        "--format", "-f",
        help="Output format: json or txt",
    ),
    save: bool = typer.Option(
        False,
        "--save",
        help="Save statistics to file",
    ),
) -> None:
    """
    Analyze audio and display/save statistics.
    
    Shows RMS level, peak, silence ratio, voice activity detection.
    
    Examples:
        audio-toolkit analyze stats audio.wav
        audio-toolkit analyze stats audio.mp3 --save -o ./reports
        audio-toolkit analyze stats audio.wav -f txt
    """
    try:
        processor = get_processor("statistics")
        
        console.print(f"\n[cyan]Analyzing:[/cyan] {input_file.name}")
        
        # Use temp dir if not saving
        if output_dir is None:
            output_dir = Path("./output")
        
        result = processor.process(
            input_path=input_file,
            output_dir=output_dir,
            silence_threshold=silence_threshold,
            vad_threshold=vad_threshold,
            output_format=output_format,
        )
        
        if result.success and result.metadata:
            stats = result.metadata
            
            # Display summary table
            table = Table(title="Audio Statistics", show_header=True, header_style="bold cyan")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="green")
            
            # File info
            file_info = stats.get("file", {})
            table.add_row("Duration", f"{file_info.get('duration_seconds', 0):.2f} seconds")
            table.add_row("Sample Rate", f"{file_info.get('sample_rate', 0)} Hz")
            table.add_row("Channels", str(file_info.get("channels", 0)))
            table.add_row("", "")
            
            # Levels
            levels = stats.get("levels", {})
            table.add_row("RMS Level", f"{levels.get('rms_db', 0):.1f} dBFS")
            table.add_row("Peak Level", f"{levels.get('peak_db', 0):.1f} dBFS")
            table.add_row("Dynamic Range", f"{levels.get('dynamic_range_db', 0):.1f} dB")
            table.add_row("", "")
            
            # Silence
            silence = stats.get("silence", {})
            table.add_row("Silence Ratio", f"{silence.get('percentage', 0):.1f}%")
            table.add_row("", "")
            
            # VAD
            vad = stats.get("vad", {})
            table.add_row("Voice Ratio", f"{vad.get('voice_ratio', 0) * 100:.1f}%")
            table.add_row("Voice Segments", str(vad.get("voice_segments", 0)))
            
            console.print(table)
            
            if save:
                console.print(f"\n[green]✓[/green] Statistics saved to: {result.output_paths[0]}")
            else:
                # Clean up the file if not saving
                if result.output_paths:
                    result.output_paths[0].unlink(missing_ok=True)
        else:
            console.print(Panel(
                f"[red]✗[/red] {result.error_message}",
                title="Analysis Failed",
                border_style="red",
            ))
            raise typer.Exit(1)
            
    except Exception as e:
        logger.exception(f"Analysis error: {e}")
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command("transcribe")
def transcribe_audio(
    input_file: Path = typer.Argument(
        ...,
        help="Input audio file",
        exists=True,
        dir_okay=False,
    ),
    output_dir: Path = typer.Option(
        Path("./output"),
        "--output", "-o",
        help="Output directory for transcription",
    ),
    model: str = typer.Option(
        "base",
        "--model", "-m",
        help="Whisper model: tiny, base, small, medium, large",
    ),
    language: str = typer.Option(
        "auto",
        "--language", "-l",
        help="Language code (e.g., 'en', 'es') or 'auto' for detection",
    ),
    output_format: str = typer.Option(
        "txt",
        "--format", "-f",
        help="Output format: txt, json, srt, vtt",
    ),
    translate: bool = typer.Option(
        False,
        "--translate",
        help="Translate to English",
    ),
) -> None:
    """
    Transcribe audio using OpenAI Whisper.
    
    Requires: pip install openai-whisper
    
    Examples:
        audio-toolkit analyze transcribe audio.wav
        audio-toolkit analyze transcribe audio.mp3 -m small -l en
        audio-toolkit analyze transcribe audio.wav -f srt --translate
    """
    try:
        processor = get_processor("transcriber")
        
        console.print(f"\n[cyan]Transcribing:[/cyan] {input_file.name}")
        console.print(f"  Model: {model}")
        console.print(f"  Language: {language}")
        console.print(f"  Task: {'translate' if translate else 'transcribe'}")
        
        with console.status("[cyan]Loading model and transcribing...[/cyan]"):
            result = processor.process(
                input_path=input_file,
                output_dir=output_dir,
                model=model,
                language=language,
                output_format=output_format,
                task="translate" if translate else "transcribe",
            )
        
        if result.success:
            metadata = result.metadata or {}
            
            console.print(Panel(
                f"[green]✓[/green] Transcription saved to: {result.output_paths[0]}\n"
                f"Language detected: {metadata.get('language_detected', 'unknown')}\n"
                f"Segments: {metadata.get('segment_count', 0)}\n"
                f"Processing time: {result.processing_time_ms:.0f}ms",
                title="Transcription Complete",
                border_style="green",
            ))
        else:
            console.print(Panel(
                f"[red]✗[/red] {result.error_message}",
                title="Transcription Failed",
                border_style="red",
            ))
            raise typer.Exit(1)
            
    except Exception as e:
        logger.exception(f"Transcription error: {e}")
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
