const fs = require('fs');

const pcbRecords = JSON.parse(fs.readFileSync('audit_pcb_records.json', 'utf8'));

// 1. Verify net connectivity of critical nets
const nets = {};
for (const r of pcbRecords) {
  const net = r.body?.netName;
  if (net) {
    if (!nets[net]) nets[net] = { tracks: 0, vias: 0, pours: 0 };
    if (r.head?.type === 'LINE') nets[net].tracks++;
    if (r.head?.type === 'VIA') nets[net].vias++;
    if (r.head?.type === 'POUR') nets[net].pours++;
  }
}

console.log('=== CRITICAL NETS HEALTH CHECK ===');
const checkNets = ['VCC_BAT', 'GND_BAT', 'DCBUS', 'GND', 'AGND', '$1N947', 'VCC_OUT', '12V', '5V', 'VCC', 'AVCC', '$1N992', '$1N988', '$1N964', '$1N963'];
for (const cn of checkNets) {
  console.log(`Net: ${cn.padEnd(12)} -> Tracks: ${nets[cn]?.tracks || 0}, Vias: ${nets[cn]?.vias || 0}, Pours: ${nets[cn]?.pours || 0}`);
}
