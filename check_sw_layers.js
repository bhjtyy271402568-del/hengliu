const fs = require('fs');

const pcbRecords = JSON.parse(fs.readFileSync('audit_pcb_records.json', 'utf8'));

const swLines = pcbRecords.filter(r => r.head?.type === 'LINE' && r.body?.netName === '$1N947');
const swPours = pcbRecords.filter(r => r.head?.type === 'POUR' && r.body?.netName === '$1N947');

console.log('=== SW NET ($1N947) LAYERS ===');
const layers = { lines: {}, pours: {} };

for (const line of swLines) {
  const l = line.body?.layerId;
  layers.lines[l] = (layers.lines[l] || 0) + 1;
}

for (const pour of swPours) {
  const l = pour.body?.layerId;
  layers.pours[l] = (layers.pours[l] || 0) + 1;
}

console.log('Lines distribution:', layers.lines);
console.log('Pours distribution:', layers.pours);

// Check what layer 1, 2, 3, 4 map to (1=Top, 2=Bottom, 3=Inner1, 4=Inner2 usually in EasyEDA)
// Wait, usually in EasyEDA Pro: 1=Top, 2=Bottom, 3=Inner1, 4=Inner2 or 1=Top, 21=Inner1, 22=Inner2, 2=Bottom?
// Let's check the stackup from audit_pcb_records.json
const layersCfg = pcbRecords.find(r => r.head?.type === 'LAYER_CONFIG');
console.log('\nLayer Config:', JSON.stringify(layersCfg?.body?.layers?.map(l => ({ id: l.id, name: l.name, type: l.type })), null, 2));

