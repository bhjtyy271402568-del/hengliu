const fs = require('fs');
const enet = JSON.parse(fs.readFileSync('parsed_enet_map.json', 'utf8'));

// Reverse map: netName -> [ { designator, pinName } ]
const netToPins = {};

for (const [des, comp] of Object.entries(enet)) {
  if (!comp.pins) continue;
  for (const [pinNum, pinData] of Object.entries(comp.pins)) {
    const net = pinData.net;
    if (net) {
      if (!netToPins[net]) netToPins[net] = [];
      netToPins[net].push({ des, pinName: pinData.name, pinNum, value: comp.value });
    }
  }
}

const u1 = enet['U1'];
const targetPins = [3, 4, 15, 5, 18, 11, 26, 22, 6, 7, 16, 17]; // VIN, EN/UVLO, SS, VREF, VC, FB, SW, PWM, IVINN, IVINP, ISN, ISP
console.log('=== LT3763 PIN CONNECTIONS ===');

for (const p of targetPins) {
  const pinData = u1.pins[String(p)];
  if (!pinData) continue;
  const net = pinData.net;
  const connected = (netToPins[net] || []).filter(c => c.des !== 'U1');
  
  const compStr = connected.map(c => {
    let val = c.value || '';
    if (val.startsWith('={')) {
      // try to find it in full_bom
      // ignoring for now to keep it brief, just show des
      return `${c.des}(${c.pinName})`;
    }
    return `${c.des}(${c.pinName}, ${val})`;
  }).join(' | ');

  console.log(`Pin ${p} (${pinData.name}) -> Net [${net}] -> ${compStr}`);
}

// Special check: Is VIN (Pin 3) directly connected to the main 36V DCBUS or VCC_BAT?
// If it is, does it have an RC filter?
const vinNet = u1.pins['3'].net;
const vinComps = netToPins[vinNet] || [];
console.log(`\nVIN (Pin 3) is on Net ${vinNet}. Connected to:`);
console.log(vinComps.map(c => `${c.des} Pin ${c.pinNum} (${c.pinName})`).join(', '));

// SW Pin (26)
const swNet = u1.pins['26'].net;
const swComps = netToPins[swNet] || [];
console.log(`\nSW (Pin 26) is on Net ${swNet}. Connected to:`);
console.log(swComps.map(c => `${c.des} Pin ${c.pinNum} (${c.pinName})`).join(', '));
