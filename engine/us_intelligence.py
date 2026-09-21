"""
TubePulse US - United States Audience Intelligence & Trend Radar
Contains niche definitions, high-RPM metrics, US trend catalog, hook formulas, and peak posting times.
"""

from datetime import datetime, timezone, timedelta

# US High-CPM Niches with historical YouTube metrics
US_NICHES = {
    "finance": {
        "id": "finance",
        "name": "US Personal Finance & Wealth",
        "badge": "💰 Top RPM",
        "avg_rpm": 34.50,
        "rpm_range": "$25 - $55",
        "cpm_range": "$40 - $90",
        "top_us_states": ["California", "New York", "Texas", "Florida", "Illinois"],
        "target_demographic": "24-48, US professionals, investors, homeowners",
        "retention_style": "Fast hard facts, proof numbers, tax code references, urgent FOMO",
        "icon": "fa-dollar-sign",
        "color": "#10b981",
        "sample_topics": [
            "The 2026 US Tax Loophole Rich Americans Quietly Use",
            "Why Your 401(k) Is Actually Costing You Thousands",
            "US Housing Market 2026: Why Buying Right Now Might Be a Trap",
            "How Everyday Americans Are Making $2,000/Mo in Passive Dividends",
            "The Federal Reserve's Unannounced Shift on Interest Rates"
        ]
    },
    "tech_ai": {
        "id": "tech_ai",
        "name": "Silicon Valley & AI Innovations",
        "badge": "⚡ Viral Growth",
        "avg_rpm": 28.00,
        "rpm_range": "$20 - $42",
        "cpm_range": "$35 - $70",
        "top_us_states": ["California", "Washington", "Texas", "Massachusetts", "Colorado"],
        "target_demographic": "18-40, tech workers, entrepreneurs, early adopters",
        "retention_style": "High-tech visual transitions, insider leaks, existential implications",
        "icon": "fa-microchip",
        "color": "#06b6d4",
        "sample_topics": [
            "OpenAI's New Model Just Terrified Silicon Valley Executives",
            "5 AI Tools That Will Replace 6-Figure US White Collar Jobs",
            "Inside Apple's Secret 10-Year Hardware Lab",
            "Why Quantum Computing in the US Just Made a Massive Leap",
            "The Rise of Autonomous AI Agents in American Corporations"
        ]
    },
    "true_crime": {
        "id": "true_crime",
        "name": "American True Crime & Unsolved FBI Files",
        "badge": "🔥 92% Avg Retention",
        "avg_rpm": 19.50,
        "rpm_range": "$14 - $28",
        "cpm_range": "$22 - $45",
        "top_us_states": ["Ohio", "Pennsylvania", "Michigan", "Texas", "Florida"],
        "target_demographic": "21-55, high female skew (68%), true crime podcast listeners",
        "retention_style": "Moody ambient soundscapes, cliffhangers before commercial breaks, timeline reveals",
        "icon": "fa-mask",
        "color": "#ef4444",
        "sample_topics": [
            "The Suburban Ohio Disappearance That Stumped the FBI for 20 Years",
            "The Highway 50 Mystery: What Happened at Mile Marker 112?",
            "How One Missing Voicemail Solved a 15-Year American Cold Case",
            "The Secret Society That Operated in Plain Sight in New England",
            "The FBI Agent Who Broke Protocol to Save a Hostage"
        ]
    },
    "luxury_megaprojects": {
        "id": "luxury_megaprojects",
        "name": "US Megaprojects & Military Engineering",
        "badge": "🚀 High Binge-Rate",
        "avg_rpm": 22.00,
        "rpm_range": "$16 - $32",
        "cpm_range": "$25 - $50",
        "top_us_states": ["Virginia", "California", "Florida", "Georgia", "Arizona"],
        "target_demographic": "25-60, high male skew (78%), engineering & military enthusiasts",
        "retention_style": "Massive scale comparisons, budget figures ($ Billions), classified aura",
        "icon": "fa-jet-fighter",
        "color": "#f59e0b",
        "sample_topics": [
            "America's $2 Trillion Secret Underground Tunnel Network",
            "Inside the US Navy's Next-Gen Stealth Destroyer",
            "How the US Is Building the World's Most Expensive Border Tech",
            "The Megaproject That Will Bring Clean Water to the American Desert",
            "Inside the Secret $50 Billion B-21 Raider Bomber Facility"
        ]
    },
    "viral_psychology": {
        "id": "viral_psychology",
        "name": "Viral US Shorts & Dark Psychology",
        "badge": "📱 10M+ View Potential",
        "avg_rpm": 11.50,
        "rpm_range": "$8 - $18",
        "cpm_range": "$12 - $28",
        "top_us_states": ["California", "New York", "Texas", "Florida", "Illinois"],
        "target_demographic": "16-35, broad American mobile viewers, TikTok & Shorts binge-watchers",
        "retention_style": "Kinetic subtitles, sub-second cuts, looping endings that replay seamlessly",
        "icon": "fa-brain",
        "color": "#8b5cf6",
        "sample_topics": [
            "3 Dark Psychology Tricks Used in Every US Supermarket",
            "If Someone Does This in Conversation, They're Testing You",
            "The Psychological Trick Used by FBI Negotiators to Read Minds",
            "Why Americans Feel More Tired After 8 Hours of Sleep",
            "The Unspoken Rule of Power Most People Learn Too Late"
        ]
    },
    "us_real_estate": {
        "id": "us_real_estate",
        "name": "US Real Estate & Housing Secrets",
        "badge": "🏡 $38+ RPM",
        "avg_rpm": 38.00,
        "rpm_range": "$28 - $60",
        "cpm_range": "$45 - $95",
        "top_us_states": ["Texas", "Florida", "North Carolina", "Tennessee", "Arizona"],
        "target_demographic": "28-55, American renters, first-time homebuyers, Airbnb hosts",
        "retention_style": "Zillow data teardowns, interest rate calculators, regional comparison maps",
        "icon": "fa-house",
        "color": "#ec4899",
        "sample_topics": [
            "Why Millions of Americans Are Moving to These 3 States in 2026",
            "The Real Reason US Home Prices Refuse to Drop",
            "How to Buy Your First Rental Property in the US with 5% Down",
            "The Death of the American Starter Home: What Nobody Is Telling You",
            "5 US Cities Where Rent Is Crashing Right Now"
        ]
    }
}

