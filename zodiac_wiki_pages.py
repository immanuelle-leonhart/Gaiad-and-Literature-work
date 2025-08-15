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

CHINESE_DIST_START = 1900
CHINESE_DIST_END   = 2100




# Robust convertdate import (avoids local shadowing and only logs to console)
import os, sys, importlib

# Robust convertdate import (no user-facing noise; explicit submodule imports)
import os, sys, importlib

# ---- Calendar libs ----
import importlib

# Hebrew via convertdate (works on your install)
try:
    H = importlib.import_module("convertdate.hebrew")
    HAVE_HEBREW = True
except Exception as e:
    H = None
    HAVE_HEBREW = False
    print("hebrew: disabled ->", e)

# Chinese via lunardate (not part of convertdate)
try:
    LunarDate = importlib.import_module("lunardate").LunarDate
    HAVE_CHINESE = True
except Exception as e:
    LunarDate = None
    HAVE_CHINESE = False
    print("chinese: disabled ->", e)




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
    {"name": "Pesach (2nd Day)", "type": "hebrew", "month": "Nisan", "day": 16},
    {"name": "Pesach (3rd Day)", "type": "hebrew", "month": "Nisan", "day": 17},
    {"name": "Pesach (4th Day)", "type": "hebrew", "month": "Nisan", "day": 18},
    {"name": "Pesach (5th Day)", "type": "hebrew", "month": "Nisan", "day": 19},
    {"name": "Pesach (6th Day)", "type": "hebrew", "month": "Nisan", "day": 20},
    {"name": "Pesach (7th Day)", "type": "hebrew", "month": "Nisan", "day": 21},
    {"name": "Pesach (8th Day)", "type": "hebrew", "month": "Nisan", "day": 22},
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

# After: from lunardate import LunarDate  (and HAVE_CHINESE = True)
if HAVE_CHINESE:
    class _CShim:
        @staticmethod
        def from_gregorian(y, m, d):
            ld = LunarDate.fromSolarDate(y, m, d)
            leap = getattr(ld, "isLeapMonth", getattr(ld, "leap", False))
            # convertdate.chinese.from_gregorian returns (cycle, year, month, leap, day)
            return (None, ld.year, ld.month, bool(leap), ld.day)

        @staticmethod
        def to_gregorian(cycle, year, month, leap, day):
            g = LunarDate(year, month, day, leap).toSolarDate()
            # convertdate.chinese.to_gregorian returns (Y, M, D)
            return (g.year, g.month, g.day)

    C = _CShim


from datetime import date, timedelta

def _cn_from_greg(g: date):
    """Return (lyear, lmonth, lday, leap_flag) using lunardate."""
    ld = LunarDate.fromSolarDate(g.year, g.month, g.day)
    # some versions use .isLeapMonth, some .leap
    leap = getattr(ld, "isLeapMonth", getattr(ld, "leap", False))
    return ld.year, ld.month, ld.day, bool(leap)

def _cn_to_greg(lyear: int, lmonth: int, lday: int, is_leap: bool = False) -> date:
    return LunarDate(lyear, lmonth, lday, is_leap).toSolarDate()

def chinese_event_matches_gregorian(g: date, ev: dict):
    """True/False/None; None for unsupported (e.g., solar terms)."""
    t = ev["type"]
    if t == "lunar":
        lyear, lmonth, lday, leap = _cn_from_greg(g)
        want_m, want_d = ev["month"], ev["day"]
        if ev.get("leap") is not None:
            return (lmonth == want_m) and (lday == want_d) and (leap is bool(ev["leap"]))
        # default: only match non-leap months (public festivals are non-leap)
        return (lmonth == want_m) and (lday == want_d) and (not leap)

    if t == "relative":
        anch = ev["anchor"]
        if anch.get("type") != "lunar":
            return None
        lyear, _, _, _ = _cn_from_greg(g)              # same Chinese year as g
        anchor_g = _cn_to_greg(lyear, anch["month"], anch["day"], bool(anch.get("leap", False)))
        target_g = anchor_g + timedelta(days=int(ev.get("offset_days", 0)))
        return g == target_g

    if t == "solar_term":
        # Not implemented here (needs astronomical solar longitude).
        return None

    return None


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


