import { oklch, useSkyClock } from "../lib/sky";

// Fixed backdrop behind the whole authenticated app — the same living
// day/night sky as the marketing landing page's hero, so the product feels
// like one continuous piece of design instead of two different apps.
export function SkyBackground() {
  const sky = useSkyClock();

  return (
    <div
      className="sky-background"
      style={{
        background: `
          radial-gradient(ellipse 70% 50% at 20% -5%, oklch(0.28 0.08 270 / 55%) 0%, transparent 70%),
          radial-gradient(ellipse 35% 35% at 85% 10%, oklch(0.75 0.12 75 / ${(sky.glow * 60).toFixed(0)}%) 0%, transparent 60%),
          linear-gradient(180deg, ${oklch(sky.top)} 0%, ${oklch(sky.bottom)} 100%)
        `,
        transition: "background 10s linear",
      }}
    >
      <div className="sky-stars" style={{ opacity: sky.star, transition: "opacity 10s linear" }}>
        {[...Array(24)].map((_, i) => (
          <div
            key={i}
            className="sky-star"
            style={{
              width: Math.random() * 2 + 1 + "px",
              height: Math.random() * 2 + 1 + "px",
              left: Math.random() * 100 + "%",
              top: Math.random() * 60 + "%",
            }}
          />
        ))}
      </div>

      <div
        className="sky-sun"
        style={{
          left: `${sky.sunPos.x}%`,
          top: `${sky.sunPos.y}%`,
          opacity: sky.sunOpacity,
        }}
      />
      <div
        className="sky-moon"
        style={{
          left: `${sky.moonPos.x}%`,
          top: `${sky.moonPos.y}%`,
          opacity: sky.moonOpacity,
        }}
      />
    </div>
  );
}
