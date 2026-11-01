"""B1 外观件与 A0 内部件（两板原生模型、散热器、风扇、铜柱、导流板等）的干涉和最小间隙检查。
用法：cq 环境 python -I check_b1.py A0装配.step b1目录 [间隙阈值mm]
做法：先用面的包围盒（放大阈值）筛候选，再用 BRepExtrema 算精确最小距离；距离 0 时再算布尔交的体积。"""
import sys, os, pickle, time
from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString
from OCP.XCAFDoc import XCAFDoc_DocumentTool
from OCP.TDF import TDF_LabelSequence, TDF_Label
from OCP.TDataStd import TDataStd_Name
from OCP.TopLoc import TopLoc_Location
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
from OCP.GProp import GProp_GProps
from OCP.BRepGProp import BRepGProp
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_FACE, TopAbs_SOLID
A0, B1 = sys.argv[1:3]; TH = float(sys.argv[3]) if len(sys.argv) > 3 else 2.0
DROP = ('FRAME', 'SHELL', 'FAN_MOUNT')
t = time.time()
doc = TDocStd_Document(TCollection_ExtendedString('doc'))
r = STEPCAFControl_Reader(); r.SetNameMode(True); r.ReadFile(A0); r.Transfer(doc)
st = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
def name(l):
    n = TDataStd_Name(); return n.Get().ToExtString() if l.FindAttribute(TDataStd_Name.GetID_s(), n) else '?'
leaves = []   # (路径名, 形状)
def walk(lab, loc, path, depth):
    if st.IsAssembly_s(lab):
        cs = TDF_LabelSequence(); st.GetComponents_s(lab, cs)
        for i in range(1, cs.Length() + 1):
            c = cs.Value(i); rl = TDF_Label(); st.GetReferredShape_s(c, rl)
            nm = name(rl)
            if depth == 0 and nm in DROP: continue
            walk(rl, loc.Multiplied(st.GetLocation_s(c)), path + [nm], depth + 1)
    else:
        s = st.GetShape_s(lab).Moved(loc)
        ex = TopExp_Explorer(s, TopAbs_SOLID); k = 0
        while ex.More():
            leaves.append(('/'.join(path), ex.Current())); ex.Next(); k += 1
        if k == 0: leaves.append(('/'.join(path), s))
roots = TDF_LabelSequence(); st.GetFreeShapes(roots)
walk(roots.Value(1), TopLoc_Location(), [], 0)
print('read', round(time.time() - t), 's,', len(leaves), 'solids')
def bbox(s, g=0.0):
    b = Bnd_Box(); BRepBndLib.Add_s(s, b); b.Enlarge(g); return b
P = pickle.load(open(os.path.join(B1, 'parts.pkl'), 'rb'))['parts']
lb = [(p, s, bbox(s)) for p, s in leaves]
res = []
for k, (shape, _) in P.items():
    faces = []; ex = TopExp_Explorer(shape.wrapped, TopAbs_FACE)
    while ex.More(): faces.append(bbox(ex.Current(), TH)); ex.Next()
    for p, s, b in lb:
        if not any(not fb.IsOut(b) for fb in faces): continue
        d = BRepExtrema_DistShapeShape(shape.wrapped, s)
        dist = d.Value() if d.IsDone() else -1
        vol = 0.0
        if dist < 1e-6:
            cm = BRepAlgoAPI_Common(shape.wrapped, s); g = GProp_GProps(); BRepGProp.VolumeProperties_s(cm.Shape(), g); vol = g.Mass()
        if dist < TH: res.append((dist, vol, k, p))
res.sort()
print(f'B1 件与内部件间隙 < {TH} mm 的：{len(res)} 处')
for dist, vol, k, p in res:
    print(f'  {dist:6.2f} mm  交体积 {vol:8.2f} mm³  {k:20s} ↔ {p}')
print('done', round(time.time() - t), 's')
