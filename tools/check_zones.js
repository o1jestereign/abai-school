const fs = require('fs'), path = require('path');
const root = path.join(__dirname, '..');
const el = () => new Proxy(function () {}, { get: () => () => ({}) });
global.window = global; global.document = { getElementById: el, createElement: el };
global.atob = (s) => Buffer.from(s, 'base64').toString('binary');
eval(fs.readFileSync(path.join(root, 'js/mapdata.js'), 'utf8').replace('window.MAPDATA', 'global.MAPDATA'));

const D = global.MAPDATA;
for (const fl of D.floors) {
  console.log(`=== FLOOR ${fl.floor} ===`);
  const bin = atob(fl.grid);
  const grid = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) grid[i] = bin.charCodeAt(i);
  
  // check stair connectivity
  console.log(`Stairs (${fl.stairs.length}):`);
  fl.stairs.forEach(s => {
    console.log(`  stair ${s.id}: (${s.x}, ${s.y}) gridVal=${grid[s.y * fl.gw + s.x]} up=${s.up} down=${s.down}`);
  });

  for (const name of ['305 кабинет', 'Кітапхана', 'Дәретхана 2.1', '123 кабинет', 'Спорт залы']) {
    const z = fl.zones.find(q => q.name === name);
    if (z) {
      console.log(`  zone '${name}': (${z.cx}, ${z.cy}) gridVal=${grid[z.cy * fl.gw + z.cx]}`);
    }
  }
}
