import { useEffect, useState } from "react";

// Same "Dawn Relay" time-of-day sky system as the marketing landing page —
// ported here so the logged-in app shares the living day/night background.
type SkyStop = {
  hour: number;
  top: [number, number, number];
  bottom: [number, number, number];
  star: number;
  glow: number;
};

const SKY_STOPS: SkyStop[] = [
  { hour: 0, top: [0.13, 0.05, 265], bottom: [0.17, 0.06, 267], star: 1, glow: 0.08 },
  { hour: 5, top: [0.14, 0.05, 266], bottom: [0.19, 0.07, 268], star: 1, glow: 0.1 },
  { hour: 6.5, top: [0.18, 0.07, 270], bottom: [0.3, 0.09, 50], star: 0.3, glow: 0.55 },
  { hour: 9, top: [0.2, 0.07, 270], bottom: [0.34, 0.08, 75], star: 0, glow: 0.35 },
  { hour: 13, top: [0.19, 0.06, 265], bottom: [0.26, 0.07, 240], star: 0, glow: 0.15 },
  { hour: 17, top: [0.18, 0.06, 266], bottom: [0.28, 0.09, 60], star: 0, glow: 0.3 },
  { hour: 18.5, top: [0.16, 0.06, 268], bottom: [0.32, 0.11, 40], star: 0.2, glow: 0.6 },
  { hour: 20, top: [0.14, 0.05, 266], bottom: [0.2, 0.07, 268], star: 0.8, glow: 0.15 },
  { hour: 24, top: [0.13, 0.05, 265], bottom: [0.17, 0.06, 267], star: 1, glow: 0.08 },
];

function lerp(a: number, b: number, t: number) {
  return a + (b - a) * t;
}

function getSkyState(hourFraction: number) {
  const h = ((hourFraction % 24) + 24) % 24;
  let i = 0;
  while (i < SKY_STOPS.length - 1 && SKY_STOPS[i + 1].hour < h) i++;
  const a = SKY_STOPS[i];
  const b = SKY_STOPS[Math.min(i + 1, SKY_STOPS.length - 1)];
  const span = b.hour - a.hour || 1;
  const t = Math.max(0, Math.min(1, (h - a.hour) / span));
  const top = a.top.map((v, idx) => lerp(v, b.top[idx], t)) as [number, number, number];
  const bottom = a.bottom.map((v, idx) => lerp(v, b.bottom[idx], t)) as [number, number, number];
  return { top, bottom, star: lerp(a.star, b.star, t), glow: lerp(a.glow, b.glow, t) };
}

export function oklch([l, c, h]: [number, number, number]) {
  return `oklch(${l.toFixed(3)} ${c.toFixed(3)} ${h.toFixed(1)})`;
}

function smoothEdge(x: number, edge0: number, edge1: number) {
  const t = Math.max(0, Math.min(1, (x - edge0) / (edge1 - edge0)));
  return t * t * (3 - 2 * t);
}

function arcPosition(t: number) {
  return { x: lerp(6, 60, t), y: 20 - Math.sin(Math.PI * t) * 11 };
}

function getCelestial(h: number) {
  const sunOpacity = smoothEdge(h, 4.5, 6.5) * (1 - smoothEdge(h, 17.5, 19.5));
  const sunT = Math.max(0, Math.min(1, (h - 4.5) / (19.5 - 4.5)));

  const hShifted = h < 12 ? h + 24 : h;
  const moonOpacity = smoothEdge(hShifted, 16.5, 18.5) * (1 - smoothEdge(hShifted, 29.5, 31.5));
  const moonT = Math.max(0, Math.min(1, (hShifted - 16.5) / (31.5 - 16.5)));

  return { sunPos: arcPosition(sunT), sunOpacity, moonPos: arcPosition(moonT), moonOpacity };
}

export function useSkyClock() {
  const [now, setNow] = useState(() => new Date());
  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 10_000);
    return () => clearInterval(id);
  }, []);
  const hourFraction = now.getHours() + now.getMinutes() / 60;
  return { ...getSkyState(hourFraction), ...getCelestial(hourFraction) };
}
