export const MOCK_SUBJECTS = [
  { id: '1', name: 'Computer Science', code: 'CS101', description: 'Intro to algorithms and data structures', resourceCount: 12 },
  { id: '2', name: 'Physics', code: 'PHY201', description: 'Quantum mechanics basics', resourceCount: 8 },
  { id: '3', name: 'Mathematics', code: 'MATH301', description: 'Linear algebra and calculus', resourceCount: 24 },
];

export const MOCK_RESOURCES = [
  { 
    id: '101', 
    title: 'Introduction to React', 
    type: 'video', 
    subjectId: '1', 
    author: 'Jane Doe',
    url: 'https://youtube.com',
    createdAt: '2026-10-01',
    isSaved: true
  },
  { 
    id: '102', 
    title: 'Calculus Cheat Sheet', 
    type: 'pdf', 
    subjectId: '3', 
    author: 'Math Dept',
    url: '/dummy.pdf',
    createdAt: '2026-10-02',
    isSaved: false
  },
  { 
    id: '103', 
    title: 'Quantum Physics Notes', 
    type: 'note', 
    subjectId: '2', 
    author: 'Albert E.',
    url: '/notes',
    createdAt: '2026-10-05',
    isSaved: true
  },
  { 
    id: '104', 
    title: 'Algorithms GitHub Repo', 
    type: 'github', 
    subjectId: '1', 
    author: 'Alan T.',
    url: 'https://github.com',
    createdAt: '2026-10-08',
    isSaved: false
  },
];
