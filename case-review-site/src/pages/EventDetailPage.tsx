import { Link, useParams } from "react-router-dom";
import sampleTimeline from "../data/sampleTimeline";
import "../styles/timeline.css";

export default function EventDetailPage() {
  const { id } = useParams();

  const event = sampleTimeline.find((item) => item.id === id);

  if (!event) {
    return (
      <div>
        <h1>Event not found</h1>
        <Link to="/timeline">Back to timeline</Link>
      </div>
    );
  }

  return (
    <div className="timelinePage">
      <header className="emailHeader">
        <p className="eyebrow">Timeline Event</p>
        <h1>{event.title}</h1>
      </header>

      <section className="evidenceCard">
        <dl className="metaGrid">
          <div>
            <dt>Date</dt>
            <dd>{event.date}</dd>
          </div>

          <div>
            <dt>Time</dt>
            <dd>{event.time || "No time recorded"}</dd>
          </div>

          <div>
            <dt>Event ID</dt>
            <dd>{event.id}</dd>
          </div>
        </dl>
      </section>

      <section className="evidenceCard">
        <h2>Summary</h2>
        <p>{event.description}</p>
      </section>

      <section className="evidenceCard">
        <h2>Linked Evidence</h2>

        {event.linkedEmailId && (
          <p>
            <Link className="inlineLink" to={`/emails/${event.linkedEmailId}`}>
              Open linked email
            </Link>
          </p>
        )}

        {event.linkedDocument && (
          <p>
            <a
              className="inlineLink"
              href={event.linkedDocument}
              target="_blank"
              rel="noreferrer"
            >
              Open linked document
            </a>
          </p>
        )}

        {!event.linkedEmailId && !event.linkedDocument && (
          <p className="muted">No linked evidence yet.</p>
        )}
      </section>

      <section className="evidenceCard">
        <h2>Notes</h2>
        <p className="muted">No notes added yet.</p>
      </section>
    </div>
  );
}
