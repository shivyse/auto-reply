"""
TubePulse US - Procedural Audio Bed & Sound Design Engine
Generates royalty-free polyphonic music tracks and cinematic sound effects in pure Python & FFmpeg.
Provides audio mixing with automated ducking for US YouTube content.
"""

import os
import math
import wave
import struct
import subprocess

AUDIO_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "media", "audio")
os.makedirs(AUDIO_DIR, exist_ok=True)

US_VOICES = [
    {
        "id": "caleb_us",
        "name": "Caleb - US Tech & Documentary (Male)",
        "accent": "General American (US)",
        "tone": "Authoritative, Crisp, Modern",
        "best_for": "Tech, AI, Silicon Valley & Megaprojects",
        "rate": 1.05,
        "pitch": 0.95
    },
    {
        "id": "marcus_us",
        "name": "Marcus - US Deep Narrator (Male)",
        "accent": "General American (Deep US)",
        "tone": "Mysterious, Cinematic, Deep Voice",
        "best_for": "True Crime, FBI Files, Unsolved Mysteries",
        "rate": 0.96,
        "pitch": 0.88
    },
    {
        "id": "sarah_us",
        "name": "Sarah - US High-Energy Analyst (Female)",
        "accent": "Standard American (US)",
        "tone": "Energetic, Fast-Paced, Engaging",
        "best_for": "Viral Shorts, Finance Hacks, Psychology",
        "rate": 1.10,
        "pitch": 1.02
    },
    {
        "id": "emily_us",
        "name": "Emily - US Warm Storyteller (Female)",
        "accent": "Standard American (Midwest)",
        "tone": "Warm, Trustworthy, Conversational",
        "best_for": "Real Estate, Long-Form Documentaries, Explanations",
        "rate": 1.00,
        "pitch": 1.00
    }
]

def synthesize_polyphonic_track(track_type: str, duration_sec: float = 30.0, output_path: str = None) -> str:
    """
    Synthesizes rich polyphonic background music without any external audio dependencies.
    Generates WAV 44.1kHz Stereo with kick, sub-bass, harmonic pads, and rhythmic pulse.
    """
    if not output_path:
        filename = f"{track_type}_{int(duration_sec)}s.wav"
        output_path = os.path.join(AUDIO_DIR, filename)

    if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
        return output_path

    sample_rate = 44100
    num_samples = int(sample_rate * duration_sec)

    with wave.open(output_path, 'w') as wav_file:
        wav_file.setnchannels(2)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)

        frames = bytearray()

        if track_type == "wall_street_pulse":
            bpm = 118
            beat_dur = 60.0 / bpm
            for i in range(num_samples):
                t = i / sample_rate
                # Bassline sequence (Am - F - C - G)
                bar = int(t / (beat_dur * 4)) % 4
                base_freq = [55.0, 43.65, 65.41, 49.0][bar] # A1, F1, C2, G1
                sub = 0.22 * math.sin(2 * math.pi * base_freq * t)

                # Synth pad with gentle vibrato
                chord_offsets = [0, 3, 7, 10] if bar == 0 else [0, 4, 7, 12]
                pad = 0.0
                for semi in chord_offsets[:3]:
                    f = base_freq * (2 ** (semi / 12.0)) * 4
                    pad += 0.05 * math.sin(2 * math.pi * f * t + 0.1 * math.sin(2 * math.pi * 4 * t))

                # Kick drum on 1 and 3
                beat_t = t % beat_dur
                kick = 0.0
                if (int(t / beat_dur) % 2 == 0) and beat_t < 0.22:
                    k_env = max(0.0, 1.0 - beat_t / 0.22)
                    k_freq = 130 * math.exp(-beat_t * 30)
                    kick = 0.45 * k_env * math.sin(2 * math.pi * k_freq * beat_t)

                # Hi-hat tick on eighth notes
                tick_t = t % (beat_dur / 2.0)
                tick = 0.0
                if tick_t < 0.04:
                    tick = 0.08 * (1.0 - tick_t / 0.04) * (math.sin(2 * math.pi * 7000 * tick_t) + math.sin(2 * math.pi * 9500 * tick_t))

                total = max(-0.95, min(0.95, sub + pad + kick + tick))
                val = int(total * 32767)
                frames.extend(struct.pack('<hh', val, val))

        elif track_type == "true_crime_noir":
            # Eerie, cinematic, deep suspense drone
            for i in range(num_samples):
                t = i / sample_rate
                # Low sub drone (43.65 Hz - F1) with slow tremolo
                drone = 0.30 * math.sin(2 * math.pi * 43.65 * t) * (0.85 + 0.15 * math.sin(2 * math.pi * 0.2 * t))
                # Dissonant minor 2nd / tritone tension
                tension = 0.12 * math.sin(2 * math.pi * 46.25 * t) * (0.5 + 0.5 * math.sin(2 * math.pi * 0.1 * t))
                # Heartbeat thud every 1.5 seconds
                hb_t = t % 1.5
                heartbeat = 0.0
                if hb_t < 0.18:
                    hb_env = max(0.0, 1.0 - hb_t / 0.18)
                    heartbeat = 0.35 * hb_env * math.sin(2 * math.pi * 55 * math.exp(-hb_t * 15) * hb_t)

                total = max(-0.95, min(0.95, drone + tension + heartbeat))
                val = int(total * 32767)
                frames.extend(struct.pack('<hh', val, val))

        elif track_type == "viral_energetic":
            bpm = 126
            beat_dur = 60.0 / bpm
            for i in range(num_samples):
                t = i / sample_rate
                # Punchy 4-on-the-floor beat
                beat_t = t % beat_dur
                kick = 0.0
                if beat_t < 0.2:
                    k_env = max(0.0, 1.0 - beat_t / 0.2)
                    kick = 0.5 * k_env * math.sin(2 * math.pi * (140 * math.exp(-beat_t * 35)) * beat_t)

                # Bouncy synth bass (110 Hz / 146.8 Hz alternating)
                bass_step = int(t / (beat_dur / 2.0)) % 4
                b_freq = [110.0, 110.0, 146.83, 130.81][bass_step]
                bass_t = (t % (beat_dur / 2.0))
                bass_env = max(0.0, 1.0 - bass_t / (beat_dur / 2.0))
                bass = 0.25 * bass_env * math.sin(2 * math.pi * b_freq * bass_t)

                # Shimmer top end
                shimmer = 0.04 * math.sin(2 * math.pi * 2200 * t) * math.sin(2 * math.pi * 440 * t)

                total = max(-0.95, min(0.95, kick + bass + shimmer))
                val = int(total * 32767)
                frames.extend(struct.pack('<hh', val, val))

        else: # lofi_chill
            bpm = 85
            beat_dur = 60.0 / bpm
            for i in range(num_samples):
                t = i / sample_rate
                # Warm jazzy 7th chord (Cmaj7 / Am7)
                bar = int(t / (beat_dur * 4)) % 2
                freqs = [261.63, 329.63, 392.00, 493.88] if bar == 0 else [220.00, 261.63, 329.63, 392.00]
                pad = 0.0
                for f in freqs:
                    pad += 0.06 * math.sin(2 * math.pi * f * t)

                # Soft muffled kick on beat 1
                b_t = t % (beat_dur * 2)
                kick = 0.0
                if b_t < 0.25:
                    kick = 0.3 * (1.0 - b_t / 0.25) * math.sin(2 * math.pi * 75 * b_t)

                total = max(-0.95, min(0.95, pad + kick))
                val = int(total * 32767)
                frames.extend(struct.pack('<hh', val, val))

        wav_file.writeframes(frames)

    return output_path

