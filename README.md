# Score Card

Live scores for the NFL, NBA, MLB, NHL, MLS, F1 and every Division I college football, basketball and hockey game, laid out after Edward Tufte: each game a line of type with a sparkline of the margin, a rug of every score in the last 30 minutes, and a scoring feed in the margin.

It reads ESPN's public scoreboard API straight from the browser. Open it on a phone and choose **Add to Home Screen** to use it like an app.

Stars, bells and sound are saved in each browser separately. Alerts and chimes work while the page is open.

## Data

- Scores, box scores, F1 sessions and championship standings: ESPN's public site API (NFL, NBA, WNBA, MLB, NHL, MLS, NWSL, Premier League, Champions League, La Liga, Bundesliga, Serie A, Ligue 1, Liga MX, F1 and Division I college football, basketball and hockey).
- Prediction markets on game pages: Polymarket (gamma API). Prices are shown as implied chances; nothing here places bets.
- Typeface: EB Garamond (SIL Open Font License, `fonts/OFL.txt`). The app icon is drawn by `tools/sc_icons.py`.
- F1 track outlines: [bacinger/f1-circuits](https://github.com/bacinger/f1-circuits) (MIT License), simplified into `circuits.json` by `.github/workflows/circuits.yml`.
