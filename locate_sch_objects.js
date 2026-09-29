const fs = require('fs');

const pcbRecords = JSON.parse(fs.readFileSync('audit_pcb_records.json', 'utf8'));
const schRecords = JSON.parse(fs.readFileSync('audit_sch_records.json', 'utf8'));

// 1. Inspect PCB tracks coordinates
const tracks = pcbRecords.filter(r => r.head?.type === 'LINE');
console.log('Sample PCB Tracks:');
console.log(JSON.stringify(tracks.slice(0, 5).map(t => ({
  net: t.body?.netName,
  start: [t.body?.startX, t.body?.startY],
  end: [t.body?.endX, t.body?.endY],
  layer: t.body?.layerId
})), null, 2));

// 2. In SCH_PAGE, let's find all texts, wires, and pins around R33 and R34
// R33 SCH position: X=913, Y=-803
// R34 SCH position: X=967, Y=-803
console.log('\n=== SCHEMATIC OBJECTS AROUND R33 (913, -803) & R34 (967, -803) ===');
const schTexts = schRecords.filter(r => r.head?.type === 'TEXT');
const schWires = schRecords.filter(r => r.head?.type === 'WIRE');

console.log('Nearby Texts in SCH:');
const nearbyTexts = schTexts.filter(t => {
  const dx = t.body?.x - 940;
  const dy = t.body?.y - (-803);
  return Math.hypot(dx, dy) < 300;
});
console.log(JSON.stringify(nearbyTexts.map(t => ({ val: t.body?.value, x: t.body?.x, y: t.body?.y })), null, 2));

// Also let's inspect objects around Q1, Q2, Q5, Q6 in SCH!
const q1 = schRecords.find(r => r.head?.type === 'COMPONENT' && r.body?.partId?.includes('Q1') || r.head?.id === 'dae1c023c48a36cb');
console.log('\nQ1 SCH pos:', q1?.body?.x, q1?.body?.y);

const q2 = schRecords.find(r => r.head?.id === '8ca4fb0b7095488f');
console.log('Q2 SCH pos:', q2?.body?.x, q2?.body?.y);

const q5 = schRecords.find(r => r.head?.id === '5af1567d71628fae');
console.log('Q5 SCH pos:', q5?.body?.x, q5?.body?.y);

const q6 = schRecords.find(r => r.head?.id === '7fbcb8d53bb95590');
console.log('Q6 SCH pos:', q6?.body?.x, q6?.body?.y);
