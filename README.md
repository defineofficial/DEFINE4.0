# DEFINE 4.0
The official project submission repository for DEFINE 4.0 — The World's Realest Hackathon.

<h1 align="center">📚 NoteVault — Academic Study Sanctuary</h1>
<p align="center"><em>A UI/UX Design Submission for the Design Track</em></p>

---

## Team Information
- **Team Name:** The Unwireds
- **Track:** Design

### Team Members

| Name | Role | GitHub | LinkedIn |
| :--- | :--- | :--- | :--- |
| **Haneen Ershad** | Lead UI/UX Designer | [@prohaneen](https://github.com/prohaneen) | [Profile](https://www.linkedin.com/in/prohaneen/) |
| **Muhammed Fazil H** | UI Designer | [@fazil-pi](https://github.com/fazil-pi) | [Profile](https://www.linkedin.com/in/muhammed-fazil-h-196b24304/) |
| **Adish S** | UI Designer | [@Adish-aster](https://github.com/Adish-aster) | [Profile](https://www.linkedin.com/in/adish-s-166aa332a/) |

---

## Project Details

### Overview
NoteVault is a high-fidelity UI/UX design concept for a centralised academic learning platform. This submission presents the complete visual design, layout, interaction patterns, and user experience for a platform that helps students discover, organise, and access their scattered study resources in one beautiful, distraction-free environment.

> **Note:** This is a design track submission. The repository contains a fully interactive, browser-rendered prototype built with React and Tailwind CSS, using rich dummy data to demonstrate every screen and interaction.

---

### Problem Statement
**What is the problem?**
Students' study materials are fragmented across dozens of platforms — university portals, YouTube, GitHub, Google Drive, and messaging apps. There is no single, beautiful interface designed specifically for organising academic resources.

**Who is affected?**
University students, entrance exam aspirants, and self-learners who work with diverse resource formats daily.

**Why does design matter here?**
Existing tools like Notion or Google Drive are generic productivity tools. They lack visual clarity for academic content — a student cannot instantly tell apart a PDF lecture, a YouTube tutorial, and a GitHub code repo at a glance. Poor information architecture leads to wasted time and lost focus.

---

### Design Solution

We designed a unified "Academic Study Sanctuary" — an editorial, focused, and visually expressive interface that solves four core user needs:

| Pillar | Design Solution |
| :--- | :--- |
| **Find** | A federated search bar with instant filter pills (PDFs, Videos, GitHub, PYQs, Textbooks) |
| **Organise** | Subject-based "Vault" cards with topic-level drill-down and progress tracking |
| **Navigate** | A persistent sidebar and a "Focus Panel" split-view for resource details |
| **Access** | Embedded resource previews and a seamless "Open Resource" CTA |

---

## Design Highlights

### 1. Editorial "Book Cover" Cards
Every resource renders as a physical book cover with a unique mesh-gradient background based on its type (e.g. warm pink for PDFs, amber for videos, green for GitHub repos). The card features a 3D isometric tilt animation on hover, making the library feel tactile and premium.

### 2. Distraction-Free Focus Panel
Clicking any resource opens a slide-in "Focus Panel" with the resource's full metadata, a read/watch progress bar, contextual highlights, and a prominent CTA — all without leaving the current view.

### 3. Active Recall Sprint UI
A dedicated flashcard drill interface featuring card-flip animations, difficulty ratings (Easy / Hard / Missed), and a spaced repetition progress summary — designed specifically for exam preparation.

### 4. AI Study Guide Interface (Design Concept)
A beautifully designed glassmorphic card representing an AI-powered summary feature. Showcases the UI pattern for how AI-generated "Key Takeaways" and summaries would surface alongside resources.

### 5. Design System & Tokens
| Token | Value |
| :--- | :--- |
| **Background** | `#F7F5F0` (Warm Paper) |
| **Text Primary** | `#131c2a` (Ink Navy) |
| **Accent** | `#5967D9` (Indigo) |
| **Display Font** | Outfit (700) |
| **Body Font** | Plus Jakarta Sans (400/600) |
| **Border Radius** | 16px — 24px |
| **Shadow Style** | Layered soft shadows + glassmorphism |

---

## Screens Designed

- **Dashboard** — Greeting, milestone banner, active recall sprint, vault stats, subject carousel, quick access archive
- **Library View** — Filter tabs, resource grid, progress indicators
- **Subject View** — Topic navigator, resource list with progress bars
- **Saved Vault** — Bookmarked resources with format filters
- **Resource Detail** — Focus Panel with metadata sidebar, embedded preview, AI study guide card
- **Flashcard Drill Modal** — Animated flashcard quiz with spaced repetition UI
- **Add Resource View** — Form to manually add a new resource to a subject

---

## Demo

**Demo Video**
[Watch Project Demo](https://www.youtube.com/watch?v=VIDEO_ID) *(Replace VIDEO_ID with your YouTube video ID)*

**Live Preview**
[Visit Live Prototype](https://your-project-url.com/) *(Add your deployment link here)*

---

## Running the Prototype Locally

```bash
# 1. Clone the repository
git clone https://github.com/prohaneen/DEFINE4.0.git
cd DEFINE4.0

# 2. Install dependencies
npm install --legacy-peer-deps

# 3. Start the prototype
npm run dev
```

Open your browser and navigate to `http://localhost:3000`
