const fs = require('fs');
const layers = JSON.parse(fs.readFileSync('pcb_layers.json', 'utf8'));

console.log('=== ALL LAYERS ===');
for (const l of layers) {
  if (l.type === 'LAYER_PHYS' || l.type === 'LAYER') {
    console.log(`[${l.type}] id=${JSON.stringify(l.head.id)}:`, JSON.stringify(l.body));
  }
}