# Curated US Trend Radar with current search volume, competition, and monetization tier
US_TREND_RADAR = [
    {
        "id": "trend-1",
        "topic": "The 2026 US Tax Code Overhaul Explained",
        "niche": "finance",
        "search_volume": "480K / mo",
        "competition": "Medium",
        "projected_rpm": "$36.50",
        "trend_score": 96,
        "hook": "If you file taxes in America, the IRS just changed the game.",
        "urgency": "High",
        "recommended_format": "Both"
    },
    {
        "id": "trend-2",
        "topic": "Why Silicon Valley Billionaires Are Buying Land in Wyoming",
        "niche": "tech_ai",
        "search_volume": "340K / mo",
        "competition": "Low",
        "projected_rpm": "$29.00",
        "trend_score": 92,
        "hook": "Billionaires aren't building mansions anymore. They're building underground fortresses.",
        "urgency": "Trending",
        "recommended_format": "Long-Form"
    },
    {
        "id": "trend-3",
        "topic": "3 Mind Games Used by American Car Dealerships",
        "niche": "viral_psychology",
        "search_volume": "890K / mo",
        "competition": "Medium-High",
        "projected_rpm": "$14.20",
        "trend_score": 98,
        "hook": "Never sign a US auto lease until you ask these three questions.",
        "urgency": "Viral",
        "recommended_format": "Shorts"
    },
    {
        "id": "trend-4",
        "topic": "The Dark Side of America's $300B Credit Card Debt Bubble",
        "niche": "finance",
        "search_volume": "290K / mo",
        "competition": "Low",
        "projected_rpm": "$38.00",
        "trend_score": 90,
        "hook": "The average American household has $10,000 in credit card debt. Here is who profits.",
        "urgency": "High",
        "recommended_format": "Long-Form"
    },
    {
        "id": "trend-5",
        "topic": "The Unsolved Vanishing of Flight 19 over the Florida Triangle",
        "niche": "true_crime",
        "search_volume": "520K / mo",
        "competition": "Medium",
        "projected_rpm": "$21.00",
        "trend_score": 94,
        "hook": "Five US Navy bombers took off into clear skies and were never seen again.",
        "urgency": "Evergreen",
        "recommended_format": "Both"
    },
    {
        "id": "trend-6",
        "topic": "Inside the US Air Force's Secret Space Drone: The X-37B",
        "niche": "luxury_megaprojects",
        "search_volume": "410K / mo",
        "competition": "Low",
        "projected_rpm": "$24.50",
        "trend_score": 89,
        "hook": "It circled Earth for 908 days in complete secrecy. What was it carrying?",
        "urgency": "Trending",
        "recommended_format": "Shorts"
    },
    {
        "id": "trend-7",
        "topic": "Why Renting in America Is Officially Cheaper Than Owning in 2026",
        "niche": "us_real_estate",
        "search_volume": "610K / mo",
        "competition": "Medium",
        "projected_rpm": "$35.00",
        "trend_score": 95,
        "hook": "The American Dream of homeownership just got mathematically dismantled.",
        "urgency": "High",
        "recommended_format": "Both"
    }
]

