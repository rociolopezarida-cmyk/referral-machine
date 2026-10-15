#!/usr/bin/env python3
"""Builds a static job-board site from today's snapshots into docs/ (GitHub Pages).
Every micro1 listing links straight to the listing with YOUR referral code.
Every Mercor listing links to your gate form (the Mercor link has a 100-uses-a-month cap, so it never goes on a public page).
Edit the CONFIG block once. Nothing else needs changing."""
import csv, glob, json, html, datetime, pathlib, re

# ---------------- CONFIG: edit these lines ----------------
SITE_NAME = "Expert Side Work"                       # your brand, never a platform name
SITE_URL = "https://YOURUSERNAME.github.io/referral-machine"   # GitHub Pages URL (Settings > Pages shows it)
MICRO1_REFERRAL_CODE = "2a70d68e-8078-44d9-b84e-8caa5cc34e7e"   # from your refer.micro1.ai link
MERCOR_GATE_FORM_URL = "https://forms.gle/REPLACE_ME"            # your 5-question Google Form
CONTACT_EMAIL = "you@example.com"
LANG = "en"
# -----------------------------------------------------------

ROOT = pathlib.Path(__file__).parent
SNAP = ROOT / "snapshots"
DOCS = ROOT / "docs"
MIN_REWARD_TO_LIST = 100

def latest(prefix):
    files = sorted(glob.glob(str(SNAP / f"{prefix}_*.csv")))
    if not files: return []
    with open(files[-1], encoding="utf-8") as f:
        return [r for r in csv.DictReader(f) if r.get("title") and not r["title"].startswith("ERROR")]

def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:80]

DISCLOSURE = (f"{SITE_NAME} is an independent site. It is not affiliated with, endorsed by or operated by any platform listed here. "
              f"Listings are republished from the platforms' public pages. Some links are referral links: if you are hired and complete the platform's "
              f"work milestone, the site owner may receive a referral bonus from the platform. This costs you nothing and does not change your pay. "
              f"You can apply directly on the platform instead at any time. Questions: {CONTACT_EMAIL}.")

CSS = """body{font-family:-apple-system,Segoe UI,Helvetica,Arial,sans-serif;max-width:860px;margin:0 auto;padding:16px;line-height:1.5;color:#1a1a1a}
a{color:#0b57d0}h1{font-size:1.6em}.meta{color:#555}.card{border:1px solid #ddd;border-radius:8px;padding:12px;margin:10px 0}
.btn{display:inline-block;background:#0b57d0;color:#fff;padding:10px 16px;border-radius:6px;text-decoration:none;font-weight:600}
.tag{display:inline-block;background:#eef;border-radius:4px;padding:2px 8px;margin-right:6px;font-size:.9em}.small{font-size:.85em;color:#666}
nav a{margin-right:12px}@media(prefers-color-scheme:dark){body{background:#111;color:#eee}.card{border-color:#333}.meta,.small{color:#aaa}a{color:#8ab4f8}}"""

def page(title, body, canonical, noindex=False, jsonld=None):
    robots = '<meta name="robots" content="noindex,follow">' if noindex else '<meta name="robots" content="index,follow">'
    ld = f'<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>' if jsonld else ""
    return f"""<!doctype html><html lang="{LANG}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>{robots}<link rel="canonical" href="{canonical}"><style>{CSS}</style>{ld}</head>
<body><nav><a href="{SITE_URL}/">All roles</a><a href="{SITE_URL}/hot.html">Hiring now</a><a href="{SITE_URL}/disclosure.html">How this site earns</a></nav>
{body}<footer class="small"><p>{html.escape(DISCLOSURE)}</p><p>Updated {datetime.date.today().isoformat()}.</p></footer></body></html>"""

def micro1_apply(url):
    return f"{url}?referralCode={MICRO1_REFERRAL_CODE}&utm_source=referral&utm_medium=share&utm_campaign=job_referral"

