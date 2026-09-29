const fs = require('fs');

const details = JSON.parse(fs.readFileSync('target_components_details.json', 'utf8'));

console.log('=== TARGET COMPONENTS SUMMARY IN 8.13 5 ===');
for (const [des, info] of Object.entries(details)) {
  if (info.status === 'NOT_FOUND') {
    console.log(`${des.padEnd(8)}: NOT FOUND IN SCHEMATIC`);
  } else {
    const lcsc = info.supplierPart || 'NO_LCSC';
    const mfr = info.mfrPart || info.allAttrs?.['LCSC Part Name'] || '';
    const val = info.value || '';
    const fp = info.allAttrs?.['Supplier Footprint'] || info.footprint;
    const dnp = info.dnp ? `[DNP: ${info.dnp}]` : '';
    console.log(`${des.padEnd(8)} | Val: ${val.padEnd(10)} | Mfr: ${mfr.padEnd(25)} | LCSC: ${lcsc.padEnd(12)} | FP: ${fp} ${dnp}`);
  }
}
