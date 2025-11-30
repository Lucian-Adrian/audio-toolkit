"""CLI commands for voice enhancement (noise reduction, dynamics, trimming)."""

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
    name="voice",
    help="Voice enhancement commands (denoise, dynamics, trim)",
    no_args_is_help=True,
)


@app.command("denoise")
def denoise_audio(
    input_file: Path = typer.Argument(
        ...,
        help="Input audio file",
        exists=True,
        dir_okay=False,
    ),
    output_dir: Path = typer.Option(
        Path("./output"),
        "--output", "-o",
        help="Output directory",
    ),
    reduction: float = typer.Option(
        12.0,
        "--reduction", "-r",
        help="Noise reduction amount in dB (0-40)",
    ),
    noise_floor_ms: int = typer.Option(
        500,
        "--noise-floor", "-n",
        help="Duration of noise estimation from start (ms)",
    ),
    smoothing: float = typer.Option(
        0.5,
        "--smoothing", "-s",
        help="Smoothing factor (0.0-1.0)",
    ),
    output_format: str = typer.Option(
        "wav",
        "--format", "-f",
        help="Output format: wav, mp3, ogg, flac",
    ),
) -> None:
    """
    Reduce background noise using spectral subtraction.
    
    This processor estimates noise from the first part of the audio
    and subtracts it from the entire signal.
    
    Examples:
        audio-toolkit voice denoise noisy.wav
        audio-toolkit voice denoise audio.mp3 -r 20 -o ./clean
        audio-toolkit voice denoise recording.wav -n 1000 -f mp3
    """
    try:
        processor = get_processor("noise_reduce")
        
        console.print(f"\n[cyan]Denoising:[/cyan] {input_file.name}")
        console.print(f"  Reduction: {reduction} dB")
        console.print(f"  Noise floor: {noise_floor_ms} ms")
        
        with console.status("[cyan]Processing...[/cyan]"):
            result = processor.process(
                input_path=input_file,
                output_dir=output_dir,
                noise_reduce_db=reduction,
                noise_floor_ms=noise_floor_ms,
                smoothing_factor=smoothing,
                output_format=output_format,
            )
        
        if result.success:
            console.print(Panel(
                f"[green]✓[/green] Denoised audio saved to: {result.output_paths[0]}\n"
                f"Processing time: {result.processing_time_ms:.0f}ms",
                title="Noise Reduction Complete",
                border_style="green",
            ))
        else:
            console.print(Panel(
                f"[red]✗[/red] {result.error_message}",
                title="Noise Reduction Failed",
                border_style="red",
            ))
            raise typer.Exit(1)
            
    except Exception as e:
        logger.exception(f"Denoise error: {e}")
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command("dynamics")
def process_dynamics(
    input_file: Path = typer.Argument(
        ...,
        help="Input audio file",
        exists=True,
        dir_okay=False,
    ),
    output_dir: Path = typer.Option(
        Path("./output"),
        "--output", "-o",
        help="Output directory",
    ),
    # Compressor options
    threshold: float = typer.Option(
        -20.0,
        "--threshold", "-t",
        help="Compressor threshold in dBFS",
    ),
    ratio: float = typer.Option(
        4.0,
        "--ratio", "-r",
        help="Compression ratio (e.g., 4.0 = 4:1)",
    ),
    attack: float = typer.Option(
        10.0,
        "--attack", "-a",
        help="Attack time in ms",
    ),
    release: float = typer.Option(
        100.0,
        "--release",
        help="Release time in ms",
    ),
    # EQ options
    eq_low: float = typer.Option(
        0.0,
        "--eq-low", "-l",
        help="Low frequency gain in dB (<200Hz)",
    ),
    eq_mid: float = typer.Option(
        0.0,
        "--eq-mid", "-m",
        help="Mid frequency gain in dB (200Hz-4kHz)",
    ),
    eq_high: float = typer.Option(
        0.0,
        "--eq-high", "-h",
        help="High frequency gain in dB (>4kHz)",
    ),
    # Output options
    gain: float = typer.Option(
        0.0,
        "--gain", "-g",
        help="Output gain in dB",
    ),
    output_format: str = typer.Option(
        "wav",
        "--format", "-f",
        help="Output format: wav, mp3, ogg, flac",
    ),
) -> None:
    """
    Apply dynamics processing (compression and 3-band EQ).
    
    The compressor reduces dynamic range, making loud parts quieter
    and allowing you to boost overall volume.
    
    The 3-band EQ adjusts low (<200Hz), mid (200Hz-4kHz), and high (>4kHz) frequencies.
    
    Examples:
        audio-toolkit voice dynamics audio.wav
        audio-toolkit voice dynamics voice.mp3 -t -15 -r 6
        audio-toolkit voice dynamics podcast.wav -l -3 -m 2 -h 1 -g 3
    """
    try:
        processor = get_processor("dynamics")
        
        console.print(f"\n[cyan]Processing dynamics:[/cyan] {input_file.name}")
        console.print(f"  Compressor: {threshold}dB threshold, {ratio}:1 ratio")
        console.print(f"  EQ: Low={eq_low}dB, Mid={eq_mid}dB, High={eq_high}dB")
        console.print(f"  Output gain: {gain}dB")
        
        with console.status("[cyan]Processing...[/cyan]"):
            result = processor.process(
                input_path=input_file,
                output_dir=output_dir,
                compressor_threshold=threshold,
                compressor_ratio=ratio,
                compressor_attack_ms=attack,
                compressor_release_ms=release,
                eq_low_gain=eq_low,
                eq_mid_gain=eq_mid,
                eq_high_gain=eq_high,
                output_gain=gain,
                output_format=output_format,
            )
        
        if result.success:
            console.print(Panel(
                f"[green]✓[/green] Processed audio saved to: {result.output_paths[0]}\n"
                f"Processing time: {result.processing_time_ms:.0f}ms",
                title="Dynamics Processing Complete",
                border_style="green",
            ))
        else:
            console.print(Panel(
                f"[red]✗[/red] {result.error_message}",
                title="Dynamics Processing Failed",
                border_style="red",
            ))
            raise typer.Exit(1)
            
    except Exception as e:
        logger.exception(f"Dynamics processing error: {e}")
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command("trim")
def trim_silence(
    input_file: Path = typer.Argument(
        ...,
        help="Input audio file",
        exists=True,
        dir_okay=False,
    ),
    output_dir: Path = typer.Option(
        Path("./output"),
        "--output", "-o",
        help="Output directory",
    ),
    mode: str = typer.Option(
        "edges",
        "--mode", "-m",
        help="Trim mode: 'edges' (start/end only) or 'all' (remove all silence)",
    ),
    threshold: float = typer.Option(
        -40.0,
        "--threshold", "-t",
        help="Silence threshold in dBFS",
    ),
    min_silence: int = typer.Option(
        500,
        "--min-silence", "-s",
        help="Minimum silence duration to detect (ms)",
    ),
    padding: int = typer.Option(
        50,
        "--padding", "-p",
        help="Padding to keep at edges after trimming (ms)",
    ),
    max_silence: int = typer.Option(
        300,
        "--max-silence",
        help="Maximum silence to keep in 'all' mode (ms)",
    ),
    output_format: str = typer.Option(
        "wav",
        "--format", "-f",
        help="Output format: wav, mp3, ogg, flac",
    ),
) -> None:
    """
    Automatically trim silence from audio files.
    
    Modes:
    - edges: Remove silence from start and end only
    - all: Remove or reduce all internal silences too
    
    Examples:
        audio-toolkit voice trim audio.wav
        audio-toolkit voice trim recording.mp3 -m all
        audio-toolkit voice trim podcast.wav -t -35 -p 100
    """
    try:
        processor = get_processor("trimmer")
        
        console.print(f"\n[cyan]Trimming silence:[/cyan] {input_file.name}")
        console.print(f"  Mode: {mode}")
        console.print(f"  Threshold: {threshold} dBFS")
        console.print(f"  Min silence: {min_silence} ms")
        
        with console.status("[cyan]Processing...[/cyan]"):
            result = processor.process(
                input_path=input_file,
                output_dir=output_dir,
                mode=mode,
                silence_threshold=threshold,
                min_silence_ms=min_silence,
                padding_ms=padding,
                max_silence_ms=max_silence,
                output_format=output_format,
            )
        
        if result.success:
            metadata = result.metadata or {}
            original = metadata.get("original_duration_ms", 0)
            processed = metadata.get("processed_duration_ms", 0)
            reduction = metadata.get("reduction_percent", 0)
            
            console.print(Panel(
                f"[green]✓[/green] Trimmed audio saved to: {result.output_paths[0]}\n"
                f"Original duration: {original / 1000:.2f}s\n"
                f"Trimmed duration: {processed / 1000:.2f}s\n"
                f"Reduction: {reduction:.1f}%\n"
                f"Processing time: {result.processing_time_ms:.0f}ms",
                title="Trim Complete",
                border_style="green",
            ))
        else:
            console.print(Panel(
                f"[red]✗[/red] {result.error_message}",
                title="Trim Failed",
                border_style="red",
            ))
            raise typer.Exit(1)
            
    except Exception as e:
        logger.exception(f"Trim error: {e}")
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command("enhance")
def enhance_voice(
    input_file: Path = typer.Argument(
        ...,
        help="Input audio file",
        exists=True,
        dir_okay=False,
    ),
    output_dir: Path = typer.Option(
        Path("./output"),
        "--output", "-o",
        help="Output directory",
    ),
    preset: str = typer.Option(
        "podcast",
        "--preset", "-p",
        help="Enhancement preset: podcast, voice, music",
    ),
    output_format: str = typer.Option(
        "wav",
        "--format", "-f",
        help="Output format: wav, mp3, ogg, flac",
    ),
) -> None:
    """
    Apply a complete voice enhancement chain.
    
    This combines noise reduction, dynamics, and trimming with
    optimized presets for different use cases.
    
    Presets:
    - podcast: Optimized for spoken word podcasts
    - voice: General voice enhancement
    - music: Light processing for music
    
    Examples:
        audio-toolkit voice enhance recording.wav
        audio-toolkit voice enhance voice.mp3 -p voice
        audio-toolkit voice enhance song.wav -p music -f mp3
    """
    try:
        # Define presets
        presets = {
            "podcast": {
                "denoise": {"noise_reduce_db": 15.0, "noise_floor_ms": 500},
                "dynamics": {
                    "compressor_threshold": -18.0,
                    "compressor_ratio": 4.0,
                    "eq_low_gain": -2.0,
                    "eq_mid_gain": 1.0,
                    "eq_high_gain": 0.5,
                    "output_gain": 3.0,
                },
                "trim": {"mode": "edges", "silence_threshold": -40.0},
            },
            "voice": {
                "denoise": {"noise_reduce_db": 12.0, "noise_floor_ms": 500},
                "dynamics": {
                    "compressor_threshold": -20.0,
                    "compressor_ratio": 3.0,
                    "eq_low_gain": 0.0,
                    "eq_mid_gain": 0.0,
                    "eq_high_gain": 0.0,
                    "output_gain": 0.0,
                },
                "trim": {"mode": "edges", "silence_threshold": -45.0},
            },
            "music": {
                "denoise": {"noise_reduce_db": 6.0, "noise_floor_ms": 300},
                "dynamics": {
                    "compressor_threshold": -25.0,
                    "compressor_ratio": 2.0,
                    "eq_low_gain": 0.0,
                    "eq_mid_gain": 0.0,
                    "eq_high_gain": 0.0,
                    "output_gain": 0.0,
                },
                "trim": {"mode": "edges", "silence_threshold": -50.0},
            },
        }
        
        if preset not in presets:
            console.print(f"[red]Unknown preset:[/red] {preset}")
            console.print(f"Available: {', '.join(presets.keys())}")
            raise typer.Exit(1)
        
        settings = presets[preset]
        
        console.print(f"\n[cyan]Enhancing voice:[/cyan] {input_file.name}")
        console.print(f"  Preset: {preset}")
        console.print(f"  Steps: denoise → dynamics → trim")
        
        # Step 1: Denoise
        console.print("\n[yellow]Step 1/3:[/yellow] Noise reduction...")
        noise_processor = get_processor("noise_reduce")
        result = noise_processor.process(
            input_path=input_file,
            output_dir=output_dir,
            output_format="wav",  # Intermediate format
            **settings["denoise"],
        )
        
        if not result.success:
            console.print(f"[red]Noise reduction failed:[/red] {result.error_message}")
            raise typer.Exit(1)
        
        intermediate_1 = result.output_paths[0]
        
        # Step 2: Dynamics
        console.print("[yellow]Step 2/3:[/yellow] Dynamics processing...")
        dynamics_processor = get_processor("dynamics")
        result = dynamics_processor.process(
            input_path=intermediate_1,
            output_dir=output_dir,
            output_format="wav",
            **settings["dynamics"],
        )
        
        if not result.success:
            intermediate_1.unlink(missing_ok=True)
            console.print(f"[red]Dynamics processing failed:[/red] {result.error_message}")
            raise typer.Exit(1)
        
        intermediate_2 = result.output_paths[0]
        intermediate_1.unlink(missing_ok=True)  # Clean up
        
        # Step 3: Trim
        console.print("[yellow]Step 3/3:[/yellow] Trimming silence...")
        trim_processor = get_processor("trimmer")
        result = trim_processor.process(
            input_path=intermediate_2,
            output_dir=output_dir,
            output_format=output_format,
            **settings["trim"],
        )
        
        intermediate_2.unlink(missing_ok=True)  # Clean up
        
        if result.success:
            # Rename to final name
            final_path = output_dir / f"{input_file.stem}_enhanced.{output_format}"
            if result.output_paths[0] != final_path:
                result.output_paths[0].rename(final_path)
            
            console.print(Panel(
                f"[green]✓[/green] Enhanced audio saved to: {final_path}\n"
                f"Preset: {preset}\n"
                f"Total processing time: {result.processing_time_ms:.0f}ms",
                title="Voice Enhancement Complete",
                border_style="green",
            ))
        else:
            console.print(Panel(
                f"[red]✗[/red] {result.error_message}",
                title="Enhancement Failed",
                border_style="red",
            ))
            raise typer.Exit(1)
            
    except typer.Exit:
        raise
    except Exception as e:
        logger.exception(f"Enhancement error: {e}")
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
