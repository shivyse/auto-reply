"""
TubePulse US - SEO, Metadata & US Monetization Engine
Generates high-CTR titles, FTC-compliant YouTube descriptions, chapter markers,
curated US search tags, and estimates US RPM revenue in USD.
"""

from .us_intelligence import US_NICHES

def generate_seo_package(topic: str, niche_id: str = "finance", format_type: str = "shorts"):
    """
    Generates a complete YouTube metadata package tailored for US search & algorithmic recommendations.
    """
    niche = US_NICHES.get(niche_id, US_NICHES["finance"])
    topic_clean = topic.strip()
    is_shorts = (format_type.lower() == "shorts")

    # 1. High-CTR Titles (Curated for US Feed click behavior)
    titles = [
        {
            "title": f"{topic_clean} (2026 EXPOSED)",
            "ctr_score": 94,
            "style": "High-Curiosity Alert",
            "recommended": True
        },
        {
            "title": f"Why 99% of Americans Are Wrong About {topic_clean}",
            "ctr_score": 91,
            "style": "Contrarian Debate",
            "recommended": False
        },
        {
            "title": f"The Secret Behind {topic_clean} That Nobody Is Talking About",
            "ctr_score": 88,
            "style": "Insider Whistleblower",
            "recommended": False
        },
        {
            "title": f"Stop Doing This in 2026: {topic_clean}",
            "ctr_score": 86,
            "style": "Urgent Warning",
            "recommended": False
        }
    ]

    # 2. Targeted US Tags
    base_tags = [
        topic_clean.lower(),
        f"{topic_clean.lower()} 2026",
        "united states",
        "us news",
        "youtube automation",
        "viral video"
    ]

    niche_specific_tags = {
        "finance": ["personal finance", "us taxes", "irs loophole", "investing in us", "401k", "passive income", "money hacks", "wall street", "federal reserve", "financial freedom"],
        "tech_ai": ["artificial intelligence", "silicon valley", "ai tools 2026", "chatgpt", "future tech", "automation", "tech news us", "software engineer", "openai updates", "ai revolution"],
        "true_crime": ["true crime documentary", "fbi files", "unsolved mystery", "american crime story", "cold case solved", "investigation discovery", "creepy mysteries", "police interrogation"],
        "luxury_megaprojects": ["us military tech", "engineering megaprojects", "billionaire lifestyle", "defense spending", "pentagon projects", "modern marvels", "classified projects", "architecture"],
        "viral_psychology": ["dark psychology", "psychology tricks", "mind tricks", "human behavior", "body language", "manipulation tactics", "fbi negotiator", "subconscious mind"],
        "us_real_estate": ["us real estate 2026", "housing market crash", "buying a house in usa", "mortgage rates", "zillow", "rental property", "moving to florida", "homeowner tips"]
    }

    all_tags = base_tags + niche_specific_tags.get(niche_id, [])
    tags_string = ", ".join(all_tags[:20])

    # 3. Hashtags
    hashtags = [
        "#Shorts" if is_shorts else "#Documentary",
        f"#{niche['name'].replace(' ', '')}",
        "#UnitedStates",
        "#TrendingUS",
        "#2026Trends"
    ]

    # 4. Timestamps & Chapters (for long-form)
    chapters = """0:00 - The Cold Open & The Shocking US Data
1:15 - What Major US Institutions Keep Hidden
3:45 - The Turning Point (Why Conventional Advice Fails)
6:30 - The 3-Step Action Blueprint for 2026
9:30 - Final Verdict & Key Takeaway""" if not is_shorts else """0:00 - Hook & Urgency Alert
0:12 - The Hidden US Metric
0:25 - The Exact Breakdown
0:38 - Final Takeaway & Loop"""

    # 5. YouTube Description (with US FTC & Disclaimer compliance)
    description = f"""🔥 What 99% of people in the United States don't realize about {topic_clean}. In this breakdown, we reveal the critical data points, the hidden mechanics, and the strategic actions you need to take in 2026.

⏰ CHAPTER TIMESTAMPS:
{chapters}

📌 PINNED COMMENT CHALLENGE:
"What do you think is the biggest surprise about {topic_clean}? Let me know your thoughts below—I reply to every comment in the first 2 hours!"

🔔 SUBSCRIBE for daily high-value intelligence on {niche['name']}:
👉 https://youtube.com/@TubePulseUS?sub_confirmation=1

🏷️ KEYWORDS & TOPICS:
{tags_string}

{" ".join(hashtags)}

----------------------------------------------------------------
⚠️ LEGAL & FTC DISCLAIMER:
This video is created strictly for educational, informational, and entertainment purposes. It does not constitute formal financial, legal, tax, or professional advice. Always consult with a licensed US Certified Public Accountant (CPA), financial fiduciary, or legal counsel before making significant decisions. Results may vary.
----------------------------------------------------------------"""

    # 6. Pinned Comment
    pinned_comment = f"🚨 QUESTION FOR US VIEWERS: What is your #1 takeaway from '{topic_clean}'? Drop your comment below and tell us which US state you're watching from!"

    return {
        "titles": titles,
        "selected_title": titles[0]["title"],
        "description": description,
        "tags": all_tags[:20],
        "tags_csv": tags_string,
        "hashtags": hashtags,
        "chapters": chapters,
        "pinned_comment": pinned_comment,
        "niche_name": niche["name"],
        "avg_us_rpm": niche["avg_rpm"]
    }

def calculate_us_revenue_projection(views: int, niche_id: str = "finance", us_audience_share: float = 0.75):
    """
    Calculates projected revenue from US YouTube views across AdSense, Sponsorships, and Affiliates.
    """
    niche = US_NICHES.get(niche_id, US_NICHES["finance"])
    us_rpm = niche["avg_rpm"]
    non_us_rpm = 3.50 # Benchmark average rest-of-world RPM

    # Blended RPM
    blended_rpm = (us_audience_share * us_rpm) + ((1.0 - us_audience_share) * non_us_rpm)

    # Gross AdSense Revenue (views / 1000 * RPM)
    adsense_revenue = round((views / 1000.0) * blended_rpm, 2)

    # Estimated brand sponsorship value (typical US CPM based brand integration)
    sponsorship_estimate = round((views / 1000.0) * (us_rpm * 0.45), 2) if views >= 50000 else 0.0

    # Estimated affiliate revenue (US conversion rate ~0.2% on financial/tech products)
    affiliate_estimate = round((views * 0.002) * 18.0, 2)

    total_projected = round(adsense_revenue + sponsorship_estimate + affiliate_estimate, 2)

    return {
        "views": views,
        "us_audience_share": f"{int(us_audience_share * 100)}%",
        "niche_rpm": f"${us_rpm:.2f}",
        "blended_rpm": f"${blended_rpm:.2f}",
        "adsense_revenue": f"${adsense_revenue:,.2f}",
        "sponsorship_revenue": f"${sponsorship_estimate:,.2f}",
        "affiliate_revenue": f"${affiliate_estimate:,.2f}",
        "total_projected_usd": f"${total_projected:,.2f}"
    }
