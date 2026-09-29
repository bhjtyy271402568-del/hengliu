const fs = require('fs');

const schRecords = JSON.parse(fs.readFileSync('audit_sch_records.json', 'utf8'));
const fullBOM = JSON.parse(fs.readFileSync('full_bom.json', 'utf8'));
const pcbRecords = JSON.parse(fs.readFileSync('audit_pcb_records.json', 'utf8'));

// 1. Check Gate Resistors for Q1, Q2, Q5, Q6, Q3, Q12
console.log('=== GATE RESISTORS & CONNECTIONS ===');
const gateRes = fullBOM.filter(b => ['R35', 'R44', 'R50', 'R54', 'R64', 'R65', 'R66', 'R68', 'R69', 'R21', 'R42', 'R43', 'R47'].includes(b.designator));
console.log(JSON.stringify(gateRes.map(r => ({ des: r.designator, val: r.value, lcsc: r.supplierPart, mfr: r.mfrPart })), null, 2));

// 2. Check Boost Diode & Boost Cap
console.log('\n=== BOOST CIRCUIT ===');
const boostComps = fullBOM.filter(b => ['C76', 'D5', 'D9', 'D13', 'D7', 'D8'].includes(b.designator));
console.log(JSON.stringify(boostComps.map(r => ({ des: r.designator, val: r.value, lcsc: r.supplierPart, mfr: r.mfrPart, fp: r.footprint })), null, 2));

// 3. Check Tracks connecting TG, BG, SW, BOOST, INTVCC
const driveNets = ['$1N988', '$1N992', '$1N990', '$1N964', '$1N963', '$1N991', '$1N987'];
const driveTracks = pcbRecords.filter(r => r.head?.type === 'LINE' && driveNets.includes(r.body?.netName));
console.log(`\n=== GATE DRIVE TRACKS COUNT: ${driveTracks.length} ===`);
const driveTrackSummary = {};
for (const t of driveTracks) {
  const n = t.body.netName;
  if (!driveTrackSummary[n]) driveTrackSummary[n] = { count: 0, minWidth: Infinity, maxWidth: -Infinity, layers: new Set() };
  const s = driveTrackSummary[n];
  s.count++;
  s.layers.add(t.body.layerId);
  if (t.body.width < s.minWidth) s.minWidth = t.body.width;
  if (t.body.width > s.maxWidth) s.maxWidth = t.body.width;
}
for (const [net, s] of Object.entries(driveTrackSummary)) {
  console.log(`Net: ${net.padEnd(10)} | Count: ${s.count} | Width: ${s.minWidth}~${s.maxWidth} mil | Layers: ${Array.from(s.layers).join(',')}`);
}
