# zodiac_push_all.py
# Hard-coded bot that creates/overwrites ALL 13×28 pages on shinto.miraheze.org

import time
from datetime import date, datetime, timedelta
from datetime import date, timedelta

# stdlib imports you need
import time
from datetime import date, datetime, timedelta

# if your script makes HTTP calls (it does, for MediaWiki):
import requests

# optional, only if you’re using type hints in the file
from typing import Dict, List, Tuple, Optional




import requests

API_URL     = "https://evolutionism.miraheze.org/w/api.php"
USERNAME    = "Immanuelle"      # <-- BotPassword username (User@BotName)
PASSWORD    = "1996ToOmega!"    # <-- BotPassword password (long random string)
USER_AGENT  = "ZodiacWikiBot/0.2 (User:Immanuelle; contact: you@example.com)"
SUMMARY     = "Create/update zodiac date page"
THROTTLE    = 0.6      # seconds between edits (be polite to the wiki)
TITLE_PREFIX = ""      # e.g., "Calendar:" if you want them in a namespace
LONGRUN_START = 2001   # per your spec
LONGRUN_END   = 2399

# --- Optional deps for non-Gregorian calendars ---
try:
    from convertdate import hebrew as H
    from convertdate import chinese as C
    HAVE_CONVERTDATE = True
except Exception:
    H = None
    C = None
    HAVE_CONVERTDATE = False

# --- Your event lists (as you provided) ---
CHINESE_EVENTS = [
    {"name": "Chinese New Year", "type": "lunar", "month": 1, "day": 1},
    {"name": "Chinese New Year's Eve", "type": "relative",
     "anchor": {"type": "lunar", "month": 1, "day": 1}, "offset_days": -1},
    {"name": "Lantern Festival", "type": "lunar", "month": 1, "day": 15},
    {"name": "Qingming", "type": "solar_term", "term": "Qingming"},      # Sun λ=15° (requires astro)
    {"name": "Dragon Boat Festival", "type": "lunar", "month": 5, "day": 5},
    {"name": "Qixi", "type": "lunar", "month": 7, "day": 7},
    {"name": "Ghost Festival", "type": "lunar", "month": 7, "day": 15},
    {"name": "Mid-Autumn Festival", "type": "lunar", "month": 8, "day": 15},
    {"name": "Double Ninth", "type": "lunar", "month": 9, "day": 9},
    {"name": "Dongzhi", "type": "solar_term", "term": "Dongzhi"}          # Solstice (requires astro)
]

HEBREW_EVENTS = [
    {"name": "Rosh Hashanah (Day 1)", "type": "hebrew", "month": "Tishrei", "day": 1},
    {"name": "Yom Kippur", "type": "hebrew", "month": "Tishrei", "day": 10},
    {"name": "Sukkot (First Day)", "type": "hebrew", "month": "Tishrei", "day": 15},
    {"name": "Shemini Atzeret", "type": "hebrew", "month": "Tishrei", "day": 22},
    {"name": "Simchat Torah (Diaspora)", "type": "hebrew", "month": "Tishrei", "day": 23, "optional": True},
    {"name": "Hanukkah (Day 1)", "type": "hebrew", "month": "Kislev", "day": 25},
    {"name": "Tu BiShvat", "type": "hebrew", "month": "Shevat", "day": 15},
    {"name": "Purim", "type": "hebrew", "month": "Adar", "day": 14, "rule": "AdarII_in_leap_year"},
    {"name": "Pesach (First Day)", "type": "hebrew", "month": "Nisan", "day": 15},
    {"name": "Lag BaOmer", "type": "hebrew", "month": "Iyar", "day": 18},
    {"name": "Shavuot", "type": "hebrew", "month": "Sivan", "day": 6},
    {"name": "Tisha B'Av", "type": "hebrew", "month": "Av", "day": 9, "rule": "postpone_if_shabbat"}
]

