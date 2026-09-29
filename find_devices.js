const fs = require('fs');
const readline = require('readline');

async function findDevices() {
  const fileStream = fs.createReadStream('audit_8_13_5_epro2/恒流源.epru');
  const rl = readline.createInterface({ input: fileStream, crlfDelay: Infinity });

  const devIds = ['7712c0e5464b3963', '7ae4e43c3bfb6c37', '995505c37d15ab91', '4ad0c75550705544'];
  let currentDocUuid = '';
  let currentDocType = '';

  for await (const line of rl) {
    if (!line.trim()) continue;
    const parts = line.split('||');
    let head = null;
    let body = null;
    try { head = JSON.parse(parts[0]); } catch(e){}
    if (parts.length > 1) {
      let bStr = parts[1];
      if (bStr.endsWith('|')) bStr = bStr.slice(0, -1);
      try { body = JSON.parse(bStr); } catch(e){}
    }

    if (head && head.type === 'DOCHEAD') {
      currentDocUuid = body?.uuid || '';
      currentDocType = body?.docType || '';
    } else {
      if (devIds.includes(currentDocUuid)) {
        console.log(`Doc UUID: ${currentDocUuid}, Type: ${currentDocType}, Line type: ${head?.type}`);
        console.log('  Body:', JSON.stringify(body, null, 2));
      }
    }
  }
}

findDevices().catch(console.error);
