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