# Hebrew month indices expected by convertdate (ECCLESIASTICAL numbering: Nisan=1… Adar=12/13)
HEBREW_MONTH_INDEX = {
    "nisan": 1, "iyyar": 2, "iyar": 2, "sivan": 3, "tammuz": 4, "av": 5, "elul": 6,
    "tishrei": 7, "tishri": 7, "cheshvan": 8, "marcheshvan": 8, "marheshvan": 8,
    "kislev": 9, "tevet": 10, "shevat": 11, "shvat": 11,
    # Adar handling depends on leap year; see helper below
}

def hebrew_month_number(name: str, hy: int, rule: str | None) -> int:
    """Return convertdate's month number for this Hebrew year hy."""
    n = name.strip().lower()
    if n.startswith("adar"):  # Adar / Adar I / Adar II
        if rule == "AdarII_in_leap_year" and H.leap(hy):
            return 13  # Adar II
        # Non-leap: Adar = 12; Leap: 'Adar' often means Adar II, but rule above catches Purim
        return 12
    return HEBREW_MONTH_INDEX[n]


# ---------- CHINESE MATCHERS ----------
from datetime import date, timedelta

def chinese_lunar_tuple(g: date):
    # (cycle, year, month, is_leap, day)
    return C.from_gregorian(g.year, g.month, g.day)

def chinese_new_year_gregorian_for_cy(cyc: int, y: int) -> date:
    # m=1, leap=False, d=1
    y1, m1, d1 = C.to_gregorian(cyc, y, 1, False, 1)
    return date(y1, m1, d1)

def chinese_event_matches_gregorian(g: date, ev: dict) -> bool | None:
    """Return True if matches, False if not, None if event type not supported."""
    if ev["type"] == "lunar":
        cyc, yy, m, leap, d = chinese_lunar_tuple(g)
        want_m = ev["month"]; want_d = ev["day"]
        # Most public festivals are in non-leap months; don't match leap months unless specified.
        if ev.get("leap") is not None:
            return (m == want_m) and (d == want_d) and (leap is bool(ev["leap"]))
        else:
            return (m == want_m) and (d == want_d) and (not leap)
    elif ev["type"] == "relative":
        # Only anchor supported here: another lunar date in the SAME Chinese year
        cyc, yy, _, _, _ = chinese_lunar_tuple(g)
        anch = ev["anchor"]
        if anch["type"] != "lunar":
            return None
        ay, am, ad = C.to_gregorian(cyc, yy, anch["month"], bool(anch.get("leap", False)), anch["day"])
        anchor_g = date(ay, am, ad)
        target = anchor_g + timedelta(days=int(ev.get("offset_days", 0)))
        return g == target
    elif ev["type"] == "solar_term":
        # Requires astro calc (sun ecliptic longitude). Left unimplemented to avoid heavy deps.
        return None
    return None

def chinese_overlap_table(m_idx: int, d_m: int,
                          start_iso_year: int = LONGRUN_START, end_iso_year: int = LONGRUN_END) -> str:
    if not HAVE_CONVERTDATE:
        return ("''Chinese calendar section requires `convertdate`. "
                "Install with `pip install convertdate`.''")
    total = end_iso_year - start_iso_year + 1
    rows = []
    for ev in CHINESE_EVENTS:
        matches = 0
        supported = True
        for y in range(start_iso_year, end_iso_year + 1):
            g = zodiac_gregorian_for_iso_year(m_idx, d_m, y)
            res = chinese_event_matches_gregorian(g, ev)
            if res is None:
                supported = False
                break
            if res:
                matches += 1
        prob = (matches / total) if supported else 0.0
        cat = f"[[Category:Days that {ev['name']} falls on]]" if matches > 0 else "—"
        note = "" if supported else " (requires solar-term calc)"
        rows.append((ev["name"] + note, matches, total, prob, cat))
    # Build wiki table
    lines = ['{| class="wikitable sortable"',
             '! Event !! Matches !! Years !! Probability !! Category']
    for name, c, t, p, cat in rows:
        lines.append(f"|-\n| {name} || {c} || {t} || {p:.2%} || {cat}")
    lines.append("|}")
    return "\n".join(lines)

# ---------- HEBREW MATCHERS ----------

