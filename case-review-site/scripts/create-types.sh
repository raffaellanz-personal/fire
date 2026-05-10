#!/bin/bash

set -e

TARGET="/Users/raffaelladelprete/Library/Mobile Documents/com~apple~CloudDocs/Documents/Personale/Houses/23 Mays Street/02 Fire/Git/case-review-site/src/types"

mkdir -p "$TARGET"

echo "Creating TypeScript models in:"
echo "$TARGET"

cat > "$TARGET/Email.ts" <<'EOF'
export interface EmailAttachment {
id: string;
title: string;
file: string;
type?: string;
}

export interface Email {
id: string;
threadId?: string;

subject: string;

from: string;
to: string[];

cc?: string[];
bcc?: string[];

date: string;

summary: string;
body: string;

rawFile?: string;

attachments?: EmailAttachment[];

relatedDocuments?: string[];
relatedIssues?: string[];
relatedLaws?: string[];
relatedTimelineEvents?: string[];

tags?: string[];

importance?: "low" | "medium" | "high" | "critical";

createdAt?: string;
updatedAt?: string;
}
EOF

cat > "$TARGET/Timeline.ts" <<'EOF'
export interface TimelineEvent {
id: string;

date: string;

title: string;

summary: string;

participants?: string[];

relatedEmails?: string[];
relatedDocuments?: string[];
relatedIssues?: string[];
relatedLaws?: string[];

strategicImportance?: "low" | "medium" | "high" | "critical";

notes?: string;
}
EOF

cat > "$TARGET/Issue.ts" <<'EOF'
export interface Issue {
id: string;

title: string;

category:
| "Safety"
| "Structural"
| "Electrical"
| "Insurance"
| "Legal"
| "Compliance"
| "Moisture"
| "Asbestos"
| "Communication"
| "Delay"
| "Other";

severity?: "low" | "medium" | "high" | "critical";

status?: "open" | "monitoring" | "resolved" | "disputed";

summary: string;

evidenceSummary?: string;

insurerPosition?: string;

strategicPosition?: string;

legalConcern?: string;

relatedEmails?: string[];
relatedDocuments?: string[];
relatedLaws?: string[];
relatedTimelineEvents?: string[];

createdAt?: string;
updatedAt?: string;
}
EOF

cat > "$TARGET/Document.ts" <<'EOF'
export interface Document {
id: string;

title: string;

file: string;

type?:
| "report"
| "policy"
| "photo"
| "invoice"
| "scope"
| "assessment"
| "legal"
| "email-attachment"
| "other";

source?: string;

date?: string;

summary?: string;

relatedEmails?: string[];
relatedIssues?: string[];
relatedLaws?: string[];
relatedTimelineEvents?: string[];

tags?: string[];

createdAt?: string;
updatedAt?: string;
}
EOF

cat > "$TARGET/Law.ts" <<'EOF'
export interface Law {
id: string;

title: string;

jurisdiction?: string;

reference?: string;

summary: string;

relevance?: string;

concern?: string;

relatedIssues?: string[];
relatedDocuments?: string[];
relatedEmails?: string[];
relatedTimelineEvents?: string[];

sourceDocument?: string;
}
EOF

cat > "$TARGET/Thread.ts" <<'EOF'
export interface Thread {
id: string;

title: string;

summary: string;

participants?: string[];

startDate?: string;
endDate?: string;

emailIds: string[];

relatedIssues?: string[];
relatedDocuments?: string[];
relatedLaws?: string[];
relatedTimelineEvents?: string[];

strategicNotes?: string;
}
EOF

echo ""
echo "Done."
echo ""

ls -1 "$TARGET"
