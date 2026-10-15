Referral machine kit v3, 15 October 2026. Works from any computer; nothing here needs a Mac, Windows or Linux specifically, because the programs run on GitHub's computers.
mercor_crawl.py   public Mercor listings with hired-this-month, slots, referral amount
micro1_crawl.py   public micro1 listings with openings, referral reward, rate, dates, eligibility wording
hot_tracker.py    diff against yesterday and 7 days ago; hot list and closures
wp_publish.py     publishes today's open listings to your WordPress site as posts, updates them daily, drafts the closed ones (needs 3 secrets, see the manual)
site_build.py     optional: a plain static site in docs/ for GitHub Pages (not needed if you use WordPress)
.github/workflows/daily.yml   the daily schedule on GitHub (create it by hand on GitHub, see the manual: the folder starts with a dot and is hidden on most computers)
tracker/          CSV templates for one Google Sheet, scorecard formulas, phone form questions
snapshots/        baseline snapshots from 13 October
Requirements: Python 3.10 or newer; no extra packages. Secrets never go in these files.
