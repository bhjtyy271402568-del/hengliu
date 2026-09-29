const fs = require('fs');

const pcbRecords = JSON.parse(fs.readFileSync('audit_pcb_records.json', 'utf8'));

// 1. Map component uuid to designator
const compMap = new Map();
for (const r of pcbRecords) {
  if (r.head?.type === 'COMPONENT') {
    compMap.set(r.head.id, { id: r.head.id, designator: '', attrs: {}, pads: {} });
  }
}
for (const r of pcbRecords) {
  if (r.head?.type === 'ATTR') {
    const b = r.body;
    if (b && b.parentId && compMap.has(b.parentId)) {
      const comp = compMap.get(b.parentId);
      if (b.key === 'Designator' || b.key === 'designator') {
        comp.designator = b.value;
      }
      comp.attrs[b.key || r.head.id] = b.value;
    }
  }
}

// 2. Map PAD_NET
for (const r of pcbRecords) {
  if (r.head?.type === 'PAD_NET') {
    // id is ["PAD_NET", compId, pinNumber, padId]
    let idParts;
    try {
      idParts = JSON.parse(r.head.id);
    } catch(e) {
      continue;
    }
    if (Array.isArray(idParts) && idParts.length >= 4) {
      const compId = idParts[1];
      const pinNum = idParts[2];
      const padId = idParts[3];
      const netName = r.body?.net || r.body?.netName || r.head?.netName || r.body?.name || '';
      
      const comp = compMap.get(compId);
      if (comp) {
        comp.pads[pinNum] = {
          padId,
          net: netName,
          body: r.body,
          head: r.head
        };
      }
    }
  }
}

// Let's inspect some PAD_NET entries to see where netName is stored
const samplePadNet = pcbRecords.filter(r => r.head?.type === 'PAD_NET').slice(0, 10);
console.log('Sample PAD_NET records:');
console.log(JSON.stringify(samplePadNet, null, 2));

// Also inspect NET records in pcbRecords
const nets = pcbRecords.filter(r => r.head?.type === 'NET').map(r => ({ id: r.head.id, name: r.body?.name || r.body?.netName, body: r.body }));
console.log(`Total NET records: ${nets.length}`);
console.log('Sample NETs:', nets.slice(0, 20));
