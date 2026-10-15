#!/usr/bin/env python3
"""
Generate a GitHub profile README in the "Kofun24" style:
  README.md, cards-languages.svg, cards-activity.svg, cards-timeline.svg

Usage:
  python generate.py <github-username> --name "Your Name" [--out ./out] [--theme aurora]
  GITHUB_TOKEN=xxx python generate.py ...   (optional, avoids API rate limits)

Only uses the Python standard library.
"""
import argparse, json, os, re, sys, urllib.request, urllib.parse
from collections import Counter
from datetime import date, datetime, timedelta

W = 860
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
SANS = "system-ui,-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif"
BG0, BG1, ACC1, ACC2 = "#0a0d13", "#1b212d", "#e2e8f0", "#94a3b8"

LANG_COLORS = {
    "Python": "#3572A5", "JavaScript": "#f1e05a", "TypeScript": "#3178c6", "Java": "#b07219",
    "C": "#555555", "C++": "#f34b7d", "C#": "#178600", "Go": "#00ADD8", "Rust": "#dea584",
    "PHP": "#4F5D95", "Ruby": "#701516", "Swift": "#F05138", "Kotlin": "#A97BFF", "Dart": "#00B4AB",
    "HTML": "#e34c26", "CSS": "#563d7c", "SCSS": "#c6538c", "Shell": "#89e051", "Vue": "#41b883",
    "Jupyter Notebook": "#DA5B0B", "TSQL": "#e2e8f0", "PLpgSQL": "#336790", "R": "#198CE7",
    "Lua": "#000080", "Dockerfile": "#384d54", "MATLAB": "#e16737", "Svelte": "#ff3e00",
}

def esc(s): return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))

def http(url, accept=None):
    h = {"User-Agent": "profile-generator"}
    if accept: h["Accept"] = accept
    tok = os.environ.get("GITHUB_TOKEN")
    if tok and "api.github.com" in url: h["Authorization"] = f"Bearer {tok}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=30) as r:
        return r.read().decode("utf-8", "replace")

# ---------------------------------------------------------------- data
def fetch_user(u):
    return json.loads(http(f"https://api.github.com/users/{u}"))

def fetch_repos(u):
    out, page = [], 1
    while True:
        batch = json.loads(http(f"https://api.github.com/users/{u}/repos?per_page=100&page={page}&type=owner"))
        out += batch
        if len(batch) < 100: break
        page += 1
    return [r for r in out if not r.get("fork")]

def fetch_contribs(u, days=90):
    """Scrape the public contribution graph; returns {date: (count, level)}."""
    html = http(f"https://github.com/users/{u}/contributions")
    cells = re.findall(r'<td[^>]*data-date="(\d{4}-\d\d-\d\d)"[^>]*?id="([^"]+)"[^>]*?data-level="(\d)"', html)
    if not cells:  # attribute order differs
        cells = [(m[0], m[2], m[1]) for m in
                 re.findall(r'<td[^>]*data-date="(\d{4}-\d\d-\d\d)"[^>]*data-level="(\d)"[^>]*id="([^"]+)"', html)]
        cells = [(d, i, l) for d, l, i in cells]
    tips = {i: t for i, t in re.findall(r'<tool-tip[^>]*for="([^"]+)"[^>]*>([^<]*)</tool-tip>', html)}
    res = {}
    for d, i, lvl in cells:
        t = tips.get(i, "")
        m = re.match(r"(\d+) contribution", t)
        res[d] = (int(m.group(1)) if m else 0, int(lvl))
    return res

