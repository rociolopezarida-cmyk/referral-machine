#!/usr/bin/env python3
"""micro1 listings crawler, version 2 (2 November 2026).

micro1's own job site blocks scripts since 29 October 2026, so this step reads aitrainer.work's open-data file
(https://aitrainer.work/data/jobs.json, CC BY 4.0, refreshed every morning). That file lists every open micro1 role with
its job id, title, pay, countries and description, but not the referral reward, the openings or the closing date.
Those three are carried forward from the most recent earlier snapshot that had them for the same job id, and left blank
for roles that were never seen by the old crawler (Nada reads the reward on her micro1 refer page).

Writes snapshots/micro1_YYYY-MM-DD.csv in the same columns as before, so hot_tracker.py and the Tuesday selection keep
working. A listing missing from today's file is closed: it is simply not in today's snapshot, which is how the old crawler
expressed it too. The micro1 part never raises on a network error: it writes a snapshot with one ERROR row instead, so the
workflow still commits the Mercor snapshot of the day.
"""
import csv, datetime, gzip, html, io, json, pathlib, re, urllib.request

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
OUT = pathlib.Path(__file__).parent / "snapshots"
OUT.mkdir(exist_ok=True)
COLS = ["date", "jobId", "title", "url", "referralReward", "referralEnabled", "openings", "rateMin", "rateMax", "created",
        "validThrough", "status", "domain", "roleType", "jobType", "tags", "skills", "eligibilityWords", "descriptionText"]
ELIG_PATTERNS = ["United States", "US-based", "U.S.", "US only", "Western Europe", "English-speaking country",
                 "licensed", "board certified", "board-certified", "bar membership", "Worldwide", "Global", "native"]
SOURCES = ["https://aitrainer.work/data/jobs.json.gz", "https://aitrainer.work/data/jobs.json"]
MIN_ROLES = 100  # fewer micro1 roles than this means the source broke; refuse to write a misleading snapshot


def fetch_jobs():
    last = None
    for url in SOURCES:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            raw = urllib.request.urlopen(req, timeout=120).read()
            if url.endswith(".gz"):
                raw = gzip.GzipFile(fileobj=io.BytesIO(raw)).read()
            data = json.loads(raw.decode("utf-8", "ignore"))
            jobs = data.get("jobs") if isinstance(data, dict) else data
            if jobs:
                return jobs
        except Exception as e:  # try the next source
            last = e
    raise RuntimeError(f"aitrainer.work open data unreadable: {last}")


def previous_values():
    """jobId -> (referralReward, referralEnabled, openings, validThrough, created) from the latest snapshot that holds them."""
    prev = {}
    for path in sorted(OUT.glob("micro1_*.csv")):
        with open(path, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                jid = (r.get("jobId") or "").strip()
                if not jid or (r.get("title") or "").startswith("ERROR"):
                    continue
                old = prev.get(jid, {})
                new = {k: (r.get(k) or old.get(k) or "") for k in ("referralReward", "referralEnabled", "openings", "validThrough", "created")}
                prev[jid] = new
    return prev


def main():
    today = datetime.date.today().isoformat()
    path = OUT / f"micro1_{today}.csv"
    try:
        jobs = fetch_jobs()
    except Exception as e:
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=COLS); w.writeheader()
            w.writerow({"date": today, "url": SOURCES[0], "title": "ERROR " + str(e)})
        print(f"micro1: source unreadable, wrote an ERROR row -> {path}")
        return
    prev = previous_values()
    rows, seen = [], set()
    for j in jobs:
        if str(j.get("platform", "")).lower() != "micro1":
            continue
        m = re.search(r"jobs\.micro1\.ai/post/([0-9a-f-]{36})", j.get("apply_url") or "")
        if not m:
            continue
        jid = m.group(1)
        if jid in seen:
            continue
        seen.add(jid)
        old = prev.get(jid, {})
        text = html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", j.get("description") or ""))).strip()
        geo = j.get("geographic_restrictions") or []
        rows.append({
            "date": today, "jobId": jid, "title": (j.get("title") or "").strip(),
            "url": f"https://jobs.micro1.ai/post/{jid}",
            "referralReward": old.get("referralReward", ""), "referralEnabled": old.get("referralEnabled", ""),
            "openings": old.get("openings", ""),
            "rateMin": j.get("pay_min") if j.get("pay_min") is not None else "",
            "rateMax": j.get("pay_max") if j.get("pay_max") is not None else "",
            "created": old.get("created") or (j.get("first_seen") or "")[:10],
            "validThrough": old.get("validThrough", ""),
            "status": "open", "domain": j.get("domain") or "", "roleType": j.get("application_type") or "",
            "jobType": j.get("pay_model") or "",
            "tags": "|".join(j.get("search_tags") or []), "skills": "|".join(j.get("required_skills") or []),
            "eligibilityWords": "|".join(sorted(set([p for p in ELIG_PATTERNS if p in text] + [g for g in geo if g]))),
            "descriptionText": text[:4000],
        })
    if len(rows) < MIN_ROLES:
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=COLS); w.writeheader()
            w.writerow({"date": today, "url": SOURCES[0], "title": f"ERROR source lists only {len(rows)} micro1 roles"})
        print(f"micro1: only {len(rows)} roles in the source, wrote an ERROR row -> {path}")
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS); w.writeheader(); w.writerows(rows)
    carried = sum(1 for r in rows if r["referralReward"])
    print(f"micro1: {len(rows)} open listings ({carried} with a reward carried from earlier snapshots) -> {path}")


if __name__ == "__main__":
    main()