def hebrew_event_matches_gregorian(g: date, ev: dict) -> bool:
    hy, hm, hd = H.from_gregorian(g.year, g.month, g.day)
    # compute the *observed* Gregorian date of the event in this Hebrew year
    tgt_month = hebrew_month_number(ev["month"], hy, ev.get("rule"))
    # base day (e.g., 9 Av)
    ty, tm, td = H.to_gregorian(hy, tgt_month, ev["day"])
    observed = date(ty, tm, td)
    # special rule: postpone Tisha B'Av if Shabbat
    if ev.get("rule") == "postpone_if_shabbat":
        if observed.weekday() == 5:  # Sat=5 in Python (Mon=0)
            observed = observed + timedelta(days=1)
    return g == observed

def hebrew_overlap_table(m_idx: int, d_m: int,
                         start_iso_year: int = LONGRUN_START, end_iso_year: int = LONGRUN_END) -> str:
    if not HAVE_CONVERTDATE:
        return ("''Hebrew calendar section requires `convertdate`. "
                "Install with `pip install convertdate`.''")
    total = end_iso_year - start_iso_year + 1
    rows = []
    for ev in HEBREW_EVENTS:
        matches = 0
        for y in range(start_iso_year, end_iso_year + 1):
            g = zodiac_gregorian_for_iso_year(m_idx, d_m, y)
            if hebrew_event_matches_gregorian(g, ev):
                matches += 1
        cat = f"[[Category:Days that {ev['name']} falls on]]" if matches > 0 else "—"
        rows.append((ev["name"], matches, total, matches/total, cat))
    lines = ['{| class="wikitable sortable"',
             '! Event !! Matches !! Years !! Probability !! Category']
    for name, c, t, p, cat in rows:
        lines.append(f"|-\n| {name} || {c} || {t} || {p:.2%} || {cat}")
    lines.append("|}")
    return "\n".join(lines)



# ------------- Page generator (minimal but complete) -------------

MONTHS = [
    "Sagittarius","Capricorn","Aquarius","Pisces","Aries","Taurus",
    "Gemini","Cancer","Leo","Virgo","Libra","Scorpio","Ophiuchus"
]
MONTH_NAMES = ["January","February","March","April","May","June",
               "July","August","September","October","November","December"]
WD_ABBR = {1:"Mon",2:"Tue",3:"Wed",4:"Thu",5:"Fri",6:"Sat",7:"Sun"}

