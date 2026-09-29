const fs = require('fs');

const pcbRecords = JSON.parse(fs.readFileSync('audit_pcb_records.json', 'utf8'));

// 1. Check SW tracks and pours
const swTracks = [];
const swVias = [];
const swPours = [];

// 2. Check Kelvin sensing tracks (ISN, ISP, IVINN, IVINP, SENSE+, SENSE-)
const kelvinNets = ['$1N980', '$1N979', '$1N983', '$1N986', '$1N978', '$1N971', 'DIANLIUKONGZHI', '$1N965'];
const kelvinTracks = [];

// 3. Check pours on L2 (layerId 15) and L3 (layerId 16)
const l2Pours = [];
const l3Pours = [];

for (const r of pcbRecords) {
  const t = r.head?.type;
  const b = r.body;
  if (!b) continue;

  if (t === 'LINE') {
    if (b.netName === '$1N990' || b.netName === 'SW') {
      swTracks.push(b);
    }
    if (kelvinNets.includes(b.netName)) {
      kelvinTracks.push(b);
    }
  } else if (t === 'VIA') {
    if (b.netName === '$1N990' || b.netName === 'SW') {
      swVias.push(b);
    }
  } else if (t === 'POUR' || t === 'POURED') {
    if (b.netName === '$1N990' || b.netName === 'SW') {
      swPours.push({ type: t, body: b });
    }
    if (b.layerId === 15) l2Pours.push(b);
    if (b.layerId === 16) l3Pours.push(b);
  }
}

console.log('=== SW NODE GEOMETRY ===');
console.log(`SW Tracks count: ${swTracks.length}`);
console.log('SW Track layers:', Array.from(new Set(swTracks.map(t => t.layerId))));
console.log(`SW Vias count: ${swVias.length}`);
console.log(`SW Pours count: ${swPours.length}`);

console.log('\n=== KELVIN & SENSITIVE TRACKS ===');
console.log(`Kelvin tracks count: ${kelvinTracks.length}`);
const kelvinSummary = {};
for (const kt of kelvinTracks) {
  if (!kelvinSummary[kt.netName]) kelvinSummary[kt.netName] = { count: 0, layers: new Set(), minWidth: Infinity, maxWidth: -Infinity };
  const s = kelvinSummary[kt.netName];
  s.count++;
  s.layers.add(kt.layerId);
  if (kt.width < s.minWidth) s.minWidth = kt.width;
  if (kt.width > s.maxWidth) s.maxWidth = kt.width;
}
for (const [net, s] of Object.entries(kelvinSummary)) {
  console.log(`Net: ${net.padEnd(16)} | Tracks: ${s.count} | Layers: ${Array.from(s.layers).join(',')} | Width: ${s.minWidth}~${s.maxWidth} mil`);
}

console.log('\n=== L2 (GND) & L3 (PWR/SIG) POURS ===');
console.log(`L2 Pours count: ${l2Pours.length}`);
console.log(`L3 Pours count: ${l3Pours.length}`);
