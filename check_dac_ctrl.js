const fs = require('fs');

const schRecords = JSON.parse(fs.readFileSync('audit_sch_records.json', 'utf8'));

// 1. Trace DAC to CTRL1
// MCU PA4 is connected to what?
let pa4Net = null;
let ctrl1Net = null;

// Find MCU component U2 and its pin 14 (PA4)
const schComps = new Map();
for (const r of schRecords) {
  if (r.head?.type === 'COMPONENT') {
    schComps.set(r.head.id, { id: r.head.id, attrs: {} });
  }
}
for (const r of schRecords) {
  if (r.head?.type === 'ATTR' && r.body?.parentId && schComps.has(r.body.parentId)) {
    schComps.get(r.body.parentId).attrs[r.body.key || r.head.id] = r.body.value;
  }
}

// Just output components near MCU and LT3763 CTRL pins
const mcuComps = Array.from(schComps.values()).filter(c => c.attrs['Designator'] === 'U2');
const ltComps = Array.from(schComps.values()).filter(c => c.attrs['Designator'] === 'U1');

console.log('MCU U2:', mcuComps.map(c => c.attrs['Manufacturer Part']));
console.log('LT3763 U1:', ltComps.map(c => c.attrs['Manufacturer Part']));

// Let's find all resistors connected to DAC_OUT, CTRL1
const texts = schRecords.filter(r => r.head?.type === 'TEXT');
console.log('\nTexts near CTRL1 / DAC:');
const dacTexts = texts.filter(t => t.body?.value?.includes('DAC') || t.body?.value?.includes('CTRL'));
console.log(dacTexts.map(t => t.body?.value));