# ---- Hebrew month labels with leap handling ----
HEB_NAMES = {
    1:"Nisan", 2:"Iyar", 3:"Sivan", 4:"Tammuz", 5:"Av", 6:"Elul",
    7:"Tishrei", 8:"Cheshvan", 9:"Kislev", 10:"Tevet", 11:"Shevat",
    # 12/13 depend on leap year
}

def hebrew_label_and_index(hy: int, hm: int) -> tuple[str, int]:
    """
    Return (display_label, sort_index) for the given Hebrew year+month.
    In leap years: 12=Adar I, 13=Adar II; otherwise 12=Adar.
    sort_index is ecclesiastical order: Nisan=1 ... Adar I/Adar=12 ... Adar II=13
    """
    if hm == 12:
        if H.leap(hy):
            return "Adar I", 12
        else:
            return "Adar", 12
    if hm == 13:
        return "Adar II", 13
    return HEB_NAMES[hm], hm

def hebrew_distribution_block(m_idx: int, d_m: int,
                              start_iso_year: int = LONGRUN_START,
                              end_iso_year: int   = LONGRUN_END) -> str:
    if not HAVE_HEBREW:
        return "<!-- Hebrew distribution skipped: convertdate.hebrew not available -->"

    from collections import Counter
    counts: Counter[tuple[int, str, int]] = Counter()  # (sort_idx, label, day)

    for y in range(start_iso_year, end_iso_year + 1):
        try:
            gdate = zodiac_gregorian_for_iso_year(m_idx, d_m, y)
        except ValueError:
            # Year doesn't have week 53, skip intercalary days
            continue
        try:
            hy, hm, hd = H.from_gregorian(gdate.year, gdate.month, gdate.day)
        except Exception:
            continue

        # label + stable sort index (Nisan=1 … Adar/Adar I=12 … Adar II=13)
        if hm == 12:
            label, idx = ("Adar I", 12) if H.leap(hy) else ("Adar", 12)
        elif hm == 13:
            label, idx = ("Adar II", 13)
        else:
            HEB_NAMES = {
                1:"Nisan", 2:"Iyar", 3:"Sivan", 4:"Tammuz", 5:"Av", 6:"Elul",
                7:"Tishrei", 8:"Cheshvan", 9:"Kislev", 10:"Tevet", 11:"Shevat"
            }
            label, idx = (HEB_NAMES[hm], hm)

        if 1 <= hd <= 30:
            counts[(idx, label, hd)] += 1

    total = sum(counts.values()) or 1  # denom = actually counted years

    lines = [
        '{| class="wikitable sortable"',
        f'! Hebrew month-day !! Count !! Probability'
    ]
    for (idx, label, hday) in sorted(counts.keys()):
        c = counts[(idx, label, hday)]
        lines.append(f"|-\n| {label} {hday} || {c} || {c/total:.2%}")
    lines.append("|}")
    lines.append(f"<small>Years tested: {total}</small>")
    return "\n".join(lines)



