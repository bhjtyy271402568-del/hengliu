const fs = require('fs');

// Read enet
const enet = JSON.parse(fs.readFileSync('网表.enet', 'utf8'));

console.log(`Enet version: ${enet.version}`);
const compKeys = Object.keys(enet.components);
console.log(`Total components in enet: ${compKeys.length}`);

// Let's create a map of designator -> info from enet
const enetMap = new Map();
for (const k of compKeys) {
  const c = enet.components[k];
  const p = c.props || {};
  const des = p['Designator'];
  if (des) {
    enetMap.set(des, {
      designator: des,
      value: p['Value'] || p['Name'] || '',
      supplierPart: p['Supplier Part'] || '',
      mfrPart: p['Manufacturer Part'] || '',
      footprint: p['FootprintName'] || p['Supplier Footprint'] || '',
      pins: c.pinInfoMap || {}
    });
  }
}

// Compare with full_bom.json from 8.13 5.epro2
const bom = JSON.parse(fs.readFileSync('full_bom.json', 'utf8'));
console.log(`BOM components from 8.13 5.epro2: ${bom.length}`);

const missingInEnet = [];
const missingInBom = [];
const valueDiffs = [];

for (const b of bom) {
  const ec = enetMap.get(b.designator);
  if (!ec) {
    missingInEnet.push(b.designator);
  } else {
    // compare values/lcsc
    if (b.value && ec.value && b.value !== ec.value && !b.value.includes(ec.value) && !ec.value.includes(b.value)) {
      valueDiffs.push({ des: b.designator, bomVal: b.value, enetVal: ec.value, bomLcsc: b.supplierPart, enetLcsc: ec.supplierPart });
    }
  }
}

for (const [des] of enetMap.entries()) {
  if (!bom.find(b => b.designator === des)) {
    missingInBom.push(des);
  }
}

console.log('Missing in Enet:', missingInEnet);
console.log('Missing in 8.13 5 BOM:', missingInBom);
console.log('Value differences count:', valueDiffs.length);
if (valueDiffs.length > 0) {
  console.log('Value differences sample:', JSON.stringify(valueDiffs.slice(0, 10), null, 2));
}

// Save complete netlist mapping
fs.writeFileSync('parsed_enet_map.json', JSON.stringify(Object.fromEntries(enetMap), null, 2));
console.log('Saved parsed_enet_map.json');
