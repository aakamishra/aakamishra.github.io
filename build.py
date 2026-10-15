"""Build the static site from data/*.json.

Usage: python3 build.py
Then preview with: python3 -m http.server 8000
"""

import json
from datetime import date
from html import escape
from pathlib import Path

ROOT = Path(__file__).parent
SITE_URL = "https://aakamishra.github.io"
ME = "Aakash Mishra"
TAGS = {
    "medical": "Medical AI",
    "systems": "Systems & optimization",
    "control": "Robotics & RL",
    "science": "Science",
}
SELECTED = [
    "ad-load-personalization",
    "semantic-caching-llm-scheduling",
    "zero-shot-cxr",
    "active-centaurs-photometry",
]
NAV = [
    ("research", "/research.html", "Research"),
    ("experience", "/experience.html", "Experience"),
    ("projects", "/projects.html", "Projects"),
    ("hobbies", "/hobbies.html", "Hobbies"),
]
THREE = (
    '<script type="importmap">{"imports": {'
    '"three": "https://cdn.jsdelivr.net/npm/three@0.160.0/build/'
    'three.module.js", "three/addons/": "https://cdn.jsdelivr.net/npm/'
    'three@0.160.0/examples/jsm/"}}</script>'
)
FONTS = (
    "https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600"
    "&display=swap"
)

site = json.loads((ROOT / "data/site.json").read_text())
papers = json.loads((ROOT / "data/papers.json").read_text())
papers.sort(key=lambda p: p["date"], reverse=True)
by_slug = {p["slug"]: p for p in papers}


def fmt_date(iso: str) -> str:
    d = date.fromisoformat(iso)
    if iso.endswith("-01-01"):
        return str(d.year)
    if iso.endswith("-01"):
        return d.strftime("%b %Y")
    return d.strftime("%b %-d, %Y")


def authors(names: list[str]) -> str:
    return ", ".join(
        f"<b>{escape(n)}</b>" if n == ME else escape(n) for n in names
    )


def media(p: dict, img_class: str = "") -> str:
    m = p.get("media")
    if not m:
        return ""
    cls = "cover" if m.get("fit") == "cover" else img_class
    return (f'<img src="{m["src"]}" alt="{escape(m["alt"])}" '
            f'class="{cls}" loading="lazy">')


def is_dark(p: dict) -> bool:
    return p.get("media", {}).get("src", "").endswith(".gif")


def link_pills(links: list[dict]) -> str:
    out = []
    for ln in links:
        ext = ln["url"].startswith("http")
        tgt = ' target="_blank" rel="noopener"' if ext else ""
        out.append(f'<a href="{escape(ln["url"])}"{tgt}>'
                   f'{escape(ln["label"])}</a>')
    return "".join(out)


def bibtex(p: dict) -> str:
    b = dict(p["bib"])
    kind, key = b.pop("type"), b.pop("key")
    fields = {
        "title": p["title"],
        "author": " and ".join(p["authors"]),
        "year": p["date"][:4],
        **b,
    }
    if "eprint" in fields:
        fields["archivePrefix"] = "arXiv"
    body = ",\n".join(f"  {k} = {{{v}}}" for k, v in fields.items())
    return f"@{kind}{{{key},\n{body}\n}}"


def page(path: str, title: str, desc: str, body: str, active: str = "",
         night: bool = False, head: str = "", scripts: str = "",
         og_image: str = "/images/me/profile.jpg") -> None:
    current = ' aria-current="page"'
    nav = "".join(
        f'<li><a href="{href}"{current if key == active else ""}>'
        f"{label}</a></li>"
        for key, href, label in NAV
    )
    social = "".join(
        f'<a href="{s["url"]}" target="_blank" rel="noopener">'
        f'{s["label"]}</a>' for s in site["social"]
    )
    full_title = ME if not title else f"{title} · {ME}"
    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(full_title)}</title>
<meta name="description" content="{escape(desc)}">
<meta property="og:title" content="{escape(full_title)}">
<meta property="og:description" content="{escape(desc)}">
<meta property="og:image" content="{SITE_URL}{og_image}">
<meta property="og:url" content="{SITE_URL}/{path}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/images/icons/favicon-32x32.png">
<link rel="apple-touch-icon" href="/images/icons/apple-icon-180x180.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}">
<link rel="stylesheet" href="/assets/site.css">
{head}
</head>
<body{' class="night"' if night else ''}>
<nav class="nav{' night' if night else ''}"><div class="wrap">
<a class="brand" href="/"><i></i>{ME}</a>
<ul>{nav}</ul>
</div></nav>
<main>
{body}
</main>
<footer class="site"><div class="wrap">
<div><a class="mail link" href="mailto:{site["email"]}">{site["email"]}</a>
<small>© {date.today().year} {ME}</small></div>
<div class="links">{social}</div>
</div></footer>
<script src="/assets/site.js" defer></script>
{scripts}
</body>
</html>
"""
    out = ROOT / path
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html)


def paper_card(p: dict) -> str:
    dark = "dark" if is_dark(p) else ""
    return f"""<a class="paper-card" href="/papers/{p["slug"]}.html">