def chinese_distribution_block(m_idx: int, d_m: int,
                               start_year: int = CHINESE_DIST_START,
                               end_year: int   = CHINESE_DIST_END) -> str:
    """
    Returns a wikitable showing how often this zodiac day maps to each Chinese lunar (month, day),
    over a *fixed* range (default 1900–2100). We do not “probe” outside that range.
    Denominator = number of ISO years in that range where this zodiac day actually exists.
    """
    if not HAVE_CHINESE:
        return "<!-- Chinese calendar section skipped: lunardate not available -->"

    # Clamp to supported window explicitly; no out-of-range probing.
    sy = max(start_year, CHINESE_DIST_START)
    sy = 1900
    ey = min(end_year, CHINESE_DIST_END)

    from collections import Counter
    counts = Counter()
    years_considered = 0

    for y in range(sy, ey + 1):
        # Compute the Gregorian date for this zodiac day in ISO year y.
        try:
            g = zodiac_gregorian_for_iso_year(m_idx, d_m, y)
        except ValueError:
            # e.g., Horus day in a year without ISO week 53 -> this zodiac day does not occur in ISO year y.
            continue

        # Convert to Chinese lunar using lunardate
        l = LunarDate.fromSolarDate(g.year, g.month, g.day)
        # Different lunardate versions expose the leap flag slightly differently; cover both.
        leap = bool(getattr(l, "leap", getattr(l, "isLeapMonth", False)))
        counts[(leap, l.month, l.day)] += 1
        years_considered += 1

    if years_considered == 0:
        return f"== Chinese lunar date distribution ({sy}–{ey}) ==\n" \
               f"<!-- No occurrence of this zodiac day in the chosen range. -->"

    def label(leap_m_d: tuple[bool, int, int]) -> str:
        leap, m, d = leap_m_d
        return f"{'Leap ' if leap else ''}Month {m} {d}"

    lines = [f"== Chinese lunar date distribution ({sy}–{ey}) ==",
             '{| class="wikitable sortable"',
             '! Chinese lunar month-day !! Count !! Probability']
    for key in sorted(counts.keys(), key=lambda t: (t[0], t[1], t[2])):
        c = counts[key]
        lines.append(f"|-\n| {label(key)} || {c} || {c/years_considered:.2%}")
    lines.append("|}")
    lines.append(f"<small>Years considered: {years_considered} (out of {ey - sy + 1} in range; "
                 f"years where this zodiac day does not occur are excluded).</small>")
    return "\n".join(lines)




# --- helper: append a category tag inline with the label when there’s a hit ---
def label_with_category(name: str, hit_count: int) -> str:
    return f"{name} [[Category:Days that {name} falls on]]" if hit_count > 0 else name


def label_with_category(name: str, hit_count: int) -> str:
    return f"{name} [[Category:Days that {name} falls on]]" if hit_count > 0 else name

def chinese_overlap_table(m_idx: int, d_m: int,
                          start_iso_year: int = LONGRUN_START, end_iso_year: int = LONGRUN_END) -> str:
    if not HAVE_CHINESE:
        return "<!-- Chinese calendar section skipped: lunardate not available -->"

    total = end_iso_year - start_iso_year + 1
    rows = []
    for ev in CHINESE_EVENTS:
        matches = 0
        supported = True
        for y in range(start_iso_year, end_iso_year + 1):
            try:
                g = zodiac_gregorian_for_iso_year(m_idx, d_m, y)
            except ValueError:
                continue  # Year doesn't have week 53, skip intercalary days
            res = chinese_event_matches_gregorian(g, ev)
            if res is None:
                supported = False
                break
            if res:
                matches += 1
        prob = (matches / total) if supported else 0.0
        name = ev["name"] + ("" if supported else " (requires solar-term calc)")
        name_cell = label_with_category(name, matches) if supported else name
        rows.append((name_cell, matches if supported else 0, total if supported else total, prob))

    lines = ['{| class="wikitable sortable"', '! Event !! Matches !! Years !! Probability']
    for name_cell, c, t, p in rows:
        lines.append(f"|-\n| {name_cell} || {c} || {t} || {p:.2%}")
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
    if not HAVE_HEBREW:
        return ("''Hebrew calendar section requires `convertdate`. "
                "Install with `pip install convertdate`.''")

    total = end_iso_year - start_iso_year + 1
    rows = []
    for ev in HEBREW_EVENTS:
        matches = 0
        for y in range(start_iso_year, end_iso_year + 1):
            try:
                g = zodiac_gregorian_for_iso_year(m_idx, d_m, y)
            except ValueError:
                continue  # Year doesn't have week 53, skip intercalary days
            if hebrew_event_matches_gregorian(g, ev):     # your existing matcher
                matches += 1
        name_cell = label_with_category(ev["name"], matches)
        rows.append((name_cell, matches, total, matches/total))

    lines = ['{| class="wikitable sortable"', '! Event !! Matches !! Years !! Probability']
    for name_cell, c, t, p in rows:
        lines.append(f"|-\n| {name_cell} || {c} || {t} || {p:.2%}")
    lines.append("|}")
    return "\n".join(lines)




# ------------- Page generator (minimal but complete) -------------

MONTHS = [
    "Sagittarius","Capricorn","Aquarius","Pisces","Aries","Taurus",
    "Gemini","Cancer","Leo","Virgo","Libra","Scorpio","Ophiuchus","Horus"
]
MONTH_NAMES = ["January","February","March","April","May","June",
               "July","August","September","October","November","December"]
