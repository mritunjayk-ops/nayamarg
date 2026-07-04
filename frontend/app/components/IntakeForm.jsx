"use client";

import { useState } from "react";
import { ArrowLeft, ArrowRight, Sparkles } from "lucide-react";

const EMPTY = {
  age_group: "",
  qualification: "",
  background: "",
  exams: "",
  years_preparing: "",
  current_situation: "",
  worries: "",
  main_stress: "",
  situation_words: "",
  interests: "",
  // survey-only fields the generator doesn't need — sent empty
  explored_alternative: "",
  alternative_path: "",
  value_rating: "",
  blueprint_interest: "",
  price_preference: "",
  trust_factor: "",
  free_blueprint: "",
  interview_interest: "",
};

const AGE = ["Under 21", "21–25", "26–30", "31–35", "Above 35"];
const QUALIFICATION = ["Class 12", "Diploma", "Bachelor's degree", "Master's degree", "Other"];
const YEARS = ["Less than 1 year", "1–2 years", "3–4 years", "5–6 years", "More than 6 years"];
const SITUATION = [
  "Still preparing",
  "Recently stopped preparing",
  "Working a job",
  "Unemployed / on a gap",
  "Studying something else",
];
const STRESS = [
  "Resume / career gap",
  "Family pressure",
  "Financial pressure",
  "Fear of starting late",
  "Confusion about what to do next",
  "Low confidence after setbacks",
];

const STEPS = ["About you", "Exam journey", "Where you are", "Direction"];

function Select({ label, value, onChange, options, placeholder }) {
  return (
    <div className="field">
      <label>{label}</label>
      <select value={value} onChange={(e) => onChange(e.target.value)}>
        <option value="">{placeholder || "Select…"}</option>
        {options.map((o) => (
          <option key={o} value={o}>{o}</option>
        ))}
      </select>
    </div>
  );
}

function Text({ label, value, onChange, placeholder, wide }) {
  return (
    <div className={`field${wide ? " wide" : ""}`}>
      <label>{label}</label>
      <input value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder} />
    </div>
  );
}

function Area({ label, value, onChange, placeholder }) {
  return (
    <div className="field wide">
      <label>{label}</label>
      <textarea value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder} />
    </div>
  );
}

export default function IntakeForm({ onGenerate, disabled }) {
  const [step, setStep] = useState(0);
  const [c, setC] = useState(EMPTY);
  const [tier, setTier] = useState("sample");
  const [language, setLanguage] = useState("english");

  const set = (key) => (val) => setC((prev) => ({ ...prev, [key]: val }));
  const last = step === STEPS.length - 1;

  return (
    <div className="panel intake">
      <div className="stepper">
        {STEPS.map((s, i) => (
          <div key={s} className={`step ${i < step ? "done" : ""} ${i === step ? "active" : ""}`}>
            <div className="bar"><i /></div>
            <div className="lbl">{s}</div>
          </div>
        ))}
      </div>

      {step === 0 && (
        <>
          <h3 className="step-title">Tell us about you</h3>
          <p className="step-sub">A few basics so the plan fits your actual situation.</p>
          <div className="grid-2">
            <Select label="Age group" value={c.age_group} onChange={set("age_group")} options={AGE} />
            <Select label="Highest qualification" value={c.qualification} onChange={set("qualification")} options={QUALIFICATION} />
            <Text label="Educational background" value={c.background} onChange={set("background")} placeholder="e.g. B.Tech Mechanical, B.Com, B.A. Political Science" wide />
          </div>
        </>
      )}

      {step === 1 && (
        <>
          <h3 className="step-title">Your exam journey</h3>
          <p className="step-sub">This is experience, not a gap — we'll reframe it as a strength.</p>
          <div className="grid-2">
            <Text label="Exam(s) prepared for" value={c.exams} onChange={set("exams")} placeholder="e.g. UPSC CSE, SSC CGL" />
            <Select label="Years preparing" value={c.years_preparing} onChange={set("years_preparing")} options={YEARS} />
            <Select label="Current situation" value={c.current_situation} onChange={set("current_situation")} options={SITUATION} />
          </div>
        </>
      )}

      {step === 2 && (
        <>
          <h3 className="step-title">Where you are right now</h3>
          <p className="step-sub">Be honest — this helps us address what's actually holding you back.</p>
          <div className="grid-2">
            <Select label="Biggest source of stress" value={c.main_stress} onChange={set("main_stress")} options={STRESS} />
            <Text label="Current worries" value={c.worries} onChange={set("worries")} placeholder="e.g. explaining the gap to recruiters" />
            <Area label="Describe your situation in your own words" value={c.situation_words} onChange={set("situation_words")} placeholder="Optional. Anything you'd want an advisor to understand about where you are and what you want." />
          </div>
        </>
      )}

      {step === 3 && (
        <>
          <h3 className="step-title">Direction & your report</h3>
          <p className="step-sub">What pulls your interest, and how you'd like the blueprint.</p>
          <div className="grid-2">
            <Text label="Areas that interest you" value={c.interests} onChange={set("interests")} placeholder="e.g. data, AI, policy, product, writing, operations" wide />
          </div>

          <div style={{ marginTop: 22 }}>
            <label className="field" style={{ marginBottom: 10, display: "block", color: "var(--text-muted)", fontSize: 12.5, fontWeight: 600, letterSpacing: "0.06em", textTransform: "uppercase" }}>
              Choose your report
            </label>
            <div className="choice-row">
              <div className={`choice ${tier === "sample" ? "on" : ""}`} onClick={() => setTier("sample")} role="button" tabIndex={0}>
                <div className="ct">Free sample</div>
                <div className="cs">A quick diagnosis and one recommended direction to get a feel for it.</div>
              </div>
              <div className={`choice ${tier === "mini" ? "on" : ""}`} onClick={() => setTier("mini")} role="button" tabIndex={0}>
                <div className="ct">Full blueprint · <span className="price">₹149</span></div>
                <div className="cs">Top 3 fitted paths, a 12-week roadmap, projects, and resume positioning.</div>
              </div>
            </div>
          </div>

          <div style={{ marginTop: 18 }}>
            <label className="field" style={{ marginBottom: 10, display: "block", color: "var(--text-muted)", fontSize: 12.5, fontWeight: 600, letterSpacing: "0.06em", textTransform: "uppercase" }}>
              Language
            </label>
            <div className="choice-row" style={{ gridTemplateColumns: "repeat(3, 1fr)" }}>
              {[["english", "English"], ["hinglish", "Hinglish"], ["hindi", "Hindi"]].map(([v, l]) => (
                <div key={v} className={`choice ${language === v ? "on" : ""}`} onClick={() => setLanguage(v)} role="button" tabIndex={0}>
                  <div className="ct">{l}</div>
                </div>
              ))}
            </div>
          </div>
        </>
      )}

      <div className="step-nav">
        <button
          type="button"
          className="btn btn-ghost"
          onClick={() => setStep((s) => Math.max(0, s - 1))}
          disabled={step === 0 || disabled}
          style={{ visibility: step === 0 ? "hidden" : "visible" }}
        >
          <ArrowLeft size={17} /> Back
        </button>

        {!last ? (
          <button type="button" className="btn btn-primary" onClick={() => setStep((s) => s + 1)}>
            Continue <ArrowRight size={17} />
          </button>
        ) : (
          <button type="button" className="btn btn-primary" onClick={() => onGenerate(c, tier, language)} disabled={disabled}>
            <Sparkles size={17} /> Generate my blueprint
          </button>
        )}
      </div>
    </div>
  );
}
