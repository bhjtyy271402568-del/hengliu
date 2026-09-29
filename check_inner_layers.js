const fs = require('fs');
const pcbRecords = JSON.parse(fs.readFileSync('audit_pcb_records.json', 'utf8'));

// Check Layer 15 (Inner1) pours and tracks
const layer15Pours = pcbRecords.filter(r => r.head?.type === 'POUR' && r.body?.layerId === 15);
const layer15Lines = pcbRecords.filter(r => r.head?.type === 'LINE' && r.body?.layerId === 15);

console.log('=== LAYER 15 (Inner1) ===');
console.log('POURS on Layer 15:');
for (const p of layer15Pours) {
  console.log(`NetName: ${p.body?.netName}, Points length: ${p.body?.path?.length}`);
}
console.log('LINES on Layer 15:');
const lineNets = {};
for (const l of layer15Lines) {
  lineNets[l.body?.netName] = (lineNets[l.body?.netName] || 0) + 1;
}
console.log(lineNets);

// Check Layer 16 (Inner2) pours and tracks
const layer16Pours = pcbRecords.filter(r => r.head?.type === 'POUR' && r.body?.layerId === 16);
const layer16Lines = pcbRecords.filter(r => r.head?.type === 'LINE' && r.body?.layerId === 16);

console.log('\n=== LAYER 16 (Inner2) ===');
console.log('POURS on Layer 16:');
for (const p of layer16Pours) {
  console.log(`NetName: ${p.body?.netName}, Points length: ${p.body?.path?.length}`);
}
console.log('LINES on Layer 16:');
const l16Nets = {};
for (const l of layer16Lines) {
  l16Nets[l.body?.netName] = (l16Nets[l.body?.netName] || 0) + 1;
}
console.log(l16Nets);
