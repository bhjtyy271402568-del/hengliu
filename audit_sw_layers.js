const fs = require('fs');

const pcbRecords = JSON.parse(fs.readFileSync('audit_pcb_records.json', 'utf8'));

// 1. Find pads of L6, Q1, Q2, Q5, Q6
const q1_q2_q5_q6_l6 = ['Q1', 'Q2', 'Q5', 'Q6', 'L6', 'U1'];
const pcbComps = new Map();
for (const r of pcbRecords) {
  if (r.head?.type === 'COMPONENT') {
    pcbComps.set(r.head.id, { id: r.head.id, designator: '' });
  }
}
for (const r of pcbRecords) {
  if (r.head?.type === 'ATTR' && r.body?.parentId && pcbComps.has(r.body.parentId)) {
    if (r.body.key === 'Designator' || r.body.key === 'designator') {
      pcbComps.get(r.body.parentId).designator = r.body.value;
    }
  }
}

console.log('=== PCB COMPONENTS WITH DESIGNATORS ===');
const targetPcbComps = {};
for (const [id, c] of pcbComps.entries()) {
  if (q1_q2_q5_q6_l6.includes(c.designator)) {
    targetPcbComps[id] = c.designator;
    console.log(`Comp: ${c.designator.padEnd(6)} | ID: ${id}`);
  }
}

// Check PAD_NET for these components
for (const r of pcbRecords) {
  if (r.head?.type === 'PAD_NET') {
    let idParts;
    try { idParts = JSON.parse(r.head.id); } catch(e){}
    if (idParts && targetPcbComps[idParts[1]]) {
      console.log(`PAD_NET: ${targetPcbComps[idParts[1]]} Pin ${idParts[2]} -> Pad ${idParts[3]}`);
    }
  }
}

// 2. Check all layer types in PCB
const layers = pcbRecords.filter(r => r.head?.type === 'LAYER').map(r => r.body);
console.log('\n=== PCB LAYERS CONFIG ===');
layers.forEach(l => {
  if (l && l.use) {
    console.log(`Layer ${l.layerId.toString().padStart(2)}: ${l.layerName.padEnd(25)} (${l.layerType})`);
  }
});
