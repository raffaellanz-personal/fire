# NEXT Session.md

## Current Project Status

IMPORTANT:

The active project repository is located locally in Git at:

```text
/Users/raffaelladelprete/Library/Mobile Documents/com~apple~CloudDocs/Documents/Personale/Houses/23 Mays Street/02 Fire/Git/case-review-site
```

This is the main working repository.

The intention is:

- local development first
- Git versioning
- later deployment to AWS
- likely static frontend hosted via S3 + CloudFront
- eventual backend via Lambda + DynamoDB

All future work should assume this repository structure and location.


We have started building a React + Vite + TypeScript evidence review platform for the 23 Mays Street fire claim.

The architecture is now moving from a static mock-up toward a real evidence management system.

---

# Current Application Structure

## Frontend Stack

- React
- Vite
- TypeScript
- React Router
- CSS modular structure

---

# Current Folder Structure

```text
case-review-site/
├── public/
│   └── evidence/
│       ├── emails/
│       │   ├── raw/
│       │   ├── rendered/
│       │   └── threads/
│       ├── documents/
│       ├── images/
│       ├── audio-recordings/
│       ├── videos/
│       ├── metadata/
│       └── data/
│
├── src/
│   ├── components/
│   ├── pages/
│   ├── data/
│   ├── styles/
│   └── types/
```

---

# Styling Architecture

## Global Variables

We created:

```text
src/styles/variables.css
```

Using CSS variables such as:

```css
--color-primary
--color-primary-hover
--color-primary-soft
--color-primary-border
```

Primary accent colour:

```css
rgb(56, 197, 240)
```

---

# Current Pages

## Working

- DashboardPage
- EmailsPage
- EmailDetailPage
- TimelinePage
- Sidebar navigation

## In Progress

- EventDetailPage
- DocumentsPage
- IssuesPage
- LawsPage
- ThreadsPage
- StrategyPage

---

# Email System Status

## First Email Loaded

File:

```text
2025_05_18_22_12_28__claims@tower.co.nz__to__raffaellanz@icloud.com__0001__Your_Tower_Claim_C90306048.emlx
```

Stored in:

```text
public/evidence/emails/raw/
```

---

# Email Detail Page Features

Current EmailDetailPage supports:

- metadata section
- summary editing
- tags
- issues
- notes
- link to original .emlx
- show/hide full email
- evidence-card layout
- editable UI state

The page is now styled more like:

- legal review software
- evidence management systems
- Notion / Linear style interface

instead of a centered email reader.

---

# Timeline System Status

Timeline currently supports:

- predefined events
- add event form
- date/time/title/description
- optional linked document
- links to emails
- editable timeline events
- delete timeline events

Initial timeline entries:

1. Fire starts at property
2. Tower first contact email

---

# CRITICAL Architectural Realisation

The major issue discovered:

Manually added timeline events only existed in component state.

Result:

- EventDetailPage could not load them
- event pages were not persistent
- links broke after refresh

---

# New Direction Agreed

We decided to:

## Use localStorage as temporary persistence layer

Instead of JSON-only.

Reason:

- allows dynamic editing
- allows event pages to work
- closer to eventual database architecture

---

# Planned Storage Architecture

## Phase 1 (current)

```text
React State
+ localStorage
```

## Phase 2

```text
API Layer
```

## Phase 3

```text
AWS Lambda
→ DynamoDB
```

IMPORTANT:

Do NOT connect React frontend directly to DynamoDB.

Correct architecture:

```text
Frontend
→ API Gateway / Lambda
→ DynamoDB
```

---

# Timeline Persistence Work

Need to complete:

```text
src/data/timelineStore.ts
```

Functions:

```ts
getTimelineEvents()
saveTimelineEvents()
```

TimelinePage should:

- load from localStorage
- save edits to localStorage
- save new events
- save deletions

EventDetailPage should:

- read same localStorage dataset
- load event dynamically

This is the NEXT CRITICAL TASK.

---

# Immediate Next Tasks

## Priority 1

Finish persistent timeline architecture:

- timelineStore.ts
- EventDetailPage
- routing
- localStorage integration

---

## Priority 2

Convert EmailDetailPage to dynamic routing:

Instead of:

```ts
sampleEmail
```

Use:

```ts
/email/:id
```

and shared email data source.

---

## Priority 3

Build email parser pipeline:

Goal:

Parse `.emlx` automatically into structured records.

Likely libraries:

```bash
mailparser
```

Need:

- subject
- sender
- recipients
- body
- attachments
- message-id
- in-reply-to
- thread references

---

## Priority 4

Threading system

Need:

- thread pages
- email chains
- chronology
- related issues
- linked documents

---

## Priority 5

Issue extraction system

Need:

- issue register
- severity
- insurer position
- strategic position
- legal concern mapping
- evidence links

---

# Longer-Term Architecture

## Evidence Types

The system should eventually support:

- emails
- documents
- photos
- videos
- audio recordings
- timelines
- issues
- legal references
- council references
- insurance policy clauses
- expert reports

---

# Important UX Direction

The UI direction chosen:

NOT:

- marketing site
- centered content
- pretty email reader

YES:

- evidence review system
- legal review tool
- insurer dispute preparation platform
- chronology-first navigation
- dense scan-friendly information

Inspired by:

- Notion
- Linear
- discovery software
- litigation evidence review tools
- Jira / Confluence style layouts

---

# Important Future Features

Future features discussed:

- automatic issue extraction
- linked evidence graph
- legal concern mapping
- insurer tactic tracking
- chronology intelligence
- PDF rendering
- attachment previews
- document OCR
- AWS deployment
- S3 storage
- DynamoDB backend
- authentication/password protection
- export bundles for lawyers
- printable legal briefs
- case summary generator

---

# Important Technical Notes

Current dev server:

```text
http://localhost:5180
```

---

# Current Known Gaps

## Missing

- persistence for emails
- dynamic email loading
- document detail pages
- issue pages
- law pages
- event detail persistence
- parser pipeline
- backend

---

# Recommended Next Session Start

Start with:

1. Create `timelineStore.ts`
2. Finish EventDetailPage
3. Add localStorage persistence
4. Verify event pages survive refresh
5. Then move to dynamic email routing
6. Then start `.emlx` parser

This is the current highest-leverage path.