<div class="media {dark}">{media(p, "contain")}</div>
<div class="body">
<span class="meta">{fmt_date(p["date"])} · {escape(p["venue"])}</span>
<h4>{escape(p["title"])}</h4>
<span class="sub">{escape(p.get("subtitle", p["summary"]))}</span>
</div></a>"""


def row(p: dict) -> str:
    return f"""<a class="row" href="/papers/{p["slug"]}.html">
<div class="media">{media(p, "contain")}</div>
<div><span class="meta">{fmt_date(p["date"])} · {escape(p["venue"])}</span>
<h4>{escape(p["title"])}</h4></div></a>"""


def build_home() -> None:
    eps = site["epsilon"]
    eps_cards = "".join(paper_card(p) for p in papers if p.get("epsilon"))
    selected = "".join(row(by_slug[s]) for s in SELECTED)
    jobs = "".join(
        f'<li><span class="who"><img class="logo sm" src="{j["logo"]}" alt="">'
        f'{escape(j["org"])}, {escape(j["role"])}</span>'
        f'<span>{escape(j["when"])}</span></li>'
        for j in site["work"][:3]
    )
    edu = "".join(
        f'<div><h3>{escape(e["school"])}</h3>'
        f'<span class="deg">{escape(e["degree"])}</span>'
        f'<span class="when">{escape(e["when"])}</span>'
        f'<ul>{"".join(f"<li>{escape(n)}</li>" for n in e["notes"])}</ul>'
        f"</div>"
        for e in site["education"]
    )
    honors = "".join(
        f'<li>{escape(h["what"])}<span>{escape(h["when"])}</span></li>'
        for h in site["honors"]
    )
    body = f"""
<header class="hero">
<canvas class="scene" aria-hidden="true"></canvas>
<div class="wrap">
<div>
<h1>{ME}</h1>
<p class="lede">{escape(site["bio"])}</p>
</div>
<div class="portrait"><div class="card">
<img src="/images/me/profile.jpg" alt="Aakash smiling at a counter with a mug of hot chocolate">
</div></div>
</div>
</header>

<section class="block wrap" id="epsilon">
<div class="eps">
<div class="top">
<div><h3>Epsilon Health</h3>
<p>{escape(eps["blurb"])}</p></div>
</div>
<div class="eps-cards">{eps_cards}</div>
</div>
</section>

<section class="block wrap">
<div class="block-head">
<h2>Papers and reports</h2>
<a class="more" href="/research.html">All {len(papers)} papers</a>
</div>
<div class="rows">{selected}</div>
</section>

<section class="block wrap" id="education">
<div class="block-head">
<h2>Education, work and honors</h2>
<a class="more" href="/experience.html">All roles</a>
</div>
<div class="two">
<div class="panel"><div class="edu">{edu}</div></div>
<div class="panel" style="display:flex;flex-direction:column;gap:28px">
<div><h3>Recent roles</h3><ul class="honors">{jobs}</ul></div>
<div><h3>Honors</h3><ul class="honors">{honors}</ul></div>
</div>
</div>
</section>
"""
    page("index.html", "", site["bio"], body, scripts=(
        f'{THREE}<script type="module" src="/assets/galaxy.js"></script>'))


def build_research() -> None:
    btns = '<button type="button" data-tag="all" aria-pressed="true">All</button>'
    btns += "".join(
        f'<button type="button" data-tag="{k}" aria-pressed="false">'
        f"{v}</button>" for k, v in TAGS.items()
    )
    items = []
    for p in papers:
        dark = " dark" if is_dark(p) else ""
        fig = (f'<a class="media{dark}" href="/papers/{p["slug"]}.html" '
               f'tabindex="-1">{media(p)}</a>' if p.get("media") else "")
        items.append(f"""<article class="pub" data-tags="{' '.join(p["tags"])}">
{fig}
<div>
<div class="meta"><span>{fmt_date(p["date"])}</span><span>{escape(p["venue"])}</span>
<span>{" · ".join(TAGS[t] for t in p["tags"])}</span></div>
<h3><a href="/papers/{p["slug"]}.html">{escape(p["title"])}</a></h3>
<p class="summary">{escape(p["summary"])}</p>
<p class="authors">{authors(p["authors"])}</p>
<div class="pills"><a href="/papers/{p["slug"]}.html">Preview</a>{link_pills(p["links"])}</div>
</div></article>""")
    body = f"""
