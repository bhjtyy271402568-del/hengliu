const fs = require('fs');
const schRecords = JSON.parse(fs.readFileSync('audit_sch_records.json', 'utf8'));

const schComps = new Map();
for (const r of schRecords) {
  if (r.head?.type === 'COMPONENT') schComps.set(r.head.id, { id: r.head.id, attrs: {} });
}
for (const r of schRecords) {
  if (r.head?.type === 'ATTR' && r.body?.parentId && schComps.has(r.body.parentId)) {
    schComps.get(r.body.parentId).attrs[r.body.key || r.head.id] = r.body.value;
  }
}

const lt3763 = Array.from(schComps.values()).find(c => c.attrs['Designator'] === 'U1');

// Pin mappings for U1
// Let's find all components that connect to specific pins of U1.
// Since EasyEDA schematic lines are connected by geometry or NetLabels, we will look for components in close physical proximity or labeled nets.

// To make this precise, we can grep the netlist or just look at components around U1 (X: 860~1000, Y: -650~-450)
const schCompsList = Array.from(schComps.values());

function getCompVal(des) {
  const c = schCompsList.find(c => c.attrs['Designator'] === des);
  return c ? `${c.attrs['Value'] || ''} (${c.attrs['Manufacturer Part'] || ''})` : 'N/A';
}

console.log('--- Checking Key LT3763 Support Components ---');

// Known from previous contexts or we can search texts near them:
// SS capacitor
console.log('C44 (SS pin):', getCompVal('C44'));
console.log('C41 (SS pin):', getCompVal('C41')); // Just guessing common designators, we need to search value around pins

const nearbyComps = schCompsList.filter(c => {
  const x = parseFloat(c.attrs['x'] || c.x || 0); // Need to get coordinates properly, wait, x/y is in body
  return true;
});

// Since we have the full parsed BOM, let's look for typical capacitor/resistor values for these functions.
const bom = JSON.parse(fs.readFileSync('full_bom.json', 'utf8'));
for(const b of bom) {
  if (b.designator === 'C44' || b.designator === 'C45' || b.designator === 'C53') {
     console.log(b.designator, b.value, b.supplierPart);
  }
}

// Let's dump all caps near U1. U1 is at PCB X: ~9000. In schematic, U1 was in "Area 2" ?
// Actually we can just run a script to find nets connected to U1 pins.
