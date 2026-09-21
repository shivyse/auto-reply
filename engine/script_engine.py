"""
TubePulse US - AI Script & Retention Engine
Generates viral, high-retention YouTube scripts optimized for American viewer psychology.
Supports both YouTube Shorts (vertical 9:16) and Long-Form (16:9 8-12 min) videos.
"""

import re
import math
from .us_intelligence import US_NICHES, US_HOOK_FORMULAS

US_POWER_WORDS = [
    "secret", "exposed", "insider", "banned", "loophole", "tax", "wealth", "fbi",
    "classified", "warning", "critical", "shocking", "wall street", "trillion", "dollar",
    "hidden", "unsolved", "billionaire", "algorithm", "mistake", "glitch", "crash"
]

def analyze_script_retention(script_text: str):
    """
    Analyzes script retention metrics tailored for US YouTube audiences.
    """
    words = re.findall(r'\b\w+\b', script_text.lower())
    word_count = len(words)
    sentences = [s.strip() for s in re.split(r'[.!?]+', script_text) if s.strip()]
    sentence_count = max(1, len(sentences))

    # Duration calculation (average US conversational YouTube pacing is 150 words per minute)
    duration_seconds = max(5, int((word_count / 150.0) * 60))
    minutes = duration_seconds // 60
    seconds = duration_seconds % 60
    duration_str = f"{minutes}m {seconds:02d}s" if minutes > 0 else f"{seconds}s"

    # Power words score
    found_power_words = [w for w in set(words) if w in US_POWER_WORDS]
    power_word_score = min(30, len(found_power_words) * 5)

    # Question & Curiosity score
    question_count = script_text.count("?")
    question_score = min(25, question_count * 8)

    # Sentence length variance (short, punchy sentences retain US audiences better)
    avg_sentence_len = word_count / sentence_count
    pace_score = 25 if 6 <= avg_sentence_len <= 14 else max(10, int(25 - abs(avg_sentence_len - 10) * 2))

    # Hook intensity (checks the first 30 words for high impact openers)
    first_30_words = " ".join(words[:30])
    hook_score = 20
    if any(k in first_30_words for k in ["stop", "why", "never", "secret", "what", "how", "if you"]):
        hook_score = 25

    total_retention_score = min(99, power_word_score + question_score + pace_score + hook_score)

    # Grade level estimation (Flesch-Kincaid)
    # Optimized target for US broad audience is Grade 6-8 (simple, engaging, conversational)
    syllables = sum(max(1, len(re.findall(r'[aeiouy]+', w))) for w in words)
    if word_count > 0 and sentence_count > 0:
        fk_grade = round(0.39 * (word_count / sentence_count) + 11.8 * (syllables / word_count) - 15.59, 1)
        fk_grade = max(3.0, min(14.0, fk_grade))
    else:
        fk_grade = 6.5

    return {
        "word_count": word_count,
        "estimated_duration_seconds": duration_seconds,
        "duration_str": duration_str,
        "retention_score": total_retention_score,
        "fk_grade": fk_grade,
        "power_words_found": found_power_words[:6],
        "pace_rating": "Optimal (Punchy)" if avg_sentence_len <= 14 else "Moderate",
        "avg_sentence_length": round(avg_sentence_len, 1)
    }

def generate_youtube_script(topic: str, niche_id: str = "finance", format_type: str = "shorts", hook_style: str = "fomo"):
    """
    Generates a full, production-ready YouTube script with visual and audio cues.
    """
    topic_clean = topic.strip() or "The 2026 US Wealth Loophole"
    niche_data = US_NICHES.get(niche_id, US_NICHES["finance"])
    
    if format_type.lower() == "shorts":
        return _generate_shorts_script(topic_clean, niche_id, niche_data, hook_style)
    else:
        return _generate_longform_script(topic_clean, niche_id, niche_data, hook_style)

