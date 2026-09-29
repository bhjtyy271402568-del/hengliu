const fs = require('fs');

const pcbRecords = JSON.parse(fs.readFileSync('audit_pcb_records.json', 'utf8'));

// Find lines with netName of TG, BG, etc.
// From U1: Pin 25 is TG ($1N992), Pin 1 is BG ($1N988)
// Let's trace lines with net $1N992 and $1N988
const tgTracks = pcbRecords.filter(r => r.head?.type === 'LINE' && r.body?.netName === '$1N992');
const bgTracks = pcbRecords.filter(r => r.head?.type === 'LINE' && r.body?.netName === '$1N988');

console.log('=== TG TRACKS ($1N992) ===');
console.log(tgTracks.map(t => ({
  start: [t.body?.startX, t.body?.startY],
  end: [t.body?.endX, t.body?.endY],
  layer: t.body?.layerId,
  width: t.body?.width
})));

console.log('\n=== BG TRACKS ($1N988) ===');
console.log(bgTracks.map(t => ({
  start: [t.body?.startX, t.body?.startY],
  end: [t.body?.endX, t.body?.endY],
  layer: t.body?.layerId,
  width: t.body?.width
})));
