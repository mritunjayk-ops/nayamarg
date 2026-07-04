"use client";

import { useEffect, useState } from "react";
import { AlertCircle, ArrowRight } from "lucide-react";
import { api } from "../lib/api";
import IntakeForm from "./components/IntakeForm";
import BlueprintResult from "./components/BlueprintResult";

export default function Home() {
  const [online, setOnline] = useState(null); // null = unknown, true/false once checked
  const [phase, setPhase] = useState("form"); // "form" | "loading" | "result"
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let active = true;
    api.getStatus().then(({ error }) => {
      if (active) setOnline(!error);
    });
    return () => {
      active = false;
    };
  }, []);

  async function handleGenerate(candidate, tier, language) {
    setError(null);
    setPhase("loading");
    const { data, error } = await api.generateBlueprint(candidate, tier, language);
    if (error) {
      setError(error);
      setPhase("form");
      return;
    }
    setResult(data);
    setPhase("result");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function restart() {
    setResult(null);
    setError(null);
    setPhase("form");
  }

  return (
    <div className="page">
      <header className="site-header">
        <div className="wrap">
          <a className="brand" href="/">
            <img className="brand-logo" src="/nayamarg_logo.svg" alt="NayaMarg logo" width={38} height={38} />
            <span className="brand-name">Naya<em>Marg</em></span>
          </a>
          <span className="header-status">
            <span className={`dot ${online ? "live" : ""}`} />
            {online === null ? "Connecting…" : online ? "Connected" : "Backend offline"}
          </span>
        </div>
      </header>

      {phase !== "result" && (
        <section className="hero">
          <div className="wrap">
            <span className="eyebrow reveal d1">For UPSC &amp; competitive-exam aspirants</span>
            <h1 className="reveal d2">
              You prepared for years. Now find your <em>new path</em>.
            </h1>
            <p className="lede reveal d3">
              NayaMarg turns your exam preparation into a real, personalized career plan —
              the roles that genuinely fit your background, and the exact topics to master to get there.
            </p>
            <div className="hero-actions reveal d4">
              <a className="btn btn-primary" href="#start">
                Build my blueprint <ArrowRight size={17} />
              </a>
            </div>
            <div className="hero-meta reveal d5">
              <div className="stat"><div className="n">3</div><div className="l">career paths, scored for fit</div></div>
              <div className="stat"><div className="n">Topic-based</div><div className="l">plan you check off as you learn</div></div>
              <div className="stat"><div className="n">₹149</div><div className="l">for the full blueprint</div></div>
            </div>
          </div>
        </section>
      )}

      <section className="section" id="start">
        <div className="wrap">
          {phase !== "result" && (
            <div className="section-head">
              <div className="section-kicker">Your blueprint</div>
              <h2>A plan built around your actual situation</h2>
              <p>Answer a few questions. It takes about two minutes — there are no wrong answers.</p>
            </div>
          )}

          {online === false && (
            <div className="notice">
              <AlertCircle size={16} />
              Can't reach the backend yet. Start it, then reload this page.
            </div>
          )}

          {error && (
            <div className="alert">
              <AlertCircle size={17} />
              <span>{error}</span>
            </div>
          )}

          {phase === "loading" && (
            <div className="panel">
              <div className="loading">
                <div className="ring" />
                <p>Reading your background and shaping a plan that fits. This can take up to a minute.</p>
              </div>
            </div>
          )}

          {phase === "form" && <IntakeForm onGenerate={handleGenerate} />}

          {phase === "result" && result && (
            <BlueprintResult result={result} pdfUrl={api.pdfUrl} onRestart={restart} />
          )}
        </div>
      </section>

      <footer className="site-footer">
        <div className="wrap">
          <span>NayaMarg · a calmer way to find your next chapter</span>
          <span>AI-assisted guidance · no job or income is guaranteed</span>
        </div>
      </footer>
    </div>
  );
}