WD_ABBR = {1:"Mon",2:"Tue",3:"Wed",4:"Thu",5:"Fri",6:"Sat",7:"Sun"}

def zodiac_to_iso(m_idx: int, d_m: int):
    # Handle regular months (1-13)
    if 1 <= m_idx <= 13 and 1 <= d_m <= 28:
        iso_week  = (m_idx - 1) * 4 + ((d_m - 1) // 7) + 1      # 1..52
        iso_wday  = ((d_m - 1) % 7) + 1                         # 1..7 (Mon..Sun)
        return iso_week, iso_wday
    # Handle Horus intercalary days (month 14, days 1-7)
    elif m_idx == 14 and 1 <= d_m <= 7:
        iso_week = 53  # Symbolic week for intercalary days
        iso_wday = d_m  # Day 1-7 maps to Mon-Sun
        return iso_week, iso_wday
    else:
        raise ValueError("month_index 1..14 (1-13 regular, 14=Horus), day_of_month 1..28 (1-7 for Horus)")

def ordinal_in_year(m_idx: int, d_m: int) -> int:
    if m_idx == 14:  # Horus intercalary days
        return 364 + d_m  # Days 365-371
    w, wd = zodiac_to_iso(m_idx, d_m)
    return (w - 1) * 7 + wd  # 1..364

def zodiac_gregorian_for_iso_year(m_idx: int, d_m: int, iso_year: int) -> date:
    w, wd = zodiac_to_iso(m_idx, d_m)
    
    # For intercalary days (Horus), only return date for 53-week years
    if m_idx == 14:  # Horus intercalary days
        try:
            return date.fromisocalendar(iso_year, w, wd)
        except ValueError:
            # This year doesn't have week 53, so no intercalary days
            raise ValueError(f"Year {iso_year} has no week 53 (no intercalary days)")
    
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
    -35: "2nd Sunday in Lent",
    -28: "3rd Sunday in Lent",
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
    # For intercalary days (Horus), use a larger span since they're rarer
    if m_idx == 14:
        span = 25  # Use ±25 years for intercalary days
    
    iso_year = datetime.now().date().isocalendar()[0]
    y0, y1 = iso_year - span, iso_year + span
    w, wd = zodiac_to_iso(m_idx, d_m)
    lines = ['{| class="wikitable"', '! ISO year !! Gregorian date (weekday) !! ISO triple']
    for y in range(y0, y1+1):
        try:
            g = zodiac_gregorian_for_iso_year(m_idx, d_m, y)
        except ValueError:
            continue  # Year doesn't have week 53, skip intercalary days
        lines.append(f"|-\n| {y} || {g.isoformat()} ({WD_ABBR[g.isoweekday()]}) || {y}-W{w}-{wd}")
    lines.append("|}")
    return "\n".join(lines)

def gregorian_distribution_block(m_idx: int, d_m: int,
                                 start_iso_year: int = LONGRUN_START,
                                 end_iso_year: int   = LONGRUN_END) -> str:
    from collections import Counter
    counts = Counter()
    years_counted = 0

    for y in range(start_iso_year, end_iso_year + 1):
        try:
            g = zodiac_gregorian_for_iso_year(m_idx, d_m, y)
        except ValueError:
            # e.g., Horus day in a year without ISO week 53
            continue
        counts[(g.month, g.day)] += 1
        years_counted += 1

    total = sum(counts.values()) or 1  # denom = only years where this zodiac day exists

    lines = ['{| class="wikitable sortable"', '! Month-day !! Count !! Probability !! Fixed-date holidays']
    for (m, d) in sorted(counts.keys()):
        c = counts[(m, d)]
        fixed_col = "—"  # <--- If you have your own fixed-holiday label logic, use it here.
        lines.append(f"|-\n| {MONTH_NAMES[m-1]} {d} || {c} || {c/total:.2%} || {fixed_col}")
    lines.append("|}")
    lines.append(f"<small>Years counted in range {start_iso_year}–{end_iso_year}: {years_counted}</small>")
    return "\n".join(lines)



def nth_weekday_overlap_block(m_idx: int, d_m: int,
                              start_iso_year: int = LONGRUN_START,
                              end_iso_year: int   = LONGRUN_END) -> str:
    # Build map only for years where this zodiac day exists
    zd = {}
    for y in range(start_iso_year, end_iso_year + 1):
        try:
            zd[y] = zodiac_gregorian_for_iso_year(m_idx, d_m, y)
        except ValueError:
            continue  # skip non-occurrence years (e.g., no ISO week 53)

    denom_years = len(zd) or 1

    rules: set[str] = set()
    hits: dict[str, int] = {}

    for y in range(start_iso_year, end_iso_year + 1):
        if y not in zd:
            continue
        hol = nth_weekday_holidays_for_year(y)
        rules |= set(hol.keys())
        zy = zd[y]
        for name, d in hol.items():
            if d == zy:
                hits[name] = hits.get(name, 0) + 1

    lines = ['{| class="wikitable sortable"', '! Holiday (rule) !! Matches !! Years considered !! Probability']
    for name in sorted(rules):
        c = hits.get(name, 0)
        lines.append(f"|-\n| {name} || {c} || {denom_years} || {c/denom_years:.2%}")
    lines.append("|}")
    lines.append(f"<small>Years considered are only those where this zodiac day exists: "
                 f"{denom_years} of {end_iso_year - start_iso_year + 1}.</small>")
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
    iso_week, iso_wd = zodiac_to_iso(m_idx, d_m)          # 1..52, 1..7 (53 for intercalary)
    ord_year = ordinal_in_year(m_idx, d_m)                # 1..364 (365-371 for intercalary)
    weekday_name = weekday_name_from_iso(iso_wd)

    lines = []

    # ALWAYS include the month template first — no f-strings, no format()
    # If your 14th month is named "Horus" in templates but "Cetus" in MONTHS, map it here.
    TEMPLATE_NAME_MAP = {
        # "Cetus": "Horus",   # uncomment if MONTHS uses "Cetus" but your template is {{Horus}}
        # otherwise leave this dict empty
    }
    tpl = TEMPLATE_NAME_MAP.get(month_name, month_name)
    lines.append("{{" + tpl + "}}")

    if m_idx == 14:  # intercalary block (rename in text if you use Cetus/Horus differently)
        jp_informal = f"14宮{d_m}日"
        lines.append(
            f"{month_name} {d_m} is the {ordinal(ord_year)} day of the year in the [[Gaiad calendar]]. "
            f"It is an intercalary day, the {ordinal(d_m)} of the 7 days of {month_name}. "
            f"It falls on a {weekday_name} in intercalary week {iso_week}."
        )
    else:
        jp_informal = f"{m_idx}宮{d_m}日"
        lines.append(
            f"{month_name} {d_m} is the {ordinal(ord_year)} day of the year in the [[Gaiad calendar]]. "
            f"It is the {ordinal(d_m)} day of {month_name}, and it is a {weekday_name}. "
            f"It corresponds to ISO week {iso_week}, weekday {iso_wd}."
        )

    lines.append("")
    lines.append(f"Its informal Japanese name is {jp_informal}.")
    lines.append("")
    lines.append(f"On this day, [[Gaiad chapter {ord_year}|Chapter {ord_year}]] of the [[Gaiad]] is read.")
    lines.append("")
    lines.append(f"[[Category:Days with weekday {weekday_name}]]")
    lines.append(f"[[Category:Days {d_m} of the Gaiad calendar]]")
    lines.append(f"[[Category:Days of {month_name}]]")
    lines.append(f"{{{{DEFAULTSORT:{jp_informal}}}}}")  # ok to use doubled braces in f-string here

    return "\n".join(lines)



def easter_offsets_block(m_idx: int, d_m: int,
                         start_iso_year: int = LONGRUN_START, end_iso_year: int = LONGRUN_END) -> str:
    # Intercalary days (Horus) will only appear in 53-week years within the date range
    
    counts = {}; total = end_iso_year - start_iso_year + 1
    for y in range(start_iso_year, end_iso_year+1):
        try:
            z = zodiac_gregorian_for_iso_year(m_idx, d_m, y)
        except ValueError:
            continue  # Year doesn't have week 53, skip intercalary days
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
    "Samhain": (10, 31),

    #Chinese

    "Qingming Festival": (4, 5),   # Tomb-Sweeping Day
    "Dongzhi Festival": (12, 22)  # Winter Solstice

}

