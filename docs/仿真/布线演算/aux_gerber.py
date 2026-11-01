"""辅助板（两层）Gerber 渲染：板框原点 (0, 0)，y 向上，单位 mm。用法：/usr/bin/python3 aux_gerber.py Gerber目录 lay.pkl"""
import sys, pickle, review60_gerber as R
R.OX = R.OY = 0.0
out = {}
for f, L in (('Gerber_TopLayer.GTL', 1), ('Gerber_BottomLayer.GBL', 2), ('Gerber_TopSolderMaskLayer.GTS', 'tsm'), ('Gerber_BottomSolderMaskLayer.GBS', 'bsm'),
             ('Gerber_TopSilkscreenLayer.GTO', 'tso'), ('Gerber_BottomSilkscreenLayer.GBO', 'bso'), ('Gerber_TopPasteMaskLayer.GTP', 'tsp'), ('Gerber_BottomPasteMaskLayer.GBP', 'bsp')):
    g = R.render(sys.argv[1] + '/' + f); out[L] = g; print(f, round(g.area, 1), len(getattr(g, 'geoms', [g])))
pickle.dump(out, open(sys.argv[2], 'wb'))
