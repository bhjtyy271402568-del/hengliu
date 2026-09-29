const fs = require('fs');

const schRecords = JSON.parse(fs.readFileSync('audit_sch_records.json', 'utf8'));
const fullBOM = JSON.parse(fs.readFileSync('full_bom.json', 'utf8'));

// Find components connected to net $1N970 (EN/UVLO of U1)
const enet = JSON.parse(fs.readFileSync('网表.enet', 'utf8'));
for (const k of Object.keys(enet.components)) {
  const c = enet.components[k];
  for (const [pNum, pInfo] of Object.entries(c.pinInfoMap || {})) {
    if (pInfo.net === '$1N970' || pInfo.net === 'EN' || pInfo.net === 'UVLO') {
      console.log(`Component ${c.props?.Designator} (${c.props?.Value}) Pin ${pNum}: Net ${pInfo.net}`);
    }
  }
}

// Also search in 8.13 5 target details for resistors around UVLO: R52, R53, etc.
const uvloTargets = ['R52', 'R53', 'R3', 'R5', 'R7', 'R15', 'R20', 'R36', 'R37', 'R38', 'R39', 'R46', 'R51'];
for (const t of uvloTargets) {
  const c = fullBOM.find(b => b.designator === t);
  if (c) {
    console.log(`Resistor ${t}: Value = ${c.value}, LCSC = ${c.supplierPart}, Comment = ${c.comment}`);
  }
}
