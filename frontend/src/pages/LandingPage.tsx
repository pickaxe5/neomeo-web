import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { SkyBackground } from "../components/SkyBackground";
import { LanguageSwitcher } from "../components/LanguageSwitcher";
import { useLanguage } from "../i18n/LanguageContext";

const CITIES = [
  { key: "landing.city.seoul", tz: "Asia/Seoul", dot: "oklch(0.75 0.12 75)" },
  { key: "landing.city.berlin", tz: "Europe/Berlin", dot: "oklch(0.65 0.12 240)" },
  { key: "landing.city.sf", tz: "America/Los_Angeles", dot: "oklch(0.7 0.1 160)" },
] as const;

function getTime(tz: string) {
  return new Date().toLocaleTimeString("en-GB", {
    timeZone: tz,
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  });
}

function getStatusKey(tz: string): string {
  const hour = parseInt(
    new Date().toLocaleTimeString("en-GB", { timeZone: tz, hour: "2-digit", hour12: false })
  );
  if (hour >= 9 && hour < 18) return "landing.statusWorking";
  if (hour >= 18 && hour < 23) return "landing.statusEvening";
  return "landing.statusSleeping";
}

function statusColor(key: string) {
  if (key === "landing.statusWorking") return "oklch(0.7 0.1 160)";
  if (key === "landing.statusEvening") return "oklch(0.75 0.12 75)";
  return "oklch(0.55 0.03 265)";
}

