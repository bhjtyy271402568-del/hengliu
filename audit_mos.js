const fs = require('fs');

const schRecords = JSON.parse(fs.readFileSync('audit_sch_records.json', 'utf8'));
const fullBOM = JSON.parse(fs.readFileSync('full_bom.json', 'utf8'));

const mosComps = fullBOM.filter(b => ['Q1', 'Q2', 'Q3', 'Q4', 'Q5', 'Q6', 'Q11', 'Q12'].includes(b.designator));
console.log('MOS Components in full BOM:');
console.log(JSON.stringify(mosComps, null, 2));