# ---------------------------------------------------------------- shared frame
def frame(h, label, right, body):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}" role="img" aria-label="{esc(label)}"><defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{BG0}"/><stop offset="1" stop-color="{BG1}"/></linearGradient><radialGradient id="au1"><stop offset="0" stop-color="{ACC1}" stop-opacity="0.42"/><stop offset="1" stop-color="{ACC1}" stop-opacity="0"/></radialGradient><radialGradient id="au2"><stop offset="0" stop-color="{ACC2}" stop-opacity="0.4"/><stop offset="1" stop-color="{ACC2}" stop-opacity="0"/></radialGradient><linearGradient id="edge" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#fff" stop-opacity="0.42"/><stop offset="0.45" stop-color="#fff" stop-opacity="0.07"/><stop offset="1" stop-color="{ACC2}" stop-opacity="0.55"/></linearGradient><linearGradient id="hl" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset="0.5" stop-color="#fff" stop-opacity="0.6"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient><linearGradient id="fade" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{ACC1}" stop-opacity="0.6"/><stop offset="1" stop-color="{ACC1}" stop-opacity="0"/></linearGradient><filter id="glow" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="2.6" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter><pattern id="grid" width="24" height="24" patternUnits="userSpaceOnUse"><path d="M24 0H0V24" fill="none" stroke="#fff" stroke-opacity="0.04"/></pattern><clipPath id="clip"><rect width="{W}" height="{h}" rx="18"/></clipPath></defs><style>@keyframes fxd1{{0%,100%{{transform:translate(0,0)}}50%{{transform:translate(-34px,20px)}}}}@keyframes fxd2{{0%,100%{{transform:translate(0,0)}}50%{{transform:translate(36px,-18px)}}}}@keyframes fxpulse{{0%,100%{{opacity:1}}50%{{opacity:.3}}}}@keyframes fxshine{{from{{transform:translateX(-344px)}}to{{transform:translateX({W}px)}}}}.fx-d1{{animation:fxd1 18s ease-in-out infinite}}.fx-d2{{animation:fxd2 22s ease-in-out infinite}}.fx-pulse{{animation:fxpulse 2.8s ease-in-out infinite}}.fx-shine{{animation:fxshine 9s ease-in-out infinite}}@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}</style><g clip-path="url(#clip)"><rect width="{W}" height="{h}" fill="url(#bg)"/><rect width="{W}" height="{h}" fill="url(#grid)"/><g class="fx-d1"><circle cx="791" cy="-32" r="516" fill="url(#au1)"/></g><g class="fx-d2"><circle cx="34" cy="{h+32}" r="473" fill="url(#au2)"/></g><rect width="{W}" height="{h}" fill="#fff" fill-opacity="0.035"/><rect x="28" y="0.6" width="804" height="1.2" fill="url(#hl)"/><rect x="0" y="0.5" width="241" height="1.6" fill="url(#hl)" class="fx-shine"/></g><rect x="0.75" y="0.75" width="{W-1.5}" height="{h-1.5}" rx="17.5" fill="none" stroke="url(#edge)" stroke-width="1.5"/><g><circle cx="32" cy="34" r="3.5" fill="{ACC1}" filter="url(#glow)" class="fx-pulse"/><text x="44" y="39" font-family="{MONO}" font-size="13" letter-spacing="3" font-weight="600" fill="{ACC1}">{esc(label.upper().split(" ")[0])}</text><text x="832" y="39" text-anchor="end" font-family="{MONO}" font-size="11.5" letter-spacing="1.5" fill="#fff" fill-opacity="0.5">{esc(right)}</text><rect x="28" y="51" width="804" height="1" fill="url(#fade)"/>{body}</g></svg>'''

# ---------------------------------------------------------------- cards
def card_languages(user, repos):
    c = Counter(r["language"] for r in repos if r.get("language"))
    top = c.most_common(3)
    total = sum(n for _, n in top) or 1
    fallback = [ACC1, ACC2, "#64748b"]
    cols = [LANG_COLORS.get(l, fallback[i]) for i, (l, _) in enumerate(top)]
    pcts = [round(100 * n / total) for _, n in top]
    bar, x = "", 28.0
    for (l, n), col in zip(top, cols):
        w = 804 * n / total
        bar += f'<rect x="{x:.1f}" y="76" width="{w:.1f}" height="12" fill="{col}" stroke="{BG0}" stroke-width="2"/>'
        x += w
    legend = ""
    for i, ((l, n), col, p) in enumerate(zip(top, cols, pcts)):
        ox = 28 + i * 268
        legend += (f'<circle cx="{ox+6}" cy="122" r="5.5" fill="{col}" filter="url(#glow)"/>'
                   f'<text x="{ox+22}" y="128" font-family="{SANS}" font-size="17" font-weight="600" fill="#fff">{esc(l)}</text>'
                   f'<text x="{ox+244}" y="128" text-anchor="end" font-family="{MONO}" font-size="15" fill="#fff" fill-opacity="0.62">{p}%</text>')
    body = (f'<defs><clipPath id="bar"><rect x="28" y="76" width="804" height="12" rx="6"/></clipPath>'
            f'<linearGradient id="gloss" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity="0.45"/><stop offset="0.6" stop-color="#fff" stop-opacity="0"/></linearGradient></defs>'
            f'<g filter="url(#glow)"><g clip-path="url(#bar)">{bar}</g></g>'
            f'<rect x="28" y="76" width="804" height="12" rx="6" fill="url(#gloss)"/>{legend}')
    return frame(178, f"Languages and tools for {user}", "BY NUMBER OF REPOS", body)

