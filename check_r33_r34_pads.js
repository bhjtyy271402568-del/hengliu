const fs = require('fs');

const pcbRecords = JSON.parse(fs.readFileSync('audit_pcb_records.json', 'utf8'));

const r33Id = '046b7c5b51227372';
const r34Id = '51a2d0e8e99c1bbe';

const pads = pcbRecords.filter(r => r.head?.type === 'PAD' && (r.body?.componentId === r33Id || r.body?.componentId === r34Id));
const nets = pcbRecords.filter(r => r.head?.type === 'NET');

console.log('R33 / R34 PADS:');
for (const p of pads) {
  const net = nets.find(n => n.head?.id === p.body?.net);
  const comp = p.body?.componentId === r33Id ? 'R33' : 'R34';
  console.log(`${comp} Pin ${p.body?.pin} -> NetID: ${p.body?.net}, NetName: ${net?.body?.name}`);
}
