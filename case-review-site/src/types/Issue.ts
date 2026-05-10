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
