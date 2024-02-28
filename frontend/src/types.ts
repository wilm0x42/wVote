export type Entry = {
  uuid: string;
  entryName: string;
  entrantName: string;
  mp3Url: string;
  pdfUrl: string;
  mp3Format: "mp3" | "external" | null;
};

export type AdminEntry = Entry & {
  entryNotes: string | null;
  isValid: boolean;
};

export type ThisWeek = {
  entries: AdminEntry[];
  theme: string;
  date: string;
  votingOpen: boolean;
};

export type NextWeek = {
  entries: AdminEntry[];
  theme: string;
  date: string;
  submissionsOpen: boolean;
};

export type Vote = {
  userID: number;
  userName: string;
};

export type AdminData = {
  votes: Vote[];
  weeks: [ThisWeek, NextWeek];
};

export type EntryVotingData = {
  uuid: string;
  mp3Format: "external" | "mp3" | null;
  entrantName: string;
  entryName: string;
  isValid: boolean;
  pdfUrl: string | null;
  mp3Url: string | null;

  entryNotes?: string;
};

export type VotingData = {
  entries: EntryVotingData[];
  theme: string;
  date: string;
  submissionsOpen: boolean;
  votingOpen: boolean;
  voteParams: string[];
  helpTipDefs: Record<string, Record<number, string>>;
};

export type UserVote = {
  entryUUID: string;
  voteForName: string;
  voteParam: string;
  rating: number;
};
