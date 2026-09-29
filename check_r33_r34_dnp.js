const fs = require('fs');

const pcbRecords = JSON.parse(fs.readFileSync('audit_pcb_records.json', 'utf8'));
const schRecords = JSON.parse(fs.readFileSync('audit_sch_records.json', 'utf8'));

// Find U6, R33, R34 in SCH and PCB
const comps = new Map();
for (const r of schRecords) {
  if (r.head?.type === 'COMPONENT') comps.set(r.head.id, { id: r.head.id, attrs: {} });
}
for (const r of schRecords) {
  if (r.head?.type === 'ATTR' && r.body?.parentId && comps.has(r.body.parentId)) {
    comps.get(r.body.parentId).attrs[r.body.key || r.head.id] = r.body.value;
  }
}

const u6 = Array.from(comps.values()).find(c => c.attrs['Designator'] === 'U6');
const r33 = Array.from(comps.values()).find(c => c.attrs['Designator'] === 'R33');
const r34 = Array.from(comps.values()).find(c => c.attrs['Designator'] === 'R34');

console.log('R33 SCH DNP Status:', r33?.attrs['Add into BOM'], r33?.attrs['Convert to PCB']);
console.log('R34 SCH DNP Status:', r34?.attrs['Add into BOM'], r34?.attrs['Convert to PCB']);

// Let's trace R33 and R34 PADs in PCB to see what networks they connect
const padNets = [];
for (const r of pcbRecords) {
  if (r.head?.type === 'PAD_NET') {
    let idParts;
    try { idParts = JSON.parse(r.head.id); } catch(e){}
    padNets.push({ compId: idParts?.[1], pin: idParts?.[2], padId: idParts?.[3] });
  }
}

// How to get the network names for R33/R34 pads?
// In easyEDA pro, PAD_NET object body is { net: "netId" } ? No, usually the PAD object has `net` attribute.
const pads = pcbRecords.filter(r => r.head?.type === 'PAD');
for (const p of pads) {
  if (p.body?.componentId === r33?.id || p.body?.componentId === r34?.id) {
    const netName = pcbRecords.find(r => r.head?.id === p.body?.net)?.body?.name;
    console.log(`PAD ${p.body?.pin} of ${p.body?.componentId === r33?.id ? 'R33' : 'R34'} is on network: ${netName} (NetID: ${p.body?.net})`);
  }
}

// Find R33 and R34 in full BOM
const bom = JSON.parse(fs.readFileSync('full_bom.json', 'utf8'));
const r33Bom = bom.find(b => b.designator === 'R33');
const r34Bom = bom.find(b => b.designator === 'R34');
console.log('\nR33 in BOM:', r33Bom?.dnp, r33Bom?.value);
console.log('R34 in BOM:', r34Bom?.dnp, r34Bom?.value);
