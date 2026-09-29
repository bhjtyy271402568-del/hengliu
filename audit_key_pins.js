const fs = require('fs');

const schRecords = JSON.parse(fs.readFileSync('audit_sch_records.json', 'utf8'));
const fullBOM = JSON.parse(fs.readFileSync('full_bom.json', 'utf8'));

// Find U1 in fullBOM
const u1 = fullBOM.find(b => b.designator === 'U1');
console.log('U1 info in BOM:', JSON.stringify(u1, null, 2));

// Let's find all pins and connected nets for U1, U6, U5, U3, U4, Q1..Q6, Q11, Q12, D6, U7
const keyDes = ['U1', 'U6', 'U5', 'U3', 'U4', 'U7', 'Q1', 'Q2', 'Q3', 'Q4', 'Q5', 'Q6', 'Q11', 'Q12', 'D6', 'D8', 'L6', 'R1', 'R12', 'R2', 'R19', 'R56', 'R57', 'R58', 'R30', 'R49', 'R4', 'C42', 'R6', 'C5', 'R17', 'C9', 'R22'];

// Let's read enet and PCB to map pins of these components
const enet = JSON.parse(fs.readFileSync('网表.enet', 'utf8'));
for (const k of Object.keys(enet.components)) {
  const c = enet.components[k];
  const des = c.props?.Designator;
  if (keyDes.includes(des)) {
    console.log(`\n=== Component ${des} (from enet) ===`);
    console.log(`Device: ${c.props?.DeviceName}, Footprint: ${c.props?.FootprintName}, Value: ${c.props?.Value || c.props?.Name}`);
    for (const [pinNum, pInfo] of Object.entries(c.pinInfoMap || {})) {
      console.log(`  Pin ${pinNum} (${pInfo.name}): Net "${pInfo.net}"`);
    }
  }
}
