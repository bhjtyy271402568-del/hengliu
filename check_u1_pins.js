const fs = require('fs');

const pcbRecords = JSON.parse(fs.readFileSync('audit_pcb_records.json', 'utf8'));
const fullBom = JSON.parse(fs.readFileSync('full_bom.json', 'utf8'));

// Find U1 in PCB
const u1Comps = pcbRecords.filter(r => r.head?.type === 'COMPONENT');
let u1Id = null;
for(const r of pcbRecords) {
  if (r.head?.type === 'ATTR' && r.body?.value === 'U1') {
    u1Id = r.body.parentId;
    break;
  }
}

// Find all PADs of U1 and their nets
const u1Pads = pcbRecords.filter(r => r.head?.type === 'PAD' && r.body?.componentId === u1Id);
const netsMap = new Map();
pcbRecords.filter(r => r.head?.type === 'NET').forEach(n => {
  if (n.body && n.body.name) netsMap.set(n.head.id, n.body.name);
});

const u1PinNets = {};
for (const p of u1Pads) {
  u1PinNets[p.body?.pin] = netsMap.get(p.body?.net) || 'NC';
}

const netToPads = {};
const allPads = pcbRecords.filter(r => r.head?.type === 'PAD');
for (const p of allPads) {
  const netName = netsMap.get(p.body?.net);
  if (netName && p.body?.componentId !== u1Id) {
    if (!netToPads[netName]) netToPads[netName] = [];
    netToPads[netName].push(p.body?.componentId);
  }
}

const compIdToDes = {};
for(const r of pcbRecords) {
  if (r.head?.type === 'ATTR' && r.body?.key === 'Designator') {
    compIdToDes[r.body.parentId] = r.body.value;
  }
}

const keyPins = [
  { pin: '3', name: 'VIN' },
  { pin: '4', name: 'EN/UVLO' },
  { pin: '6', name: 'SS' },
  { pin: '8', name: 'VREF' },
  { pin: '9', name: 'VC' },
  { pin: '10', name: 'FB' },
  { pin: '14', name: 'CTRL2' },
  { pin: '15', name: 'CTRL1' },
  { pin: '16', name: 'ISP' },
  { pin: '17', name: 'ISN' },
  { pin: '28', name: 'BOOST' }
];

for (const kp of keyPins) {
  const netName = u1PinNets[kp.pin];
  let connectedComps = [];
  if (netName && netToPads[netName]) {
    const ids = Array.from(new Set(netToPads[netName]));
    connectedComps = ids.map(id => compIdToDes[id] || id);
  }
  
  const compVals = connectedComps.map(des => {
    const bomItem = fullBom.find(b => b.designator === des);
    return `${des}(${bomItem ? bomItem.value : '?'})`;
  }).filter(v => !v.includes('undefined'));

  console.log(`Pin ${kp.pin.padEnd(2)} (${kp.name.padEnd(8)}) -> Net: ${String(netName).padEnd(10)} -> Comps: ${compVals.join(', ')}`);
}
