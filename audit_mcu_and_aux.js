const fs = require('fs');

const schRecords = JSON.parse(fs.readFileSync('audit_sch_records.json', 'utf8'));
const fullBOM = JSON.parse(fs.readFileSync('full_bom.json', 'utf8'));

// Find MCU U2 (STM32G431RBT6) and Auxiliary chips (U5, U6, U3, U4)
const enet = JSON.parse(fs.readFileSync('网表.enet', 'utf8'));

console.log('=== MCU U2 (STM32G431RBT6) PINS & NETS ===');
for (const k of Object.keys(enet.components)) {
  const c = enet.components[k];
  if (c.props?.Designator === 'U2') {
    for (const [pNum, pInfo] of Object.entries(c.pinInfoMap || {})) {
      console.log(`Pin ${pNum.padStart(2)} (${pInfo.name.padEnd(12)}): Net "${pInfo.net}"`);
    }
  }
}

console.log('\n=== AUX REGULATOR U5 (JW5026 - 5V) PINS & NETS ===');
for (const k of Object.keys(enet.components)) {
  const c = enet.components[k];
  if (c.props?.Designator === 'U5') {
    for (const [pNum, pInfo] of Object.entries(c.pinInfoMap || {})) {
      console.log(`Pin ${pNum} (${pInfo.name.padEnd(8)}): Net "${pInfo.net}"`);
    }
  }
}
