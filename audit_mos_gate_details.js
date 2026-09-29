const fs = require('fs');

const pcbRecords = JSON.parse(fs.readFileSync('audit_pcb_records.json', 'utf8'));

// In PCB, let's map lines/tracks from U1 Pin 25 (TG) and Pin 1 (BG) through resistors to Q1, Q2, Q5, Q6 Pin 4 (Gate)
const pcbComps = new Map();
for (const r of pcbRecords) {
  if (r.head?.type === 'COMPONENT') {
    pcbComps.set(r.head.id, { id: r.head.id, designator: '', x: r.body?.x, y: r.body?.y });
  }
}
for (const r of pcbRecords) {
  if (r.head?.type === 'ATTR' && r.body?.parentId && pcbComps.has(r.body.parentId)) {
    if (r.body.key === 'Designator') pcbComps.get(r.body.parentId).designator = r.body.value;
  }
}

// Find designator of comps around X=9000~10500, Y=-400~500
const powerComps = Array.from(pcbComps.values()).filter(c => ['Q1', 'Q2', 'Q5', 'Q6', 'R33', 'R34', 'R42', 'R43', 'R47', 'U1', 'D9', 'D5', 'C76'].includes(c.designator));
console.log('Power Stage Components:');
console.log(JSON.stringify(powerComps, null, 2));

// Check PAD_NET for these power components
const powerCompIds = new Set(powerComps.map(c => c.id));
const powerPadNets = [];
for (const r of pcbRecords) {
  if (r.head?.type === 'PAD_NET') {
    let idParts;
    try { idParts = JSON.parse(r.head.id); } catch(e){}
    if (idParts && powerCompIds.has(idParts[1])) {
      const des = powerComps.find(c => c.id === idParts[1])?.designator;
      powerPadNets.push({ des, compId: idParts[1], pin: idParts[2], pad: idParts[3] });
    }
  }
}
console.log('\nPower Pad Nets:');
console.log(JSON.stringify(powerPadNets, null, 2));
