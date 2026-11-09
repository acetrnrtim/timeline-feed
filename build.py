#!/usr/bin/env python3
"""Build widget.json (today's tasks + Meeting Tracker) from a saved dump of the timeline's data/users/me docs.
Usage: python3 build.py <dir containing the doc JSON files> [YYYY-MM-DD]"""
import json, glob, datetime, sys, os
from zoneinfo import ZoneInfo
D = sys.argv[1].rstrip('/') + '/'
now = datetime.datetime.now(ZoneInfo('America/New_York'))
today = sys.argv[2] if len(sys.argv) > 2 else now.date().isoformat()
docs = {}
for f in glob.glob(D + '*.json'):
    d = json.load(open(f))
    docs[d.get('id') or os.path.basename(f)[:-5]] = d.get('data', d)
cats = {k: v['name'] for k, v in docs.items() if v.get('kind') == 'cat'}
parse = datetime.date.fromisoformat
def occurs(r, d):
    if d < r['start'] or (r.get('end') and d > r['end']) or d in r.get('skips', []): return False
    if r['freq'] == 'interval': return (parse(d) - parse(r['start'])).days % max(1, r.get('every', 2)) == 0
    if r['freq'] == 'weekly': return (parse(d).weekday() + 1) % 7 in r.get('days', [])
    return True
out = []
for k, v in docs.items():
    if v.get('kind') == 'task' and v.get('date') == today:
        out.append(dict(id=k, label=v['label'], abc=v.get('abc'), cat=cats.get(v.get('cat')), done=bool(v.get('done')), order=v.get('order', 0)))
    if v.get('kind') == 'rec' and v.get('start') and occurs(v, today):
        out.append(dict(id=k + '@' + today, label=v['label'], abc=v.get('abc'), cat=cats.get(v.get('cat')), done=bool((v.get('done') or {}).get(today)), order=v.get('order', 0)))
rank = {'A': 0, 'B': 1, 'C': 2, 'R': 3}
out.sort(key=lambda e: (rank.get(e['abc'], 4), e['order']))
for e in out: e.pop('order')
trk = None
for k, v in docs.items():
    if v.get('kind') == 'rec' and v.get('track'):
        n = sum(1 for x in (v.get('done') or {}).values() if x)
        n += sum(1 for t in docs.values() if t.get('kind') == 'task' and t.get('done') and (t.get('fromRec') == k or (v.get('abc') == 'R' and t.get('abc') == 'R')))
        trk = dict(label=v.get('trackLabel') or v['label'], count=n, goal=v.get('trackGoal'))
lim = {'A': 2, 'B': 4, 'C': 2, 'R': 1}
open_ = {L: max(0, lim[L] - sum(1 for e in out if e['abc'] == L)) for L in lim}
json.dump(dict(date=today, generated=now.isoformat(timespec='seconds'), tasks=out, tracker=trk, openSlots=open_),
          open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'widget.json'), 'w'), indent=1)
print('built', today, len(out), 'tasks', trk)
