#!/usr/bin/env python3
"""Compares today's snapshots with yesterday's and with 7 days ago. Writes snapshots/hot_report_YYYY-MM-DD.csv
and prints the hot list. Hot = Mercor hired-this-month rising day over day with slots left, or micro1 openings moving,
or new today with a high reward."""
import csv, glob, datetime, pathlib, collections
SNAP = pathlib.Path(__file__).parent / "snapshots"
def load(prefix, date):
    p = SNAP / f"{prefix}_{date}.csv"
    if not p.exists(): return {}
    key = "listingId" if prefix == "mercor" else "jobId"
    with open(p, encoding="utf-8") as f:
        return {r[key]: r for r in csv.DictReader(f) if r.get(key)}
def num(x):
    try: return float(x)
    except: return None
def main():
    today = datetime.date.today(); d1 = today - datetime.timedelta(days=1); d7 = today - datetime.timedelta(days=7)
    out = []
    for prefix in ("mercor", "micro1"):
        T, Y, W = load(prefix, today.isoformat()), load(prefix, d1.isoformat()), load(prefix, d7.isoformat())
        for k, r in T.items():
            y, w = Y.get(k), W.get(k)
            row = {"platform": prefix, "id": k, "title": r["title"], "url": r["url"], "new_today": "yes" if (Y and not y) else "",
                   "reward": r.get("referralAmount") or r.get("referralReward"), "posted": r.get("postedAt") or r.get("created")}
            if prefix == "mercor":
                h, rem = num(r.get("hiredThisMonth")), num(r.get("remainingSlots"))
                row["hired"] = h; row["left"] = rem; row["max"] = r.get("maxHeadcount")
                row["hired_delta_1d"] = (h - num(y["hiredThisMonth"])) if (y and h is not None and num(y["hiredThisMonth"]) is not None) else ""
                row["hired_delta_7d"] = (h - num(w["hiredThisMonth"])) if (w and h is not None and num(w["hiredThisMonth"]) is not None) else ""
                row["left_delta_1d"] = (rem - num(y["remainingSlots"])) if (y and rem is not None and num(y["remainingSlots"]) is not None) else ""
                hot = ((row["hired_delta_1d"] != "" and row["hired_delta_1d"] > 0) or (row["new_today"] and num(row["reward"]) and num(row["reward"]) >= 400)) and (rem or 0) >= 10
            else:
                o = num(r.get("openings")); row["left"] = o
                row["openings_delta_1d"] = (o - num(y["openings"])) if (y and o is not None and num(y["openings"]) is not None) else ""
                row["openings_delta_7d"] = (o - num(w["openings"])) if (w and o is not None and num(w["openings"]) is not None) else ""
                row["expires"] = r.get("validThrough")
                hot = (row["openings_delta_1d"] != "" and row["openings_delta_1d"] != 0) or (row["new_today"] and num(row["reward"]) and num(row["reward"]) >= 1000 and (o or 0) >= 20)
            row["hot"] = "HOT" if hot else ""
            out.append(row)
        for k, r in Y.items():
            if Y and k not in T:
                out.append({"platform": prefix, "id": k, "title": r["title"], "url": r["url"], "hot": "CLOSED today", "reward": r.get("referralAmount") or r.get("referralReward")})
    cols = ["platform","hot","new_today","title","reward","hired","hired_delta_1d","hired_delta_7d","left","left_delta_1d","openings_delta_1d","openings_delta_7d","max","posted","expires","url","id"]
    path = SNAP / f"hot_report_{today.isoformat()}.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore"); w.writeheader(); w.writerows(out)
    hot = [r for r in out if r.get("hot")]
    print(f"hot report -> {path}; {len(hot)} flagged")
    for r in sorted(hot, key=lambda r: -(num(r.get("reward")) or 0))[:40]:
        print(f"  {r['platform']:<7} {r['hot']:<13} ${r.get('reward')}  {r['title'][:70]}  {r['url']}")
if __name__ == "__main__":
    main()
