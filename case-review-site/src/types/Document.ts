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
