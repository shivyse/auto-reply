"""
TubePulse US - Procedural Audio Bed & Sound Design Engine
Generates royalty-free polyphonic music tracks, visceral sound effects, 808 sub drops,
and multi-layer sound-designed soundtracks with automated cut whooshes.
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

def generate_viral_soundtrack_with_sfx(duration_sec: float, niche: str, cut_times: list, output_path: str = None) -> str:
    """
    Synthesizes an adrenaline-pumping, viral sound-designed audio track:
    1. 808 Sub Boom at t=0s to stop the scroll
    2. Driving 128 BPM electronic kick & sub-bass rhythm
    3. Micro-whoosh transitions at each cut timestamp
    4. Payoff bell/chime impact near the climax
    """
    if not output_path:
        output_path = os.path.join(AUDIO_DIR, f"soundtrack_{niche}_{int(duration_sec)}s.wav")

    sample_rate = 44100
    num_samples = int(sample_rate * duration_sec)
    bpm = 128
    beat_dur = 60.0 / bpm

    with wave.open(output_path, 'w') as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        frames = bytearray()

        for i in range(num_samples):
            t = i / sample_rate

            # 1. Opening 808 Sub Boom at t=0 to grab attention in frame 1
            boom = 0.0
            if t < 1.2:
                env = (1.0 - t / 1.2) ** 2
                f_boom = 95 * math.exp(-t * 4.5)
                boom = 0.60 * env * math.sin(2 * math.pi * f_boom * t)

            # 2. Driving 128 BPM Kick & Sub-Bass Groove
            b_t = t % beat_dur
            kick = 0.0
            if b_t < 0.20:
                k_env = max(0.0, 1.0 - b_t / 0.20)
                kick = 0.45 * k_env * math.sin(2 * math.pi * (140 * math.exp(-b_t * 32)) * b_t)

            # Rolling Bassline (Am - F - C - G pattern)
            bar = int(t / (beat_dur * 4)) % 4
            base_freq = [55.0, 43.65, 65.41, 49.0][bar]
            sub = 0.22 * math.sin(2 * math.pi * base_freq * t)

            # Hi-hat tick every 16th note for speed sensation
            tick_t = t % (beat_dur / 4.0)
            hihat = 0.0
            if tick_t < 0.03:
                hihat = 0.06 * (1.0 - tick_t / 0.03) * (math.sin(2 * math.pi * 8000 * tick_t) + math.sin(2 * math.pi * 11000 * tick_t))

            # 3. Synchronized Micro-Whooshes at cut timestamps
            sfx = 0.0
            for ct in cut_times:
                dt = t - ct
                if 0 <= dt < 0.28:
                    s_env = math.sin(math.pi * dt / 0.28)
                    f_sfx = 280 + 1600 * (dt / 0.28)
                    sfx += 0.32 * s_env * math.sin(2 * math.pi * f_sfx * dt)

            # 4. Payoff Cash Register Chime near the 75% mark
            chime = 0.0
            payoff_t = duration_sec * 0.72
            dt_chime = t - payoff_t
            if 0 <= dt_chime < 1.2:
                c_env = (1.0 - dt_chime / 1.2) ** 2
                chime = 0.35 * c_env * (math.sin(2 * math.pi * 1760 * dt_chime) + 0.6 * math.sin(2 * math.pi * 3520 * dt_chime))

            total = max(-0.95, min(0.95, boom + kick + sub + hihat + sfx + chime))
            val = int(total * 32767)
            frames.extend(struct.pack('<hh', val, val))

        wav.writeframes(frames)

    return output_path

def synthesize_polyphonic_track(track_type: str, duration_sec: float = 30.0, output_path: str = None) -> str:
    """Synthesizes rich polyphonic background music without external audio dependencies."""
    if not output_path:
        filename = f"{track_type}_{int(duration_sec)}s.wav"
        output_path = os.path.join(AUDIO_DIR, filename)

    if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
        return output_path

    # Delegate to viral sound-designed track generator
    cuts = [1.2 * i for i in range(1, int(duration_sec // 1.2))]
    return generate_viral_soundtrack_with_sfx(duration_sec, track_type, cuts, output_path)

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

def ensure_default_audio():
    synthesize_polyphonic_track("wall_street_pulse", 30.0)
    synthesize_polyphonic_track("true_crime_noir", 30.0)
    synthesize_polyphonic_track("viral_energetic", 30.0)
    synthesize_polyphonic_track("lofi_chill", 30.0)
    generate_sfx("whoosh")
    generate_sfx("impact")
    generate_sfx("chime")
