const fs = require('fs');

const schRecords = JSON.parse(fs.readFileSync('audit_sch_records.json', 'utf8'));
const fullBOM = JSON.parse(fs.readFileSync('full_bom.json', 'utf8'));

// Find components around gate drive in latest SCH
const gateNets = ['$1N988', '$1N992', '$1N991', '$1N987', 'TG', 'BG'];
// Let's find all resistors connected to these nets
// In SCH records, let's search for pin connections or texts near Q1, Q2, Q5, Q6
const mosList = ['Q1', 'Q2', 'Q5', 'Q6'];
for (const m of mosList) {
  const c = fullBOM.find(b => b.designator === m);
  console.log(`MOS ${m}:`, JSON.stringify(c, null, 2));
}

// Let's search all resistors with 10Ω or 22Ω or 0Ω or similar
const smallResistors = fullBOM.filter(b => b.designator.startsWith('R') && ['0Ω', '2.2Ω', '4.7Ω', '10Ω', '22Ω', '47Ω', '100Ω'].includes(b.value));
console.log('\nSmall Resistors in latest BOM:');
console.log(smallResistors.map(r => `${r.designator}: ${r.value} (${r.supplierPart})`).join('\n'));
