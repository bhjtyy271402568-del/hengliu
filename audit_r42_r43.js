const fs = require('fs');

const schRecords = JSON.parse(fs.readFileSync('audit_sch_records.json', 'utf8'));

// Search for WIREs and ATTRs around R42, R43, R47, R33, R34, R68, R69, Q1, Q2, Q5, Q6
const comps = new Map();
for (const r of schRecords) {
  if (r.head?.type === 'COMPONENT') {
    comps.set(r.head.id, { id: r.head.id, designator: '', attrs: {} });
  }
}
for (const r of schRecords) {
  if (r.head?.type === 'ATTR' && r.body?.parentId && comps.has(r.body.parentId)) {
    if (r.body.key === 'Designator') comps.get(r.body.parentId).designator = r.body.value;
    comps.get(r.body.parentId).attrs[r.body.key || r.head.id] = r.body.value;
  }
}

const checkList = ['R42', 'R43', 'R47', 'R33', 'R34', 'R68', 'R69', 'Q1', 'Q2', 'Q5', 'Q6'];
for (const [id, c] of comps.entries()) {
  if (checkList.includes(c.designator)) {
    console.log(`Comp: ${c.designator.padEnd(5)} | ID: ${id} | Val: ${c.attrs['Value']} | Comment: ${c.attrs['Comment']}`);
  }
}
