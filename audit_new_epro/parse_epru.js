const fs = require("fs");
const path = require("path");

const inputPath = process.argv[2];
if (!inputPath) throw new Error("Usage: node parse_epru.js <file.epru>");

function parseRecord(line) {
  const split = line.indexOf("||");
  if (split < 0) return null;
  const header = JSON.parse(line.slice(0, split));
  let payloadText = line.slice(split + 2);
  if (payloadText.endsWith("|")) payloadText = payloadText.slice(0, -1);
  const payload = payloadText ? JSON.parse(payloadText) : {};
  return { ...header, payload };
}

const all = [];
let docType = null;
let docUuid = null;
for (const line of fs.readFileSync(path.resolve(inputPath), "utf8").split(/\r?\n/)) {
  if (!line) continue;
  const record = parseRecord(line);
  if (!record) continue;
  if (record.type === "DOCHEAD") {
    docType = record.payload.docType || null;
    docUuid = record.payload.uuid || `${docType}:unknown`;
  }
  record.docType = docType;
  record.docUuid = docUuid;
  all.push(record);
}

const page = all.filter((r) => r.docType === "SCH_PAGE");
const pageDocUuid = page[0]?.docUuid || "";
const deviceMeta = new Map();
const footprintMeta = new Map();
const footprintPads = new Map();
for (const r of all) {
  if (r.docType === "DEVICE" && r.type === "META") {
    deviceMeta.set(r.docUuid, {
      title: r.payload.title || "",
      ...(r.payload.attributes || {}),
    });
  }
  if (r.docType === "FOOTPRINT" && r.type === "META") {
    footprintMeta.set(r.docUuid, {
      title: r.payload.title || "",
      description: r.payload.description || "",
    });
  }
  if (r.docType === "FOOTPRINT" && r.type === "PAD") {
    if (!footprintPads.has(r.docUuid)) footprintPads.set(r.docUuid, []);
    footprintPads.get(r.docUuid).push(r.payload);
  }
}
const attrs = new Map();
for (const r of all) {
  if (r.type !== "ATTR" || !r.payload.parentId) continue;
  const scopedParent = `${r.docUuid}|${r.payload.parentId}`;
  if (!attrs.has(scopedParent)) attrs.set(scopedParent, {});
  attrs.get(scopedParent)[r.payload.key] = r.payload.value;
}

const partPins = new Map();
for (const r of all) {
  if (r.type !== "PIN" || !r.payload.partId) continue;
  const pinAttrs = attrs.get(`${r.docUuid}|${r.id}`) || {};
  const scopedPart = `${r.docUuid}|${r.payload.partId}`;
  if (!partPins.has(scopedPart)) partPins.set(scopedPart, []);
  partPins.get(scopedPart).push({
    number: String(pinAttrs["Pin Number"] || ""),
    name: String(pinAttrs["Pin Name"] || ""),
    x: Number(r.payload.x),
    y: Number(r.payload.y),
    length: Number(r.payload.length || 0),
    rotation: Number(r.payload.rotation || 0),
  });
}

function transformPoint(x, y, rotation, mirror) {
  let px = x;
  let py = y;
  if (mirror) px = -px;
  const rot = ((Number(rotation) % 360) + 360) % 360;
  if (rot === 0) return [px, py];
  // EasyEDA schematic rotations use screen coordinates (positive angles are
  // clockwise), unlike the conventional mathematical counter-clockwise rule.
  if (rot === 90) return [py, -px];
  if (rot === 180) return [-px, -py];
  if (rot === 270) return [-py, px];
  const rad = (-rot * Math.PI) / 180;
  return [
    px * Math.cos(rad) - py * Math.sin(rad),
    px * Math.sin(rad) + py * Math.cos(rad),
  ];
}

function key(x, y) {
  return `${Number(x).toFixed(6)},${Number(y).toFixed(6)}`;
}

class DSU {
  constructor() {
    this.parent = new Map();
  }
  add(x) {
    if (!this.parent.has(x)) this.parent.set(x, x);
  }
  find(x) {
    this.add(x);
    const p = this.parent.get(x);
    if (p !== x) this.parent.set(x, this.find(p));
    return this.parent.get(x);
  }
  union(a, b) {
    const ra = this.find(a);
    const rb = this.find(b);
    if (ra !== rb) this.parent.set(rb, ra);
  }
}

