import { useState } from "react";
import { Link } from "react-router-dom";

import sampleTimeline from "../data/sampleTimeline";

import "../styles/mail.css";
import "../styles/timeline.css";

export default function TimelinePage() {
  const [events, setEvents] = useState(sampleTimeline);

  const [date, setDate] = useState("");
  const [time, setTime] = useState("");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [documentLink, setDocumentLink] = useState("");

  function addEvent() {
    if (!date || !title.trim()) return;

    const newEvent = {
      id: crypto.randomUUID(),
      date,
      time,
      title,
      description,
      linkedEmailId: null,
      linkedDocument: documentLink || null,
    };

    setEvents([newEvent, ...events]);

    setDate("");
    setTime("");
    setTitle("");
    setDescription("");
    setDocumentLink("");
  }

  return (
    <div className="timelinePage">
      <header className="emailHeader">
        <p className="eyebrow">Claim Chronology</p>
        <h1>Timeline</h1>
      </header>

      <section className="evidenceCard">
        <h2>Add Timeline Event</h2>

        <div className="timelineForm">
          <input
            type="date"
            value={date}
            onChange={(event) => setDate(event.target.value)}
          />

          <input
            type="time"
            value={time}
            onChange={(event) => setTime(event.target.value)}
          />

          <input
            type="text"
            placeholder="Short event title"
            value={title}
            onChange={(event) => setTitle(event.target.value)}
          />

          <textarea
            placeholder="Event description"
            value={description}
            onChange={(event) => setDescription(event.target.value)}
          />

          <input
            type="text"
            placeholder="Optional document link, e.g. /evidence/documents/fire-report.pdf"
            value={documentLink}
            onChange={(event) => setDocumentLink(event.target.value)}
          />

          <button className="primaryButton" onClick={addEvent}>
            Add Event
          </button>
        </div>
      </section>

      <div className="timelineList">
        {events.map((event) => (
          <section className="timelineEventCard" key={event.id}>
            <div className="timelineLeft">
              <p className="timelineDate">{event.date}</p>
              <p className="timelineTime">{event.time || "No time"}</p>
            </div>

            <div className="timelineRight">
              <h2>{event.title}</h2>
              <p>{event.description}</p>

              <div className="timelineLinks">
                <Link className="inlineLink" to={`/timeline/${event.id}`}>
                  Open event page
                </Link>

                {event.linkedEmailId && (
                  <Link
                    className="inlineLink"
                    to={`/emails/${event.linkedEmailId}`}
                  >
                    Open linked email
                  </Link>
                )}

                {event.linkedDocument && (
                  <a
                    className="inlineLink"
                    href={event.linkedDocument}
                    target="_blank"
                    rel="noreferrer"
                  >
                    Open linked document
                  </a>
                )}
              </div>
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}
