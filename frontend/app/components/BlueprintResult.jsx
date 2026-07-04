"use client";

import { Download, RotateCcw, FileText } from "lucide-react";

const SNAPSHOT_LABELS = {
  age_group: "Age",
  qualification: "Qualification",
  background: "Background",
  exam_history: "Exam history",
  current_situation: "Situation",
  main_stress: "Main stress",
  interests: "Interests",
};

export default function BlueprintResult({ result, pdfUrl, onRestart }) {
  const bp = result.blueprint || {};
  const snapshot = bp.snapshot || {};
  const paths = Array.isArray(bp.paths) ? bp.paths : [];
  const learning = bp.learning && typeof bp.learning === "object" ? bp.learning : {};
  const courses = Array.isArray(learning.courses) ? learning.courses : [];
  const modules = Array.isArray(learning.modules) ? learning.modules : [];
  const projects = Array.isArray(bp.projects) ? bp.projects : [];
  const strengths = Array.isArray(bp.strengths) ? bp.strengths : [];
  const bullets = Array.isArray(bp.resume_bullets) ? bp.resume_bullets : [];
  const signals = Array.isArray(bp.market_signals) ? bp.market_signals : [];
  const snapshotEntries = Object.entries(snapshot).filter(([, v]) => v);

  return (
    <div className="panel intake">
      <div className="result-head">
        <span className="tier-badge">
          {result.tier === "mini" ? "Full blueprint" : "Free sample"}
        </span>
      </div>
      {result.summary && <p className="bp-summary">{result.summary}</p>}

      {snapshotEntries.length > 0 && (
        <section className="bp-block">
          <h3>Your snapshot</h3>
          <div className="snapshot">
            {snapshotEntries.map(([k, v]) => (
              <div className="cell" key={k}>
                <div className="k">{SNAPSHOT_LABELS[k] || k}</div>
                <div className="v">{v}</div>
              </div>
            ))}
          </div>
        </section>
      )}

      {bp.diagnosis && (
        <section className="bp-block">
          <h3>Where you stand</h3>
          <p className="prose">{bp.diagnosis}</p>
        </section>
      )}

      {strengths.length > 0 && (
        <section className="bp-block">
          <h3>Strengths you already have</h3>
          <div className="chips">
            {strengths.map((s, i) => (
              <span className="chip" key={i}>{s}</span>
            ))}
          </div>
        </section>
      )}

      {paths.length > 0 && (
        <section className="bp-block">
          <h3>Career paths that fit you</h3>
          <div className="paths">
            {paths.map((p, i) => (
              <article className="path" key={i}>
                <div className="score">
                  <div className="num">{p.score ?? "—"}</div>
                  <div className="of">/ 100 fit</div>
                </div>
                <div>
                  <div className="rank">Path {p.rank ?? i + 1}</div>
                  <h4>{p.title || "Career path"}</h4>
                  {p.why && <p className="why">{p.why}</p>}
                  {Array.isArray(p.proof_points) && p.proof_points.length > 0 && (
                    <ul className="proof">
                      {p.proof_points.map((pt, j) => (
                        <li key={j}>{pt}</li>
                      ))}
                    </ul>
                  )}
                </div>
              </article>
            ))}
          </div>
        </section>
      )}

      {modules.length > 0 && (
        <section className="bp-block">
          <h3>Your learning plan{learning.estimated_duration ? ` · about ${learning.estimated_duration}` : ""}</h3>
          <p className="prose" style={{ marginBottom: 18 }}>
            {learning.pace_assumption ? `${learning.pace_assumption}. ` : ""}
            Work through the topics at your own pace — check each one off as you master it. There's no fixed deadline.
          </p>

          {courses.length > 0 && (
            <div className="course-list">
              {courses.map((c, i) => (
                <a key={i} className="course" href={c.url || "#"} target="_blank" rel="noreferrer">
                  {c.name || "Course"}{c.provider ? ` · ${c.provider}` : ""}
                </a>
              ))}
            </div>
          )}

          <div className="modules">
            {modules.map((m, i) => (
              <div className="module" key={i}>
                <div className="module-title">{m.title || `Module ${i + 1}`}</div>
                <div className="topics-list">
                  {(Array.isArray(m.topics) ? m.topics : []).map((t, j) => (
                    <div className="topic" key={j}>
                      <span className="topic-check" aria-hidden="true" />
                      <div className="topic-body">
                        <div className="topic-head">
                          <span className="topic-name">{t.topic || "Topic"}</span>
                          {t.estimate && <span className="topic-est">{t.estimate}</span>}
                        </div>
                        {t.details && <div className="topic-details">{t.details}</div>}
                        {t.course && <div className="topic-course">from {t.course}</div>}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {projects.length > 0 && (
        <section className="bp-block">
          <h3>Projects to prove your skills</h3>
          <div className="projects">
            {projects.map((pr, i) => (
              <div className="project" key={i}>
                <h5>{pr.name || "Project"}</h5>
                {pr.description && <p>{pr.description}</p>}
                {Array.isArray(pr.skills) && pr.skills.length > 0 && (
                  <div className="chips">
                    {pr.skills.map((s, j) => (
                      <span className="chip" key={j}>{s}</span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {bullets.length > 0 && (
        <section className="bp-block">
          <h3>Resume positioning</h3>
          <ul className="proof">
            {bullets.map((b, i) => (
              <li key={i}>{b}</li>
            ))}
          </ul>
        </section>
      )}

      {signals.length > 0 && (
        <section className="bp-block">
          <h3>Market signals used</h3>
          <div className="signals">
            {signals.map((s, i) => (
              <div className="signal" key={i}>
                <div className="src">{s.source || "source"}</div>
                <div className="ttl">{s.title || ""}</div>
              </div>
            ))}
          </div>
        </section>
      )}

      <div className="result-actions">
        {result.pdf_url && (
          <a className="btn btn-primary" href={pdfUrl(result.pdf_url)} target="_blank" rel="noreferrer">
            <Download size={17} /> Download PDF
          </a>
        )}
        <button className="btn btn-ghost" type="button" onClick={onRestart}>
          <RotateCcw size={16} /> Start over
        </button>
      </div>

      <p className="disclaimer">
        <FileText size={13} style={{ verticalAlign: "-2px", marginRight: 6 }} />
        This is AI-assisted guidance to help you plan — please verify specifics before acting on them.
        NayaMarg does not guarantee any job or income outcome.
      </p>
    </div>
  );
}
