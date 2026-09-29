const fs = require('fs');

const pcbRecords = JSON.parse(fs.readFileSync('audit_pcb_records.json', 'utf8'));
const r33Id = '046b7c5b51227372';

const pads = pcbRecords.filter(r => r.head?.type === 'PAD_NET' || r.head?.type === 'PAD' || (r.body && r.body.componentId === r33Id));
console.log('R33 related PCB records:');
console.log(JSON.stringify(pads.filter(p => JSON.stringify(p).includes(r33Id)), null, 2));

// Wait, the PAD_NET format was: ["PAD_NET","046b7c5b51227372","2","e7"]
const padNets = pcbRecords.filter(r => r.head?.type === 'PAD_NET' && r.head?.id?.includes(r33Id));
console.log('\nR33 PAD_NETs:');
console.log(JSON.stringify(padNets, null, 2));

// Find the corresponding nets for these PAD_NETs. The body of PAD_NET should contain the net name or id.
for (const p of padNets) {
  console.log('PAD_NET body:', p.body);
}