function pointOnSegment([x, y], [x1, y1, x2, y2]) {
  // The epro2 interchange format contains small sub-grid coordinate drift
  // (often 0.1 to 0.4 schematic units) even for connections the editor treats
  // as snapped. Use the editor-scale tolerance instead of exact equality.
  const tolerance = 0.5;
  const dx = x2 - x1;
  const dy = y2 - y1;
  const length2 = dx * dx + dy * dy;
  if (length2 === 0) return Math.hypot(x - x1, y - y1) <= tolerance;
  const t = Math.max(0, Math.min(1, ((x - x1) * dx + (y - y1) * dy) / length2));
  const nearestX = x1 + t * dx;
  const nearestY = y1 + t * dy;
  return Math.hypot(x - nearestX, y - nearestY) <= tolerance;
}

const wireIds = new Set(page.filter((r) => r.type === "WIRE").map((r) => r.id));
const wireSegments = [];
for (const r of page) {
  if (r.type !== "LINE" || !wireIds.has(r.payload.lineGroup)) continue;
  const p = r.payload;
  if (![p.startX, p.startY, p.endX, p.endY].every(Number.isFinite)) continue;
  wireSegments.push({
    wireId: p.lineGroup,
    points: [Number(p.startX), Number(p.startY), Number(p.endX), Number(p.endY)],
  });
}

const components = page
  .filter((r) => r.type === "COMPONENT")
  .map((r) => {
    const a = attrs.get(`${r.docUuid}|${r.id}`) || {};
    const inherited = deviceMeta.get(a.Device || "") || {};
    const effective = { ...inherited };
    for (const [field, value] of Object.entries(a)) {
      if (value !== null && value !== undefined && value !== "") effective[field] = value;
    }
    const symbolUuid = a.Symbol || "";
    const pins = (partPins.get(`${symbolUuid}|${r.payload.partId}`) || []).map((pin) => {
      const pinRad = (-pin.rotation * Math.PI) / 180;
      const innerX = pin.x + pin.length * Math.cos(pinRad);
      const innerY = pin.y + pin.length * Math.sin(pinRad);
      const [dx, dy] = transformPoint(
        pin.x,
        pin.y,
        r.payload.rotation || 0,
        Boolean(r.payload.isMirror),
      );
      const [dx2, dy2] = transformPoint(
        innerX,
        innerY,
        r.payload.rotation || 0,
        Boolean(r.payload.isMirror),
      );
      return {
        number: pin.number,
        name: pin.name,
        x: Number(r.payload.x) + dx,
        y: Number(r.payload.y) + dy,
        x2: Number(r.payload.x) + dx2,
        y2: Number(r.payload.y) + dy2,
      };
    });
    return {
      id: r.id,
      partId: r.payload.partId,
      symbolUuid,
      ref: a.Designator || "",
      value: effective.Value || effective.Name || "",
      mpn: effective["Manufacturer Part"] || "",
      manufacturer: effective.Manufacturer || "",
      supplierPart: effective["Supplier Part"] || "",
      supplierFootprint: effective["Supplier Footprint"] || "",
      footprintId: effective.Footprint || "",
      footprintTitle: footprintMeta.get(effective.Footprint || "")?.title || "",
      datasheet: effective.Datasheet || "",
      addIntoBom: effective["Add into BOM"] || "",
      convertToPcb: effective["Convert to PCB"] || "",
      tolerance: effective.Tolerance || "",
      voltageRating:
        effective["Voltage Rating"] ||
        effective["Voltage-Supply(Max)"] ||
        effective["Voltage - Input(DC)"] ||
        "",
      currentRating:
        effective["Current Rating"] ||
        effective["Current(A)"] ||
        effective["Output Current"] ||
        "",
      powerRating: effective["Power(Watts)"] || effective.Power || "",
      description: effective.Description || "",
      x: Number(r.payload.x),
      y: Number(r.payload.y),
      rotation: Number(r.payload.rotation || 0),
      pins,
    };
  });

const dsu = new DSU();
const firstPointByWire = new Map();
for (const seg of wireSegments) {
  const [x1, y1, x2, y2] = seg.points;
  dsu.union(key(x1, y1), key(x2, y2));
  const firstPoint = firstPointByWire.get(seg.wireId);
  if (firstPoint) dsu.union(key(x1, y1), firstPoint);
  else firstPointByWire.set(seg.wireId, key(x1, y1));
}