<header class="page-head wrap">
<h1>Research</h1>
</header>
<section class="wrap">
<div class="filters" role="group" aria-label="Filter by topic">{btns}</div>
<div class="pubs">{"".join(items)}</div>
</section>"""
    page("research.html", "Research",
         "Papers, posts and reports by Aakash Mishra.", body, "research")


def build_papers() -> None:
    for i, p in enumerate(papers):
        newer = papers[i - 1] if i > 0 else None
        older = papers[i + 1] if i + 1 < len(papers) else None
        nxt = ""
        if newer:
            nxt += (f'<a href="/papers/{newer["slug"]}.html"><span>Newer</span>'
                    f'{escape(newer["title"])}</a>')
        else:
            nxt += "<div></div>"
        if older:
            nxt += (f'<a class="r" href="/papers/{older["slug"]}.html">'
                    f'<span>Older</span>{escape(older["title"])}</a>')
        dark = " dark" if is_dark(p) else ""
        caption = escape(p["media"]["alt"]) if p.get("media") else ""
        figure = (f'<figure class="figure"><div class="frame{dark}">'
                  f'{media(p)}</div><figcaption>{caption}</figcaption>'
                  f'</figure>' if p.get("media") else "")
        sub = (f'<p class="subtitle">{escape(p["subtitle"])}</p>'
               if p.get("subtitle") else "")
        advisor = (f" · Advised by {escape(p['advisor'])}"
                   if p.get("advisor") else "")
        abstract = "".join(f"<p>{escape(t)}</p>" for t in p["abstract"])
        bib_id = f"bib-{p['slug']}"
        body = f"""
<header class="paper-hero wrap">
<div class="crumb"><a href="/research.html">Research</a> / {escape(p["venue"])}</div>
<h1>{escape(p["title"])}</h1>
{sub}
<p class="authors">{authors(p["authors"])}</p>
<p class="meta">{escape(p["venue"])} · {fmt_date(p["date"])}{advisor}</p>
<div class="pills">{link_pills(p["links"])}<a href="#cite">Cite</a></div>
{figure}
</header>
<section class="wrap paper-body">
<div>
<p class="tldr">{escape(p["summary"])}</p>
<h2>{p.get("abstract_label", "Abstract")}</h2>
<div class="abstract">{abstract}</div>
<div class="bib" id="cite"><h2>Cite</h2>
<pre id="{bib_id}">{escape(bibtex(p))}</pre>
<button type="button" data-copy="{bib_id}">Copy</button></div>
</div>
<aside class="side"><dl>
<dt>Venue</dt><dd>{escape(p["venue"])}</dd>
<dt>Date</dt><dd>{fmt_date(p["date"])}</dd>
<dt>Topic</dt><dd>{" · ".join(TAGS[t] for t in p["tags"])}</dd>
<dt>Authors</dt><dd>{len(p["authors"])}</dd>
</dl></aside>
</section>
<nav class="wrap next" aria-label="More research">{nxt}</nav>
"""
        og = p["media"]["src"] if p.get("media") else "/images/me/profile.jpg"
        page(f"papers/{p['slug']}.html", p["title"], p["summary"], body,
             "research", og_image=og)


def build_experience() -> None:
    jobs = []
    for j in site["work"]:
        pts = "".join(f"<li>{escape(x)}</li>" for x in j["points"])
        org = escape(j["org"])
        if j.get("url"):
            org = f'<a class="link" href="{j["url"]}" target="_blank" rel="noopener">{org}</a>'
        links = "".join(
            f'<a href="/papers/{s}.html">{escape(by_slug[s]["title"])}</a>'
            for s in j.get("papers", [])
        )
        where = f'<small>{escape(j["where"])}</small>' if j.get("where") else ""
        jobs.append(f"""<div class="job">
<div class="when">{escape(j["when"])}{where}</div>
<div><div class="job-head"><img class="logo" src="{j["logo"]}" alt="{escape(j["org"])} logo">
<div><h3>{org}</h3><div class="role">{escape(j["role"])}</div></div></div>
<ul>{pts}</ul>
{f'<div class="papers">{links}</div>' if links else ""}</div>
</div>""")
    body = f"""
<header class="page-head wrap">
<h1>Experience</h1>
<p>Six roles since 2020, from network security at MIT to medical imaging at Epsilon.</p>
</header>
<section class="wrap timeline">{"".join(jobs)}</section>"""
    page("experience.html", "Experience",
         "Work history of Aakash Mishra.", body, "experience")


def build_projects() -> None:
    cards, rest = [], []
    for pr in site["projects"]:
        text = (f'<span class="year">{escape(pr["year"])}</span>'
                f'<h3>{escape(pr["title"])}</h3><p>{escape(pr["text"])}</p>'
                f'<div class="pills">{link_pills(pr["links"])}</div>')
        if pr["img"]:
            cards.append(f"""<article class="proj">
