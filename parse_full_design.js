const fs = require('fs');

const schRecords = JSON.parse(fs.readFileSync('audit_sch_records.json', 'utf8'));
const pcbRecords = JSON.parse(fs.readFileSync('audit_pcb_records.json', 'utf8'));

// 1. SCH Components
const schComps = new Map();
for (const r of schRecords) {
  if (r.head?.type === 'COMPONENT') {
    schComps.set(r.head.id, { id: r.head.id, ticket: r.head.ticket, body: r.body, attrs: {} });
  }
}
for (const r of schRecords) {
  if (r.head?.type === 'ATTR') {
    const b = r.body;
    if (b && b.parentId && schComps.has(b.parentId)) {
      const comp = schComps.get(b.parentId);
      comp.attrs[b.key || r.head.id] = b.value;
    }
  }
}

// 2. PCB Components & Footprints
const pcbComps = new Map();
const pcbPads = [];
const pcbTracks = [];
const pcbVias = [];
const pcbPours = [];
const pcbRules = [];
const pcbRuleSelectors = [];
const pcbLayers = [];
const pcbNets = new Map();
const padNets = [];

for (const r of pcbRecords) {
  const t = r.head?.type;
  const b = r.body || {};
  if (t === 'COMPONENT') {
    pcbComps.set(r.head.id, { id: r.head.id, body: b, attrs: {} });
  } else if (t === 'ATTR') {
    if (b && b.parentId && pcbComps.has(b.parentId)) {
      pcbComps.get(b.parentId).attrs[b.key || r.head.id] = b.value;
    }
  } else if (t === 'NET') {
    pcbNets.set(b.netName || b.name || r.head?.id, { id: r.head?.id, body: b });
  } else if (t === 'PAD_NET') {
    padNets.push({ head: r.head, body: b });
  } else if (t === 'VIA') {
    pcbVias.push({ head: r.head, body: b });
  } else if (t === 'LINE') {
    pcbTracks.push({ head: r.head, body: b });
  } else if (t === 'POUR' || t === 'POURED' || t === 'FILL') {
    pcbPours.push({ head: r.head, body: b, type: t });
  } else if (t === 'RULE') {
    pcbRules.push({ head: r.head, body: b });
  } else if (t === 'RULE_SELECTOR') {
    pcbRuleSelectors.push({ head: r.head, body: b });
  } else if (t === 'LAYER' || t === 'LAYER_PHYS') {
    pcbLayers.push({ head: r.head, body: b, type: t });
  }
}

// Combine SCH and PCB component info
const fullBOM = [];
for (const [id, c] of schComps.entries()) {
  const des = c.attrs['Designator'] || c.attrs['designator'] || '';
  if (!des) continue;
  fullBOM.push({
    schId: id,
    designator: des,
    value: c.attrs['Value'] || c.attrs['value'] || c.attrs['Comment'] || '',
    comment: c.attrs['Comment'] || c.attrs['comment'] || '',
    device: c.attrs['Device'] || '',
    footprint: c.attrs['Footprint'] || c.attrs['footprint'] || '',
    supplierPart: c.attrs['Supplier Part'] || c.attrs['LCSC'] || c.attrs['jlcbom_type'] || '',
    dnp: c.attrs['DNP'] || c.attrs['dnp'] || c.attrs['BOM'] || '',
    attrs: c.attrs
  });
}

fullBOM.sort((a, b) => {
  const parseDes = (s) => {
    const m = s.match(/^([A-Za-z]+)(\d+)/);
    if (!m) return [s, 0];
    return [m[1], parseInt(m[2], 10)];
  };
  const [pA, nA] = parseDes(a.designator);
  const [pB, nB] = parseDes(b.designator);
  if (pA !== pB) return pA.localeCompare(pB);
  return nA - nB;
});

// Output Summary
console.log(`=== DESIGN AUDIT SUMMARY ===`);
console.log(`SCH Components count: ${fullBOM.length}`);
console.log(`PCB Components count: ${pcbComps.size}`);
console.log(`PCB Nets count: ${pcbNets.size}`);
console.log(`PCB Vias count: ${pcbVias.length}`);
console.log(`PCB Tracks count: ${pcbTracks.length}`);
console.log(`PCB Pours/Fills count: ${pcbPours.length}`);
console.log(`PCB Rules count: ${pcbRules.length}`);
console.log(`PCB Rule Selectors count: ${pcbRuleSelectors.length}`);
console.log(`PCB Layers count: ${pcbLayers.length}`);

// Save summary json files
fs.writeFileSync('full_bom.json', JSON.stringify(fullBOM, null, 2));
fs.writeFileSync('pcb_layers.json', JSON.stringify(pcbLayers, null, 2));
fs.writeFileSync('pcb_rules.json', JSON.stringify(pcbRules, null, 2));
fs.writeFileSync('pcb_rule_selectors.json', JSON.stringify(pcbRuleSelectors, null, 2));
fs.writeFileSync('pcb_pours.json', JSON.stringify(pcbPours, null, 2));
fs.writeFileSync('pcb_vias.json', JSON.stringify(pcbVias, null, 2));
fs.writeFileSync('pcb_pad_nets.json', JSON.stringify(padNets, null, 2));

console.log('Successfully written full_bom.json, pcb_layers.json, pcb_rules.json, pcb_rule_selectors.json, pcb_pours.json, pcb_vias.json, pcb_pad_nets.json');