// A WIRE record is already a complete EasyEDA electrical net. Only repair
// geometric joins inside the same WIRE group; joining different groups based
// solely on drawing overlap can incorrectly short crossing wires.
for (let i = 0; i < wireSegments.length; i++) {
  const a = wireSegments[i].points;
  for (let j = i + 1; j < wireSegments.length; j++) {
    if (wireSegments[i].wireId !== wireSegments[j].wireId) continue;
    const b = wireSegments[j].points;
    for (const p of [
      [a[0], a[1]],
      [a[2], a[3]],
    ]) {
      if (pointOnSegment(p, b)) dsu.union(key(p[0], p[1]), key(b[0], b[1]));
    }
    for (const p of [
      [b[0], b[1]],
      [b[2], b[3]],
    ]) {
      if (pointOnSegment(p, a)) dsu.union(key(p[0], p[1]), key(a[0], a[1]));
    }
  }
}

for (const component of components) {
  for (const pin of component.pins) {
    const pinKey = key(pin.x, pin.y);
    dsu.add(pinKey);
    for (const seg of wireSegments) {
      if (pointOnSegment([pin.x, pin.y], seg.points)) {
        dsu.union(pinKey, key(seg.points[0], seg.points[1]));
      }
    }
  }
}
for (const component of components) {
  for (const pin of component.pins) {
    pin.localRoot = dsu.find(key(pin.x, pin.y));
  }
}

const rootNames = new Map();
for (const wireId of wireIds) {
  const a = attrs.get(`${pageDocUuid}|${wireId}`) || {};
  const name = String(a.NET || "");
  if (!name) continue;
  const first = wireSegments.find((s) => s.wireId === wireId);
  if (!first) continue;
  const root = dsu.find(key(first.points[0], first.points[1]));
  if (!rootNames.has(root)) rootNames.set(root, new Set());
  rootNames.get(root).add(name);
}

// EasyEDA Pro exports power symbols such as GND, VCC and AVCC as unnamed
// one-pin components whose Name attribute is the global net name.
for (const component of components) {
  if (component.ref || component.pins.length !== 1) continue;
  const name = String(component.value || "");
  if (!name || name.startsWith("=")) continue;
  const pin = component.pins[0];
  const root = dsu.find(key(pin.x, pin.y));
  if (!rootNames.has(root)) rootNames.set(root, new Set());
  rootNames.get(root).add(name);
}

// Identically named global labels are the same electrical net.
const nameRoots = new Map();
for (const [root, names] of rootNames) {
  for (const name of names) {
    if (nameRoots.has(name)) dsu.union(root, nameRoots.get(name));
    else nameRoots.set(name, root);
  }
}

const finalRootNames = new Map();
for (const [root, names] of rootNames) {
  const finalRoot = dsu.find(root);
  if (!finalRootNames.has(finalRoot)) finalRootNames.set(finalRoot, new Set());
  for (const name of names) finalRootNames.get(finalRoot).add(name);
}

for (const component of components) {
  for (const pin of component.pins) {
    const root = dsu.find(key(pin.x, pin.y));
    pin.root = root;
    const names = [...(finalRootNames.get(root) || [])].sort();
    const touchesWire = wireSegments.some((seg) =>
      pointOnSegment([pin.x, pin.y], seg.points),
    );
    pin.net = names.length
      ? names.join("|")
      : touchesWire
        ? `$W:${root}`
        : `$P:${key(pin.x, pin.y)}`;
  }
}

console.log(
  JSON.stringify(
    {
      componentCount: components.length,
      wireCount: wireIds.size,
      wireSegmentCount: wireSegments.length,
      footprintCount: footprintMeta.size,
      footprintStats: [...footprintMeta].map(([id, meta]) => {
        const pads = footprintPads.get(id) || [];
        return {
          id,
          title: meta.title,
          description: meta.description,
          padCount: pads.length,
          padNumbers: [...new Set(pads.map((pad) => String(pad.num || "")))].sort(),
          pads: pads.map((pad) => ({
            num: String(pad.num || ""),
            layerId: pad.layerId,
            hole: pad.hole,
            x: pad.x,
            y: pad.y,
            rotation: pad.rotation,
            padType: pad.defaultPad?.padType || "",
            width: pad.defaultPad?.width,
            height: pad.defaultPad?.height,
          })),
        };
      }),
      components,
    },
    null,
    2,
  ),
);
