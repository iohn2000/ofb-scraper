# howto
- scrape_two_step.py is the main file
- test_charts.py regenerates charts from db

- Individuelle Entwicklung statt Vergleich: Die Statistiken sollten zeigen, wie sich ein Kind im Vergleich zu sich selbst (frühere Spiele) verbessert hat, nicht im Vergleich zu anderen.

chart generation is also in scrape_two_step.py

-fix sqlite db


Repair path (works in ~90% of cases)
✅ Method 1: .recover (BEST)
This is the official SQLite recovery mechanism.

sqlite3 ofb_stats.db <<EOF
.mode insert
#.output dump.sql
.recover
EO

Then rebuild:
sqlite3 fixed.db < dump.sql

✅ This preserves maximum data.

✅ Method 2: .dump (older SQLite)
If .recover is not available:
sqlite3 ofb_stats.db .dump > dump.sql
sqlite3 fixed.db < dump.sql

⚠️ This may fail earlier than .recover, but still worth trying.
