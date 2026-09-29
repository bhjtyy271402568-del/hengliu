const fs = require('fs');

const fullBOM = JSON.parse(fs.readFileSync('full_bom.json', 'utf8'));

console.log('=== FULL BOM CATEGORIES & COUNTS ===');
const cats = {};
for (const b of fullBOM) {
  const p = b.designator.match(/^[A-Za-z]+/)?.[0] || 'Other';
  if (!cats[p]) cats[p] = [];
  cats[p].push(b);
}
for (const [k, v] of Object.entries(cats)) {
  console.log(`${k.padEnd(6)}: ${v.length} components`);
}

// Check electrolytic / polymer capacitors (C5, C9, C17, C18)
console.log('\n=== BULK CAPACITORS ===');
const bulkCaps = fullBOM.filter(b => ['C5', 'C9', 'C17', 'C18', 'C75', 'C85', 'C86'].includes(b.designator));
console.log(JSON.stringify(bulkCaps, null, 2));

// Check diodes (D1..D13)
console.log('\n=== ALL DIODES ===');
const diodes = fullBOM.filter(b => b.designator.startsWith('D'));
console.log(JSON.stringify(diodes, null, 2));

// Check connectors (CN1..CN19, K1, K2)
console.log('\n=== CONNECTORS & TERMINALS ===');
const conns = fullBOM.filter(b => b.designator.startsWith('CN') || b.designator.startsWith('K'));
console.log(JSON.stringify(conns, null, 2));