def zodiac_to_iso(m_idx: int, d_m: int):
    if not (1 <= m_idx <= 13 and 1 <= d_m <= 28):
        raise ValueError("month_index 1..13, day_of_month 1..28 required")
    iso_week  = (m_idx - 1) * 4 + ((d_m - 1) // 7) + 1      # 1..52
    iso_wday  = ((d_m - 1) % 7) + 1                         # 1..7 (Mon..Sun)
    return iso_week, iso_wday

def ordinal_in_year(m_idx: int, d_m: int) -> int:
    w, wd = zodiac_to_iso(m_idx, d_m)
    return (w - 1) * 7 + wd  # 1..364

def zodiac_gregorian_for_iso_year(m_idx: int, d_m: int, iso_year: int) -> date:
    w, wd = zodiac_to_iso(m_idx, d_m)
    return date.fromisocalendar(iso_year, w, wd)

def reading_for_ordinal(ord1: int) -> str:
    return f"Chapter {ord1} of the Gaiad"

def nth_weekday_of_month(year: int, month: int, weekday_mon0: int, n: int) -> date:
    """weekday_mon0: 0=Mon .. 6=Sun; n>=1"""
    d = date(year, month, 1)
    delta = (weekday_mon0 - d.weekday()) % 7
    first = d + timedelta(days=delta)
    return first + timedelta(weeks=n-1)

def last_weekday_of_month(year: int, month: int, weekday_mon0: int) -> date:
    """weekday_mon0: 0=Mon .. 6=Sun"""
    if month == 12:
        d = date(year, 12, 31)
    else:
        d = date(year, month + 1, 1) - timedelta(days=1)
    delta = (d.weekday() - weekday_mon0) % 7
    return d - timedelta(days=delta)

def nth_weekday_holidays_for_year(year: int):
    """
    Returns {label: gregorian_date} for Nth-weekday style holidays.
    Labels are explicit about country; US/CA Thanksgiving are separate.
    """
    rules = {}

    # --- United States (federal) ---
    rules["US Martin Luther King Jr. Day (3rd Mon Jan)"] = nth_weekday_of_month(year, 1, 0, 3)
    rules["US Presidents Day (Washington’s Birthday, 3rd Mon Feb)"] = nth_weekday_of_month(year, 2, 0, 3)
    rules["US Memorial Day (last Mon May)"] = last_weekday_of_month(year, 5, 0)
    rules["US Labor Day (1st Mon Sep)"] = nth_weekday_of_month(year, 9, 0, 1)
    rules["US Columbus Day / Indigenous Peoples’ Day (2nd Mon Oct)"] = nth_weekday_of_month(year, 10, 0, 2)
    us_thanks = nth_weekday_of_month(year, 11, 3, 4)  # Thu=3
    rules["US Thanksgiving (4th Thu Nov)"] = us_thanks

    # Black Friday = day after US Thanksgiving
    rules["US Black Friday (Fri after US Thanksgiving)"] = us_thanks + timedelta(days=1)

    # --- United States (common observances) ---
    rules["US Mother’s Day (2nd Sun May)"] = nth_weekday_of_month(year, 5, 6, 2)  # Sun=6
    rules["US Father’s Day (3rd Sun Jun)"] = nth_weekday_of_month(year, 6, 6, 3)

    # --- Canada (national/federal) ---
    rules["Canada Labour Day (1st Mon Sep)"] = nth_weekday_of_month(year, 9, 0, 1)
    rules["Canada Thanksgiving (2nd Mon Oct)"] = nth_weekday_of_month(year, 10, 0, 2)

    # --- Canada (provincial examples) ---
    rules["Canada Family Day (most prov., 3rd Mon Feb)"] = nth_weekday_of_month(year, 2, 0, 3)
    rules["Canada Civic Holiday (1st Mon Aug)"] = nth_weekday_of_month(year, 8, 0, 1)
    rules["Yukon Discovery Day (3rd Mon Aug)"] = nth_weekday_of_month(year, 8, 0, 3)

    # --- Japan (national holidays via Happy Monday rules) ---
    rules["Japan Coming of Age Day (2nd Mon Jan)"] = nth_weekday_of_month(year, 1, 0, 2)
    rules["Japan Marine Day (3rd Mon Jul)"] = nth_weekday_of_month(year, 7, 0, 3)
    rules["Japan Respect for the Aged Day (3rd Mon Sep)"] = nth_weekday_of_month(year, 9, 0, 3)
    rules["Japan Sports Day (2nd Mon Oct)"] = nth_weekday_of_month(year, 10, 0, 2)

    return rules

def easter_sunday_gregorian(year: int) -> date:
    a = year % 19; b = year // 100; c = year % 100
    d = b // 4; e = b % 4; f = (b + 8) // 25; g = (b - f + 1) // 3
    h = (19*a + b - d - g + 15) % 30
    i = c // 4; k = c % 4
    l = (32 + 2*e + 2*i - h - k) % 7
    m = (a + 11*h + 22*l) // 451
    month = (h + l - 7*m + 114) // 31
    day = ((h + l - 7*m + 114) % 31) + 1
    return date(year, month, day)

EASTER_OFFSET_LABELS = {
    -63: "Septuagesima Sunday",
    -56: "Sexagesima Sunday",
    -49: "Quinquagesima Sunday",
    -47: "Mardi Gras/Carnival",
    -46: "Ash Wednesday",
    -21: "Laetare Sunday",
    -14: "Passion Sunday (Fifth Sunday of Lent)",
    -7 : "Palm Sunday",
    -6: "Holy Monday",
    -5: "Holy Tuesday",
    -4: "Spy Wednesday",
    -3 : "Maundy Thursday",
    -2 : "Good Friday",
    -1 : "Holy Saturday",
     0 : "Easter Sunday",
    +1:  "Easter Monday",
    +2:  "Easter Tuesday",
    +3:  "Easter Wednesday",
    +4:  "Easter Thursday",
    +5:  "Easter Friday",
    +6:  "Easter Saturday",
    +7:  "Second Sunday of Easter (Divine Mercy Sunday)",
    +14: "Third Sunday of Easter",
    +21: "Fourth Sunday of Easter",
    +28: "Fifth Sunday of Easter",
    +35: "Sixth Sunday of Easter",
    +39: "Ascension Thursday",
    +42: "Seventh Sunday of Easter",
    +49: "Pentecost Sunday",
    +56: "Trinity Sunday",
    +60: "Corpus Christi (Latin/Thu)",
}

def recent_block(m_idx: int, d_m: int, span: int = 5) -> str:
    iso_year = datetime.now().date().isocalendar()[0]
    y0, y1 = iso_year - span, iso_year + span
    w, wd = zodiac_to_iso(m_idx, d_m)
    lines = ['{| class="wikitable"', '! ISO year !! Gregorian date (weekday) !! ISO triple']
    for y in range(y0, y1+1):
        g = zodiac_gregorian_for_iso_year(m_idx, d_m, y)
        lines.append(f"|-\n| {y} || {g.isoformat()} ({WD_ABBR[g.isoweekday()]}) || {y}-W{w}-{wd}")
    lines.append("|}")
    return "\n".join(lines)

def gregorian_distribution_block(m_idx: int, d_m: int,
                                 start_iso_year: int = LONGRUN_START,
                                 end_iso_year: int   = LONGRUN_END) -> str:
    # Count how often this zodiac date lands on each Gregorian month-day
    counts = {}
    total = end_iso_year - start_iso_year + 1
    for y in range(start_iso_year, end_iso_year + 1):
        g = zodiac_gregorian_for_iso_year(m_idx, d_m, y)
        key = (g.month, g.day)
        counts[key] = counts.get(key, 0) + 1

    # Reverse index of fixed-date events: (month, day) -> [names]
    fixed_index = {}
    for name, (fm, fd) in FIXED_DATE_EVENTS.items():
        fixed_index.setdefault((fm, fd), []).append(name)

    # Build table
    lines = [
        '{| class="wikitable sortable"',
        '! Month-day !! Count !! Probability !! Fixed-date holidays'
    ]
    for (m, d) in sorted(counts.keys()):
        c = counts[(m, d)]
        names = fixed_index.get((m, d), [])
        holiday_cell = "<br/>".join(sorted(names)) if names else "—"
        lines.append(
            f"|-\n| {MONTH_NAMES[m-1]} {d} || {c} || {c/total:.2%} || {holiday_cell}"
        )
    lines.append("|}")
    return "\n".join(lines)


def nth_weekday_overlap_block(m_idx: int, d_m: int,
                              start_iso_year: int = LONGRUN_START, end_iso_year: int = LONGRUN_END) -> str:
    total = end_iso_year - start_iso_year + 1
    zd = {y: zodiac_gregorian_for_iso_year(m_idx, d_m, y) for y in range(start_iso_year, end_iso_year+1)}
    rules = set(); hits = {}
    for y in range(start_iso_year, end_iso_year+1):
        hol = nth_weekday_holidays_for_year(y)
        rules |= hol.keys()
        for name, d in hol.items():
            if d == zd[y]:
                hits[name] = hits.get(name, 0) + 1
    lines = ['{| class="wikitable sortable"', '! Holiday (rule) !! Matches !! Years !! Probability']
    for name in sorted(rules):
        c = hits.get(name, 0)
        lines.append(f"|-\n| {name} || {c} || {total} || {c/total:.2%}")
    lines.append("|}")
    return "\n".join(lines)

def ordinal(n: int) -> str:
    if 10 <= n % 100 <= 20: suf = "th"
    else: suf = {1:"st", 2:"nd", 3:"rd"}.get(n % 10, "th")
    return f"{n}{suf}"

def weekday_name_from_iso(wd: int) -> str:
    # ISO weekday: 1=Mon … 7=Sun
    return ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"][wd-1]

def build_description_block(m_idx: int, d_m: int) -> str:
    """Returns the short description block you want, with categories + DEFAULTSORT."""
    month_name = MONTHS[m_idx-1]
    iso_week, iso_wd = zodiac_to_iso(m_idx, d_m)          # 1..52, 1..7
    ord_year = ordinal_in_year(m_idx, d_m)                # 1..364
    weekday_name = weekday_name_from_iso(iso_wd)
    jp_informal = f"{m_idx}宮{d_m}日"

    lines = []
    lines.append(f"{month_name} {d_m} is the {ordinal(ord_year)} day of the year in the Gaiad calendar. "
                 f"It is the {ordinal(d_m)} day of {month_name}, and it is a {weekday_name}. "
                 f"It corresponds to ISO week {iso_week}, weekday {iso_wd}.")
    lines.append("")
    lines.append(f"Its informal Japanese name is {jp_informal}.")
    lines.append("")
    lines.append(f"On this day, [[Gaiad chapter {ord_year}|Chapter {ord_year}]] of the [[Gaiad]] is read.")
    lines.append("")
    lines.append(f"[[Category:Days with weekday {weekday_name}]]")
    lines.append(f"[[Category:Days {d_m} of the Gaiad calendar]]")
    lines.append(f"[[Category:Days of {month_name}]]")
    lines.append(f"{{{{DEFAULTSORT:{jp_informal}}}}}")
    return "\n".join(lines)


def easter_offsets_block(m_idx: int, d_m: int,
                         start_iso_year: int = LONGRUN_START, end_iso_year: int = LONGRUN_END) -> str:
    counts = {}; total = end_iso_year - start_iso_year + 1
    for y in range(start_iso_year, end_iso_year+1):
        z = zodiac_gregorian_for_iso_year(m_idx, d_m, y)
        e = easter_sunday_gregorian(y)
        off = (z - e).days
        counts[off] = counts.get(off, 0) + 1
    lines = ['{| class="wikitable sortable"', '! Offset (days vs Easter) !! Label !! Count !! Probability']
    for off in sorted(counts.keys()):
        label = EASTER_OFFSET_LABELS.get(off, "")
        c = counts[off]
        lines.append(f"|-\n| {off:+d} || {label} || {c} || {c/total:.2%}")
    lines.append("|}")
    return "\n".join(lines)

def ordinal(n: int) -> str:
    if 10 <= n % 100 <= 20: suf = "th"
    else: suf = {1:"st",2:"nd",3:"rd"}.get(n % 10, "th")
    return f"{n}{suf}"

# ---- FIXED-DATE EVENTS YOU CARE ABOUT ----
# name -> (month, day)
FIXED_DATE_EVENTS = {
    # Shinto / Japan (fixed)
    "Kinen-sai": (2, 17),
    "Nagoshi no Ōharai": (6, 30),                     # 大祓（夏越の祓）
    "Niiname-sai (新嘗祭)": (11, 23),
    "Kōrei-sai (皇霊祭)": (3, 21),
    "Shindensai (神殿祭)": (9, 21),
    # Golden Week (7-day run you specified)
    "Shōwa Day (Golden Week 1)": (4, 29),
    "Golden Week 2": (4, 30),
    "Golden Week 3 (May Day)": (5, 1),
    "Golden Week 4": (5, 2),
    "Constitution Memorial Day (Golden Week 5)": (5, 3),
    "Greenery Day (Golden Week 6)": (5, 4),
    "Children’s Day (Golden Week 7)": (5, 5),
    # Other JP fixed
    "Tanabata": (7, 7),
    "Shichi-Go-San": (11, 15),
    "Hinamatsuri": (3, 3),

    # North America (fixed)
    "Ides of March": (3, 15),
    "Bastille Day": (7, 14),
    "Guy Fawkes Night": (11, 5),
    "New Year’s Eve": (12, 31),
    "Valentine’s Day": (2, 14),
    "Groundhog Day": (2, 2),
    "St. Patrick’s Day": (3, 17),
    "Halloween": (10, 31),
    "Cinco de Mayo": (5, 5),
    "Remembrance Day": (11, 11),
    "Christmas Day": (12, 25),
    "Boxing Day": (12, 26),
    #Wiccan

    "Yule (Winter Solstice)": (12, 21),
    "Imbolc": (2, 1),
    "Ostara (Spring Equinox)": (3, 20),
    "Beltane": (5, 1),
    "Litha (Summer Solstice)": (6, 21),
    "Lughnasadh / Lammas": (8, 1),
    "Mabon (Autumn Equinox)": (9, 22),
    "Samhain": (10, 31)
}

def zodiac_possible_monthdays(m_idx: int, d_m: int,
                              start_iso_year: int = LONGRUN_START,
                              end_iso_year: int   = LONGRUN_END):
    """All Gregorian (month,day) this zodiac date can land on across the window."""
    s = set()
    for y in range(start_iso_year, end_iso_year+1):
        g = zodiac_gregorian_for_iso_year(m_idx, d_m, y)
        s.add((g.month, g.day))
    return s

def categories_for_fixed_dates(m_idx: int, d_m: int) -> list[str]:
    poss = zodiac_possible_monthdays(m_idx, d_m)
    cats = []
    for name, (m, d) in FIXED_DATE_EVENTS.items():
        if (m, d) in poss:
            cats.append(f"[[Category:Days that {name} falls on]]")
    return cats

def categories_for_nth_weekday(m_idx: int, d_m: int,
                               start_iso_year: int = LONGRUN_START,
                               end_iso_year: int   = LONGRUN_END) -> list[str]:
    """Add a category for each weekday-rule holiday that ever coincides."""
    # Your script already defines nth_weekday_holidays_for_year(year)
    hits = set()
    for y in range(start_iso_year, end_iso_year+1):
        z = zodiac_gregorian_for_iso_year(m_idx, d_m, y)
        for label, d in nth_weekday_holidays_for_year(y).items():
            if d == z:
                hits.add(label)
    return [f"[[Category:Days that {label} falls on]]" for label in sorted(hits)]

def categories_for_easter_offsets(m_idx: int, d_m: int,
                                  start_iso_year: int = LONGRUN_START,
                                  end_iso_year: int   = LONGRUN_END) -> list[str]:
    """Add a category for each named feast (in EASTER_OFFSET_LABELS) that ever coincides."""
    cats = []
    # build offset counts once (you already have a function, keeping it inline)
    seen_offsets = set()
    for y in range(start_iso_year, end_iso_year+1):
        z = zodiac_gregorian_for_iso_year(m_idx, d_m, y)
        e = easter_sunday_gregorian(y)
        off = (z - e).days
        seen_offsets.add(off)
    for off in sorted(seen_offsets):
        label = EASTER_OFFSET_LABELS.get(off)
        if label:
            cats.append(f"[[Category:Days that {label} falls on]]")
    return cats


def build_page(m_idx: int, d_m: int) -> (str, str):
    base = f"{MONTHS[m_idx-1]} {d_m}"
    title = f"{TITLE_PREFIX}{base}" if TITLE_PREFIX else base
    w, wd = zodiac_to_iso(m_idx, d_m)
    ord1 = ordinal_in_year(m_idx, d_m)
    reading = reading_for_ordinal(ord1)

    # neighbors
    pm, pd = (m_idx, d_m-1) if d_m>1 else ((13 if m_idx==1 else m_idx-1), 28)
    nm, nd = (m_idx, d_m+1) if d_m<28 else ((1 if m_idx==13 else m_idx+1), 1)
    prev_title = f"{MONTHS[pm-1]} {pd}"
    next_title = f"{MONTHS[nm-1]} {nd}"

    parts = []
    parts.append(build_description_block(m_idx, d_m))

    parts.append("\n== Recent (±5 ISO years) ==")
    parts.append(recent_block(m_idx, d_m, span=5))

    parts.append(f"\n== Long-run Gregorian distribution ({LONGRUN_START}–{LONGRUN_END}) ==")
    parts.append(gregorian_distribution_block(m_idx, d_m, LONGRUN_START, LONGRUN_END))

    parts.append("\n== Nth-weekday holidays (overlap probabilities) ==")
    parts.append(nth_weekday_overlap_block(m_idx, d_m, LONGRUN_START, LONGRUN_END))

    parts.append("\n== Easter-relative distribution ==")
    parts.append(easter_offsets_block(m_idx, d_m, LONGRUN_START, LONGRUN_END))

    parts.append("\n== Chinese calendar overlaps ==")
    parts.append(chinese_overlap_table(m_idx, d_m, LONGRUN_START, LONGRUN_END))

    parts.append("\n== Hebrew calendar overlaps ==")
    parts.append(hebrew_overlap_table(m_idx, d_m, LONGRUN_START, LONGRUN_END))


    parts.append("\n== See also ==")
    parts.append(f"* [[{prev_title}]]")
    parts.append(f"* [[{next_title}]]")
        # --- Auto-categories based on overlaps across the long-run window ---
    category_lines = []
    category_lines += categories_for_fixed_dates(m_idx, d_m)
    category_lines += categories_for_nth_weekday(m_idx, d_m)
    category_lines += categories_for_easter_offsets(m_idx, d_m)

    if category_lines:
        parts.append("\n".join(category_lines))
    parts.append("\n[[Category:Gaiad calendar days]]\n")
    parts.append("\n<!-- Generated by zodiac_push_all.py -->\n")
    return title, "\n".join(parts)

# ------------- Minimal MediaWiki client -------------

class Wiki:
    def __init__(self, api_url: str):
        self.api = api_url
        self.s = requests.Session()
        self.s.headers.update({"User-Agent": USER_AGENT})
        self.csrf = None

    def _check(self, r):
        try:
            r.raise_for_status()
        except requests.HTTPError:
            print("HTTP", r.status_code, r.url)
            print("Body:", r.text[:1000])
            raise

    def get(self, **params):
        params.setdefault("format", "json")
        r = self.s.get(self.api, params=params, timeout=60)
        self._check(r)
        return r.json()

    def post(self, **data):
        data.setdefault("format", "json")
        r = self.s.post(self.api, data=data, timeout=90)
        self._check(r)
        return r.json()

    def login_bot(self, username: str, password: str):
        t = self.get(action="query", meta="tokens", type="login")["query"]["tokens"]["logintoken"]
        j = self.post(action="login", lgname=username, lgpassword=password, lgtoken=t)
        if j.get("login", {}).get("result") != "Success":
            raise RuntimeError(f"Login failed: {j}")
        self.csrf = self.get(action="query", meta="tokens", type="csrf")["query"]["tokens"]["csrftoken"]

    def edit(self, title: str, text: str, summary: str):
        if not self.csrf:
            raise RuntimeError("Not logged in")
        j = self.post(
            action="edit",
            title=title,
            text=text,               # replaces content (create or overwrite)
            token=self.csrf,
            summary=summary,
            bot="1",
            minor="1",
        )
        if "error" in j:
            raise RuntimeError(f"Edit failed for {title}: {j['error']}")
        return j.get("edit", {}).get("result", "OK")

# ------------- Run all pages -------------

def main():
    wiki = Wiki(API_URL)
    wiki.login_bot(USERNAME, PASSWORD)

    targets = [(m_idx, d) for m_idx in range(1, 14) for d in range(1, 29)]  # all 13×28
    total = len(targets)
    ok = 0
    for i, (m_idx, d) in enumerate(targets, 1):
        title, text = build_page(m_idx, d)
        try:
            res = wiki.edit(title, text, SUMMARY)
            ok += 1
            print(f"[{i}/{total}] [{res}] {title}")
        except Exception as e:
            print(f"[{i}/{total}] [ERROR] {title} :: {e}")
        time.sleep(THROTTLE)

    print(f"Done. Success {ok}/{total}.")

if __name__ == "__main__":
    main()
