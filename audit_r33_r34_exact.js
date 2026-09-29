const fs = require('fs');

const pcbRecords = JSON.parse(fs.readFileSync('audit_pcb_records.json', 'utf8'));

// Find lines/tracks connecting to R33, R34, Q1, Q2, Q5, Q6
// R33 PCB pos: (8647.13, -656.89)
// R34 PCB pos: (8658.84, -514.75)
// Notice pos around X=8647, Y=-656: near U6 (LM5164, X=8672, Y=-789)!
// Let's find all tracks connecting to R33, R34, Q1, Q2, Q5, Q6

const targetComps = [
  { des: 'R33', x: 8647.13, y: -656.89 },
  { des: 'R34', x: 8658.84, y: -514.75 },
  { des: 'Q1', x: 10058.64, y: 206.22 },
  { des: 'Q2', x: 10128.39, y: -92.85 },
  { des: 'Q5', x: 9825.39, y: -95.85 },
  { des: 'Q6', x: 9836.64, y: 206.22 }
];

console.log('=== TRACKS NEAR TARGET COMPONENTS ===');
const tracks = pcbRecords.filter(r => r.head?.type === 'LINE');

for (const tc of targetComps) {
  console.log(`\n--- Tracks near ${tc.des} (X: ${tc.x.toFixed(1)}, Y: ${tc.y.toFixed(1)}) ---`);
  const nearby = tracks.filter(t => {
    const b = t.body;
    const dist1 = Math.hypot(b.startX - tc.x, b.startY - tc.y);
    const dist2 = Math.hypot(b.endX - tc.x, b.endY - tc.y);
    return dist1 < 60 || dist2 < 60;
  });
  const nets = new Set(nearby.map(t => t.body.netName));
  console.log(`Found ${nearby.length} tracks. Nets: ${Array.from(nets).join(', ')}`);
  nearby.forEach(t => {
    console.log(`  Track Net: ${t.body.netName.padEnd(12)} | Layer: ${t.body.layerId} | Start: (${t.body.startX.toFixed(1)}, ${t.body.startY.toFixed(1)}) -> End: (${t.body.endX.toFixed(1)}, ${t.body.endY.toFixed(1)})`);
  });
}
