const fs = require("fs");
const path = require("path");

const root = process.argv[2] ? path.resolve(process.argv[2]) : __dirname;
function findFirstFile(dir, extension) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      const nested = findFirstFile(full, extension);
      if (nested) return nested;
    } else if (entry.name.toLowerCase().endsWith(extension)) {
      return full;
    }
  }
  return null;
}
const schPath = findFirstFile(path.join(root, "SHEET"), ".esch");
if (!schPath) throw new Error(`No .esch file found under ${root}`);
const project = JSON.parse(fs.readFileSync(path.join(root, "project.json"), "utf8"));

function readJsonLines(file) {
  return fs
    .readFileSync(file, "utf8")
    .split(/\r?\n/)
    .filter(Boolean)
    .map((line) => JSON.parse(line));
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

function attrsFor(records, parentId) {
  const out = {};
  for (const r of records) {
    if (r[0] === "ATTR" && r[2] === parentId) out[r[3]] = r[4];
  }
  return out;
}

function transformPoint(x, y, rotation, mirror) {
  let px = x;
  let py = y;
  if (mirror) px = -px;
  const rot = ((Number(rotation) % 360) + 360) % 360;
  if (rot === 0) return [px, py];
  if (rot === 90) return [-py, px];
  if (rot === 180) return [-px, -py];
  if (rot === 270) return [py, -px];
  const rad = (rot * Math.PI) / 180;
  return [
    px * Math.cos(rad) - py * Math.sin(rad),
    px * Math.sin(rad) + py * Math.cos(rad),
  ];
}

function pointOnSegment([x, y], [x1, y1, x2, y2]) {
  const eps = 1e-6;
  const cross = (x - x1) * (y2 - y1) - (y - y1) * (x2 - x1);
  if (Math.abs(cross) > eps) return false;
  return (
    x >= Math.min(x1, x2) - eps &&
    x <= Math.max(x1, x2) + eps &&
    y >= Math.min(y1, y2) - eps &&
    y <= Math.max(y1, y2) + eps
  );
}

const records = readJsonLines(schPath);
const components = new Map();
const wires = [];
const wireAttrs = new Map();

for (const r of records) {
  if (r[0] === "COMPONENT") {
    components.set(r[1], {
      id: r[1],
      title: r[2],
      x: Number(r[3]),
      y: Number(r[4]),
      rotation: Number(r[5] || 0),
      mirror: Number(r[6] || 0),
      attrs: {},
      pins: [],
    });
  } else if (r[0] === "ATTR" && components.has(r[2])) {
    components.get(r[2]).attrs[r[3]] = r[4];
  } else if (r[0] === "WIRE") {
    wires.push({ id: r[1], segments: r[2] });
  } else if (r[0] === "ATTR") {
    if (!wireAttrs.has(r[2])) wireAttrs.set(r[2], {});
    wireAttrs.get(r[2])[r[3]] = r[4];
  }
}

const symbolCache = new Map();
function loadSymbol(symbolId) {
  if (symbolCache.has(symbolId)) return symbolCache.get(symbolId);
  const file = path.join(root, "SYMBOL", `${symbolId}.esym`);
  const sRecords = readJsonLines(file);
  const pinAttrs = new Map();
  for (const r of sRecords) {
    if (r[0] === "ATTR") {
      if (!pinAttrs.has(r[2])) pinAttrs.set(r[2], {});
      pinAttrs.get(r[2])[r[3]] = r[4];
    }
  }
  const pins = [];
  for (const r of sRecords) {
    if (r[0] !== "PIN") continue;
    const a = pinAttrs.get(r[1]) || {};
    pins.push({
      id: r[1],
      part: Number(r[2] || 1),
      x: Number(r[4]),
      y: Number(r[5]),
      name: a.NAME || "",
      number: String(a.NUMBER || ""),
      type: a["Pin Type"] || "",
    });
  }
  symbolCache.set(symbolId, pins);
  return pins;
}

for (const c of components.values()) {
  const device = project.devices?.[c.attrs.Device];
  const inherited = device?.attributes || {};
  c.fullAttrs = { ...inherited, ...c.attrs };
  c.ref = c.attrs.Designator || "";
  c.value = c.attrs.Value || inherited.Value || "";
  c.mpn = c.attrs["Manufacturer Part"] || inherited["Manufacturer Part"] || "";
  c.footprint =
    c.attrs["Supplier Footprint"] || inherited["Supplier Footprint"] || "";
  const symbolId = c.attrs.Symbol || inherited.Symbol;
  if (!symbolId) continue;
  const partMatch = c.title.match(/\.(\d+)$/);
  const part = partMatch ? Number(partMatch[1]) : 1;
  const symbolPins = loadSymbol(symbolId).filter((p) => p.part === part);
  for (const p of symbolPins) {
    const [dx, dy] = transformPoint(p.x, p.y, c.rotation, c.mirror);
    c.pins.push({
      ...p,
      x: c.x + dx,
      y: c.y + dy,
      netKey: null,
      net: "",
    });
  }
}

const dsu = new DSU();
for (const w of wires) dsu.add(`W:${w.id}`);

// Attach pins to wire records. If more than one wire record touches the same pin,
// they are electrically the same net.
for (const c of components.values()) {
  for (const p of c.pins) {
    const touching = [];
    for (const w of wires) {
      if (w.segments.some((s) => pointOnSegment([p.x, p.y], s))) {
        touching.push(`W:${w.id}`);
      }
    }
    if (touching.length) {
      p.netKey = touching[0];
      for (let i = 1; i < touching.length; i++) dsu.union(touching[0], touching[i]);
    } else {
      p.netKey = `P:${p.x},${p.y}`;
      dsu.add(p.netKey);
    }
  }
}

// Coincident pins are connected even when no explicit wire segment is present.
const pinAt = new Map();
for (const c of components.values()) {
  for (const p of c.pins) {
    const key = `${p.x},${p.y}`;
    if (pinAt.has(key)) dsu.union(pinAt.get(key), p.netKey);
    else pinAt.set(key, p.netKey);
  }
}

// Components without a designator are net symbols. Their displayed Name is the
// net name; identically named symbols are globally connected.
const firstByLabel = new Map();
for (const c of components.values()) {
  if (c.ref || !c.attrs.Name || c.pins.length !== 1) continue;
  const label = String(c.attrs.Name);
  c.isNetLabel = true;
  c.netLabel = label;
  const key = c.pins[0].netKey;
  if (firstByLabel.has(label)) dsu.union(firstByLabel.get(label), key);
  else firstByLabel.set(label, key);
}

const labelsByRoot = new Map();
for (const w of wires) {
  const label = wireAttrs.get(w.id)?.NET;
  if (!label) continue;
  const rootKey = dsu.find(`W:${w.id}`);
  if (!labelsByRoot.has(rootKey)) labelsByRoot.set(rootKey, new Set());
  labelsByRoot.get(rootKey).add(String(label));
}
for (const c of components.values()) {
  if (!c.isNetLabel) continue;
  const rootKey = dsu.find(c.pins[0].netKey);
  if (!labelsByRoot.has(rootKey)) labelsByRoot.set(rootKey, new Set());
  labelsByRoot.get(rootKey).add(c.netLabel);
}

for (const c of components.values()) {
  for (const p of c.pins) {
    const rootKey = dsu.find(p.netKey);
    const labels = labelsByRoot.get(rootKey);
    p.net = labels?.size ? [...labels].sort().join("|") : `$${rootKey}`;
  }
}

function designatorSort(a, b) {
  const ma = String(a.ref).match(/^([A-Za-z]+)(\d+)$/);
  const mb = String(b.ref).match(/^([A-Za-z]+)(\d+)$/);
  if (!ma || !mb) return String(a.ref).localeCompare(String(b.ref));
  const prefix = ma[1].localeCompare(mb[1]);
  return prefix || Number(ma[2]) - Number(mb[2]);
}

const actual = [...components.values()].filter((c) => c.ref).sort(designatorSort);
const summary = {
  componentCount: actual.length,
  wireCount: wires.length,
  components: actual.map((c) => ({
    ref: c.ref,
    value: c.value,
    mpn: c.mpn,
    footprint: c.footprint,
    addIntoBom: c.fullAttrs["Add into BOM"] || "",
    convertToPcb: c.fullAttrs["Convert to PCB"] || "",
    voltageRating:
      c.fullAttrs["Voltage Rating"] ||
      c.fullAttrs["Voltage Rated"] ||
      c.fullAttrs["Working Voltage"] ||
      "",
    powerRating:
      c.fullAttrs["Power(Watts)"] ||
      c.fullAttrs["Power Rating"] ||
      c.fullAttrs.Power ||
      "",
    tolerance: c.fullAttrs.Tolerance || "",
    x: c.x,
    y: c.y,
    rotation: c.rotation,
    pins: c.pins.map((p) => ({
      number: p.number,
      name: p.name,
      x: p.x,
      y: p.y,
      net: p.net,
    })),
  })),
};

process.stdout.write(JSON.stringify(summary, null, 2));