def zodiac_possible_monthdays(m_idx: int, d_m: int,
                              start_iso_year: int = LONGRUN_START,
                              end_iso_year: int   = LONGRUN_END):
    """All Gregorian (month,day) this zodiac date can land on across the window."""
    # Intercalary days (Horus) will only appear in 53-week years within the date range
    
    s = set()
    for y in range(start_iso_year, end_iso_year+1):
        try:
            g = zodiac_gregorian_for_iso_year(m_idx, d_m, y)
        except ValueError:
            continue  # Year doesn't have week 53, skip intercalary days
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
    # Intercalary days (Horus) will only appear in 53-week years within the date range
    
    # Your script already defines nth_weekday_holidays_for_year(year)
    hits = set()
    for y in range(start_iso_year, end_iso_year+1):
        try:
            z = zodiac_gregorian_for_iso_year(m_idx, d_m, y)
        except ValueError:
            continue  # Year doesn't have week 53, skip intercalary days
        for label, d in nth_weekday_holidays_for_year(y).items():
            if d == z:
                hits.add(label)
    return [f"[[Category:Days that {label} falls on]]" for label in sorted(hits)]

def categories_for_easter_offsets(m_idx: int, d_m: int,
                                  start_iso_year: int = LONGRUN_START,
                                  end_iso_year: int   = LONGRUN_END) -> list[str]:
    """Add a category for each named feast (in EASTER_OFFSET_LABELS) that ever coincides."""
    # Intercalary days (Horus) will only appear in 53-week years within the date range
    
    cats = []
    # build offset counts once (you already have a function, keeping it inline)
    seen_offsets = set()
    for y in range(start_iso_year, end_iso_year+1):
        try:
            z = zodiac_gregorian_for_iso_year(m_idx, d_m, y)
        except ValueError:
            continue  # Year doesn't have week 53, skip intercalary days
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
    parts.append("\n== Calculations ==")

    parts.append("\n=== Recent (±5 ISO years) ===")
    parts.append(recent_block(m_idx, d_m, span=5))

    parts.append(f"\n=== Long-run Gregorian distribution ({LONGRUN_START}–{LONGRUN_END}) ===")
    parts.append(gregorian_distribution_block(m_idx, d_m, LONGRUN_START, LONGRUN_END))

    parts.append("\n=== Nth-weekday holidays (overlap probabilities) ===")
    parts.append(nth_weekday_overlap_block(m_idx, d_m, LONGRUN_START, LONGRUN_END))

    parts.append("\n=== Easter-relative distribution ===")
    parts.append(easter_offsets_block(m_idx, d_m, LONGRUN_START, LONGRUN_END))

    parts.append("\n=== Chinese calendar overlaps ===")
    parts.append(chinese_overlap_table(m_idx, d_m, LONGRUN_START, LONGRUN_END))

    #parts.append(f"\n== Chinese lunar date distribution ({LONGRUN_START}–{LONGRUN_END}) ==")
    parts.append(chinese_distribution_block(m_idx, d_m, LONGRUN_START, LONGRUN_END))

    parts.append("\n=== Hebrew calendar overlaps ===")
    parts.append(hebrew_overlap_table(m_idx, d_m, LONGRUN_START, LONGRUN_END))

    parts.append(f"\n=== Hebrew date distribution ({LONGRUN_START}–{LONGRUN_END}) ===")
    parts.append(hebrew_distribution_block(m_idx, d_m, LONGRUN_START, LONGRUN_END))



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

    # Regular months: 13×28 = 364 days
    targets = [(m_idx, d) for m_idx in range(1, 14) for d in range(1, 29)]
    # Add Horus intercalary days: 7 days
    targets.extend([(14, d) for d in range(1, 8)])  # Horus 1-7
    
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

    print(f"Done. Success {ok}/{total}. (364 regular + 7 intercalary)")

if __name__ == "__main__":
    main()
