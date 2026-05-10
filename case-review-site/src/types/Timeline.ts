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
