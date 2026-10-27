import json, math, itertools
g = json.load(open('pagedata.json'))
def shape(c, p):
    x, y, w, h, net, num, th = p
    return dict(ref=c['r'], num=num, net=net, x0=x, y0=y, x1=x + w, y1=y + h, round=bool(th) and abs(w - h) < 0.05,
                layers={0, 1} if th else ({1} if c['b'] else {0}))
def gap(a, b):
    if a['round'] and b['round']:
        return math.dist(((a['x0']+a['x1'])/2, (a['y0']+a['y1'])/2), ((b['x0']+b['x1'])/2, (b['y0']+b['y1'])/2)) - (a['x1']-a['x0'])/2 - (b['x1']-b['x0'])/2
    if a['round'] or b['round']:
        r, q = (a, b) if a['round'] else (b, a)
        cx, cy, rad = (r['x0']+r['x1'])/2, (r['y0']+r['y1'])/2, (r['x1']-r['x0'])/2
        dx = max(q['x0'] - cx, 0, cx - q['x1']); dy = max(q['y0'] - cy, 0, cy - q['y1'])
        return math.hypot(dx, dy) - rad
    dx = max(a['x0'] - b['x1'], b['x0'] - a['x1'], 0); dy = max(a['y0'] - b['y1'], b['y0'] - a['y1'], 0)
    return math.hypot(dx, dy)
for board in ('main', 'aux'):
    S = [shape(c, p) for c in g[board]['c'] for p in c['p']]
    bad = []
    for a, b in itertools.combinations(S, 2):
        if a['ref'] == b['ref'] or not (a['layers'] & b['layers']):
            continue
        if a['net'] and a['net'] == b['net']:
            continue
        d = gap(a, b)
        if d < 0.2:
            bad.append((round(d, 2), f"{a['ref']}.{a['num']}({a['net']})", f"{b['ref']}.{b['num']}({b['net']})", '顶' if a['layers'] & b['layers'] == {0} else ('底' if a['layers'] & b['layers'] == {1} else '两层')))
    bad.sort()
    print('==', board, len(bad))
    for x in bad: print(' ', x)