def _generate_shorts_script(topic: str, niche_id: str, niche_data: dict, hook_style: str):
    """Generates a high-speed 30-50 second viral vertical Shorts script."""
    
    if niche_id == "finance":
        hook = f"Stop scrolling if you live in America and have more than $1,000 in a checking account."
        beats = [
            ("0:00 - 0:04", "HOOK (Visual: Big Red Alert Card)", hook),
            ("0:04 - 0:12", "PAIN POINT (Visual: Bank Statement Graph)", "Because while standard US banks are paying you 0.01% interest, inflation is quietly draining your purchasing power every single month."),
            ("0:12 - 0:22", "THE REVELATION (Visual: High-Yield Treasury Ticker)", f"Regarding '{topic}', the top 1% of Americans don't leave cash sitting idle. They leverage Treasury bills, high-yield municipal accounts, and index-linked yields paying over 5%."),
            ("0:22 - 0:34", "RETENTION RESET (Visual: Calculator & Arrow)", "Here is the exact math: On a $20,000 safety fund, that is the difference between making $2 a year versus $1,000 in pure passive returns."),
            ("0:34 - 0:45", "LOOP & CTA (Visual: Follow Arrow + Loop Hook)", "Tap the subscribe button below so you never miss another US wealth update. And remember...")
        ]
    elif niche_id == "tech_ai":
        hook = f"Silicon Valley engineers just leaked what AI is doing behind closed doors, and it changes everything."
        beats = [
            ("0:00 - 0:04", "HOOK (Visual: Neon Glitch & Warning Badge)", hook),
            ("0:04 - 0:14", "THE SHOCK (Visual: Server Rack & Neural Graphic)", f"When looking into '{topic}', the speed of development isn't linear anymore. We are seeing autonomous systems solve multi-step engineering problems in seconds."),
            ("0:14 - 0:26", "WHAT IT MEANS (Visual: Silicon Valley Map & Data)", "In 2026, the workers who earn top tier US salaries aren't the ones writing code by hand—they are the ones orchestrating multi-agent AI workflows."),
            ("0:26 - 0:36", "RETENTION RESET (Visual: Split Screen Chart)", "If you don't adapt right now, your skill set could become obsolete faster than you think."),
            ("0:36 - 0:45", "LOOP & CTA (Visual: Subscribe Pulse)", "Drop a comment with what you think happens next, and subscribe for daily tech intelligence.")
        ]
    elif niche_id == "true_crime":
        hook = f"In the summer of 2004, a quiet suburban family in Ohio disappeared overnight, leaving their dinner on the table."
        beats = [
            ("0:00 - 0:05", "HOOK (Visual: Moody Noir Filter, Police Siren)", hook),
            ("0:05 - 0:16", "THE EVIDENCE (Visual: Unsolved Case File Graphic)", f"This is the mystery surrounding '{topic}'. When local detectives and FBI profilers arrived, there were zero signs of forced entry. The front door was unlocked, cars parked in the driveway."),
            ("0:16 - 0:28", "THE TWIST (Visual: Map Coordinates & Timeline)", "Then, fourteen days later, a mysterious cell phone ping hit a tower 800 miles away in the Nevada desert."),
            ("0:28 - 0:38", "CLIFFHANGER (Visual: Classified Stamp)", "To this day, federal authorities have kept three files classified. Part two is pinned in the comments below."),
            ("0:38 - 0:45", "LOOP & CTA (Visual: Follow for Part 2)", "Hit subscribe to see what the FBI found inside that Nevada locker...")
        ]
    else: # viral_psychology / real estate / luxury
        hook = f"99% of people in the US have no idea this psychological trick is being used on them every single day."
        beats = [
            ("0:00 - 0:04", "HOOK (Visual: Bold Yellow Text 'YOU ARE BEING TRICKED')", hook),
            ("0:04 - 0:14", "THE EXPERIMENT (Visual: Fast Zoom & Split Screen)", f"Here is the breakdown on '{topic}'. When you walk into major American retail stores, the lighting, music tempo, and aisle layout are engineered to induce 'sensory decathlon'."),
            ("0:14 - 0:25", "THE SECRET (Visual: Price Tag Breakdown)", "Notice how prices always end in .99? Your brain reads the leftmost digit first, making a $9.99 item feel closer to $9 than $10."),
            ("0:25 - 0:35", "ACTION STEP (Visual: Brain Scan Graphic)", "Once you notice this, you can never unsee it. Next time you shop, look at eye level—that's where the highest markups are placed."),
            ("0:35 - 0:45", "LOOP & CTA (Visual: Subscribe Loop)", "Share this with someone who needs to save money, and follow for more psychological secrets.")
        ]

    # Combine into readable full text and timed segments
    full_speech_script = " ".join([b[2] for b in beats])
    analysis = analyze_script_retention(full_speech_script)

    # Kinetic subtitle segments (ideal for FFmpeg subtitle overlay cards)
    subtitles = []
    for beat in beats:
        subtitles.append({
            "timestamp": beat[0],
            "role": beat[1],
            "text": beat[2],
            "duration_est": max(3, len(beat[2].split()) // 2.5)
        })

    return {
        "topic": topic,
        "niche": niche_id,
        "format": "Shorts (9:16)",
        "hook": hook,
        "beats": beats,
        "full_text": full_speech_script,
        "subtitles": subtitles,
        "analysis": analysis,
        "recommended_bgm": "Viral Shorts Energetic" if niche_id != "true_crime" else "True Crime Noir"
    }

def _generate_longform_script(topic: str, niche_id: str, niche_data: dict, hook_style: str):
    """Generates an 8-12 minute high-RPM long-form video script with multiple retention resets."""
    
    sections = [
        {
            "title": "Act 0: The Cold Open & The 3-Second Hook",
            "time": "0:00 - 1:15",
            "purpose": "Hook the US viewer, state the stakes, prevent drop-off before first ad slot",
            "voiceover": (
                f"If you live in the United States and look at your bank account, your career, or your living expenses lately, "
                f"you already know something fundamentally changed. Today, we are pulling back the curtain on '{topic}'. "
                f"By the end of this video, you will understand the exact mechanics that 99% of people are completely blind to—"
                f"and more importantly, the three critical strategic moves you need to make before the end of this year. "
                f"Before we dive in, make sure to hit that subscribe button with notifications turned on—let's break down the data."
            )
        },
        {
            "title": "Act 1: The Hidden Reality Nobody Mentions",
            "time": "1:15 - 3:45",
            "purpose": "Present hard US data, Federal Reserve/IRS figures, and establish immediate authority",
            "voiceover": (
                f"To understand why this is happening, we have to look back at the economic policy shifts over the last 36 months. "
                f"In the United States, middle-class purchasing power has faced an unprecedented squeeze. "
                f"While corporate balance sheets have reported record gains, the median American worker has watched housing, healthcare, "
                f"and grocery bills outpace wage increases by a wide margin. "
                f"When you examine the data behind '{topic}', you realize this wasn't an accident—it is the direct byproduct of deliberate structural incentives. "
                f"Take a look at this chart on your screen right now..."
            )
        },
        {
            "title": "Act 2: The Mid-Point Retention Reset & The Twist",
            "time": "3:45 - 6:30",
            "purpose": "Reset attention span right before the 5-minute mark where typical YouTube drop-off occurs",
            "voiceover": (
                f"Now, here is the part where most conventional financial and tech advice completely falls apart. "
                f"You have probably been told by mainstream media and internet gurus that the solution is simply to 'save more' or 'work overtime'. "
                f"That might have worked in 1995, but in 2026, the mathematical reality is stark. "
                f"The wealthiest top 5% of US households play by a completely different playbook. "
                f"Instead of trading hours for dollars, they structure assets to capture asymmetric upside while shielding themselves from currency devaluation. "
                f"Here is how their system actually operates..."
            )
        },
        {
            "title": "Act 3: The 3-Step Action Blueprint",
            "time": "6:30 - 9:30",
            "purpose": "Deliver immense actionable value to guarantee high likes, comments, and shares",
            "voiceover": (
                f"So what does this mean for you, and how do you protect and grow your position? "
                f"Step one: Audit your current exposure. If more than 40% of your net worth is sitting in depreciating cash or high-fee retirement vehicles, you are actively losing ground. "
                f"Step two: Reposition toward productive, cash-flowing collateral that adjusts automatically with inflation. "
                f"And step three: Build sovereign skill sets in high-demand US digital and automation sectors that cannot be outsourced or automated overnight."
            )
        },
        {
            "title": "Act 4: The Conclusion & The Engagement Loop",
            "time": "9:30 - 10:45",
            "purpose": "High-converting American CTA, algorithm engagement prompt, and end-screen teaser",
            "voiceover": (
                f"The bottom line is simple: America has always rewarded those who understand the rules of the game before the crowd catches up. "
                f"I want to hear from you in the comments below: Which of these shifts are you seeing most in your city right now? "
                f"I read and reply to every single comment during the first 2 hours after upload. "
                f"If you found this breakdown valuable, smash the like button and share it with someone who needs to hear it. "
                f"Click the video on your screen right now to see our next deep dive—I'll see you in the next one."
            )
        }
    ]

    full_text = " ".join([s["voiceover"] for s in sections])
    analysis = analyze_script_retention(full_text)

    return {
        "topic": topic,
        "niche": niche_id,
        "format": "Long-Form (16:9)",
        "sections": sections,
        "full_text": full_text,
        "analysis": analysis,
        "recommended_bgm": "Wall Street Tech Pulse" if niche_id in ["finance", "tech_ai"] else "True Crime Noir"
    }
