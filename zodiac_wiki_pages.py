# zodiac_push_all.py
# Hard-coded bot that creates/overwrites ALL 13×28 pages on shinto.miraheze.org

import time
from datetime import date, datetime, timedelta
import requests

API_URL     = "https://evolutionism.miraheze.org/w/api.php"
USERNAME    = "Immanuelle"      # <-- BotPassword username (User@BotName)
PASSWORD    = "1996ToOmega!"    # <-- BotPassword password (long random string)
USER_AGENT  = "ZodiacWikiBot/0.2 (User:Immanuelle; contact: you@example.com)"
SUMMARY     = "Create/update zodiac date page"
THROTTLE    = 0.6      # seconds between edits (be polite to the wiki)
TITLE_PREFIX = ""      # e.g., "Calendar:" if you want them in a namespace
LONGRUN_START = 1582   # per your spec
LONGRUN_END   = 2582

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
    d = date(year, month, 1)
    delta = (weekday_mon0 - d.weekday()) % 7
    first = d + timedelta(days=delta)
    return first + timedelta(weeks=n-1)

def nth_weekday_holidays_for_year(year: int):
    return {
        "U.S. Thanksgiving (4th Thu Nov)": nth_weekday_of_month(year, 11, weekday_mon0=3, n=4),
    }

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
    -46: "Ash Wednesday",
    -7 : "Palm Sunday",
    -3 : "Maundy Thursday",
    -2 : "Good Friday",
    -1 : "Holy Saturday",
     0 : "Easter Sunday",
    +39: "Ascension Thursday",
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
                                 start_iso_year: int = LONGRUN_START, end_iso_year: int = LONGRUN_END) -> str:
    counts = {}
    total = end_iso_year - start_iso_year + 1
    for y in range(start_iso_year, end_iso_year+1):
        g = zodiac_gregorian_for_iso_year(m_idx, d_m, y)
        key = (g.month, g.day)
        counts[key] = counts.get(key, 0) + 1
    lines = ['{| class="wikitable sortable"', '! Month-day !! Count !! Probability']
    for (m, d) in sorted(counts.keys()):
        c = counts[(m, d)]
        lines.append(f"|-\n| {MONTH_NAMES[m-1]} {d} || {c} || {c/total:.2%}")
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
    parts.append("{{Short description|Date in the 13×28 ISO-anchored zodiac calendar}}")
    parts.append(f"{{DISPLAYTITLE:{base}}}\n")
    parts.append(
        f"'''{base}''' is the '''{ordinal(ord1)}''' day of the year in the 13×28 zodiac calendar "
        f"(months: Sagittarius → … → Scorpio → Ophiuchus). "
        f"It corresponds to ISO week '''{w}''', weekday '''{wd}''' (1=Mon … 7=Sun). "
        f"On this day, {reading} is read."
    )

    parts.append("\n== Recent (±5 ISO years) ==")
    parts.append(recent_block(m_idx, d_m, span=5))

    parts.append(f"\n== Long-run Gregorian distribution ({LONGRUN_START}–{LONGRUN_END}) ==")
    parts.append(gregorian_distribution_block(m_idx, d_m, LONGRUN_START, LONGRUN_END))

    parts.append("\n== Nth-weekday holidays (overlap probabilities) ==")
    parts.append(nth_weekday_overlap_block(m_idx, d_m, LONGRUN_START, LONGRUN_END))

    parts.append("\n== Easter-relative distribution ==")
    parts.append(easter_offsets_block(m_idx, d_m, LONGRUN_START, LONGRUN_END))

    parts.append("\n== See also ==")
    parts.append(f"* [[{prev_title}]]")
    parts.append(f"* [[{next_title}]]")
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
