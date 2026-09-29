const fs = require('fs');

const pcbRecords = JSON.parse(fs.readFileSync('audit_pcb_records.json', 'utf8'));

// Find R1 and R12 in PCB
const comps = Array.from(new Map(pcbRecords.filter(r => r.head?.type === 'COMPONENT').map(r => [r.head.id, r])).values());
for (const r of pcbRecords) {
  if (r.head?.type === 'ATTR' && r.body?.key === 'Designator') {
    const c = comps.find(comp => comp.head.id === r.body.parentId);
    if (c) {
      c.designator = r.body.value;
    }
  }
}

const r1 = comps.find(c => c.designator === 'R1');
const r12 = comps.find(c => c.designator === 'R12');

console.log('R1 PCB:', r1?.head?.id, r1?.body?.x, r1?.body?.y);
console.log('R12 PCB:', r12?.head?.id, r12?.body?.x, r12?.body?.y);

// Find pads of R1 and R12
const r1Pads = pcbRecords.filter(r => r.head?.type === 'PAD' && r.body?.componentId === r1?.head?.id);
const r12Pads = pcbRecords.filter(r => r.head?.type === 'PAD' && r.body?.componentId === r12?.head?.id);

console.log('\nR1 Pads:');
for (const p of r1Pads) console.log(`Pin ${p.body?.pin}, Net: ${p.body?.net}, pos: (${p.body?.x}, ${p.body?.y})`);

console.log('\nR12 Pads:');
for (const p of r12Pads) console.log(`Pin ${p.body?.pin}, Net: ${p.body?.net}, pos: (${p.body?.x}, ${p.body?.y})`);

// Find all POURs or Tracks that are on R1, R12
const pours = pcbRecords.filter(r => r.head?.type === 'POUR');
const lines = pcbRecords.filter(r => r.head?.type === 'LINE');

function findOverlaps(x, y, dist) {
  const overPours = pours.filter(p => {
    // simplified bounding box check if possible, or just exact net match
    return false; 
  });
  const overLines = lines.filter(l => {
    const startDist = Math.hypot(l.body?.startX - x, l.body?.startY - y);
    const endDist = Math.hypot(l.body?.endX - x, l.body?.endY - y);
    return startDist < dist || endDist < dist;
  });
  return overLines.map(l => `${l.body?.netName} (Layer ${l.body?.layerId}) w:${l.body?.width}`);
}

if (r1Pads.length > 0) {
  console.log('\nLines near R1 Pad 1:', findOverlaps(r1Pads[0].body?.x, r1Pads[0].body?.y, 50));
  console.log('Lines near R1 Pad 2:', findOverlaps(r1Pads[1].body?.x, r1Pads[1].body?.y, 50));
}
if (r12Pads.length > 0) {
  console.log('\nLines near R12 Pad 1:', findOverlaps(r12Pads[0].body?.x, r12Pads[0].body?.y, 50));
  console.log('Lines near R12 Pad 2:', findOverlaps(r12Pads[1].body?.x, r12Pads[1].body?.y, 50));
}
