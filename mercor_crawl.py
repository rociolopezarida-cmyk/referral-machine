#!/usr/bin/env python3
"""Mercor public listings crawler. Reads the data block embedded in work.mercor.com/jobs
and writes snapshots/mercor_YYYY-MM-DD.csv. No login, no API key."""
import json, re, csv, sys, datetime, urllib.request, pathlib
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
OUT = pathlib.Path(__file__).parent / "snapshots"
OUT.mkdir(exist_ok=True)
def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "ignore")
def main():
    html = fetch("https://work.mercor.com/jobs")
    i = html.find("__NEXT_DATA__"); j = html.find(">", i) + 1; k = html.find("</script>", j)
    data = json.loads(html[j:k])
    listings = data["props"]["pageProps"]["dehydratedState"]["queries"][0]["state"]["data"]["listings"]
    today = datetime.date.today().isoformat()
    cols = ["date","listingId","title","url","referralAmount","rateMin","rateMax","payRateFrequency","commitment","hoursPerWeek","postedAt","location","eligibleLocation","ineligibleLocation","listingDomain","listingType","status","hiredThisMonth","remainingSlots","suppliedSlots","maxHeadcount"]
    rows = []
    for l in listings:
        slug = re.sub(r"[^a-z0-9]+", "-", l["title"].lower()).strip("-")
        rows.append({"date": today, "listingId": l["listingId"], "title": l["title"],
            "url": f"https://work.mercor.com/jobs/{l['listingId']}/{slug}",
            "referralAmount": l.get("referralAmount"), "rateMin": l.get("rateMin"), "rateMax": l.get("rateMax"),
            "payRateFrequency": l.get("payRateFrequency"), "commitment": l.get("commitment"), "hoursPerWeek": l.get("hoursPerWeek"),
            "postedAt": (l.get("postedAt") or "")[:10], "location": l.get("location"),
            "eligibleLocation": "|".join(l.get("eligibleLocation") or []), "ineligibleLocation": "|".join(l.get("ineligibleLocation") or []),
            "listingDomain": l.get("listingDomain"), "listingType": l.get("listingType"), "status": l.get("status"),
            "hiredThisMonth": l.get("recentCandidatesCount"), "remainingSlots": l.get("remainingSlots"),
            "suppliedSlots": l.get("suppliedSlots"), "maxHeadcount": l.get("maxFutureHcg")})
    path = OUT / f"mercor_{today}.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)
    print(f"mercor: {len(rows)} listings -> {path}")
if __name__ == "__main__":
    main()
