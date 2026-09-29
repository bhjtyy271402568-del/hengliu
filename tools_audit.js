const fs = require('fs');
const readline = require('readline');

async function parseProject() {
  const fileStream = fs.createReadStream('audit_8_13_5_epro2/恒流源.epru');
  const rl = readline.createInterface({
    input: fileStream,
    crlfDelay: Infinity
  });

  const schPageDoc = { id: '17ebccfb17acd8d7', records: [] };
  const pcbDoc = { id: 'eb0c77c148accbe4', records: [] };
  const devices = new Map(); // uuid -> device info
  const footprints = new Map(); // uuid -> footprint info
  const symbols = new Map(); // uuid -> symbol info

  let currentDocUuid = null;
  let currentDocType = null;
  let currentDocRecords = [];

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
      currentDocUuid = body?.uuid || head.ticket;
      currentDocType = body?.docType;
      currentDocRecords = [];
    } else {
      const record = { head, body };
      if (currentDocUuid === schPageDoc.id) {
        schPageDoc.records.push(record);
      } else if (currentDocUuid === pcbDoc.id) {
        pcbDoc.records.push(record);
      } else if (currentDocType === 'DEVICE' && head?.type === 'META') {
        devices.set(currentDocUuid, body);
      }
    }
  }

  console.log(`Loaded SCH_PAGE records: ${schPageDoc.records.length}`);
  console.log(`Loaded PCB records: ${pcbDoc.records.length}`);
  console.log(`Loaded Devices: ${devices.size}`);

  fs.writeFileSync('audit_sch_records.json', JSON.stringify(schPageDoc.records, null, 2));
  fs.writeFileSync('audit_pcb_records.json', JSON.stringify(pcbDoc.records, null, 2));
  console.log('Saved raw records to audit_sch_records.json and audit_pcb_records.json');
}

parseProject().catch(console.error);
