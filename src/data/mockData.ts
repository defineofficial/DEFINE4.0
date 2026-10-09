import { Resource, Flashcard } from '../types';

export const INITIAL_RESOURCES: Resource[] = [
  {
    id: 'pyq-graph-2025',
    title: 'DSA 2025 Graph questions',
    type: 'pyq',
    typeBadge: 'PYQ',
    subject: 'CS204',
    subjectName: 'Data Structures & Algorithms',
    topic: 'Graphs',
    author: 'University Midterms',
    meta: '2025 Semester Prep · 12 pages · 18 questions',
    progress: 33,
    isPending: true,
    saved: true,
    imageUrl: 'https://lh3.googleusercontent.com/aida-public/AB6AXuBAp05pdoeEwPjdYDYXKXdTTru-Cva2OF0Iw4TassR-BVQzxw7quQXMsnP3pg9phOM4yYYl3CG21YMPAWYN_ygBt2Z36I3sjJqIB-VVjLM4IhXFwIeGCGZPJZwAxpcpwRF7daa6PDe70zz3Be29uRoxumlG6-PL_JXYLJe8fLUOup--dW4pk3x7Dp37tRs_8uJidwK9gYSqSXEnpe2Ra6Ui5XvTU1YMXirVEgThXLxni29vo4Yd7OU',
    colorClass: 'bg-[#dae3f7] text-[#3f4dbf]',
    spineGradient: 'from-[#65738d] via-[#dfe8fd] to-white',
    icon: 'assignment',
    pages: '12 pages',
    questionsCount: 18,
    updatedAt: 'Opened yesterday',
    highlights: [
      'Breadth-First Search (BFS) & DFS traversal algorithms',
      'Figure 7.1 Graph Schema and FIFO Queue discovery sequences',
      'Negative edge weight implications on shortest path validity'
    ]
  },
  {
    id: 'doc-graph-traversal',
    title: 'Graph traversal · Revision notes',
    type: 'doc',
    typeBadge: 'DOC',
    subject: 'CS204',
    subjectName: 'Data Structures & Algorithms',
    topic: 'Graphs',
    author: 'Prof. Raman',
    meta: 'Summary & proofs · 8 pages',
    progress: 10,
    isPending: false,
    saved: true,
    imageUrl: 'https://lh3.googleusercontent.com/aida-public/AB6AXuBll6nrCz0mrYVkun1fIxqxJzoViKbJGH0s8DY2kVcI7LXoYfBE2QfQrkACGlIuXZHmOKnwQ93Pgyotjly43fq1PU5_CSb85lQVrNUHQgWiqpOANE1g2uxHBNn_U1wvgsLj8elBKWhCVyAzIVK0sZ6D6HRW1U3RJ3yxQ72YAdkP3CgMFEMX1CjwpnV1f4RtkK5FHjDVv7BAVCynCDN4fN6eNCyNaxj6YYQvZ1bPhDXh-GdULmQxlpYj6c_iZql4kPA7',
    colorClass: 'bg-[#dce5dd] text-[#151d19]',
    spineGradient: 'from-[#3f4dbf] via-[#dfe0ff] to-white',
    icon: 'description',
    pages: '8 pages',
    updatedAt: 'Updated 6 Oct',
    highlights: [
      'Cycle detection proofs using DFS color coding (White, Gray, Black)',
      'Topological sorting with Kahn’s Algorithm',
      'Adjacency list memory layout optimizations'
    ]
  },
  {
    id: 'pdf-lecture-slides',
    title: 'Graphs - Lecture slides',
    type: 'pdf',
    typeBadge: 'PDF',
    subject: 'CS204',
    subjectName: 'Data Structures & Algorithms',
    topic: 'Graphs',
    author: 'Prof. Meera Shah',
    meta: '38 slides · Department of CS',
    progress: 0,
    isPending: false,
    saved: false,
    imageUrl: 'https://lh3.googleusercontent.com/aida-public/AB6AXuBgxyg1T7k9cJZC6WxP1uq2Yqg2PkdbaWQya-TGuk9wdqjuSvPWg2VSYv5Rnf0TZPEsC0bNZpYhhmukrw0ZrRbQaG0WssimibuTaTok4Wd2Q2YopaiV3lPFjCkfeLnWJmaOujObIiFtnD2tctigHrzbLeygdVZ5UJsMnsTzLoZzONxkyyxAdPAVhxgYq0YTX-tmAu22QsvuQyvOdalcyrZUeLwdsBRdploGeNgSjbw4sWdo7Aidxfo',
    colorClass: 'bg-[#d6e3ff] text-[#0d1c32]',
    spineGradient: 'from-[#4d5a74] via-[#dfe8fd] to-white',
    icon: 'slideshow',
    pages: '38 slides',
    updatedAt: 'Slides deck',
    highlights: [
      'Directed Acyclic Graphs (DAGs) and topological order',
      'Adjacency matrix visualizations vs adjacency list space analysis',
      'Midterm revision handout and practice derivations'
    ]
  },
  {
    id: 'video-bfs-dfs',
    title: 'BFS & DFS · Visual walkthrough',
    type: 'video',
    typeBadge: 'VIDEO',
    subject: 'CS204',
    subjectName: 'Data Structures & Algorithms',
    topic: 'Graphs',
    author: 'Abdul Bari',
    meta: '24 mins · 4K Lecture',
    progress: 40,
    isPending: true,
    saved: true,
    imageUrl: 'https://lh3.googleusercontent.com/aida-public/AB6AXuAWA9MvxZOoKh3ZyMNW3XRmBOiJLq51DIC0dceMNrLzDDVAjoSaIdu6WezigOUEQbw6ZP4azDxmF4xCbHrGu1FsJg5fggNy8LbcXirdjPczHQTIF4gZJqbtkxJNRA5_6Z2ehJZcuAU2njgTzrJwnSNbwcMFSWF-b8_2U8Tv6aXhocbFVzfZdtGRmgznk65HFlN_cOeqI28T54IOkxQYiuiySdekhPnu3wunqp1Fuxat9of3omSga00',
    colorClass: 'bg-[#ffdad6] text-[#ba1a1a]',
    spineGradient: 'from-[#ba1a1a] via-[#ffdad6] to-white',
    icon: 'play_circle',
    duration: '24 mins',
    updatedAt: '09:42 of 24:00',
    highlights: [
      'Visual traversal simulation on 8-node test network',
      'Queue FIFO invariants and recursive stack tracking',
      'Asymptotic complexity O(V + E) verified on whiteboard'
    ]
  },
  {
    id: 'code-python-graphs',
    title: 'Graph algorithms in Python',
    type: 'repo',
    typeBadge: 'CODE',
    subject: 'CS204',
    subjectName: 'Data Structures & Algorithms',
    topic: 'Graphs',
    author: 'TheAlgorithms',
    meta: 'Jupyter Notebook · MIT License',
    progress: 0,
    isPending: false,
    saved: false,
    imageUrl: 'https://lh3.googleusercontent.com/aida-public/AB6AXuBhVf-zXgwxCcEhOqfWkrjIeDX5mHB2c9j2HzmdinMW3m9bULx6uUNV8fGA-rC3fFu1HME_jzcks3H-lDcNw2yWhnIVgBBrj1-RL1Wp2wqZO3pDo2HB62Jnp894AEf6aLVgtFdv5olrtxWwLwQGiQiMFza6EWMCsx1lO9jcJ8o8Ogc_twMf1s7DprjeavVWxfGbnPVjojh5-qux30eqOd1DyY9WcbCzl72-IINUz5yLvgJk33ZyxiQ',
    colorClass: 'bg-[#e7eeff] text-[#3f4dbf]',
    spineGradient: 'from-[#202938] via-[#58605a] to-white',
    icon: 'terminal',
    pages: '18 examples',
    updatedAt: 'MIT License',
    highlights: [
      'Production Python implementations for Dijkstra and A*',
      'Heapq priority queue integrations with adjacency maps',
      'Benchmark scripts tested against 100k random nodes'
    ]
  },
  {
    id: 'book-clrs-intro',
    title: 'Introduction to Algorithms (CLRS)',
    type: 'book',
    typeBadge: 'BOOK',
    subject: 'CS204',
    subjectName: 'Data Structures & Algorithms',
    topic: 'Graphs',
    author: 'Cormen, Leiserson, Rivest, Stein',
    meta: 'Ch. 22 · Elementary Graphs · MIT Press',
    progress: 15,
    isPending: false,
    saved: true,
    imageUrl: 'https://lh3.googleusercontent.com/aida-public/AB6AXuBvy18sEH2Yq-aXeDVqsPPsLzuDzGZjcuy3gUC3xj-7WGbR0OcbACuqnweJ9zYD9w5dYKk27lV_LzCuy4U6QBhdJyGaHfcoJBVEm6KVq_1HeFeX3AukX20WAoliJxqak_JiuvzW5g3cphMBAIOJYlfOckS6qa5lEuqoLNyTvYpUDT-qxXWkhtqNXtYhbjW5cYbg-1ajgrgUkoJNXJZBwvJTw8caLU-l81uau4uZ0NkANya7SsR2QMc',
    colorClass: 'bg-[#d6e3ff] text-[#0d1c32]',
    spineGradient: 'from-[#65738d] via-[#dfe8fd] to-white',
    icon: 'menu_book',
    pages: 'Ch. 20–22',
    updatedAt: 'MIT Press',
    highlights: [
      'Chapter 22: Elementary Graph Algorithms',
      'Theorems 22.1 & 22.2: Shortest-path properties of breadth-first search',
      'Exercises and formal induction problem sets'
    ]
  },
  {
    id: 'os-concurrency-sync',
    title: 'Process Synchronization & Semaphores',
    type: 'notes',
    typeBadge: 'CHEAT SHEET',
    subject: 'CS206',
    subjectName: 'Operating Systems',
    topic: 'Concurrency',
    author: 'Operating Systems Group',
    meta: 'Updated 3 days ago · 14 pages',
    progress: 60,
    isPending: false,
    saved: false,
    colorClass: 'bg-[#dce5dd] text-[#151d19]',
    icon: 'description',
    pages: '14 pages',
    updatedAt: 'Updated 3 days ago',
    highlights: [
      'Dining Philosophers and Readers-Writers solutions',
      'Mutex locks vs Binary Semaphores comparisons',
      'Coffman conditions for deadlock prevention'
    ]
  },
  {
    id: 'ma202-svd-decomp',
    title: 'Eigenvalues & SVD Decomposition',
    type: 'video',
    typeBadge: 'VIDEO TUTORIAL',
    subject: 'MA202',
    subjectName: 'Linear Algebra',
    topic: 'Decomposition',
    author: '3Blue1Brown',
    meta: '18:15 of 22:00 · 82% complete',
    progress: 82,
    isPending: false,
    saved: false,
    colorClass: 'bg-[#d6e3ff] text-[#0d1c32]',
    icon: 'play_circle',
    duration: '22 mins',
    updatedAt: '82% complete',
    highlights: [
      'Geometric interpretation of orthogonal transformation',
      'Singular Value Decomposition compression matrix factorizations',
      'Principal Component Analysis connection'
    ]
  }
];

