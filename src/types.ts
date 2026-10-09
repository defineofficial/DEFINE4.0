export type ResourceType = 'pyq' | 'notes' | 'video' | 'textbook' | 'repo' | 'pdf' | 'doc' | 'book';

export interface Resource {
  id: string;
  title: string;
  type: ResourceType;
  typeBadge: string;
  subject: string;
  subjectName: string;
  topic: string;
  author: string;
  meta: string;
  progress: number;
  isPending: boolean;
  saved: boolean;
  imageUrl?: string;
  colorClass: string;
  spineGradient?: string;
  icon: string;
  highlights?: string[];
  pages?: string;
  questionsCount?: number;
  duration?: string;
  updatedAt?: string;
}

export interface Flashcard {
  id: string;
  topic: string;
  badge: string;
  question: string;
  hint: string;
  answerTitle: string;
  complexity: string;
  details: string[];
  formula: string;
  userRating: 'hard' | 'good' | 'easy' | null;
}

export type ScreenType = 'dashboard' | 'collections' | 'reader' | 'library' | 'saved' | 'profile' | 'add';
