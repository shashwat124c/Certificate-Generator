import { useEffect, useMemo, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "";
const TERMINAL_STATES = new Set(["completed", "partial", "failed"]);

function parseRecipients(value) {
  return value
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line, index) => {
      const separator = line.lastIndexOf(",");
      if (separator < 1) {
        return { line: index + 1, name: line, email: "", invalid: true };
      }
      return {
        line: index + 1,
        name: line.slice(0, separator).trim(),
        email: line.slice(separator + 1).trim(),
        invalid: false,
      };
    });
}

function formatStatus(status) {
  return (status || "queued").replaceAll("_", " ");
}

function getLocalDate() {
  const today = new Date();
  today.setMinutes(today.getMinutes() - today.getTimezoneOffset());
  return today.toISOString().slice(0, 10);
}

async function requestJson(path, options) {
  const response = await fetch(`${API_BASE}${path}`, options);
  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json")
    ? await response.json()
    : null;
  if (!response.ok) {
    const message = payload?.details?.join(" ") || payload?.error || "Request failed.";
    throw new Error(message);
  }
  return payload;
}

function App() {
  const [certificate, setCertificate] = useState({
    title: "Certificate of Completion",
    course: "",
    issued_on: getLocalDate(),
    issuer: "",
  });
  const [recipientText, setRecipientText] = useState("");
  const [jobId, setJobId] = useState(null);
  const [job, setJob] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [pollError, setPollError] = useState("");

  const recipients = useMemo(() => parseRecipients(recipientText), [recipientText]);
  const isFinished = TERMINAL_STATES.has(job?.status);

  useEffect(() => {
    if (!jobId || isFinished) return undefined;

    let cancelled = false;
    let timer;
    const poll = async () => {
      try {
        const latest = await requestJson(`/api/v1/jobs/${jobId}`);
        if (cancelled) return;
        setJob(latest);
        setPollError("");
        if (!TERMINAL_STATES.has(latest.status)) {
          timer = window.setTimeout(poll, 1100);
        }
      } catch (pollFailure) {
        if (cancelled) return;
        setPollError(pollFailure.message);
        timer = window.setTimeout(poll, 2200);
      }
    };

    poll();
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [jobId, isFinished]);

  function updateCertificate(event) {
    const { name, value } = event.target;
    setCertificate((current) => ({ ...current, [name]: value }));
  }

  async function submitJob(event) {
    event.preventDefault();
    setError("");
    setPollError("");
    setJob(null);
    setJobId(null);

    const validRecipients = recipients.filter(
      (recipient) => !recipient.invalid && recipient.name && recipient.email,
    );
    if (validRecipients.length !== recipients.length) {
      setError("Use one recipient per line in the format: Full name, email@example.com");
      return;
    }

    setSubmitting(true);
    try {
      const created = await requestJson("/api/v1/jobs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          certificate,
          recipients: validRecipients.map(({ name, email }) => ({ name, email })),
        }),
      });
      setJob(created);
      setJobId(created.job_id);
    } catch (submissionError) {
      setError(submissionError.message);
    } finally {
      setSubmitting(false);
    }
  }

  function fillSample() {
    setCertificate((current) => ({
      ...current,
      course: "Flask Backend Development",
      issuer: "CertGen Academy",
    }));
    setRecipientText(
      "Ada Lovelace, ada@example.com\nGrace Hopper, grace@example.com",
    );
    setError("");
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="#top" aria-label="CertGen home">
          <span className="brand-mark" aria-hidden="true">C</span>
          <span>certgen</span>
        </a>
        <span className="topbar-note"><span className="live-dot" /> Bulk certificate studio</span>
      </header>

      <main id="top" className="layout">
        <section className="intro">
          <p className="eyebrow">CERTIFICATES, WITHOUT THE REPETITION</p>
          <h1>Make every<br /><em>achievement</em> official.</h1>
          <p className="intro-copy">
            Create a batch once. CertGen prepares a personal PDF for each recipient
            and keeps the results together in one trackable job.
          </p>
          <div className="process-note">
            <span className="process-number">01</span>
            <span>One request, every recipient</span>
            <span className="process-rule" />
            <span className="process-number">02</span>
            <span>PDFs, ready to download</span>
          </div>
        </section>

        <section className="workspace" aria-label="Create a certificate batch">
          <form className="form-card" onSubmit={submitJob}>
            <div className="card-heading">
              <div>
                <p className="eyebrow">NEW GENERATION JOB</p>
                <h2>Set up your certificates</h2>
              </div>
              <span className="fixed-template"><span className="template-icon">✳</span> Fixed template</span>
            </div>

            <div className="section-label"><span>1</span> Certificate details</div>
            <div className="field-grid">
              <label className="field field-wide">
                <span>Certificate title</span>
                <input name="title" value={certificate.title} onChange={updateCertificate} required maxLength={120} />
              </label>
              <label className="field field-wide">
                <span>Course or event</span>
                <input name="course" value={certificate.course} onChange={updateCertificate} placeholder="e.g. Product Design Foundations" required maxLength={180} />
              </label>
              <label className="field">
                <span>Issue date</span>
                <input type="date" name="issued_on" value={certificate.issued_on} onChange={updateCertificate} required />
              </label>
              <label className="field">
                <span>Issued by <small>Optional</small></span>
                <input name="issuer" value={certificate.issuer} onChange={updateCertificate} placeholder="Organization name" maxLength={120} />
              </label>
            </div>

            <div className="recipient-heading">
              <div className="section-label"><span>2</span> Recipients</div>
              <button className="text-button" type="button" onClick={fillSample}>Use sample data</button>
            </div>
            <label className="field recipient-field">
              <span className="sr-only">Recipient names and email addresses</span>
              <textarea
                value={recipientText}
                onChange={(event) => setRecipientText(event.target.value)}
                placeholder={"Ada Lovelace, ada@example.com\nGrace Hopper, grace@example.com"}
                rows={5}
                required
              />
            </label>
            <div className="field-hint">
              <span>One person per line, separated by a comma</span>
              <span className="recipient-count"><strong>{recipients.length}</strong> {recipients.length === 1 ? "recipient" : "recipients"}</span>
            </div>

            {error && <div className="alert error-alert" role="alert">{error}</div>}

            <div className="form-footer">
              <span className="privacy-note"><span className="lock-icon">⌑</span> One individual PDF for each recipient</span>
              <button className="submit-button" type="submit" disabled={submitting}>
                {submitting ? "Starting job…" : "Generate certificates"}
                {!submitting && <span aria-hidden="true">↗</span>}
              </button>
            </div>
          </form>

          {job && (
            <section className="job-card" aria-live="polite">
              <div className="job-topline">
                <div>
                  <p className="eyebrow">GENERATION JOB</p>
                  <h2>{isFinished ? "Your batch is ready" : "Preparing your batch"}</h2>
                </div>
                <span className={`status-pill status-${job.status}`}>{formatStatus(job.status)}</span>
              </div>
              <div className="job-meta">
                <span>Job ID</span><code>{job.job_id}</code>
              </div>
              <div className="progress-label"><span>Progress</span><strong>{job.progress_percent ?? 0}%</strong></div>
              <div className="progress-track" role="progressbar" aria-valuenow={job.progress_percent ?? 0} aria-valuemin="0" aria-valuemax="100">
                <span style={{ width: `${job.progress_percent ?? 0}%` }} />
              </div>
              <div className="stats-row">
                <div><strong>{job.successful ?? 0}</strong><span>Ready</span></div>
                <div><strong>{job.processed ?? 0}<small> / {job.total}</small></strong><span>Processed</span></div>
                <div><strong>{job.failed ?? 0}</strong><span>Failed</span></div>
              </div>
              {pollError && <div className="alert poll-alert" role="status">Can’t refresh status right now. Retrying…</div>}
              {job.recipients?.length > 0 && (
                <div className="recipient-results">
                  <div className="results-heading"><span>Recipient</span><span>Result</span></div>
                  {job.recipients.map((recipient) => (
                    <div className="result-row" key={recipient.recipient_id}>
                      <div className="recipient-identity">
                        <span className={`result-avatar ${recipient.status === "failed" ? "avatar-failed" : ""}`}>
                          {recipient.name.slice(0, 1).toUpperCase()}
                        </span>
                        <span><strong>{recipient.name}</strong><small>{recipient.email}</small></span>
                      </div>
                      <div className="result-action">
                        {recipient.status === "completed" ? (
                          <a className="download-link" href={`${API_BASE}${recipient.download_url}`} download>
                            Download <span aria-hidden="true">↓</span>
                          </a>
                        ) : (
                          <span className={`recipient-status recipient-${recipient.status}`}>
                            {recipient.status === "failed" ? "Failed" : formatStatus(recipient.status)}
                          </span>
                        )}
                      </div>
                      {recipient.error && <p className="recipient-error">{recipient.error}</p>}
                    </div>
                  ))}
                </div>
              )}
              {!isFinished && <p className="polling-note"><span className="spinner" /> This page updates as certificates are generated.</p>}
            </section>
          )}
        </section>
      </main>

      <footer className="footer"><span>CertGen</span><span>Every achievement deserves to be recognized.</span></footer>
    </div>
  );
}

export default App;
