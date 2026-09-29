const fs = require('fs');

const schRecords = JSON.parse(fs.readFileSync('audit_sch_records.json', 'utf8'));
const pcbRecords = JSON.parse(fs.readFileSync('audit_pcb_records.json', 'utf8'));
const fullBOM = JSON.parse(fs.readFileSync('full_bom.json', 'utf8'));

// In EasyEDA Pro SCH:
// WIRE records have: path [[x1, y1, 'L', x2, y2, ...]], netName or netlabel attached
// PIN records in SYMBOL/DEVICE or ELE_PLACEHOLDER/LINE have coordinates (x, y)
// NETLABEL / TEXT records have coordinates (x, y) and text (net name)
// Also in PCB records:
// LINE/TRACK and VIA records have netName!
// POURED/POUR records have netName!
// PAD records or PAD_NET have net bindings!

// Let's inspect WIRE, TEXT, ATTR, NETLABEL in SCH
const schWires = schRecords.filter(r => r.head?.type === 'WIRE');
const schTexts = schRecords.filter(r => r.head?.type === 'TEXT');
const schAttrs = schRecords.filter(r => r.head?.type === 'ATTR');

console.log(`SCH Wires: ${schWires.length}, Texts: ${schTexts.length}`);
console.log('Sample SCH Wire:', JSON.stringify(schWires[0], null, 2));
console.log('Sample SCH Text:', JSON.stringify(schTexts[0], null, 2));

// Let's inspect PCB Tracks, Vias, Pours and Pads
const pcbPads = pcbRecords.filter(r => r.head?.type === 'PAD');
const pcbTracks = pcbRecords.filter(r => r.head?.type === 'LINE');
const pcbVias = pcbRecords.filter(r => r.head?.type === 'VIA');
const pcbPours = pcbRecords.filter(r => r.head?.type === 'POURED' || r.head?.type === 'POUR');

console.log(`PCB Tracks: ${pcbTracks.length}, Vias: ${pcbVias.length}, Pours: ${pcbPours.length}`);
console.log('Sample PCB Track:', JSON.stringify(pcbTracks[0], null, 2));
console.log('Sample PCB Via:', JSON.stringify(pcbVias[0], null, 2));
console.log('Sample PCB Pour:', JSON.stringify(pcbPours[0], null, 2));