<div class="media"><img src="{pr["img"]}" alt="" loading="lazy"></div>
<div class="body">{text}</div>
</article>""")
        else:
            rest.append(f'<article class="small-proj">{text}</article>')
    body = f"""
<header class="page-head wrap">
<h1>Projects</h1>
<p>Open-source tools, systems and competition work. For papers and reports, see <a class="link" href="/research.html">Research</a>.</p>
</header>
<section class="wrap grid2">{"".join(cards)}</section>
<section class="block wrap">
<div class="block-head"><h2>Libraries and smaller tools</h2></div>
<div class="small-projs">{"".join(rest)}</div>
</section>"""
    page("projects.html", "Projects",
         "Open-source projects by Aakash Mishra.", body, "projects")


def build_hobbies() -> None:
    shots = []
    for s in site["sky"]:
        when = f"<dt>When</dt><dd>{escape(s['when'])}</dd>" if s.get("when") else ""
        wide = f" {s['wide']}" if s.get("wide") else ""
        shots.append(f"""<article class="shot{wide}" id="{s["id"]}">
<div class="media"><img src="{s["img"]}" alt="{escape(s["name"])}" loading="lazy"></div>
<dl class="plate">
<dt class="obj">{escape(s["name"])}<small>{escape(s["cat"])} · {escape(s["kind"])}</small></dt>
<dt>Where</dt><dd>{escape(s["constellation"])}</dd>
<dt>Distance</dt><dd>{escape(s["distance"])}</dd>
<dt>Gear</dt><dd>{escape(s["scope"])}</dd>
{when}
</dl></article>""")
    life = "".join(
        f"""<figure><img src="{h["img"]}" alt="{escape(h["alt"])}" loading="lazy">
<figcaption><h3>{escape(h["title"])}</h3><p>{escape(h["text"])}</p></figcaption></figure>"""
        for h in site["hobbies"]
    )
    sky_json = json.dumps(
        [{k: s[k] for k in ("id", "label", "ra", "dec")}
         | {"side": s.get("side", "right")} for s in site["sky"]]
    )
    body = f"""
<header class="page-head wrap">
<h1>Astrophotography and surfing</h1>
</header>

<section class="wrap">
<div class="story">
<div><p>I started with a Nikon and a Newtonian reflector I built myself, and later shot deep-sky objects through Harvard's Clay Telescope. In high school I ran the astronomy club, and that interest turned into research: <a class="link" href="/papers/active-centaurs-photometry.html">photometry of active Centaurs</a>.</p></div>
<div><p>The sphere below shows where each photo on this page sits in the sky. The gold line is the ecliptic, the path the Sun, Moon and planets follow, which is why Saturn and Jupiter sit right on it. Drag to turn the sky and click a label to jump to the photo.</p>
<p><a class="link" href="https://scienceofspace101.wixsite.com/astronomy" target="_blank" rel="noopener">My old astronomy site</a></p></div>
</div>
<div class="sky-stage" style="margin-top:36px">
<canvas aria-label="3D celestial sphere with the photographed objects marked"></canvas>
<div class="sky-labels"></div>
<div class="sky-legend"><span><i style="background:#7FDBEF"></i>Celestial equator</span><span><i style="background:#FFC98A"></i>Ecliptic</span></div>
<div class="sky-hint">Drag to rotate · Comet and planet positions are for summer 2020</div>
</div>
<script type="application/json" id="sky-data">{sky_json}</script>
<div class="gallery">{"".join(shots)}</div>
</section>

<section class="block wrap">
<div class="block-head"><h2>Surfing and photography</h2></div>
<div class="life">{life}</div>
</section>
"""
    page("hobbies.html", "Hobbies",
         "Astrophotography, surfing and photography.", body, "hobbies",
         night=True, og_image="/images/space7.JPG",
         scripts=f'{THREE}<script type="module" src="/assets/sky.js"></script>')


def build_redirect(path: str, target: str) -> None:
    (ROOT / path).write_text(
        f'<!doctype html><meta charset="utf-8">'
        f'<meta http-equiv="refresh" content="0; url={target}">'
        f'<link rel="canonical" href="{target}">'
        f'<title>Moved</title><p>Moved to <a href="{target}">{target}</a>.</p>\n'
    )


if __name__ == "__main__":
    build_home()
    build_research()
    build_papers()
    build_experience()
    build_projects()
    build_hobbies()
    build_redirect("academics.html", "/#education")
    print(f"Built {6 + len(papers)} pages.")
