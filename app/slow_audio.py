"""Audio time-stretch processor with practical fallback strategies."""

from __future__ import annotations

from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class SlowAudioProcessor:
    """Slow audio by a large factor, with graceful quality tradeoffs."""

    def slow_file(self, input_path: str, output_path: str, factor: float = 100.0) -> str:
        src = Path(input_path)
        dst = Path(output_path)
        if not src.exists():
            raise FileNotFoundError(f"Source audio not found: {src}")

        # Attempt high-quality path first.
        try:
            import librosa
            import soundfile as sf

            y, sr = librosa.load(str(src), sr=None, mono=True)
            stretched = librosa.effects.time_stretch(y, rate=max(0.01, 1.0 / factor))
            sf.write(str(dst), stretched, sr)
            return str(dst)
        except Exception as exc:
            logger.warning("librosa stretch unavailable (%s), using frame-rate fallback.", exc)

        # Simple fallback: changes pitch but works reliably with ffmpeg backend.
        from pydub import AudioSegment

        seg = AudioSegment.from_file(str(src))
        lower_rate = int(seg.frame_rate / factor)
        altered = seg._spawn(seg.raw_data, overrides={"frame_rate": max(100, lower_rate)})
        stretched = altered.set_frame_rate(seg.frame_rate)
        stretched.export(str(dst), format=dst.suffix.replace(".", "") or "wav")
        return str(dst)
