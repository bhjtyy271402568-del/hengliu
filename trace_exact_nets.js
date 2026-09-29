const fs = require('fs');

const schRecords = JSON.parse(fs.readFileSync('audit_sch_records.json', 'utf8'));
const pcbRecords = JSON.parse(fs.readFileSync('audit_pcb_records.json', 'utf8'));

// 1. SCH Components
const schComps = new Map();
for (const r of schRecords) {
  if (r.head?.type === 'COMPONENT') {
    schComps.set(r.head.id, {
      id: r.head.id,
      ticket: r.head.ticket,
      body: r.body,
      attrs: {}
    });
  }
}
for (const r of schRecords) {
  if (r.head?.type === 'ATTR' && r.body?.parentId && schComps.has(r.body.parentId)) {
    schComps.get(r.body.parentId).attrs[r.body.key || r.head.id] = r.body.value;
  }
}

// 2. PCB Components
const pcbComps = new Map();
for (const r of pcbRecords) {
  if (r.head?.type === 'COMPONENT') {
    pcbComps.set(r.head.id, {
      id: r.head.id,
      body: r.body,
      attrs: {},
      pads: []
    });
  }
}
for (const r of pcbRecords) {
  if (r.head?.type === 'ATTR' && r.body?.parentId && pcbComps.has(r.body.parentId)) {
    pcbComps.get(r.body.parentId).attrs[r.body.key || r.head.id] = r.body.value;
  }
}

// Build designator map for SCH and PCB
const schByDes = new Map();
for (const [id, c] of schComps.entries()) {
  const des = c.attrs['Designator'] || c.attrs['designator'];
  if (des) schByDes.set(des, c);
}

const pcbByDes = new Map();
for (const [id, c] of pcbComps.entries()) {
  const des = c.attrs['Designator'] || c.attrs['designator'];
  if (des) pcbByDes.set(des, c);
}

console.log(`SCH by Des: ${schByDes.size}, PCB by Des: ${pcbByDes.size}`);

// Let's inspect R33, R34 in SCH and PCB
console.log('\n=== R33 & R34 IN SCHEMATIC ===');
console.log('R33:', JSON.stringify(schByDes.get('R33'), null, 2));
console.log('R34:', JSON.stringify(schByDes.get('R34'), null, 2));

console.log('\n=== R33 & R34 IN PCB ===');
console.log('R33 PCB:', JSON.stringify(pcbByDes.get('R33'), null, 2));
console.log('R34 PCB:', JSON.stringify(pcbByDes.get('R34'), null, 2));
