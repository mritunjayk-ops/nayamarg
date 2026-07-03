"use client";

import {
  ArrowUpRight,
  BadgeCheck,
  BriefcaseBusiness,
  CheckCircle2,
  ClipboardList,
  Download,
  FileText,
  Gauge,
  GraduationCap,
  Loader2,
  Search,
  Sparkles,
  Target,
  WandSparkles,
} from "lucide-react";
import { useState } from "react";

const API_BASE_URL = (process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000").replace(/\/$/, "");

const initialCandidate = {
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
  explored_alternative: "",
  alternative_path: "",
  value_rating: "",
  blueprint_interest: "",
  price_preference: "",
  trust_factor: "",
  free_blueprint: "",
  interview_interest: "",
};

export default function Home() {
  const [candidate, setCandidate] = useState(initialCandidate);
  const [tier, setTier] = useState("mini");
  const [language, setLanguage] = useState("english");
  const [blueprint, setBlueprint] = useState({ loading: false, message: "Ready to generate a candidate-specific blueprint.", url: "" });
  const [jobRole, setJobRole] = useState("");
  const [jobLocation, setJobLocation] = useState("");
  const [jobs, setJobs] = useState([]);
  const [scores, setScores] = useState([]);
  const [jobState, setJobState] = useState({ loading: false, message: "Search jobs after entering the candidate profile." });
  const [resumeRole, setResumeRole] = useState("");
  const [resumeState, setResumeState] = useState({ loading: false, message: "Generate an ATS resume from the profile.", url: "", preview: null });

  function updateCandidate(field, value) {
    setCandidate((current) => ({ ...current, [field]: value }));
  }

  async function generateBlueprint() {
    setBlueprint({ loading: true, message: "Running transition agents and exporting PDF...", url: "" });
    const response = await fetch(`${API_BASE_URL}/api/intake/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ candidate, tier, language }),
    });
    if (!response.ok) {
      setBlueprint({ loading: false, message: "Blueprint generation failed. Check backend logs.", url: "" });
      return;
    }
    const result = await response.json();
    setBlueprint({ loading: false, message: result.summary, url: `${API_BASE_URL}${result.pdf_url}` });
  }

  async function searchJobs() {
    setJobState({ loading: true, message: "Searching and scoring job matches..." });
    setJobs([]);
    setScores([]);
    const searchResponse = await fetch(`${API_BASE_URL}/api/jobs/search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ candidate, role: jobRole, location: jobLocation, remote_only: true, limit: 15 }),
    });
    if (!searchResponse.ok) {
      setJobState({ loading: false, message: "Job search failed. Check backend logs." });
      return;
    }
    const searchResult = await searchResponse.json();
    const scoreResponse = await fetch(`${API_BASE_URL}/api/jobs/score`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ candidate, jobs: searchResult.jobs }),
    });
    const scoreResult = scoreResponse.ok ? await scoreResponse.json() : { results: [] };
    setJobs(searchResult.jobs);
    setScores(scoreResult.results);
    setJobState({ loading: false, message: `Found ${searchResult.jobs.length} job leads for "${searchResult.query}".` });
  }

  async function generateResume(job = null) {
    const targetRole = job?.title || resumeRole || "Data Analyst";
    setResumeState({ loading: true, message: `Generating resume for ${targetRole}...`, url: "", preview: null });
    const response = await fetch(`${API_BASE_URL}/api/resumes/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ candidate, target_role: targetRole, job }),
    });
    if (!response.ok) {
      setResumeState({ loading: false, message: "Resume generation failed. Check backend logs.", url: "", preview: null });
      return;
    }
    const result = await response.json();
    setResumeState({
      loading: false,
      message: `Generated resume for ${targetRole}.`,
      url: `${API_BASE_URL}${result.pdf_url}`,
      preview: result.resume,
    });
  }

  const scoresById = new Map(scores.map((score) => [score.job_id, score]));

  return (
    <main className="app-shell">
      <aside className="side-rail">
        <div className="brand-lockup">
          <div className="brand-mark">
            <Sparkles size={18} />
          </div>
          <div>
            <p className="eyebrow">NayaMarg</p>
            <h1>Transition OS</h1>
          </div>
        </div>
        <nav className="nav-stack" aria-label="Workflow">
          <a href="#intake"><ClipboardList size={16} /> Intake</a>
          <a href="#blueprint"><Target size={16} /> Blueprint</a>
          <a href="#jobs"><BriefcaseBusiness size={16} /> Jobs</a>
          <a href="#resume"><FileText size={16} /> Resume</a>
        </nav>
      </aside>

      <section className="main-stage">
        <header className="hero-panel">
          <div>
            <p className="eyebrow">AI guidance for serious aspirants</p>
            <h2>From exam preparation to a credible career transition.</h2>
            <p>
              Generate a transition blueprint, discover realistic job leads, score fit, and create a role-specific resume from one candidate profile.
            </p>
          </div>
          <div className="hero-metrics" aria-label="Product modules">
            <Metric icon={<Gauge size={18} />} label="Fit scoring" value="100 pt" />
            <Metric icon={<GraduationCap size={18} />} label="Roadmap" value="12 weeks" />
            <Metric icon={<BadgeCheck size={18} />} label="Outputs" value="PDF" />
          </div>
        </header>

        <section className="content-grid">
          <section id="intake" className="panel intake-panel">
            <PanelTitle icon={<ClipboardList size={18} />} title="Candidate Intake" subtitle="Tell us where you are now so the agent can map your next move." />
            <div className="form-grid">
              <Field label="Age group" value={candidate.age_group} onChange={(value) => updateCandidate("age_group", value)} type="select" options={["Under 21", "21-25", "26-30", "31-35", "Above 35"]} />
              <Field label="Qualification" value={candidate.qualification} onChange={(value) => updateCandidate("qualification", value)} type="select" options={["Bachelor's Degree", "Master's Degree", "Diploma", "PhD", "Other"]} />
              <Field label="Degree / background" value={candidate.background} onChange={(value) => updateCandidate("background", value)} placeholder="B.Tech CS, BA Political Science..." />
              <Field label="Exams prepared" value={candidate.exams} onChange={(value) => updateCandidate("exams", value)} placeholder="UPSC CSE; State PSC; SSC" />
              <Field label="Preparation years" value={candidate.years_preparing} onChange={(value) => updateCandidate("years_preparing", value)} type="select" options={["Less than 1 year", "1-2 years", "3-4 years", "5-6 years", "More than 6 years"]} />
              <Field label="Current situation" value={candidate.current_situation} onChange={(value) => updateCandidate("current_situation", value)} type="select" options={["Not sure what to do next", "Looking for a job", "Preparing full-time", "Working but want to switch", "Planning higher education"]} />
              <Field label="Main stress" value={candidate.main_stress} onChange={(value) => updateCandidate("main_stress", value)} type="select" options={["My resume has large gap years", "I don't know which career fits me", "I don't know what to learn next", "I feel too old to start over", "Financial pressure", "Family pressure", "Fear of failure"]} />
              <Field label="Interesting areas" value={candidate.interests} onChange={(value) => updateCandidate("interests", value)} placeholder="AI / ML; Data Analytics; Product" />
              <Field className="wide" label="Worries" value={candidate.worries} onChange={(value) => updateCandidate("worries", value)} placeholder="resume gap; family pressure; confidence; financial urgency" />
              <Field className="wide" label="Situation in their own words" value={candidate.situation_words} onChange={(value) => updateCandidate("situation_words", value)} textarea placeholder="Paste the candidate story here." />
            </div>
          </section>

          <section id="blueprint" className="panel action-panel">
            <PanelTitle icon={<WandSparkles size={18} />} title="Blueprint Agent" subtitle="Generate the candidate-specific transition PDF." />
            <div className="control-row">
              <Select label="Tier" value={tier} onChange={setTier} options={[["sample", "Free sample report"], ["mini", "INR 99 mini blueprint"]]} />
              <Select label="Language" value={language} onChange={setLanguage} options={[["english", "English"], ["hinglish", "Hinglish"], ["hindi", "Hindi"]]} />
              <button className="primary-button" onClick={generateBlueprint} type="button" disabled={blueprint.loading}>
                {blueprint.loading ? <Loader2 className="spin" size={16} /> : <Download size={16} />}
                Generate PDF
              </button>
            </div>
            <ResultLine message={blueprint.message} url={blueprint.url} label="Open blueprint PDF" />
          </section>

          <section id="jobs" className="panel action-panel">
            <PanelTitle icon={<BriefcaseBusiness size={18} />} title="Job Search Agent" subtitle="Find and score remote/startup job leads." />
            <div className="control-row">
              <Field label="Target role" value={jobRole} onChange={setJobRole} placeholder="AI data analyst" compact />
              <Field label="Location" value={jobLocation} onChange={setJobLocation} placeholder="Remote / India" compact />
              <button className="primary-button" onClick={searchJobs} type="button" disabled={jobState.loading}>
                {jobState.loading ? <Loader2 className="spin" size={16} /> : <Search size={16} />}
                Search
              </button>
            </div>
            <p className="muted">{jobState.message}</p>
            <div className="job-list">
              {jobs.map((job) => {
                const score = scoresById.get(job.id);
                return <JobCard key={job.id} job={job} score={score} onResume={() => generateResume(job)} />;
              })}
            </div>
          </section>

          <section id="resume" className="panel action-panel">
            <PanelTitle icon={<FileText size={18} />} title="Resume Agent" subtitle="Generate an ATS resume from the profile or selected job." />
            <div className="control-row">
              <Field label="Resume role" value={resumeRole} onChange={setResumeRole} placeholder="Data Analyst" compact />
              <button className="primary-button" onClick={() => generateResume()} type="button" disabled={resumeState.loading}>
                {resumeState.loading ? <Loader2 className="spin" size={16} /> : <FileText size={16} />}
                Generate Resume
              </button>
            </div>
            <ResultLine message={resumeState.message} url={resumeState.url} label="Open resume PDF" />
            {resumeState.preview && <pre className="resume-preview">{JSON.stringify(resumeState.preview, null, 2)}</pre>}
          </section>
        </section>
      </section>
    </main>
  );
}

function Metric({ icon, label, value }) {
  return (
    <div className="metric">
      {icon}
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function PanelTitle({ icon, title, subtitle }) {
  return (
    <div className="panel-title">
      <div className="panel-icon">{icon}</div>
      <div>
        <h3>{title}</h3>
        <p>{subtitle}</p>
      </div>
    </div>
  );
}

function Field({ label, value, onChange, placeholder, type, options = [], textarea = false, className = "", compact = false }) {
  return (
    <label className={`field ${className} ${compact ? "compact" : ""}`}>
      <span>{label}</span>
      {textarea ? (
        <textarea value={value} onChange={(event) => onChange(event.target.value)} placeholder={placeholder} rows={5} />
      ) : type === "select" ? (
        <select value={value} onChange={(event) => onChange(event.target.value)}>
          <option value="">{`Select ${label.toLowerCase()}`}</option>
          {options.map((option) => <option key={option}>{option}</option>)}
        </select>
      ) : (
        <input value={value} onChange={(event) => onChange(event.target.value)} placeholder={placeholder} />
      )}
    </label>
  );
}

function Select({ label, value, onChange, options }) {
  return (
    <label className="field compact">
      <span>{label}</span>
      <select value={value} onChange={(event) => onChange(event.target.value)}>
        {options.map(([optionValue, optionLabel]) => <option key={optionValue} value={optionValue}>{optionLabel}</option>)}
      </select>
    </label>
  );
}

function ResultLine({ message, url, label }) {
  return (
    <div className="result-line">
      <CheckCircle2 size={16} />
      <span>{message}</span>
      {url && <a href={url} target="_blank" rel="noreferrer">{label} <ArrowUpRight size={14} /></a>}
    </div>
  );
}

function JobCard({ job, score, onResume }) {
  return (
    <article className="job-card">
      <div className="job-header">
        <div>
          <p className="eyebrow">{job.source}</p>
          <h4>{job.title}</h4>
          <span>{job.company || "Company varies"} · {job.location || "Remote"}</span>
        </div>
        <strong>{score ? `${score.fit_score}/100` : "New"}</strong>
      </div>
      <p>{(job.description || "Open this source to review current roles.").slice(0, 260)}</p>
      {score && <p className="strategy">{score.recommendation}: {score.application_strategy}</p>}
      <div className="job-actions">
        <a href={job.apply_url} target="_blank" rel="noreferrer">Open role <ArrowUpRight size={14} /></a>
        <button type="button" onClick={onResume}>Tailor resume</button>
      </div>
    </article>
  );
}
