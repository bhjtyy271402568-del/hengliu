"""只导出 A0 的外壳件（FRAME / SHELL / FAN_MOUNT）为 GLB，供网页里和 B1 对比。
用法：python -I export_a0_shell.py A0装配.step 输出.glb [网格精度mm]"""
import sys
from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString, TCollection_AsciiString
from OCP.XCAFDoc import XCAFDoc_DocumentTool
from OCP.TDF import TDF_LabelSequence, TDF_Label
from OCP.TDataStd import TDataStd_Name
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.RWGltf import RWGltf_CafWriter
from OCP.RWMesh import RWMesh_NameFormat
from OCP.TColStd import TColStd_IndexedDataMapOfStringString
from OCP.Message import Message_ProgressRange
A0, OUT = sys.argv[1:3]; DEF = float(sys.argv[3]) if len(sys.argv) > 3 else 0.2
KEEP = ('FRAME', 'SHELL', 'FAN_MOUNT')
doc = TDocStd_Document(TCollection_ExtendedString('doc'))
r = STEPCAFControl_Reader(); r.SetNameMode(True); r.SetColorMode(True); r.ReadFile(A0); r.Transfer(doc)
st = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
roots = TDF_LabelSequence(); st.GetFreeShapes(roots); root = roots.Value(1)
def name(l):
    n = TDataStd_Name(); return n.Get().ToExtString() if l.FindAttribute(TDataStd_Name.GetID_s(), n) else '?'
cs = TDF_LabelSequence(); st.GetComponents_s(root, cs)
for i in range(1, cs.Length() + 1):
    c = cs.Value(i); rl = TDF_Label(); st.GetReferredShape_s(c, rl)
    if name(rl) not in KEEP: st.RemoveComponent(c)
st.UpdateAssemblies()
BRepMesh_IncrementalMesh(st.GetShape_s(root), DEF, False, 0.5, True)
gw = RWGltf_CafWriter(TCollection_AsciiString(OUT), True)
gw.SetNodeNameFormat(RWMesh_NameFormat.RWMesh_NameFormat_ProductOrInstance)
gw.Perform(doc, TColStd_IndexedDataMapOfStringString(), Message_ProgressRange())
print('ok', OUT)
