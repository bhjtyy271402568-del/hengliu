const fs = require('fs');

const schRecords = JSON.parse(fs.readFileSync('audit_sch_records.json', 'utf8'));

// Find all components in Power Stage
const powerDes = ['Q1', 'Q2', 'Q5', 'Q6', 'R5', 'R46', 'R32', 'R51', 'D5', 'C76', 'C91', 'C92', 'C93', 'C96', 'C97', 'L6', 'CN19'];

const comps = [];
for (const r of schRecords) {
  if (r.head?.type === 'COMPONENT') {
    comps.push(r);
  }
}
const compMap = new Map();
for (const c of comps) {
  compMap.set(c.head.id, { id: c.head.id, x: c.body?.x, y: c.body?.y, rotation: c.body?.rotation, attrs: {} });
}
for (const r of schRecords) {
  if (r.head?.type === 'ATTR' && r.body?.parentId && compMap.has(r.body.parentId)) {
    compMap.get(r.body.parentId).attrs[r.body.key || r.head.id] = r.body.value;
  }
}

console.log('=== POWER STAGE COMPONENTS DETAILS ===');
for (const [id, c] of compMap.entries()) {
  const des = c.attrs['Designator'];
  if (powerDes.includes(des)) {
    console.log(`Comp: ${des.padEnd(5)} | Val: ${(c.attrs['Value'] || c.attrs['Name'] || '').padEnd(12)} | Mfr: ${(c.attrs['Manufacturer Part'] || '').padEnd(20)} | Pos: (${c.x}, ${c.y}) | Rot: ${c.rotation}`);
  }
}

// Trace Wires and Texts around these components
const schTexts = schRecords.filter(r => r.head?.type === 'TEXT');
const powerTexts = schTexts.filter(t => t.body?.x >= 2100 && t.body?.x <= 2600 && t.body?.y >= -1350 && t.body?.y <= -900);
console.log('\n=== TEXTS & LABELS IN POWER STAGE ===');
console.log(powerTexts.map(t => `Text: "${t.body?.value}" at (${t.body?.x}, ${t.body?.y})`).join('\n'));
