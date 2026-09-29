const fs = require('fs');

const pcbRecords = JSON.parse(fs.readFileSync('audit_pcb_records.json', 'utf8'));

// 1. Build a map of all components with their coordinates, layers, rotation
const comps = new Map();
for (const r of pcbRecords) {
  if (r.head?.type === 'COMPONENT') {
    comps.set(r.head.id, {
      id: r.head.id,
      x: r.body?.x,
      y: r.body?.y,
      rotation: r.body?.rotation,
      layerId: r.body?.layerId,
      designator: '',
      pads: []
    });
  }
}

for (const r of pcbRecords) {
  if (r.head?.type === 'ATTR' && r.body?.parentId && comps.has(r.body.parentId)) {
    if (r.body.key === 'Designator' || r.body.key === 'designator') {
      comps.get(r.body.parentId).designator = r.body.value;
    }
  }
}

// Convert comps map to designator map
const desCompMap = new Map();
for (const [id, c] of comps.entries()) {
  if (c.designator) {
    desCompMap.set(c.designator, c);
  }
}

console.log(`Total placed components: ${desCompMap.size}`);

// Inspect key components coordinates
const keyComponents = [
  'U1', 'Q1', 'Q2', 'Q5', 'Q6', 'L6', 'R1', 'R12',
  'C10', 'C11', 'C12', 'C13', 'C14', 'C15', 'C16', 'C19', 'C20', 'C36', 'C43',
  'C5', 'C9', 'Q3', 'Q12', 'Q4', 'D6', 'D8', 'U7', 'Q11',
  'C76', 'C75', 'C85', 'C49', 'R23', 'R24', 'C77', 'R59', 'R60',
  'R4', 'C42', 'R22', 'R56', 'R57', 'R58', 'R30', 'R49', 'U6', 'U5', 'U2'
];

console.log('\n=== KEY POWER & SENSITIVE COMPONENT POSITIONS (mm) ===');
const compPositions = {};
for (const des of keyComponents) {
  const c = desCompMap.get(des);
  if (c) {
    // EasyEDA Pro coordinates are usually in mm (or 10mil, let's check values)
    compPositions[des] = { x: c.x, y: c.y, rot: c.rotation, layer: c.layerId === 1 ? 'TOP' : (c.layerId === 2 ? 'BOT' : c.layerId) };
    console.log(`${des.padEnd(6)} -> X: ${c.x?.toFixed(2).padStart(8)}, Y: ${c.y?.toFixed(2).padStart(8)}, Layer: ${compPositions[des].layer}, Rot: ${c.rot}`);
  } else {
    console.log(`${des.padEnd(6)} -> NOT PLACED`);
  }
}

fs.writeFileSync('pcb_comp_positions.json', JSON.stringify(compPositions, null, 2));
