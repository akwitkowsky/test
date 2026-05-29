// One-off icon generator. Renders the app icon SVG to the PNG sizes the
// manifest + iOS need. Run with: node scripts/gen-icons.mjs
// (sharp is a dev-time-only dependency and is not required to build/run the app)
import sharp from 'sharp';
import { mkdir } from 'node:fs/promises';

const OUT = new URL('../public/icons/', import.meta.url);

// "any" icon: dollar sign fills most of the frame.
const icon = (size, inset) => {
  const pad = Math.round(size * inset);
  const fontSize = Math.round((size - pad * 2) * 1.05);
  const cy = size / 2 + fontSize * 0.34;
  const radius = Math.round(size * 0.22);
  return Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}">
  <rect width="${size}" height="${size}" rx="${radius}" ry="${radius}" fill="#0a0e12"/>
  <text x="50%" y="${cy}" text-anchor="middle"
        font-family="Helvetica, Arial, sans-serif" font-weight="800"
        font-size="${fontSize}" fill="#2bd97c">$</text>
</svg>`);
};

await mkdir(OUT, { recursive: true });

const jobs = [
  { name: 'icon-192.png', size: 192, inset: 0.14 },
  { name: 'icon-512.png', size: 512, inset: 0.14 },
  // maskable: extra padding so the glyph survives Android's circle mask
  { name: 'icon-maskable-512.png', size: 512, inset: 0.22 },
  // iOS home screen icon (iOS applies its own rounded mask)
  { name: 'apple-touch-icon.png', size: 180, inset: 0.14 },
];

for (const { name, size, inset } of jobs) {
  await sharp(icon(size, inset)).png().toFile(new URL(name, OUT).pathname);
  console.log('wrote', name);
}
