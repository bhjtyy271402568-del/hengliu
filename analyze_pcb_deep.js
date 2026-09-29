const fs = require('fs');

const pcbRecords = JSON.parse(fs.readFileSync('audit_pcb_records.json', 'utf8'));

// 1. Group records
const vias = [];
const tracks = [];
const pours = [];
const poureds = [];
const comps = new Map();
const attrs = [];
const nets = new Set();

for (const r of pcbRecords) {
  const t = r.head?.type;
  const b = r.body;
  if (!b) continue;
  if (t === 'VIA') {
    vias.push(b);
    if (b.netName) nets.add(b.netName);
  } else if (t === 'LINE') {
    tracks.push(b);
    if (b.netName) nets.add(b.netName);
  } else if (t === 'POUR') {
    pours.push(b);
    if (b.netName) nets.add(b.netName);
  } else if (t === 'POURED') {
    poureds.push(b);
  } else if (t === 'COMPONENT') {
    comps.set(r.head.id, { id: r.head.id, body: b, attrs: {} });
  } else if (t === 'ATTR') {
    if (b.parentId && comps.has(b.parentId)) {
      comps.get(b.parentId).attrs[b.key || r.head.id] = b.value;
    }
  }
}

console.log(`=== PCB ENTITY COUNTS ===`);
console.log(`Total Nets: ${nets.size}`);
console.log(`Total Vias: ${vias.length}`);
console.log(`Total Tracks: ${tracks.length}`);
console.log(`Total POUR regions: ${pours.length}`);
console.log(`Total POURED meshes: ${poureds.length}`);
console.log(`Total Components: ${comps.size}`);

// 2. Via statistics by Net
const viaStats = {};
for (const v of vias) {
  const net = v.netName || 'NO_NET';
  if (!viaStats[net]) {
    viaStats[net] = {
      count: 0,
      diameters: {},
      holeDiameters: {},
      minX: Infinity, maxX: -Infinity,
      minY: Infinity, maxY: -Infinity
    };
  }
  const s = viaStats[net];
  s.count++;
  const d = v.viaDiameter;
  const hd = v.holeDiameter;
  s.diameters[d] = (s.diameters[d] || 0) + 1;
  s.holeDiameters[hd] = (s.holeDiameters[hd] || 0) + 1;
  const x = v.centerX || 0;
  const y = v.centerY || 0;
  if (x < s.minX) s.minX = x;
  if (x > s.maxX) s.maxX = x;
  if (y < s.minY) s.minY = y;
  if (y > s.maxY) s.maxY = y;
}

console.log('\n=== VIA DISTRIBUTION FOR KEY POWER NETS ===');
const powerNets = ['GND', 'GND_BAT', 'DCBUS', 'VCC_BAT', 'VCC_OUT', '$1N947', 'SW', '12V', '5V', '3.3V', 'AVCC', 'INTVCC'];
for (const pNet of Object.keys(viaStats).sort((a, b) => viaStats[b].count - viaStats[a].count)) {
  const s = viaStats[pNet];
  if (s.count >= 5 || powerNets.includes(pNet)) {
    console.log(`Net: ${pNet.padEnd(12)} | Vias: ${s.count.toString().padEnd(4)} | Hole Dia: ${JSON.stringify(s.holeDiameters)} | Pad Dia: ${JSON.stringify(s.diameters)}`);
  }
}

// 3. POUR analysis
console.log('\n=== POUR REGIONS BY LAYER AND NET ===');
const pourStats = {};
for (const p of pours) {
  const key = `Layer ${p.layerId} | Net: ${p.netName || 'NONE'}`;
  if (!pourStats[key]) pourStats[key] = [];
  pourStats[key].push(p);
}
for (const [k, v] of Object.entries(pourStats)) {
  console.log(`${k.padEnd(30)} -> Count: ${v.length}`);
}

// Save detailed stats to file
fs.writeFileSync('pcb_via_stats.json', JSON.stringify(viaStats, null, 2));
fs.writeFileSync('pcb_pour_stats.json', JSON.stringify(pourStats, null, 2));
