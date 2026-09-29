const fs = require('fs');

const schRecords = JSON.parse(fs.readFileSync('audit_sch_records.json', 'utf8'));

// Group SCH records
const comps = [];
const attrs = [];
const texts = [];
const wires = [];

for (const r of schRecords) {
  const t = r.head?.type;
  if (t === 'COMPONENT') comps.push(r);
  else if (t === 'ATTR') attrs.push(r);
  else if (t === 'TEXT') texts.push(r);
  else if (t === 'WIRE') wires.push(r);
}

const compMap = new Map();
for (const c of comps) {
  compMap.set(c.head.id, {
    id: c.head.id,
    x: c.body?.x,
    y: c.body?.y,
    rotation: c.body?.rotation,
    attrs: {}
  });
}
for (const a of attrs) {
  if (a.body?.parentId && compMap.has(a.body.parentId)) {
    compMap.get(a.body.parentId).attrs[a.body.key || a.head.id] = a.body.value;
  }
}

// Trace each component around key areas:
// Area 1: Power MOS (Q1, Q2, Q5, Q6)
// Area 2: LT3763 (U1)
// Area 3: Input protection (Q3, Q12, Q4, Q11, D6, U7)
// Area 4: Aux Buck 12V (U6), 5V (U5), 3.3V (U3, U4)
// Area 5: MCU (U2)

function getCompsInBox(minX, maxX, minY, maxY) {
  const list = [];
  for (const c of compMap.values()) {
    if (c.x >= minX && c.x <= maxX && c.y >= minY && c.y <= maxY) {
      list.push({
        des: c.attrs['Designator'],
        val: c.attrs['Value'] || c.attrs['Name'],
        x: c.x,
        y: c.y,
        mfr: c.attrs['Manufacturer Part']
      });
    }
  }
  return list;
}

console.log('=== COMPS NEAR Q1 (915, -310) ===');
console.log(getCompsInBox(800, 1100, -450, -200));

console.log('=== COMPS NEAR Q2, Q5, Q6 (2200~2500, -1300~-1000) ===');
console.log(getCompsInBox(2150, 2550, -1350, -950));

console.log('=== COMPS NEAR R33, R34 (800~1050, -950~-750) ===');
console.log(getCompsInBox(800, 1050, -950, -750));
