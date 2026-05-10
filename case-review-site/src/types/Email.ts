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