function LiveClocks() {
  const { t } = useLanguage();
  const [times, setTimes] = useState(CITIES.map((c) => getTime(c.tz)));
  useEffect(() => {
    const id = setInterval(() => setTimes(CITIES.map((c) => getTime(c.tz))), 1000);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="landing-card landing-clocks">
      <div className="landing-clocks-head">
        <span className="dot" />
        <span>LIVE CLOCKS</span>
      </div>
      {CITIES.map((city, i) => {
        const statusKey = getStatusKey(city.tz);
        return (
          <div key={city.tz} className="landing-clock-row">
            <div className="landing-clock-city">
              <span className="dot" style={{ background: city.dot }} />
              <div className="name">{t(city.key)}</div>
            </div>
            <div className="landing-clock-time">
              <div className="time">{times[i]}</div>
              <div className="status" style={{ color: statusColor(statusKey) }}>
                {t(statusKey)}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

function TimelineMocks() {
  const { t } = useLanguage();
  const mocks = [
    {
      team: t("landing.mockSeoulTeam"),
      city: "Seoul, KST",
      time: "18:07",
      localTime: "10:07",
      summary: t("landing.mockSeoulSummary"),
      items: [t("landing.mockSeoulItem1"), t("landing.mockSeoulItem2")],
      dot: "oklch(0.75 0.12 75)",
    },
    {
      team: t("landing.mockBerlinTeam"),
      city: "Berlin, CET",
      time: "11:30",
      localTime: "18:30",
      summary: t("landing.mockBerlinSummary"),
      items: [t("landing.mockBerlinItem1"), t("landing.mockBerlinItem2")],
      dot: "oklch(0.65 0.12 240)",
    },
  ];

  return (
    <div className="landing-mock-timeline">
      {mocks.map((card) => (
        <div key={card.team} className="landing-card">
          <div className="landing-mock-card-head">
            <div className="landing-mock-team">
              <span className="dot" style={{ background: card.dot }} />
              <div>
                <div className="name">{card.team}</div>
                <div className="city">{card.city}</div>
              </div>
            </div>
            <div className="landing-mock-time">
              <div className="time">{card.time}</div>
              <div className="local">
                {t("landing.myTime")} {card.localTime}
              </div>
            </div>
          </div>
          <p className="landing-mock-summary">{card.summary}</p>
          <div className="landing-mock-items">
            {card.items.map((item) => (
              <div key={item}>· {item}</div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function scrollTo(id: string) {
  document.querySelector(id)?.scrollIntoView({ behavior: "smooth" });
}

export function LandingPage() {
  const { t } = useLanguage();

  const features = [
    { title: t("landing.feature1Title"), desc: t("landing.feature1Desc"), color: "oklch(0.75 0.12 75)" },
    { title: t("landing.feature2Title"), desc: t("landing.feature2Desc"), color: "oklch(0.65 0.12 240)" },
    { title: t("landing.feature3Title"), desc: t("landing.feature3Desc"), color: "oklch(0.7 0.1 160)" },
    { title: t("landing.feature4Title"), desc: t("landing.feature4Desc"), color: "oklch(0.55 0.15 300)" },
    { title: t("landing.feature5Title"), desc: t("landing.feature5Desc"), color: "oklch(0.6 0.18 30)" },
    { title: t("landing.feature6Title"), desc: t("landing.feature6Desc"), color: "oklch(0.75 0.12 75)" },
  ];

  const steps = [
    { num: "01", title: t("landing.step1Title"), desc: t("landing.step1Desc") },
    { num: "02", title: t("landing.step2Title"), desc: t("landing.step2Desc") },
    { num: "03", title: t("landing.step3Title"), desc: t("landing.step3Desc") },
    { num: "04", title: t("landing.step4Title"), desc: t("landing.step4Desc") },
  ];

  const solutionItems = [
    { title: t("landing.solutionItem1Title"), desc: t("landing.solutionItem1Desc") },
    { title: t("landing.solutionItem2Title"), desc: t("landing.solutionItem2Desc") },
    { title: t("landing.solutionItem3Title"), desc: t("landing.solutionItem3Desc") },
  ];

  const roadmapItems = [
    { title: t("landing.roadmapItem1Title"), desc: t("landing.roadmapItem1Desc"), color: "oklch(0.65 0.12 240)" },
    { title: t("landing.roadmapItem2Title"), desc: t("landing.roadmapItem2Desc"), color: "oklch(0.7 0.1 160)" },
    { title: t("landing.roadmapItem3Title"), desc: t("landing.roadmapItem3Desc"), color: "oklch(0.75 0.12 75)" },
  ];

  return (
    <div className="landing">
      <SkyBackground />

      <header className="landing-navbar">
        <div className="landing-navbar-inner">
          <Link to="/" className="brand">
            <span className="brand-ko">너머</span>
            <span className="brand-en">NEOMEO</span>
          </Link>
          <nav className="landing-navbar-links">
            <a onClick={() => scrollTo("#landing-solution")}>{t("landing.navSolution")}</a>
            <a onClick={() => scrollTo("#landing-features")}>{t("landing.navFeatures")}</a>
            <a onClick={() => scrollTo("#landing-roadmap")}>{t("landing.navRoadmap")}</a>
            <a onClick={() => scrollTo("#landing-how")}>{t("landing.navHow")}</a>
          </nav>
          <div className="landing-navbar-actions">
            <LanguageSwitcher className="navbar-lang" />
            <Link to="/login">
              <button className="primary">{t("landing.ctaButton")}</button>
            </Link>
          </div>
        </div>
      </header>

      <section className="landing-hero">
        <div className="landing-hero-grid">
          <div>
            <div className="landing-eyebrow">
              <span className="landing-eyebrow-dot" />
              {t("landing.eyebrow")}
            </div>
            <h1 className="landing-hero-title">
              {t("landing.heroTitleLine1")}
              <br />
              <span className="accent">{t("landing.heroTitleLine2")}</span>
              <br />
              {t("landing.heroTitleLine3")}
            </h1>
            <p className="landing-hero-sub">
              {t("landing.heroSub")} <strong>{t("landing.heroSubStrong")}</strong>
            </p>
            <div className="landing-hero-ctas">
              <Link to="/login">
                <button className="primary">{t("landing.heroCtaPrimary")}</button>
              </Link>
              <Link to="/login">
                <button>{t("landing.heroCtaSecondary")}</button>
              </Link>
            </div>
            <div className="landing-hero-trust">
              {[t("landing.trustGithub"), t("landing.trustOnboarding"), t("landing.trustFree")].map((label) => (
                <span key={label}>
                  <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                    <path
                      d="M7 1a6 6 0 1 0 0 12A6 6 0 0 0 7 1zm2.5 4.5L6 9 4.5 7.5"
                      stroke="currentColor"
                      strokeWidth="1.5"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                  {label}
                </span>
              ))}
            </div>
          </div>
          <div>
            <LiveClocks />
            <TimelineMocks />
          </div>
        </div>
      </section>

      <section id="landing-solution" className="landing-section">
        <div className="landing-grid-2">
          <div>
            <div className="landing-eyebrow">{t("landing.solutionEyebrow")}</div>
            <h2 style={{ fontSize: 34, fontWeight: 800, letterSpacing: "-0.02em", lineHeight: 1.25 }}>
              {t("landing.solutionTitle")}
            </h2>
            <p style={{ color: "var(--text-dim)", fontSize: 15, lineHeight: 1.7 }}>
              {t("landing.solutionDesc")}{" "}
              <strong style={{ color: "var(--text-h)" }}>{t("landing.solutionDescStrong")}</strong>{" "}
              {t("landing.solutionDescEnd")}
            </p>
            <div className="landing-solution-list">
              {solutionItems.map((item) => (
                <div key={item.title} className="landing-solution-item">
                  <span className="check">
                    <span />
                  </span>
                  <div>
                    <strong>{item.title}</strong>
                    <p>{item.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
          <div className="landing-card">
            <h3 style={{ marginBottom: 12 }}>{t("landing.solutionMockGreeting")}</h3>
            <p style={{ color: "var(--text-dim)", fontSize: 12.5, marginBottom: 14 }}>
              {t("landing.solutionMockTime")}
            </p>
            <div className="landing-solution-list">
              <div className="landing-solution-item">
                <span className="check">
                  <span />
                </span>
                <div>
                  <strong>{t("landing.solutionMockQ1")}</strong>
                  <p>{t("landing.solutionMockQ1From")}</p>
                </div>
              </div>
              <div className="landing-solution-item">
                <span className="check">
                  <span />
                </span>
                <div>
                  <strong>{t("landing.solutionMockQ2")}</strong>
                  <p>{t("landing.solutionMockQ2From")}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section id="landing-features" className="landing-section">
        <div className="landing-section-head">
          <h2>
            {t("landing.featuresTitle1")}
            <br />
            {t("landing.featuresTitle2")}
          </h2>
          <p>{t("landing.featuresSub")}</p>
        </div>
        <div className="landing-feature-grid">
          {features.map((f) => (
            <div key={f.title} className="landing-card">
              <div className="landing-card-icon" style={{ background: `${f.color}22`, color: f.color }}>
                ●
              </div>
              <h3>{f.title}</h3>
              <p>{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      <section id="landing-roadmap" className="landing-section">
        <div className="landing-section-head">
          <div className="landing-eyebrow">{t("landing.roadmapEyebrow")}</div>
          <h2>
            {t("landing.roadmapTitle1")}
            <br />
            {t("landing.roadmapTitle2")}
          </h2>
          <p>{t("landing.roadmapSub")}</p>
        </div>
        <div className="landing-feature-grid">
          {roadmapItems.map((item) => (
            <div key={item.title} className="landing-card">
              <div className="landing-card-icon" style={{ background: `${item.color}22`, color: item.color }}>
                ●
              </div>
              <div className="badge muted" style={{ marginBottom: 10 }}>
                {t("landing.roadmapBadge")}
              </div>
              <h3>{item.title}</h3>
              <p>{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      <section id="landing-how" className="landing-section">
        <div className="landing-section-head">
          <h2>
            {t("landing.howTitle1")}
            <br />
            {t("landing.howTitle2")}
          </h2>
          <p>{t("landing.howSub")}</p>
        </div>
        <div className="landing-steps-grid">
          {steps.map((s) => (
            <div key={s.num} className="landing-card">
              <div className="landing-step-num">{s.num}</div>
              <h3>{s.title}</h3>
              <p>{s.desc}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="landing-section landing-cta">
        <div className="landing-eyebrow">{t("landing.ctaEyebrow")}</div>
        <h2>{t("landing.ctaTitle")}</h2>
        <p>{t("landing.ctaSub")}</p>
        <div className="landing-cta-actions">
          <Link to="/login">
            <button className="primary">{t("landing.ctaPrimary")}</button>
          </Link>
          <Link to="/login">
            <button>{t("landing.ctaSecondary")}</button>
          </Link>
        </div>
        <p className="landing-cta-fine">{t("landing.ctaFine")}</p>
      </section>

      <footer className="landing-footer">
        <div className="landing-footer-inner">
          <div className="landing-footer-brand">
            <span className="brand-ko" style={{ fontSize: 16 }}>
              너머
            </span>
            <p>{t("landing.footerTagline")}</p>
          </div>
          <div className="landing-footer-bottom">
            <p>{t("landing.footerCopyright")}</p>
            <div className="landing-footer-cities">
              {CITIES.map((city) => (
                <span key={city.key}>{t(city.key)}</span>
              ))}
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
