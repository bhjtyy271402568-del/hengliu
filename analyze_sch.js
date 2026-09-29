const fs = require('fs');

const schRecords = JSON.parse(fs.readFileSync('audit_sch_records.json', 'utf8'));

const compMap = new Map();

for (const r of schRecords) {
  const t = r.head?.type;
  if (t === 'COMPONENT') {
    const id = r.head?.id;
    compMap.set(id, {
      id,
      ticket: r.head?.ticket,
      body: r.body,
      attrs: {}
    });
  }
}

for (const r of schRecords) {
  const t = r.head?.type;
  if (t === 'ATTR') {
    const b = r.body;
    if (b && b.parentId && compMap.has(b.parentId)) {
      const comp = compMap.get(b.parentId);
      const k = b.key || r.head?.id;
      comp.attrs[k] = b.value;
    }
  }
}

const compList = Array.from(compMap.values()).map(c => {
  return {
    id: c.id,
    designator: c.attrs['Designator'] || c.attrs['designator'] || '',
    value: c.attrs['Value'] || c.attrs['value'] || '',
    comment: c.attrs['Comment'] || c.attrs['comment'] || '',
    footprint: c.attrs['Footprint'] || c.attrs['footprint'] || '',
    supplierPart: c.attrs['Supplier Part'] || c.attrs['LCSC'] || c.attrs['jlcbom_type'] || '',
    device: c.attrs['Device'] || '',
    symbol: c.attrs['Symbol'] || '',
    dnp: c.attrs['DNP'] || c.attrs['dnp'] || c.attrs['BOM'] || '',
    allAttrs: c.attrs
  };
}).filter(c => c.designator || c.value);

// Sort by designator prefix and number
compList.sort((a, b) => {
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

console.log(`Total active components: ${compList.length}`);
console.log('Sample parsed components:');
console.log(compList.slice(0, 15).map(c => `${c.designator}: ${c.value} | FP: ${c.footprint} | LCSC: ${c.supplierPart} | DNP: ${c.dnp}`).join('\n'));

fs.writeFileSync('parsed_bom.json', JSON.stringify(compList, null, 2));

// Group by prefix
const prefixGroups = {};
for (const c of compList) {
  const p = (c.designator.match(/^[A-Za-z]+/)?.[0]) || 'Other';
  if (!prefixGroups[p]) prefixGroups[p] = [];
  prefixGroups[p].push(c);
}

console.log('\nComponents by category:');
for (const [p, items] of Object.entries(prefixGroups)) {
  console.log(`  ${p} (${items.length}): ${items.map(i => `${i.designator}(${i.value})`).join(', ')}`);
}