def build():
    DOCS.mkdir(exist_ok=True); (DOCS / "jobs").mkdir(exist_ok=True)
    rows = []
    for r in latest("micro1"):
        reward = float(r.get("referralReward") or 0)
        if r.get("status") != "open" or reward < MIN_REWARD_TO_LIST: continue
        rows.append(dict(platform="micro1", title=r["title"], url=r["url"], apply=micro1_apply(r["url"]), direct=True,
            rate=f"${r.get('rateMin')} to ${r.get('rateMax')} an hour" if r.get("rateMin") else "", openings=r.get("openings"),
            posted=r.get("created"), expires=r.get("validThrough"), domain=r.get("domain"), text=(r.get("descriptionText") or "")[:2500],
            elig=r.get("eligibilityWords") or "", skills=(r.get("skills") or "").replace("|", ", ")))
    for r in latest("mercor"):
        if r.get("status") not in ("ACTIVE", "active", "") or float(r.get("referralAmount") or 0) < MIN_REWARD_TO_LIST: continue
        rows.append(dict(platform="mercor", title=r["title"], url=r["url"], apply=MERCOR_GATE_FORM_URL, direct=False,
            rate=f"${r.get('rateMin')} to ${r.get('rateMax')} per {r.get('payRateFrequency','hour')}" if r.get("rateMin") else "", openings=r.get("remainingSlots"),
            posted=r.get("postedAt"), expires="", domain=r.get("listingDomain"), text="", elig=r.get("location") or "",
            skills="", hired=r.get("hiredThisMonth")))
    rows.sort(key=lambda x: (x["posted"] or ""), reverse=True)
    urls = []
    for x in rows:
        fn = f"jobs/{x['platform']}-{slug(x['title'])}.html"; x["page"] = fn
        canonical = f"{SITE_URL}/{fn}"; urls.append(canonical)
        ld = {"@context": "https://schema.org", "@type": "JobPosting", "title": x["title"], "datePosted": x["posted"] or datetime.date.today().isoformat(),
              "description": html.escape(x["text"] or f"{x['title']} on {x['platform']}: remote, flexible, paid per hour."),
              "hiringOrganization": {"@type": "Organization", "name": x["platform"]}, "jobLocationType": "TELECOMMUTE",
              "applicantLocationRequirements": {"@type": "Country", "name": "Remote"}, "employmentType": "CONTRACTOR", "directApply": False}
        if x["expires"]: ld["validThrough"] = x["expires"]
        cta = (f'<a class="btn" href="{html.escape(x["apply"])}" rel="nofollow sponsored">Apply on {x["platform"]} (referral link)</a>' if x["direct"]
               else f'<a class="btn" href="{html.escape(x["apply"])}">Request the application link (2 minutes)</a><p class="small">This platform limits how many people can use one referral link each month, so we send it after a short eligibility check.</p>')
        body = f"""<h1>{html.escape(x['title'])}</h1><p class="meta">{x['platform']} · remote · {html.escape(x['rate'])}{(' · ' + str(x['openings']) + ' openings') if x['openings'] else ''}{(' · posted ' + x['posted']) if x['posted'] else ''}</p>
<p>{cta}</p><div class="card"><p>{html.escape(x['text']) if x['text'] else 'Open the platform page for the full description.'}</p>
{('<p class="small">Skills named on the listing: ' + html.escape(x['skills']) + '</p>') if x['skills'] else ''}
{('<p class="small">Eligibility wording found on the listing: ' + html.escape(x['elig']) + '</p>') if x['elig'] else ''}
<p class="small">Original listing: <a href="{html.escape(x['url'])}" rel="nofollow">{html.escape(x['url'])}</a></p></div>"""
        (DOCS / fn).write_text(page(f"{x['title']} (remote, {x['rate']})", body, canonical, jsonld=ld), encoding="utf-8")
    def listing_html(items):
        return "".join(f'<div class="card"><a href="{SITE_URL}/{i["page"]}"><b>{html.escape(i["title"])}</b></a> <span class="tag">{i["platform"]}</span><br><span class="meta">{html.escape(i["rate"])}{(" · " + str(i["openings"]) + " openings") if i["openings"] else ""}{(" · posted " + i["posted"]) if i["posted"] else ""}</span></div>' for i in items)
    (DOCS / "index.html").write_text(page(f"{SITE_NAME}: remote expert work for AI projects", f"<h1>{SITE_NAME}</h1><p>Hourly remote work for professionals, republished daily from the platforms' public pages. {len(rows)} open roles.</p>{listing_html(rows)}", f"{SITE_URL}/"), encoding="utf-8")
    hot = [x for x in rows if x["platform"] == "mercor" and float(x.get("hired") or 0) >= 50] + [x for x in rows if x["platform"] == "micro1" and float(x["openings"] or 0) >= 50 and (x["posted"] or "") >= (datetime.date.today() - datetime.timedelta(days=21)).isoformat()]
    (DOCS / "hot.html").write_text(page("Hiring now", "<h1>Hiring now</h1><p>Roles with high hiring activity in the last 30 days or many openings posted in the last three weeks.</p>" + listing_html(hot), f"{SITE_URL}/hot.html"), encoding="utf-8")
    (DOCS / "disclosure.html").write_text(page("How this site earns", f"<h1>How this site earns</h1><p>{html.escape(DISCLOSURE)}</p>", f"{SITE_URL}/disclosure.html"), encoding="utf-8")
    (DOCS / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + "".join(f"<url><loc>{u}</loc></url>" for u in [f"{SITE_URL}/", f"{SITE_URL}/hot.html"] + urls) + "</urlset>", encoding="utf-8")
    (DOCS / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n", encoding="utf-8")
    (DOCS / ".nojekyll").write_text("", encoding="utf-8")
    print(f"site: {len(rows)} job pages, {len(hot)} hot -> {DOCS}")

if __name__ == "__main__":
    build()
