import { useState } from "react";

import sampleEmail from "../data/sampleEmail";

import "../styles/mail.css";

export default function EmailDetailPage() {
  const [showFullEmail, setShowFullEmail] = useState(false);

  const [summary, setSummary] = useState(sampleEmail.summary);

  const [tags, setTags] = useState<string[]>(["Tower", "Claim C90306048"]);
  const [tagInput, setTagInput] = useState("");

  const [issues, setIssues] = useState<string[]>([]);
  const [issueInput, setIssueInput] = useState("");

  const [notes, setNotes] = useState("");

  function addTag() {
    const value = tagInput.trim();
    if (!value || tags.includes(value)) return;

    setTags([...tags, value]);
    setTagInput("");
  }

  function removeTag(tag: string) {
    setTags(tags.filter((item) => item !== tag));
  }

  function addIssue() {
    const value = issueInput.trim();
    if (!value) return;

    setIssues([...issues, value]);
    setIssueInput("");
  }

  function removeIssue(issue: string) {
    setIssues(issues.filter((item) => item !== issue));
  }

  return (
    <div className="emailDetail">
      <header className="emailHeader">
        <p className="eyebrow">Email Evidence Record</p>
        <h1>{sampleEmail.subject}</h1>
      </header>

      <section className="evidenceCard">
        <dl className="metaGrid">
          <div>
            <dt>Date</dt>
            <dd>{sampleEmail.date}</dd>
          </div>

          <div>
            <dt>From</dt>
            <dd>{sampleEmail.from}</dd>
          </div>

          <div>
            <dt>To</dt>
            <dd>{sampleEmail.to.join(", ")}</dd>
          </div>

          <div>
            <dt>Subject</dt>
            <dd>{sampleEmail.subject}</dd>
          </div>

          <div>
            <dt>In response to</dt>
            <dd className="muted">No linked prior email yet</dd>
          </div>

          <div>
            <dt>Thread</dt>
            <dd>
              <span className="threadBadge">Tower Claim Initiation</span>
            </dd>
          </div>
        </dl>
      </section>

      <section className="evidenceCard">
        <h2>Tags</h2>

        <div className="tagRow">
          {tags.map((tag) => (
            <button
              key={tag}
              className="tagPill"
              onClick={() => removeTag(tag)}
              title="Click to remove"
            >
              {tag} ×
            </button>
          ))}
        </div>

        <div className="inlineForm">
          <input
            value={tagInput}
            onChange={(event) => setTagInput(event.target.value)}
            placeholder="Add tag..."
          />

          <button className="secondaryButton" onClick={addTag}>
            Add tag
          </button>
        </div>
      </section>

      <section className="evidenceCard">
        <h2>Summary</h2>

        <textarea
          className="summaryEditor"
          value={summary}
          onChange={(event) => setSummary(event.target.value)}
        />
      </section>

      <section className="evidenceCard">
        <h2>Key Issues</h2>

        {issues.length === 0 ? (
          <p className="muted">No issues identified yet.</p>
        ) : (
          <ul className="issuesList">
            {issues.map((issue) => (
              <li key={issue}>
                <span>{issue}</span>

                <button onClick={() => removeIssue(issue)}>Remove</button>
              </li>
            ))}
          </ul>
        )}

        <div className="inlineForm">
          <input
            value={issueInput}
            onChange={(event) => setIssueInput(event.target.value)}
            placeholder="Add issue or concern..."
          />

          <button className="secondaryButton" onClick={addIssue}>
            Add issue
          </button>
        </div>
      </section>

      <section className="evidenceCard">
        <h2>Notes</h2>

        <textarea
          className="notesEditor"
          value={notes}
          onChange={(event) => setNotes(event.target.value)}
          placeholder="Add legal, factual, strategy, or follow-up notes about this email..."
        />
      </section>

      <section className="evidenceCard">
        <h2>Evidence Links</h2>

        <div className="sourceLinks">
          <a
            href={sampleEmail.rawFile}
            target="_blank"
            rel="noreferrer"
            className="inlineLink"
          >
            Open original .emlx file
          </a>

          <button
            className="primaryButton"
            onClick={() => setShowFullEmail(!showFullEmail)}
          >
            {showFullEmail ? "Hide full email" : "Show full email"}
          </button>
        </div>
      </section>

      {showFullEmail && (
        <section className="evidenceCard">
          <h2>Full Email</h2>

          <div className="emailBody">
            <pre>{sampleEmail.body}</pre>
          </div>
        </section>
      )}
    </div>
  );
}
