const fs = require('fs');

const schRecords = JSON.parse(fs.readFileSync('audit_sch_records.json', 'utf8'));

// Build complete map of all components, pins, and nets in latest 8.13 5 SCH
const comps = new Map();
for (const r of schRecords) {
  if (r.head?.type === 'COMPONENT') {
    comps.set(r.head.id, { id: r.head.id, ticket: r.head.ticket, body: r.body, attrs: {}, pins: [] });
  }
}
for (const r of schRecords) {
  if (r.head?.type === 'ATTR') {
    const b = r.body;
    if (b && b.parentId && comps.has(b.parentId)) {
      const comp = comps.get(b.parentId);
      comp.attrs[b.key || r.head.id] = b.value;
    }
  }
}

// Map each component by Designator
const desMap = new Map();
for (const [id, c] of comps.entries()) {
  const des = c.attrs['Designator'] || c.attrs['designator'];
  if (des) {
    desMap.set(des, c);
  }
}

console.log(`Found ${desMap.size} designators in latest SCH.`);

// Let's inspect specific components in detail
const targets = [
  'U1', 'U6', 'U5', 'U3', 'U4', 'U7', 'U2', 'U8', 'U9',
  'Q1', 'Q2', 'Q3', 'Q4', 'Q5', 'Q6', 'Q11', 'Q12',
  'D6', 'D8', 'D10', 'D1', 'D2', 'D3', 'D4', 'D5', 'D7', 'D9', 'D11', 'D13',
  'L6', 'L7', 'L2',
  'R1', 'R12', 'R2', 'R19', 'R56', 'R57', 'R58', 'R30', 'R49', 'R4', 'C42',
  'R6', 'C5', 'R17', 'C9', 'R22', 'R28', 'R13', 'R16', 'R29', 'C22', 'C25',
  'R8', 'R9', 'R10', 'R11', 'C7', 'C8', 'R68', 'R69',
  'R23', 'R24', 'C49', 'R59', 'R60', 'C77', 'C75', 'C76', 'C85', 'C86',
  'R33', 'R34', 'R35', 'R44', 'R50', 'R54', 'R64', 'R65', 'R66'
];

const targetDetails = {};
for (const t of targets) {
  const c = desMap.get(t);
  if (c) {
    targetDetails[t] = {
      designator: t,
      value: c.attrs['Value'] || c.attrs['value'] || c.attrs['Comment'] || '',
      supplierPart: c.attrs['Supplier Part'] || c.attrs['LCSC'] || '',
      mfrPart: c.attrs['Manufacturer Part'] || c.attrs['DeviceName'] || '',
      footprint: c.attrs['Footprint'] || c.attrs['FootprintName'] || '',
      dnp: c.attrs['DNP'] || c.attrs['BOM'] || '',
      allAttrs: c.attrs
    };
  } else {
    targetDetails[t] = { designator: t, status: 'NOT_FOUND' };
  }
}

console.log(JSON.stringify(targetDetails, null, 2));
fs.writeFileSync('target_components_details.json', JSON.stringify(targetDetails, null, 2));
