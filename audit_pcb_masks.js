const fs = require('fs');

const pcbRecords = JSON.parse(fs.readFileSync('audit_pcb_records.json', 'utf8'));

// Inspect pads, testpoints, vias in pads
const pads = pcbRecords.filter(r => r.head?.type === 'PAD');
console.log(`Total explicit PAD records in PCB root: ${pads.length}`);

// Check rules for paste mask and solder mask
const pasteRules = pcbRecords.filter(r => r.head?.type === 'RULE' && (r.head.id.includes('PASTE') || r.head.id.includes('SOLDER')));
console.log('\n=== PASTE & SOLDER MASK RULES ===');
console.log(JSON.stringify(pasteRules, null, 2));

// Check testpoints
const strings = pcbRecords.filter(r => r.head?.type === 'STRING' || r.head?.type === 'TEXT');
console.log('\n=== PCB STRINGS / SILKSCREEN ===');
console.log(strings.map(s => s.body?.text || s.body?.value || JSON.stringify(s.body)));