def generate_sfx(sfx_type: str) -> str:
    """Generates sound effects like whoosh, impact, chime."""
    filename = f"sfx_{sfx_type}.wav"
    output_path = os.path.join(AUDIO_DIR, filename)

    if os.path.exists(output_path):
        return output_path

    sample_rate = 44100
    duration = 0.8
    num_samples = int(sample_rate * duration)

    with wave.open(output_path, 'w') as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        frames = bytearray()

        if sfx_type == "whoosh":
            for i in range(num_samples):
                t = i / sample_rate
                # Frequency sweep up and down
                f = 200 + 1200 * math.sin(math.pi * t / duration)
                env = math.sin(math.pi * t / duration) ** 2
                val = int(0.6 * env * math.sin(2 * math.pi * f * t) * 32767)
                frames.extend(struct.pack('<hh', val, val))
        elif sfx_type == "impact":
            for i in range(num_samples):
                t = i / sample_rate
                env = max(0.0, 1.0 - t / duration) ** 3
                f = 90 * math.exp(-t * 8)
                val = int(0.7 * env * math.sin(2 * math.pi * f * t) * 32767)
                frames.extend(struct.pack('<hh', val, val))
        else: # chime / bell
            for i in range(num_samples):
                t = i / sample_rate
                env = max(0.0, 1.0 - t / duration) ** 2
                sample = 0.4 * env * (math.sin(2 * math.pi * 1760 * t) + 0.5 * math.sin(2 * math.pi * 3520 * t))
                val = int(sample * 32767)
                frames.extend(struct.pack('<hh', val, val))

        wav.writeframes(frames)

    return output_path

# Pre-generate standard audio assets
def ensure_default_audio():
    synthesize_polyphonic_track("wall_street_pulse", 30.0)
    synthesize_polyphonic_track("true_crime_noir", 30.0)
    synthesize_polyphonic_track("viral_energetic", 30.0)
    synthesize_polyphonic_track("lofi_chill", 30.0)
    generate_sfx("whoosh")
    generate_sfx("impact")
    generate_sfx("chime")
