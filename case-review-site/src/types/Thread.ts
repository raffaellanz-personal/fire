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