# US Hook Formulas engineered for instant attention retention
US_HOOK_FORMULAS = [
    {
        "name": "The Pattern Interrupt (FOMO)",
        "formula": "Stop scrolling if you live in the United States and [Relatable Action]. Because in 2026, [Urgent Revelation]...",
        "best_for": "Shorts / TikTok",
        "retention_impact": "+34% first 5s retention",
        "example": "Stop scrolling if you live in the US and have a 401(k). Because new federal regulations just flipped the script on your retirement."
    },
    {
        "name": "The Insider Whistleblower",
        "formula": "What [Industry/Government] doesn't want Americans to find out about [Topic]...",
        "best_for": "Long-Form / Documentaries",
        "retention_impact": "+28% binge watch rate",
        "example": "What major US banks will never tell you about your savings account interest rate."
    },
    {
        "name": "The Contrarian Contradiction",
        "formula": "99% of Americans believe [Common Myth]. But the actual data reveals the exact opposite...",
        "best_for": "Educational / Finance",
        "retention_impact": "+41% comment section debates",
        "example": "99% of Americans think buying a home is always an asset. Here is why the wealthiest 1% rent instead."
    },
    {
        "name": "The FBI / Detective Cliffhanger",
        "formula": "On a normal Tuesday afternoon in [American City], [Normal Person] did [Everyday Thing]. Minutes later, everything changed...",
        "best_for": "True Crime / Mystery",
        "retention_impact": "+50% average view duration",
        "example": "On a rainy evening in Austin, Texas, a software engineer walked into his garage and vanished forever."
    }
]

# Peak US Posting Times across major US timezones
US_POSTING_WINDOWS = {
    "weekday": [
        {
            "name": "Morning Commute / Coffee Window",
            "est": "7:00 AM - 9:00 AM EST",
            "cst": "6:00 AM - 8:00 AM CST",
            "pst": "4:00 AM - 6:00 AM PST",
            "target": "US East Coast workers, early morning mobile viewers",
            "best_format": "Shorts & Quick News",
            "viewer_index": 78
        },
        {
            "name": "US Lunch Peak (High Conversion)",
            "est": "12:00 PM - 2:00 PM EST",
            "cst": "11:00 AM - 1:00 PM CST",
            "pst": "9:00 AM - 11:00 AM PST",
            "target": "Office workers, students on lunch break, high CTR window",
            "best_format": "Shorts & 8-10 min videos",
            "viewer_index": 92
        },
        {
            "name": "US Evening Primetime (Highest Views & RPM)",
            "est": "5:00 PM - 8:30 PM EST",
            "cst": "4:00 PM - 7:30 PM CST",
            "pst": "2:00 PM - 5:30 PM PST",
            "target": "National prime living room & TV viewing, peak ad auctions",
            "best_format": "Long-form 10-15m deep dives & viral shorts",
            "viewer_index": 100
        }
    ],
    "weekend": [
        {
            "name": "Saturday Morning Binge",
            "est": "9:00 AM - 12:00 PM EST",
            "cst": "8:00 AM - 11:00 AM CST",
            "pst": "6:00 AM - 9:00 AM PST",
            "target": "Relaxed weekend leisure browsing, high watch duration",
            "best_format": "Documentary & Long-form",
            "viewer_index": 95
        },
        {
            "name": "Sunday Night Reset",
            "est": "6:00 PM - 9:30 PM EST",
            "cst": "5:00 PM - 8:30 PM CST",
            "pst": "3:00 PM - 6:30 PM PST",
            "target": "Pre-workweek browsing, high finance and self-improvement interest",
            "best_format": "Finance, Tech & Educational",
            "viewer_index": 97
        }
    ]
}

def get_current_us_times():
    """Returns formatted current times across major US timezones."""
    utc_now = datetime.now(timezone.utc)
    # Daylight saving check or standard offsets
    # EST is UTC-5 (or EDT UTC-4), CST is UTC-6, MST is UTC-7, PST is UTC-8
    # Using EDT/CDT/PDT standard seasonal approximations:
    est_now = utc_now - timedelta(hours=4) # EDT (US Eastern)
    cst_now = utc_now - timedelta(hours=5) # CDT (US Central)
    mst_now = utc_now - timedelta(hours=6) # MDT (US Mountain)
    pst_now = utc_now - timedelta(hours=7) # PDT (US Pacific)

    return {
        "EST": est_now.strftime("%I:%M %p EDT, %b %d"),
        "CST": cst_now.strftime("%I:%M %p CDT, %b %d"),
        "MST": mst_now.strftime("%I:%M %p MDT, %b %d"),
        "PST": pst_now.strftime("%I:%M %p PDT, %b %d"),
        "iso_est": est_now.isoformat()
    }

def get_next_optimal_upload_time():
    """Calculates the next optimal US upload slot based on current EST time."""
    utc_now = datetime.now(timezone.utc)
    est_now = utc_now - timedelta(hours=4)
    hour = est_now.hour

    if hour < 11:
        recommended = "Today at 12:00 PM EDT (US Lunch Break Peak)"
        reason = "Allows YouTube 1 hour processing time before 12-2 PM East/Central peak traffic."
    elif hour < 16:
        recommended = "Today at 4:30 PM EDT (US Evening Primetime)"
        reason = "Catches the 5:00 PM - 8:30 PM EDT national living room & mobile rush."
    elif hour < 20:
        recommended = "Tonight at 8:00 PM EDT (Late Coast / Pacific Peak)"
        reason = "Maximizes California/Pacific 5:00 PM commute while keeping East Coast night viewers."
    else:
        recommended = "Tomorrow at 11:30 AM EDT"
        reason = "Fresh video ready for the midday national traffic surge."

    return {
        "recommended_slot": recommended,
        "reasoning": reason,
        "buffer_advice": "Upload 90 minutes before scheduled public release for 1080p60 encoding and Content ID checks."
    }
