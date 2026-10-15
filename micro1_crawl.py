#!/usr/bin/env python3
"""micro1 public listings crawler. Reads the sitemap of jobs.micro1.ai, opens every listing page
and extracts the embedded data block (openings, referral reward, rate, dates, status, domain, skills,
eligibility wording). Writes snapshots/micro1_YYYY-MM-DD.csv. No login, no API key."""
import json, re, csv, html, datetime, urllib.request, pathlib, concurrent.futures, time
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
OUT = pathlib.Path(__file__).parent / "snapshots"
OUT.mkdir(exist_ok=True)
ELIG_PATTERNS = ["United States", "US-based", "U.S.", "US only", "Western Europe", "English-speaking country",
                 "licensed", "board certified", "board-certified", "bar membership", "Worldwide", "Global", "native"]
def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "ignore")
def parse(page):
    chunks = re.findall(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)', page, re.S)
    data = "".join(json.loads('"' + c + '"') for c in chunks)
    i = data.find('"$L15",null,{"id":')
    j = data.find('{"id":', i if i >= 0 else 0)
    obj, _ = json.JSONDecoder().raw_decode(data[j:])
    d = obj["data"]
    desc = d.get("job_description")
    if isinstance(desc, str) and desc.startswith("$"):
        m = re.search(re.escape(desc[1:]) + r":T([0-9a-f]+),", data)
        if m:
            n = int(m.group(1), 16); desc = data[m.end():m.end() + n]
    d["job_description"] = desc or ""
    m = re.search(r"14:T([0-9a-f]+),", data)
    if m:
        ld, _ = json.JSONDecoder().raw_decode(data[m.end():])
        d["validThrough"] = ld.get("validThrough"); d["datePosted"] = ld.get("datePosted")
    return d
def one(url):
    for attempt in range(3):
        try:
            d = parse(fetch(url)); d["url"] = url; return d
        except Exception as e:
            err = e; time.sleep(2)
    return {"url": url, "error": str(err)}
def main():
    sm = fetch("https://jobs.micro1.ai/sitemap.xml")
    urls = re.findall(r"<loc>(https://jobs\.micro1\.ai/post/[^<]+)</loc>", sm)
    with concurrent.futures.ThreadPoolExecutor(6) as ex:
        results = list(ex.map(one, urls))
    today = datetime.date.today().isoformat()
    cols = ["date","jobId","title","url","referralReward","referralEnabled","openings","rateMin","rateMax","created","validThrough","status","domain","roleType","jobType","tags","skills","eligibilityWords","descriptionText"]
    rows = []
    for d in results:
        if "error" in d:
            rows.append({"date": today, "url": d["url"], "title": "ERROR " + d["error"]}); continue
        text = re.sub(r"<[^>]+>", " ", d["job_description"]); text = html.unescape(re.sub(r"\s+", " ", text)).strip()
        rate = d.get("ideal_hourly_rate") or {}
        rows.append({"date": today, "jobId": d["client_job_id"], "title": d["job_role_name"].strip(), "url": d["url"],
            "referralReward": d.get("referral_reward_amount"), "referralEnabled": d.get("is_referral_enabled"),
            "openings": d.get("no_of_openings"), "rateMin": rate.get("min"), "rateMax": rate.get("max"),
            "created": (d.get("create_datetime") or "")[:10], "validThrough": (d.get("validThrough") or "")[:10],
            "status": d.get("job_status"), "domain": d.get("domain_slug"), "roleType": d.get("role_type"), "jobType": d.get("job_type"),
            "tags": "|".join(d.get("job_tags") or []), "skills": "|".join(d.get("required_skills") or []),
            "eligibilityWords": "|".join(p for p in ELIG_PATTERNS if p in text), "descriptionText": text[:4000]})
    path = OUT / f"micro1_{today}.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)
    print(f"micro1: {len(rows)} listings -> {path}")
if __name__ == "__main__":
    main()