def card_activity(user, contribs):
    today = date.today()
    start = today - timedelta(days=89)
    start -= timedelta(days=(start.weekday() + 1) % 7)  # back to Sunday
    cell, pitch, x0, y0 = 22, 26, 64, 86
    days, d = [], start
    while d <= today:
        days.append(d); d += timedelta(days=1)
    opac = {0: 0.075, 1: 0.3, 2: 0.5, 3: 0.75, 4: 1}
    cols, months = {}, []
    for d in days:
        wk = (d - start).days // 7
        cols.setdefault(wk, []).append(d)
    grid = ""
    for wk, ds in cols.items():
        x = x0 + wk * pitch
        grid += "<g>"
        for d in ds:
            cnt, lvl = contribs.get(d.isoformat(), (0, 0))
            row = (d.weekday() + 1) % 7
            fill = f'#fff" fill-opacity="{opac[0]}' if lvl == 0 else f'{ACC1}" fill-opacity="{opac[lvl]}'
            grid += f'<rect x="{x}.0" y="{y0 + row * pitch}.0" width="{cell}.0" height="{cell}.0" rx="5" fill="{fill}"/>'
        grid += "</g>"
        if ds[0].day <= 7 and (not months or months[-1][1] != ds[0].month):
            months.append((x, ds[0].month, ds[0].strftime("%b")))
    mlab = "".join(f'<text x="{x}.0" y="74" font-family="{MONO}" font-size="11" fill="#fff" fill-opacity="0.55">{n}</text>' for x, _, n in months)
    dlab = "".join(f'<text x="28" y="{y0 + r * pitch + 15}" font-family="{MONO}" font-size="11" fill="#fff" fill-opacity="0.45">{t}</text>'
                   for r, t in ((1, "Mon"), (3, "Wed"), (5, "Fri")))
    window = [(k, v[0]) for k, v in contribs.items() if start.isoformat() <= k <= today.isoformat()]
    last90 = [(k, c) for k, c in window if k >= (today - timedelta(days=89)).isoformat()]
    total = sum(c for _, c in last90)
    best = max(last90, key=lambda t: t[1], default=("", 0))
    if best[1]:
        bd = datetime.strptime(best[0], "%Y-%m-%d")
        best_lbl = f"{bd.strftime('%b')} {bd.day}"
    else:
        best_lbl = "—"
    avg = f"{total / 90:.1f}"
    legend = f'<text x="64" y="291" font-family="{MONO}" font-size="11" fill="#fff" fill-opacity="0.5">Less</text>'
    for i, o in enumerate([0.075, 0.3, 0.5, 0.75, 1]):
        f = f'#fff" fill-opacity="{o}' if i == 0 else f'{ACC1}" fill-opacity="{o}'
        legend += f'<rect x="{96 + i*18}" y="280" width="13" height="13" rx="3" fill="{f}"/>'
    legend += f'<text x="190" y="291" font-family="{MONO}" font-size="11" fill="#fff" fill-opacity="0.5">More</text>'
    def stat(y, big, small):
        return (f'<text x="494" y="{y}" font-family="{SANS}" font-size="32" font-weight="700" letter-spacing="-0.5" fill="#fff">{big}</text>'
                f'<text x="494" y="{y+22}" font-family="{SANS}" font-size="14" fill="#fff" fill-opacity="0.62">{esc(small)}</text>')
    body = (mlab + dlab + grid + legend + stat(110, total, "Contributions") + stat(170, best[1], f"Best day · {best_lbl}")
            + stat(230, avg, "Daily average") + '<rect x="468" y="82" width="1" height="186" fill="#fff" fill-opacity="0.08"/>')
    return frame(318, f"Contribution heatmap for {user}", "LAST 90 DAYS", body)

