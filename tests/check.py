"""ScoreCard checks: open the app in a headless Chrome with fake games, and
fail loudly if a change broke the layout. Run before every update:

    python3 tests/check.py            (serves the repo itself on a free port)

Every request to ESPN, Polymarket, Jolpica and Google Fonts is answered
here with fixed fixtures, so the checks are the same every run and need no
network. Each check names what it guards against."""
import asyncio, json, math, os, subprocess, sys, time, datetime as dt
from playwright.async_api import async_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import socket
def _free_port():   # a port of its own, so a stray server elsewhere can't stand in for this one
    with socket.socket() as so: so.bind(("127.0.0.1", 0)); return so.getsockname()[1]
PORT = _free_port()
now = time.time(); start = now - 100 * 60
# Finished games are dated just after midnight today in the browser's time
# zone (fixed below), so "today only" keeps them whenever the checks run.
from zoneinfo import ZoneInfo
TZ = "America/Chicago"
midnight = dt.datetime.now(ZoneInfo(TZ)).replace(hour=0, minute=5, second=0, microsecond=0).timestamp()
iso = lambda t: dt.datetime.fromtimestamp(t, dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")

def team(id, ab, name, color, alt="bbbbbb"):
    return {"id": id, "abbreviation": ab, "displayName": name, "shortDisplayName": name.split()[-1], "color": color, "alternateColor": alt}
def comp(away, ascore, home, hscore, als, hls):
    return {"competitors": [
        {"homeAway": "away", "score": str(ascore), "team": away, "linescores": [{"value": v} for v in als]},
        {"homeAway": "home", "score": str(hscore), "team": home, "linescores": [{"value": v} for v in hls]}]}
def game(id, date, state, detail, c, clock=0, period=1, sit=None):
    if sit: c = dict(c, situation=sit)
    return {"id": id, "date": iso(date), "status": {"clock": clock, "period": period, "type": {"state": state, "shortDetail": detail}}, "competitions": [c]}
# Bears ball, 3rd and 7 at the Detroit 34 (ESPN counts yards from the home goal line)
SIT401 = {"down": 3, "distance": 7, "yardLine": 34, "possession": "3", "isRedZone": False, "downDistanceText": "3rd & 7 at DET 34", "shortDownDistanceText": "3rd & 7", "possessionText": "DET 34"}
def DRV(id, tm, a, b, res, score=False):
    return {"id": id, "team": {"id": tm}, "start": {"yardLine": a}, "end": {"yardLine": b}, "shortDisplayResult": res, "isScore": score, "description": ""}
SUM401 = {"header": {"competitions": [{"status": {"type": {"state": "in", "shortDetail": "7:00 - 3rd"}}, "competitors": [{"homeAway": "away", "team": {"id": "3"}, "score": "17"}, {"homeAway": "home", "team": {"id": "8"}, "score": "20"}]}]},
    "boxscore": {"players": []},
    "drives": {"previous": [DRV("d1", "3", 75, 0, "TD", True), DRV("d2", "8", 25, 52, "PUNT"), DRV("d3", "3", 80, 3, "FG", True), DRV("d4", "8", 30, 100, "TD", True)],
               "current": DRV("d5", "3", 70, 34, "")}}

NFL = {"events": [
    game("401", start, "in", "7:00 - 3rd", comp(team("3", "CHI", "Chicago Bears", "0b162a", "c83803"), 17, team("8", "DET", "Detroit Lions", "0076b6"), 20, [7, 10], [13, 7]), 420, 3, SIT401),
    game("402", midnight, "post", "Final", comp(team("21", "PHI", "Philadelphia Eagles", "06424d"), 24, team("6", "DAL", "Dallas Cowboys", "002a5c"), 21, [7, 7, 3, 7], [3, 14, 0, 4]))]}
# wide college names: four letters and a long display name
NCAAM = {"events": [
    game("501", start, "in", "14:01 - 2nd", comp(team("2449", "NDSU", "North Dakota State Bison", "0a5640"), 38, team("23", "SJSU", "San Jose State Spartans", "0055a2"), 31, [30, 8], [25, 6]), 841, 2),
    game("502", start, "in", "End of 1st", comp(team("2450", "NCWU", "North Carolina Wesleyan Battling Bishops", "000000"), 2, team("151", "ECU", "East Carolina Pirates", "4b1869"), 12, [2], [12]), 0, 1),
    game("504", start, "in", "Halftime", comp(team("2509", "PURD", "Purdue Boilermakers", "000000"), 60, team("356", "ILL", "Illinois Fighting Illini", "e84a27"), 44, [60], [44]), 0, 2),
    game("503", start, "in", "3:14 - 2nd", comp(team("222", "VILL", "Villanova Wildcats", "00205b"), 46, team("2305", "KU", "Kansas Jayhawks", "0051ba"), 55, [20, 26], [25, 30]), 194, 2)]}

def P(per, clk, tm, text, a, h):
    return {"period": {"number": per}, "clock": {"value": clk, "displayValue": "%d:%02d" % (clk // 60, clk % 60)}, "team": {"id": tm}, "text": text, "awayScore": a, "homeScore": h, "scoringType": {"displayName": "Touchdown"}}
# A basketball game, play by play: a 10-0 home run in the middle, shots with
# court spots, fouls, a timeout, ESPN's win chance, and team totals.
def _bball():
    plays, a, h, n, wp = [], 0, 0, 0, []
    seq = [("away", 2, 8, 10, "4001"), ("home", 3, 3, 2, "4101"), ("away", 3, 40, 20, "4002"), ("home", 2, 25, 1, "4102"), ("home", 2, 24, 3, "4101"),
           ("home", 3, 47, 2, "4102"), ("home", 3, 2, 2, "4101"), ("away", 2, 20, 8, "4001")]
    for i, (sd, v, x, y, who) in enumerate(seq):
        n += 1
        if sd == "away": a += v
        else: h += v
        tid = "2449" if sd == "away" else "23"
        plays.append({"id": "p%d" % n, "type": {"text": "Jump Shot"}, "text": "shot", "shootingPlay": True, "scoringPlay": True, "scoreValue": v, "pointsAttempted": v,
                      "coordinate": {"x": x, "y": y}, "team": {"id": tid}, "period": {"number": 1}, "clock": {"displayValue": "%d:%02d" % (19 - i * 2, 30)},
                      "awayScore": a, "homeScore": h, "participants": [{"athlete": {"id": who}}]})
        wp.append({"playId": "p%d" % n, "homeWinPercentage": 0.4 + 0.05 * i})
        n += 1
        plays.append({"id": "p%d" % n, "type": {"text": "Jump Shot"}, "text": "miss", "shootingPlay": True, "scoringPlay": False, "scoreValue": 0, "pointsAttempted": 2,
                      "coordinate": {"x": 50 - x, "y": y + 3}, "team": {"id": "23" if sd == "away" else "2449"}, "period": {"number": 1}, "clock": {"displayValue": "%d:%02d" % (19 - i * 2, 10)},
                      "awayScore": a, "homeScore": h, "participants": [{"athlete": {"id": "4102"}}]})
    for k in range(3):
        plays.append({"id": "f%d" % k, "type": {"text": "Personal Foul"}, "text": "foul", "team": {"id": "23"}, "period": {"number": 2}, "clock": {"displayValue": "10:00"}})
    plays.append({"id": "t1", "type": {"text": "Full Timeout"}, "text": "timeout", "team": {"id": "2449"}, "period": {"number": 2}, "clock": {"displayValue": "9:00"}})
    stats = lambda fg, tp: [{"name": "fieldGoalsMade-fieldGoalsAttempted", "displayValue": fg}, {"name": "fieldGoalPct", "displayValue": "45"},
                            {"name": "threePointFieldGoalsMade-threePointFieldGoalsAttempted", "displayValue": tp}, {"name": "threePointFieldGoalPct", "displayValue": "33"},
                            {"name": "totalRebounds", "displayValue": "20"}, {"name": "totalTurnovers", "displayValue": "6"}, {"name": "largestLead", "displayValue": "8"}, {"name": "leadChanges", "displayValue": "3"}]
    pl = lambda id, nm: {"athlete": {"id": id, "displayName": nm, "shortName": nm}, "stats": ["10"]}
    return {"header": {"competitions": [{"status": {"type": {"state": "in", "shortDetail": "14:01 - 2nd"}}, "competitors": [{"homeAway": "away", "team": {"id": "2449"}, "score": "38"}, {"homeAway": "home", "team": {"id": "23"}, "score": "31"}]}]},
            "boxscore": {"players": [{"team": {"id": "2449", "abbreviation": "NDSU", "displayName": "North Dakota State"}, "statistics": [{"labels": ["PTS"], "athletes": [pl("4001", "A. Away"), pl("4002", "B. Away")]}]},
                                     {"team": {"id": "23", "abbreviation": "SJSU", "displayName": "San Jose State"}, "statistics": [{"labels": ["PTS"], "athletes": [pl("4101", "C. Home"), pl("4102", "D. Home")]}]}],
                         "teams": [{"team": {"id": "2449"}, "statistics": stats("14-30", "4-12")}, {"team": {"id": "23"}, "statistics": stats("12-31", "3-11")}]},
            "plays": plays, "winprobability": wp}
SUM501 = _bball()
SUM402 = {"header": {"competitions": [{"status": {"type": {"state": "post", "shortDetail": "Final"}}, "competitors": [{"homeAway": "away", "team": {"id": "21"}, "score": "24"}, {"homeAway": "home", "team": {"id": "6"}, "score": "21"}]}]},
    "boxscore": {"players": []},
    "scoringPlays": [P(1, 600, "21", "Jalen Hurts 12 yd run", 7, 0), P(2, 700, "6", "CeeDee Lamb 34 yd pass", 7, 10), P(3, 400, "21", "Field goal", 10, 10), P(4, 40, "21", "A.J. Brown 22 yd pass", 17, 10)]}

def sched_game(i, d, opp, oid, home, us, them, state="post"):
    me = {"id": "8", "homeAway": "home" if home else "away", "winner": (us > them) if state == "post" else None, "team": {"id": "8", "abbreviation": "DET", "displayName": "Detroit Lions"},
          "score": {"value": us, "displayValue": str(us)} if state == "post" else None,
          "leaders": [{"name": "passingLeader", "displayName": "Passing Leader", "leaders": [{"displayValue": "26/39, 206 YDS", "athlete": {"id": "3046779", "displayName": "Jared Goff"}}]}]}
    op = {"id": oid, "homeAway": "away" if home else "home", "winner": (them > us) if state == "post" else None, "team": {"id": oid, "abbreviation": opp, "displayName": opp + " Team", "color": "aa3333"},
          "score": {"value": them, "displayValue": str(them)} if state == "post" else None}
    return {"id": "9%02d" % i, "date": d, "competitions": [{"date": d, "status": {"type": {"state": state, "shortDetail": "Final" if state == "post" else ""}}, "broadcasts": [{"media": {"shortName": "FOX"}}], "competitors": [me, op]}]}
SCHED8 = {"team": {"id": "8", "abbreviation": "DET", "displayName": "Detroit Lions", "color": "0076b6", "recordSummary": "8-3", "standingSummary": "2nd in NFC North", "groups": {"id": "10"}},
          "events": [sched_game(i, iso(now + (i - 11) * 7 * 86400), o, str(100 + i), i % 2 == 0, 10 + (i * 7) % 25, 7 + (i * 5) % 24, "post" if i < 11 else "pre")
                     for i, o in enumerate(["NO", "CHI", "GB", "MIN", "TB", "DAL", "LAR", "SEA", "NYG", "ATL", "CHI", "GB", "MIN", "BUF"])]}
def ent(id, ab, nm, w, l):
    pct = w / (w + l)
    return {"team": {"id": id, "abbreviation": ab, "displayName": nm}, "stats": [{"name": "winPercent", "value": pct, "displayValue": ("%.3f" % pct)[1:]}, {"name": "overall", "displayValue": "%d-%d" % (w, l)}, {"name": "differential", "displayValue": "+12"}]}
DIV = {"standings": {"entries": [ent("3", "CHI", "Chicago Bears", 9, 2), ent("8", "DET", "Detroit Lions", 8, 3), ent("9", "GB", "Green Bay Packers", 6, 5)]}}
STAND_GROUP = dict(DIV, name="NFC North")
STAND_ALL = {"name": "National Football League", "children": [dict(DIV, name="American Football Conference"), dict(DIV, name="National Football Conference")]}
def RR(rd, name, grid, pos, pts, status="Finished"):
    return {"round": str(rd), "raceName": name + " Grand Prix", "Results": [{"grid": str(grid), "position": str(pos), "positionText": str(pos) if status == "Finished" else "R", "points": str(pts), "status": status,
            "Driver": {"driverId": "hadjar", "permanentNumber": "6", "code": "HAD", "givenName": "Isack", "familyName": "Hadjar", "nationality": "French", "dateOfBirth": "2004-09-28"}, "Constructor": {"name": "RB F1 Team"}}]}
DRV = {"MRData": {"RaceTable": {"Races": [RR(1, "Australian", 11, 8, 4), RR(2, "Chinese", 7, 5, 10), RR(3, "Japanese", 14, 0, 0, "Collision")]}}}
DRVS = {"MRData": {"StandingsTable": {"StandingsLists": [{"DriverStandings": [{"position": "9", "points": "14", "wins": "0", "Constructors": [{"name": "RB F1 Team"}]}]}]}}}
DRVI = {"MRData": {"DriverTable": {"Drivers": [RR(1, "x", 0, 0, 0)["Results"][0]["Driver"]]}}}
FONTCSS = ("@font-face{font-family:'EB Garamond';src:url(/fonts/EBGaramond%5Bwght%5D.ttf);font-weight:400 800}"
           "@font-face{font-family:'Source Serif 4';src:url(/fonts/SourceSerif4%5Bopsz,wght%5D.ttf);font-weight:200 900}")

async def route(r):
    u = r.request.url
    if u.startswith("http://localhost:%d" % PORT): return await r.continue_()
    if "fonts.googleapis.com" in u: return await r.fulfill(status=200, body=FONTCSS, headers={"Content-Type": "text/css"})
    body = {"events": []}
    if "football/nfl/scoreboard" in u: body = NFL
    elif "mens-college-basketball/scoreboard" in u: body = NCAAM
    elif "summary?event=402" in u: body = SUM402
    elif "summary?event=401" in u: body = SUM401
    elif "summary?event=501" in u: body = SUM501
    elif "/teams/8/schedule" in u: body = SCHED8
    elif "/standings" in u and "group=" in u: body = STAND_GROUP
    elif "football/nfl/standings" in u: body = STAND_ALL
    elif "drivers/hadjar/results" in u: body = DRV
    elif "drivers/hadjar/driverStandings" in u: body = DRVS
    elif "drivers/hadjar.json" in u: body = DRVI
    elif "polymarket" in u: body = []
    await r.fulfill(status=200, body=json.dumps(body), headers={"Access-Control-Allow-Origin": "*", "Content-Type": "application/json"})

DRAWN_JS = "(sel) => { const c = document.querySelector(sel); if (!c || !c.width) return false; const d = c.getContext('2d').getImageData(0,0,c.width,c.height).data; for (let i = 3; i < d.length; i += 4) if (d[i]) return true; return false; }"
FAILS = []
def check(ok, what):
    print(("  ok    " if ok else "  FAIL  ") + what)
    if not ok: FAILS.append(what)

async def page(b, w, hsh="", mobile=False):
    pg = await b.new_page(viewport={"width": w, "height": 900}, device_scale_factor=2, has_touch=mobile, is_mobile=mobile, timezone_id=TZ)
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
    await pg.route("**/*", route)
    await pg.goto("http://localhost:%d/index.html%s" % (PORT, hsh))
    await pg.wait_for_timeout(1800)
    if os.environ.get("SHOTS"):   # SHOTS=1 saves what each check saw, to /tmp/check-*.png
        await pg.wait_for_timeout(800)
        await pg.screenshot(path="/tmp/check-%d%s.png" % (w, hsh.replace("#", "-")), full_page=True)
    return pg, errs

async def main():
    srv = subprocess.Popen([sys.executable, "-m", "http.server", str(PORT)], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1)
    try:
        async with async_playwright() as p:
            chrome = os.environ.get("CHROME") or ("/usr/bin/google-chrome" if os.path.exists("/usr/bin/google-chrome") else None)
            b = await p.chromium.launch(executable_path=chrome) if chrome else await p.chromium.launch()
            for w, label in [(393, "phone"), (440, "big phone"), (640, "small tablet"), (1280, "desktop")]:
                print("Scores list, %s (%d wide)" % (label, w))
                pg, errs = await page(b, w, mobile=w < 600)
                check(not errs, "no script errors" + (": " + errs[0] if errs else ""))
                inside = await pg.evaluate("!!document.querySelector('.wrap #games') && !!document.querySelector('.wrap .days')")
                check(inside, "the scores sit inside the page wrapper (a stray tag once broke the margins)")
                m = await pg.evaluate("""(() => { const h = document.querySelector('header .row').getBoundingClientRect(), g = document.querySelector('#games').getBoundingClientRect(), bd = document.querySelector('#board').getBoundingClientRect();
                    return [Math.round(h.left), Math.round(g.left), Math.round(h.right), Math.round(document.querySelector('.livec').getBoundingClientRect().right), Math.round(bd.right)] })()""")
                check(abs(m[0] - m[1]) <= 1, "scores line up with the masthead on the left (%s vs %s)" % (m[0], m[1]))
                check(abs(m[3] - m[4]) <= 2, "masthead reaches the page's right edge (live count %s, page %s)" % (m[3], m[4]))
                ov = await pg.evaluate("Math.max(...[...document.querySelectorAll('table.agate')].map(t => t.getBoundingClientRect().right)) - document.querySelector('#games').getBoundingClientRect().right")
                check(ov <= 1, "no score table runs past the page edge (%dpx over)" % ov)
                if ov > 1: print(await pg.evaluate("[...document.querySelectorAll('tr.row')].map(r=>[...r.cells].map(c=>c.className.split(' ')[0]+':'+Math.round(c.getBoundingClientRect().width)).join(' ')).join(' | ')"))
                ov2 = await pg.evaluate("document.documentElement.scrollWidth - innerWidth")
                check(ov2 <= 0, "the page can't be pushed sideways (%dpx)" % ov2)
                ws = await pg.evaluate("[...document.querySelectorAll('tr.row td.sp canvas')].map(c => Math.round(c.getBoundingClientRect().width))")
                lo = 100 if w < 600 else 160
                check(ws and min(ws) >= lo, "every margin line gets room: narrowest %s, want %d+" % (min(ws) if ws else None, lo))
                check(ws and max(ws) - min(ws) <= 3, "margin lines line up across leagues (%s)" % sorted(set(ws)))
                drawn = await pg.evaluate("""[...document.querySelectorAll('tr.row td.sp canvas')].every(c => { if (!c.width) return false;
                    const d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data; for (let i = 3; i < d.length; i += 4) if (d[i]) return true; return false; })""")
                check(drawn, "every margin line is drawn")
                mf = await pg.evaluate("""(() => { const c = document.querySelector('canvas.mfield'); if (!c || !c.width) return false; const d = c.getContext('2d').getImageData(0,0,c.width,c.height).data; for (let i = 3; i < d.length; i += 4) if (d[i]) return true; return false; })()""")
                check(mf, "live football shows its little field under the clock")
                await pg.close()
            print("Game page, phone")
            pg, errs = await page(b, 393, "#game-ncaam-502", True)
            check(not errs, "no script errors" + (": " + errs[0] if errs else ""))
            o = await pg.evaluate("""(() => { const a = document.querySelector('.dteam.away .nm').getBoundingClientRect(), m = document.querySelector('.dmid').getBoundingClientRect(), h = document.querySelector('.dteam.home .nm').getBoundingClientRect();
                return [a.right, m.left, m.right, h.left] })()""")
            check(o[0] <= o[1] + 1 and o[2] <= o[3] + 1, "long team names never run into the clock")
            await pg.close()
            pg, errs = await page(b, 393, "#game-nfl-402", True)
            await pg.wait_for_timeout(800)
            check(not errs, "game with scoring plays opens without errors")
            n = await pg.evaluate("document.querySelectorAll('table.plays-t tr.pl').length")
            check(n == 4, "scoring plays listed (%d)" % n)
            try:   # slower machines take a moment to load the game
                await pg.wait_for_function("(() => { const c = document.querySelector('#driver canvas'); if (!c || !c.width) return false; const d = c.getContext('2d').getImageData(0,0,c.width,c.height).data; for (let i = 3; i < d.length; i += 4) if (d[i]) return true; return false; })()", timeout=8000)
                big = True
            except Exception:
                big = False
            check(big, "the big margin chart is drawn")
            r = await pg.evaluate("(() => { const r = document.querySelector('#driver canvas').getBoundingClientRect(); return [r.left, r.right, innerWidth, document.documentElement.scrollWidth] })()")
            check(abs(r[0]) <= 1 and abs(r[1] - r[2]) <= 1 and r[3] <= r[2], "the margin chart runs edge to edge, no sideways scroll (%d-%d of %d)" % (r[0], r[1], r[2]))
            await pg.close()
            print("Live football game, phone")
            pg, errs = await page(b, 393, "#game-nfl-401", True)
            check(not errs, "no script errors" + (": " + errs[0] if errs else ""))
            for sel, what in [("canvas.field", "the field strip is drawn"), ("canvas.drives", "the drive chart is drawn")]:
                try:
                    await pg.wait_for_function("(%s)('%s')" % (DRAWN_JS, sel), timeout=8000); ok = True
                except Exception: ok = False
                check(ok, what)
            txt = await pg.evaluate("(document.querySelector('.fsit') || {}).textContent || ''")
            check("CHI ball" in txt and "3rd and 7" in txt, "the field says whose ball and the down (%r)" % txt)
            st = await pg.evaluate("[...document.querySelectorAll('#detail canvas[data-k]')].map(c => c.className)")
            check(len(st) >= 3, "game charts are set to draw in on scroll (%d)" % len(st))
            # a short screen, so the drives start out of view and are scrolled to
            await pg.set_viewport_size({"width": 393, "height": 500}); await pg.evaluate("window.scrollTo(0, 0)"); await pg.wait_for_timeout(600)
            blank = await pg.evaluate("""(() => { const c = document.querySelector('canvas.drives'), w = c.width, d = c.getContext('2d').getImageData(0, 0, w, c.height).data; let n = 0; for (let i = 3; i < d.length; i += 4) if (d[i]) n++; return n })()""")
            await pg.evaluate("document.querySelector('canvas.drives').scrollIntoView({block: 'center'})"); await pg.wait_for_timeout(350)
            mid = await pg.evaluate("""(() => { const c = document.querySelector('canvas.drives'), w = c.width, d = c.getContext('2d').getImageData(0, 0, w, c.height).data; let n = 0; for (let i = 3; i < d.length; i += 4) if (d[i]) n++; return n })()""")
            await pg.wait_for_timeout(1250)
            u = await pg.evaluate("document.querySelector('canvas.drives').classList.contains('unseen')")
            check(not u, "the drive chart draws in once scrolled to")
            await pg.wait_for_timeout(1500)
            px = await pg.evaluate("""(() => { const c = document.querySelector('canvas.drives'), d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data; let n = 0; for (let i = 3; i < d.length; i += 4) if (d[i]) n++; return n })()""")
            check(px > 500, "the drives have run their course (%d px)" % px)
            check(blank < mid < px * 0.95, "the drives run in rather than appearing at once (%d, %d, then %d px)" % (blank, mid, px))
            await pg.close()
            print("Live basketball game, phone")
            pg, errs = await page(b, 393, "#game-ncaam-501", True)
            check(not errs, "no script errors" + (": " + errs[0] if errs else ""))
            for sel, what in [("canvas.court", "the shot charts are drawn"), ("canvas.hot", "the top scorers' lines are drawn"), ("#driver canvas", "the margin chart is drawn")]:
                try:
                    await pg.wait_for_function("(%s)('%s')" % (DRAWN_JS, sel), timeout=8000); ok = True
                except Exception: ok = False
                check(ok, what)
            b2 = await pg.evaluate("(() => { const d = document.querySelector('.dduel .drows'); return d ? d.className : '' })()")
            check("rv-bars" in b2, "team stats bars are set to grow in (%r)" % b2)
            n = await pg.evaluate("[document.querySelectorAll('canvas.court').length, document.querySelectorAll('.dduel .drow').length, document.querySelectorAll('.hrow').length, document.querySelectorAll('.dfouls .frow').length]")
            check(n[0] == 2, "a court for each team (%d)" % n[0])
            check(n[1] >= 4, "team stats compared side by side (%d rows)" % n[1])
            check(n[2] == 4, "two top scorers a side (%d)" % n[2])
            check(n[3] == 2, "fouls and timeouts for each team (%d)" % n[3])
            cap = await pg.evaluate("(document.querySelector('#driver .cap') || {}).textContent || ''")
            check("runs of" in cap and "ESPN" in cap, "the chart notes the runs and ESPN's line (%r)" % cap[:60])
            ov = await pg.evaluate("document.documentElement.scrollWidth - innerWidth")
            check(ov <= 0, "the game page can't be pushed sideways (%dpx)" % ov)
            await pg.close()
            for hsh, sel, what in [("#team-nfl-8", ".tsched tr", "team page"), ("#standings-nfl", ".tstand tr", "league standings"), ("#driver-hadjar", "canvas.fin", "F1 driver page")]:
                print(what.capitalize())
                pg, errs = await page(b, 393, hsh, True)
                await pg.wait_for_timeout(600)
                check(not errs, "no script errors" + (": " + errs[0] if errs else ""))
                check(await pg.evaluate("document.querySelectorAll('%s').length" % sel) > 0, what + " shows its content")
                await pg.close()
            await b.close()
    finally:
        srv.terminate()
    print("\n%s" % ("All checks passed." if not FAILS else "%d check(s) failed." % len(FAILS)))
    sys.exit(1 if FAILS else 0)

asyncio.run(main())
