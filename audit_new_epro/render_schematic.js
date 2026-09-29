const fs = require("fs");
const path = require("path");

const [inputPath, outputPath, x0Arg, y0Arg, x1Arg, y1Arg] = process.argv.slice(2);
if (!outputPath) {
  throw new Error("Usage: node render_schematic.js in.epru out.svg x0 y0 x1 y1");
}
const x0 = Number(x0Arg);
const y0 = Number(y0Arg);
const x1 = Number(x1Arg);
const y1 = Number(y1Arg);

function recordFromLine(line) {
  const split = line.indexOf("||");
  if (split < 0) return null;
  const header = JSON.parse(line.slice(0, split));
  let text = line.slice(split + 2);
  if (text.endsWith("|")) text = text.slice(0, -1);
  return { ...header, payload: text ? JSON.parse(text) : {} };
}

const records = [];
let docType = "";
let docUuid = "";
for (const line of fs.readFileSync(path.resolve(inputPath), "utf8").split(/\r?\n/)) {
  if (!line) continue;
  const record = recordFromLine(line);
  if (!record) continue;
  if (record.type === "DOCHEAD") {
    docType = record.payload.docType || "";
    docUuid = record.payload.uuid || "";
  }
  record.docType = docType;
  record.docUuid = docUuid;
  records.push(record);
}

const attrs = new Map();
for (const record of records) {
  if (record.type !== "ATTR" || !record.payload.parentId) continue;
  const key = `${record.docUuid}|${record.payload.parentId}`;
  if (!attrs.has(key)) attrs.set(key, {});
  attrs.get(key)[record.payload.key] = record.payload.value;
}

const symbolParts = new Map();
const symbolPins = new Map();
for (const record of records) {
  if (record.docType !== "SYMBOL") continue;
  if (record.type === "PART") {
    symbolParts.set(`${record.docUuid}|${record.payload.title}`, record.payload.BBOX);
  }
  if (record.type === "PIN") {
    const a = attrs.get(`${record.docUuid}|${record.id}`) || {};
    const key = `${record.docUuid}|${record.payload.partId}`;
    if (!symbolPins.has(key)) symbolPins.set(key, []);
    symbolPins.get(key).push({
      number: String(a["Pin Number"] || ""),
      name: String(a["Pin Name"] || ""),
      x: Number(record.payload.x),
      y: Number(record.payload.y),
      length: Number(record.payload.length || 0),
      rotation: Number(record.payload.rotation || 0),
    });
  }
}

function transform(x, y, rotation, mirror) {
  if (mirror) x = -x;
  const rad = (-Number(rotation || 0) * Math.PI) / 180;
  return [
    x * Math.cos(rad) - y * Math.sin(rad),
    x * Math.sin(rad) + y * Math.cos(rad),
  ];
}
function sx(x) {
  return x - x0;
}
function sy(y) {
  return y1 - y;
}
function esc(text) {
  return String(text)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

const page = records.filter((record) => record.docType === "SCH_PAGE");
const wireIds = new Set(page.filter((record) => record.type === "WIRE").map((record) => record.id));
const out = [];
const width = x1 - x0;
const height = y1 - y0;
out.push(
  `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} ${height}" width="${width * 4}" height="${height * 4}">`,
  `<rect width="100%" height="100%" fill="white"/>`,
  `<g fill="none" stroke-linecap="round" stroke-linejoin="round">`,
);
for (const record of page) {
  if (record.type !== "LINE" || !wireIds.has(record.payload.lineGroup)) continue;
  const p = record.payload;
  if (
    Math.max(p.startX, p.endX) < x0 ||
    Math.min(p.startX, p.endX) > x1 ||
    Math.max(p.startY, p.endY) < y0 ||
    Math.min(p.startY, p.endY) > y1
  ) {
    continue;
  }
  out.push(
    `<line x1="${sx(p.startX)}" y1="${sy(p.startY)}" x2="${sx(p.endX)}" y2="${sy(p.endY)}" stroke="#1677ff" stroke-width="1.2"/>`,
  );
}
out.push(`</g>`);

for (const record of page) {
  if (record.type !== "COMPONENT") continue;
  const a = attrs.get(`${record.docUuid}|${record.id}`) || {};
  const ref = String(a.Designator || "");
  const value = String(a.Name || a.Value || "");
  const symbol = String(a.Symbol || "");
  const partId = String(record.payload.partId || "");
  const cx = Number(record.payload.x);
  const cy = Number(record.payload.y);
  if (cx < x0 - 100 || cx > x1 + 100 || cy < y0 - 100 || cy > y1 + 100) continue;

  const bbox = symbolParts.get(`${symbol}|${partId}`);
  if (bbox) {
    const corners = [
      transform(bbox[0], bbox[1], record.payload.rotation, record.payload.isMirror),
      transform(bbox[2], bbox[1], record.payload.rotation, record.payload.isMirror),
      transform(bbox[2], bbox[3], record.payload.rotation, record.payload.isMirror),
      transform(bbox[0], bbox[3], record.payload.rotation, record.payload.isMirror),
    ].map(([x, y]) => `${sx(cx + x)},${sy(cy + y)}`);
    out.push(`<polygon points="${corners.join(" ")}" fill="none" stroke="#555" stroke-width="0.7"/>`);
  }

  for (const pin of symbolPins.get(`${symbol}|${partId}`) || []) {
    const rad = (-pin.rotation * Math.PI) / 180;
    const innerX = pin.x + pin.length * Math.cos(rad);
    const innerY = pin.y + pin.length * Math.sin(rad);
    const [px1, py1] = transform(pin.x, pin.y, record.payload.rotation, record.payload.isMirror);
    const [px2, py2] = transform(innerX, innerY, record.payload.rotation, record.payload.isMirror);
    out.push(
      `<line x1="${sx(cx + px1)}" y1="${sy(cy + py1)}" x2="${sx(cx + px2)}" y2="${sy(cy + py2)}" stroke="#d4380d" stroke-width="1.4"/>`,
      `<text x="${sx(cx + px1) + 1}" y="${sy(cy + py1) - 1}" font-size="5" fill="#a8071a">${esc(pin.number)}</text>`,
    );
  }
  const label = [ref, value].filter(Boolean).join(" ");
  out.push(
    `<circle cx="${sx(cx)}" cy="${sy(cy)}" r="1.5" fill="#222"/>`,
    `<text x="${sx(cx) + 3}" y="${sy(cy) - 3}" font-size="7" font-family="Arial,sans-serif" fill="#111">${esc(label)}</text>`,
  );
}
out.push(`</svg>`);
fs.writeFileSync(path.resolve(outputPath), out.join("\n"));