export const TOPICS_CS204 = [
  { id: 'all', name: 'All resources', count: 42 },
  { id: 'arrays', name: 'Arrays & sorting', count: 8 },
  { id: 'linked_lists', name: 'Linked lists', count: 7 },
  { id: 'stacks_queues', name: 'Stacks & queues', count: 6 },
  { id: 'trees', name: 'Trees', count: 6 },
  { id: 'graphs', name: 'Graphs', count: 6, active: true },
  { id: 'dp', name: 'Dynamic programming', count: 9 },
];

export const FLASHCARD_DATA: Flashcard[] = [
  {
    id: 'fc-1',
    topic: 'Traversal Complexity',
    badge: 'Core Concept',
    question: 'What is the time complexity of Breadth-First Search (BFS) when implemented using an Adjacency List?',
    hint: 'Consider that every vertex is visited once and every edge incident to it is scanned.',
    answerTitle: 'Time Complexity: O(V + E)',
    complexity: 'O(V + E)',
    details: [
      '• V (Vertices): Each node enters and exits the Queue exactly once.',
      '• E (Edges): Every incident edge is examined twice (undirected) or once (directed).',
      '💡 Contrast: Using an Adjacency Matrix requires inspecting V elements per vertex, resulting in O(V²).'
    ],
    formula: 'Queue Q; Q.push(src); visited[src]=true; while(!Q.empty()) { ... }',
    userRating: null
  },
  {
    id: 'fc-2',
    topic: 'Graph Data Structures',
    badge: 'Memory & State',
    question: 'Which fundamental abstract data structures govern the frontier exploration in BFS vs DFS?',
    hint: 'Think First-In-First-Out vs Last-In-First-Out ordering principles.',
    answerTitle: 'BFS uses a FIFO Queue; DFS uses a LIFO Stack (or Recursion)',
    complexity: 'O(V) Space',
    details: [
      '• BFS uses a standard Queue to guarantee exploring vertices level-by-level (shallowest first).',
      '• DFS uses a Stack (call stack or explicit) exploring along each branch to maximum depth.',
      '💡 Exam Pitfall: If edges have uniform weights, BFS guarantees shortest hop paths; DFS does not.'
    ],
    formula: 'BFS: Queue<Node> q; | DFS: Stack<Node> s OR recursive dfs(u)',
    userRating: null
  },
  {
    id: 'fc-3',
    topic: 'Shortest Path Algorithms',
    badge: 'Core Theorem',
    question: 'Why does standard Dijkstra’s Algorithm fail or produce incorrect shortest paths with negative edge weights?',
    hint: 'Dijkstra is greedy: once a node’s distance is finalized/popped from PriorityQueue, can a later path reduce it?',
    answerTitle: 'Greedy Choice Property is Invalidated',
    complexity: 'O((V+E) log V)',
    details: [
      '• Dijkstra assumes that adding another edge to an existing path can never decrease its cumulative distance.',
      '• If negative weights exist, a longer hop path might actually have a smaller total weight.',
      '💡 Solution: Use Bellman-Ford Algorithm (O(V·E)) or Johnson’s Algorithm for graphs with negative weights.'
    ],
    formula: 'Dijkstra requires: weight(u, v) >= 0 for all edges (u, v) in E',
    userRating: null
  },
  {
    id: 'fc-4',
    topic: 'Directed Acyclic Graphs (DAG)',
    badge: 'Prerequisite Test',
    question: 'What strict condition must a graph satisfy to possess a valid Topological Ordering?',
    hint: 'Can you topologically sort a graph that contains a mutual dependency or cycle?',
    answerTitle: 'Graph must be a DAG (Directed & Acyclic)',
    complexity: 'O(V + E)',
    details: [
      '• A valid linear ordering u precedes v for every directed edge (u → v) is impossible if a cycle exists.',
      '• Detectable via DFS back-edges or Kahn’s Algorithm (In-degree queue tracking).',
      '💡 In-degree check: Vertices with inDegree == 0 are processed first.'
    ],
    formula: 'Topological Sort exists <=> Graph G has zero directed cycles',
    userRating: null
  },
  {
    id: 'fc-5',
    topic: 'Minimum Spanning Trees (MST)',
    badge: 'Structural Theorem',
    question: 'For any connected, undirected graph with V vertices, how many edges does its Spanning Tree contain?',
    hint: 'A tree is minimally connected and contains zero cycles.',
    answerTitle: 'Exactly V - 1 Edges',
    complexity: '|E_mst| = V - 1',
    details: [
      '• Any spanning tree connects all V vertices without any simple cycles, requiring exactly V - 1 edges.',
      '• If an edge is removed, the graph disconnects. If an edge is added, a cycle is created.',
      '💡 Algorithms: Kruskal’s (Union-Find) and Prim’s algorithms both find MST with V - 1 edges.'
    ],
    formula: 'Kruskal: Sort edges by weight; add if union(u,v) is true until count == V-1',
    userRating: null
  }
];

export const WORKSPACES = [
  {
    id: 'cs-sem4',
    shortName: 'CS · Sem 4',
    fullName: 'My study workspace · CS · Sem 4',
    degree: 'Computer Science & Engineering · Semester 4',
    stats: '3 active subjects · 128 resources'
  },
  {
    id: 'gate-cse-2026',
    shortName: 'GATE CSE 2026',
    fullName: 'GATE CSE Exam Prep Workspace',
    degree: 'National Examination Track',
    stats: 'Algorithms, TOC, Compilers · 94 resources'
  },
  {
    id: 'ai-ml-vault',
    shortName: 'AI & Data Vault',
    fullName: 'Machine Learning & Deep Math Workspace',
    degree: 'Advanced Specialization',
    stats: 'Linear Algebra, Optimization · 48 resources'
  }
];
