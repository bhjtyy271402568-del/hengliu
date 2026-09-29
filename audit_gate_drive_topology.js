const fs = require('fs');

const schRecords = JSON.parse(fs.readFileSync('audit_sch_records.json', 'utf8'));

// Build pin-net mapping for Q1, Q2, Q5, Q6, U1 and their gate resistors
const enet = JSON.parse(fs.readFileSync('网表.enet', 'utf8'));

console.log('=== GATE RESISTOR NET CONNECTIONS ===');
const targetDes = ['Q1', 'Q2', 'Q5', 'Q6', 'R21', 'R35', 'R42', 'R43', 'R44', 'R47', 'R50', 'R54', 'R64', 'R65', 'R66', 'U1', 'D5', 'D9', 'D13'];

for (const k of Object.keys(enet.components)) {
  const c = enet.components[k];
  const des = c.props?.Designator;
  if (targetDes.includes(des)) {
    console.log(`\nComponent ${des} (${c.props?.Value || c.props?.Name || ''}):`);
    for (const [pNum, pInfo] of Object.entries(c.pinInfoMap || {})) {
      console.log(`  Pin ${pNum} (${pInfo.name}): Net "${pInfo.net}"`);
    }
  }
}
