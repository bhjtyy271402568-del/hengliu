const fs = require('fs');
const schRecords = JSON.parse(fs.readFileSync('audit_sch_records.json', 'utf8'));
const fullBom = JSON.parse(fs.readFileSync('full_bom.json', 'utf8'));

// In schematic, components have PIN objects inside them or as separate records
const pins = schRecords.filter(r => r.head?.type === 'PIN');
const wires = schRecords.filter(r => r.head?.type === 'WIRE');
const netLabels = schRecords.filter(r => r.head?.type === 'NETLABEL');

// Find U1
const comps = schRecords.filter(r => r.head?.type === 'COMPONENT');
let u1Id = null;
for(const r of schRecords) {
  if (r.head?.type === 'ATTR' && r.body?.value === 'U1') {
    u1Id = r.body.parentId;
    break;
  }
}

const u1Pins = pins.filter(p => p.body?.componentId === u1Id || p.body?.ownerId === u1Id || p.head?.parentId === u1Id || (p.body && JSON.stringify(p.body).includes(u1Id)));
console.log(`Found ${u1Pins.length} pins for U1`);
if (u1Pins.length === 0) {
  // PINs might be stored differently. Let's just search for the strings 'U1' or look for specific passive components.
}

// Instead of complex parsing, let's just use the bounding box logic we used before.
const compMap = new Map();
for (const c of comps) {
  compMap.set(c.head.id, { id: c.head.id, x: c.body?.x, y: c.body?.y, attrs: {} });
}
for (const r of schRecords) {
  if (r.head?.type === 'ATTR' && r.body?.parentId && compMap.has(r.body.parentId)) {
    compMap.get(r.body.parentId).attrs[r.body.key || r.head.id] = r.body.value;
  }
}

// Get comps around U1 (X: 800~1000, Y: -650~-400)
const u1AreaComps = Array.from(compMap.values()).filter(c => c.x > 750 && c.x < 1100 && c.y > -700 && c.y < -350);
console.log('\n--- Components around U1 ---');
for(const c of u1AreaComps) {
  const des = c.attrs['Designator'];
  if (des) {
    const val = c.attrs['Value'] || '';
    console.log(`${des.padEnd(5)}: ${val.padEnd(10)} at (${c.x}, ${c.y})`);
  }
}

// Also let's check input area (Q3, Q12) around X: 1100~1500, Y: -800~-500
const inAreaComps = Array.from(compMap.values()).filter(c => c.x > 1100 && c.x < 1700 && c.y > -1000 && c.y < -500);
console.log('\n--- Components around Input (Q3, Q12) ---');
for(const c of inAreaComps) {
  const des = c.attrs['Designator'];
  if (des) {
    const val = c.attrs['Value'] || '';
    console.log(`${des.padEnd(5)}: ${val.padEnd(10)} at (${c.x}, ${c.y})`);
  }
}

