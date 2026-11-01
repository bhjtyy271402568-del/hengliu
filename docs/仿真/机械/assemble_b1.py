"""把 B1 外观件换进 Codex A0 装配（去掉 FRAME / SHELL / FAN_MOUNT），保留两板原生模型颜色。
用法：python assemble_b1.py A0装配.step b1目录 输出目录 [网格精度mm]
输出：B1_双板散热完整装配.step（不含刻字填色）、B1_render.glb（含刻字填色，供渲染）。"""
import sys, os, pickle, time
from OCP.STEPCAFControl import STEPCAFControl_Reader, STEPCAFControl_Writer
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString, TCollection_AsciiString
from OCP.XCAFDoc import XCAFDoc_DocumentTool, XCAFDoc_ColorType
from OCP.TDF import TDF_LabelSequence, TDF_Label
from OCP.TDataStd import TDataStd_Name
from OCP.Quantity import Quantity_Color, Quantity_TOC_RGB
from OCP.TopLoc import TopLoc_Location
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.RWGltf import RWGltf_CafWriter
from OCP.RWMesh import RWMesh_NameFormat
from OCP.TColStd import TColStd_IndexedDataMapOfStringString
from OCP.Message import Message_ProgressRange
from OCP.STEPControl import STEPControl_AsIs
A0, B1, OUT = sys.argv[1:4]; DEF = float(sys.argv[4]) if len(sys.argv) > 4 else 0.15
os.makedirs(OUT, exist_ok=True)
t = time.time()
doc = TDocStd_Document(TCollection_ExtendedString('doc'))
r = STEPCAFControl_Reader(); r.SetNameMode(True); r.SetColorMode(True); r.ReadFile(A0); r.Transfer(doc)
st = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main()); ct = XCAFDoc_DocumentTool.ColorTool_s(doc.Main())
roots = TDF_LabelSequence(); st.GetFreeShapes(roots); root = roots.Value(1)
print('read', round(time.time() - t), 's')
def name(l):
    n = TDataStd_Name(); return n.Get().ToExtString() if l.FindAttribute(TDataStd_Name.GetID_s(), n) else '?'
comps = TDF_LabelSequence(); st.GetComponents_s(root, comps)
drop = []
for i in range(1, comps.Length() + 1):
    c = comps.Value(i); rl = TDF_Label(); st.GetReferredShape_s(c, rl)
    if name(rl) in ('FRAME', 'SHELL', 'FAN_MOUNT'): drop.append(c)
for c in drop: st.RemoveComponent(c)
print('removed', len(drop))
P = pickle.load(open(os.path.join(B1, 'parts.pkl'), 'rb'))
def add(nm, shape, rgb):
    loc = shape.wrapped.Location()                       # 顶层带位置的形状（如顶盖刻字），位置要放到实例上，否则会丢
    lab = st.AddShape(shape.wrapped.Located(TopLoc_Location()), False)
    TDataStd_Name.Set_s(lab, TCollection_ExtendedString(nm))
    ct.SetColor(lab, Quantity_Color(rgb[0], rgb[1], rgb[2], Quantity_TOC_RGB), XCAFDoc_ColorType.XCAFDoc_ColorGen)
    st.AddComponent(root, lab, loc)
for k, (shape, rgb) in P['parts'].items(): add('B1_' + k, shape, rgb)
st.UpdateAssemblies()
w = STEPCAFControl_Writer(); w.SetNameMode(True); w.SetColorMode(True)
w.Transfer(doc, STEPControl_AsIs); w.Write(os.path.join(OUT, 'B1_双板散热完整装配.step'))
print('step written', round(time.time() - t), 's')
for k, shape in P['ink'].items(): add(k, shape, (0.86, 0.87, 0.88))
st.UpdateAssemblies()
shape = st.GetShape_s(root)
BRepMesh_IncrementalMesh(shape, DEF, False, 0.5, True)
gw = RWGltf_CafWriter(TCollection_AsciiString(os.path.join(OUT, 'B1_render.glb')), True)
gw.SetNodeNameFormat(RWMesh_NameFormat.RWMesh_NameFormat_ProductOrInstance)   # 节点用零件名，方便网页按名字设材质
gw.Perform(doc, TColStd_IndexedDataMapOfStringString(), Message_ProgressRange())
print('glb written', round(time.time() - t), 's', os.path.getsize(os.path.join(OUT, 'B1_render.glb')) // 1024, 'KB')