def card_timeline(user, joined, repos):
    pts = [("Joined GitHub", joined, ACC1, None)]
    rs = sorted(repos, key=lambda r: r["created_at"])[:8]
    for r in rs:
        pts.append((r["name"], datetime.strptime(r["created_at"][:10], "%Y-%m-%d"),
                    LANG_COLORS.get(r.get("language"), ACC2), r))
    n = len(pts)
    xs = [100 + i * (660 / max(n - 1, 1)) for i in range(n)]
    y = 162
    first, last = pts[0][1].year, pts[-1][1].year
    rng = f"{first} – {last}" if first != last else str(first)
    g = (f'<line x1="76" y1="{y}" x2="784" y2="{y}" stroke="#fff" stroke-opacity="0.08" stroke-width="6" stroke-linecap="round"/>'
         f'<defs><linearGradient id="tl" gradientUnits="userSpaceOnUse" x1="100" y1="{y}" x2="760" y2="{y}"><stop offset="0" stop-color="{ACC1}"/><stop offset="1" stop-color="{ACC2}"/></linearGradient></defs>'
         f'<line x1="100" y1="{y}" x2="760" y2="{y}" stroke="url(#tl)" stroke-opacity="0.28" stroke-width="9" stroke-linecap="round"/>'
         f'<line x1="100" y1="{y}" x2="760" y2="{y}" stroke="url(#tl)" stroke-width="2.5" stroke-linecap="round"/>')
    for i, ((name, dt, col, _), x) in enumerate(zip(pts, xs)):
        up = i % 2 == 0
        label = name if len(name) <= 13 else name[:12] + "…"
        dtxt = str(dt.year) if i == 0 else dt.strftime("%b %Y")
        big = i == 0
        r1, r2 = (16, 8) if big else (13, 6)
        ty, dy = (98, 119) if up else (220, 241)
        l1, l2 = (128, 149) if up else (175, 196)
        g += f'<line x1="{x:.1f}" y1="{l1}" x2="{x:.1f}" y2="{l2}" stroke="{col}" stroke-opacity="0.45" stroke-dasharray="2 3"/>'
        g += f'<circle cx="{x:.1f}" cy="{y}" r="{r1}" fill="{col}" fill-opacity="0.16"/>'
        g += f'<circle cx="{x:.1f}" cy="{y}" r="{r2}" fill="{col}" stroke="{BG0}" stroke-width="2.5" filter="url(#glow)"/>'
        if big: g += f'<circle cx="{x:.1f}" cy="{y}" r="2.8" fill="{BG0}"/>'
        g += (f'<text x="{x:.1f}" y="{ty}" text-anchor="middle" font-family="{SANS}" font-size="16" font-weight="700" fill="#fff">{esc(label)}</text>'
              f'<text x="{x:.1f}" y="{dy}" text-anchor="middle" font-family="{MONO}" font-size="13" fill="#fff" fill-opacity="0.6">{dtxt}</text>')
    return frame(269, f"Timeline of repositories created by {user}", rng, g)

# ---------------------------------------------------------------- README
def readme(user, name, avatar, theme):
    av = urllib.parse.quote(avatar, safe="")
    nm = urllib.parse.quote(name)
    base = (f"https://www.gitskins.com/api/section/hero?username={user.lower()}&theme={theme}&avatar={av}"
            f"&variant=living-identity&label={nm}&v=wow-living-identity-1")
    def card(f, alt): return f'<div align="center">\n\n<img\n  src="./{f}"\n  alt="{alt}"\n  width="100%"\n/>\n\n</div>\n\n<br>\n'
    return f'''<!-- ================= HERO SECTION ================= -->

<div align="center">

<picture>
  <source
    media="(prefers-color-scheme: light)"
    srcset="{base}&mode=light"
  />
  <img
    src="{base}&mode=dark"
    width="100%"
    alt="{name} Living Identity Banner"
  />
</picture>

<br>

<sub>BUILD • LEARN • CREATE</sub>

</div>

<br>

---

<!-- ================= LANGUAGES ================= -->

{card("cards-languages.svg", "Programming languages and technologies")}
<!-- ================= ACTIVITY ================= -->

{card("cards-activity.svg", "GitHub contribution activity")}
<!-- ================= TIMELINE ================= -->

{card("cards-timeline.svg", "GitHub repository development timeline")}
---

<!-- ================= FOOTER ================= -->

<div align="center">

<sub>✦ BUILDING IDEAS INTO REALITY ✦</sub>

</div>
'''

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("username")
    ap.add_argument("--name", help="Display name for the hero banner")
    ap.add_argument("--out", default="./out")
    ap.add_argument("--theme", default="aurora")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    user = fetch_user(a.username)
    login = user["login"]
    repos = fetch_repos(login)
    try: contribs = fetch_contribs(login)
    except Exception as e:
        print("! could not read contribution graph:", e, file=sys.stderr); contribs = {}
    joined = datetime.strptime(user["created_at"][:10], "%Y-%m-%d")

    files = {
        "cards-languages.svg": card_languages(login, repos),
        "cards-activity.svg": card_activity(login, contribs),
        "cards-timeline.svg": card_timeline(login, joined, repos),
        "README.md": readme(login, a.name or user.get("name") or login, user["avatar_url"], a.theme),
    }
    for f, c in files.items():
        with open(os.path.join(a.out, f), "w", encoding="utf-8") as fh: fh.write(c)
    print(f"Wrote {len(files)} files to {a.out} for {login} ({len(repos)} repos)")

if __name__ == "__main__":
    main()