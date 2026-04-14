"""
generate_horoscopes.py
NUZU News — Daily Horoscope Generator
Fetches all 12 signs from the Aztro API and saves to horoscopes.json.
Run once per day via GitHub Actions before bot.py.
"""

import json
import requests
from datetime import date
import time

SIGNS = [
    'aries', 'taurus', 'gemini', 'cancer', 'leo', 'virgo',
    'libra', 'scorpio', 'sagittarius', 'capricorn', 'aquarius', 'pisces'
]

SIGN_META = {
    'aries':       {'symbol': '♈', 'dates': 'Mar 21 – Apr 19', 'element': 'Fire',  'emoji': '🐏'},
    'taurus':      {'symbol': '♉', 'dates': 'Apr 20 – May 20', 'element': 'Earth', 'emoji': '🐂'},
    'gemini':      {'symbol': '♊', 'dates': 'May 21 – Jun 20', 'element': 'Air',   'emoji': '👯'},
    'cancer':      {'symbol': '♋', 'dates': 'Jun 21 – Jul 22', 'element': 'Water', 'emoji': '🦀'},
    'leo':         {'symbol': '♌', 'dates': 'Jul 23 – Aug 22', 'element': 'Fire',  'emoji': '🦁'},
    'virgo':       {'symbol': '♍', 'dates': 'Aug 23 – Sep 22', 'element': 'Earth', 'emoji': '🌾'},
    'libra':       {'symbol': '♎', 'dates': 'Sep 23 – Oct 22', 'element': 'Air',   'emoji': '⚖️'},
    'scorpio':     {'symbol': '♏', 'dates': 'Oct 23 – Nov 21', 'element': 'Water', 'emoji': '🦂'},
    'sagittarius': {'symbol': '♐', 'dates': 'Nov 22 – Dec 21', 'element': 'Fire',  'emoji': '🏹'},
    'capricorn':   {'symbol': '♑', 'dates': 'Dec 22 – Jan 19', 'element': 'Earth', 'emoji': '🐐'},
    'aquarius':    {'symbol': '♒', 'dates': 'Jan 20 – Feb 18', 'element': 'Air',   'emoji': '🏺'},
    'pisces':      {'symbol': '♓', 'dates': 'Feb 19 – Mar 20', 'element': 'Water', 'emoji': '🐟'},
}

# Fallback descriptions if API is down
FALLBACKS = {
    'aries':       "Bold moves pay off today. Trust your instincts — your energy is magnetic.",
    'taurus':      "Steady progress brings rewards. A financial opportunity may surface.",
    'gemini':      "Communication is your superpower today. Share your ideas freely.",
    'cancer':      "Home and heart take center stage. Nurture the relationships that matter.",
    'leo':         "Your natural charisma shines. Leadership roles favor you now.",
    'virgo':       "Details others overlook are your advantage. Precision wins the day.",
    'libra':       "Balance in all things. A diplomatic touch resolves a lingering tension.",
    'scorpio':     "Deep insight cuts through confusion. Trust your perception above all.",
    'sagittarius': "Adventure calls. Expand your horizons — even a small step counts.",
    'capricorn':   "Long-term planning pays dividends. Your discipline sets you apart.",
    'aquarius':    "Innovative thinking sparks something new. Collaborate with open minds.",
    'pisces':      "Intuition and creativity flow easily. Listen to your inner voice.",
}


def fetch_horoscope(sign):
    """Fetch daily horoscope from Aztro API (free, no auth required)."""
    try:
        url = f"https://aztro.sameerkumar.website/?sign={sign}&day=today"
        resp = requests.post(url, timeout=12)
        if resp.status_code == 200:
            d = resp.json()
            meta = SIGN_META[sign]
            return {
                'sign': sign,
                'name': sign.title(),
                'symbol': meta['symbol'],
                'emoji': meta['emoji'],
                'dates': meta['dates'],
                'element': meta['element'],
                'description': d.get('description', FALLBACKS[sign]),
                'lucky_number': d.get('lucky_number', ''),
                'lucky_color': d.get('color', ''),
                'mood': d.get('mood', ''),
                'compatibility': d.get('compatibility', '').title(),
                'current_date': d.get('current_date', str(date.today())),
                'source': 'api',
            }
    except Exception as e:
        print(f"  ⚠ API error for {sign}: {e} — using fallback")

    # Fallback: static content
    meta = SIGN_META[sign]
    return {
        'sign': sign,
        'name': sign.title(),
        'symbol': meta['symbol'],
        'emoji': meta['emoji'],
        'dates': meta['dates'],
        'element': meta['element'],
        'description': FALLBACKS[sign],
        'lucky_number': '',
        'lucky_color': '',
        'mood': '',
        'compatibility': '',
        'current_date': str(date.today()),
        'source': 'fallback',
    }


def main():
    print(f"NUZU Horoscopes — fetching for {date.today()}")
    horoscopes = []
    for sign in SIGNS:
        print(f"  Fetching {sign}...", end=' ')
        h = fetch_horoscope(sign)
        horoscopes.append(h)
        print(f"✓ [{h['source']}]")
        time.sleep(0.4)  # gentle pacing

    output = {
        'updated': str(date.today()),
        'total': len(horoscopes),
        'horoscopes': horoscopes,
    }

    with open('horoscopes.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    api_count = sum(1 for h in horoscopes if h['source'] == 'api')
    print(f"\n✅ Saved horoscopes.json  ({api_count}/12 from API, {12 - api_count}/12 fallback)")


if __name__ == '__main__':
    main()
