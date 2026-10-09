import { BookText } from 'lucide-react'

export default function Documentation() {
  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', paddingBottom: '3rem' }}>
      <div style={{ marginBottom: '2rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <div style={{ 
          width: '48px', height: '48px', borderRadius: 'var(--radius-md)', 
          background: 'var(--accent-primary)', display: 'flex', 
          alignItems: 'center', justifyContent: 'center' 
        }}>
          <BookText size={24} color="white" />
        </div>
        <div>
          <h1>Platform Documentation</h1>
          <p className="text-secondary">Learn how to use NoteVault's core features.</p>
        </div>
      </div>

      <div className="glass-panel" style={{ padding: '2rem', borderRadius: 'var(--radius-lg)', display: 'flex', flexDirection: 'column', gap: '2rem' }}>
        
        <section>
          <h2 style={{ color: 'var(--accent-primary)', marginBottom: '0.75rem' }}>1. Resource Library</h2>
          <p>
            The Resource Library is the central hub for all learning materials. It displays notes, PDFs, videos, and GitHub repositories uploaded by the community. 
            All resources are displayed as interactive cards. You can quickly see the resource type via the colored badges and see who uploaded it.
          </p>
        </section>

        <section>
          <h2 style={{ color: 'var(--accent-primary)', marginBottom: '0.75rem' }}>2. Engineering Subjects</h2>
          <p>
            NoteVault is strictly categorized by English Engineering Classes. When you browse the <strong>Subjects</strong> tab, you can drill down into specific modules (e.g., Thermodynamics, Fluid Mechanics) and see only the resources associated with that specific engineering discipline.
          </p>
        </section>

        <section>
          <h2 style={{ color: 'var(--accent-primary)', marginBottom: '0.75rem' }}>3. Adding a Resource</h2>
          <p>
            Any authenticated user can contribute to the vault. Click <strong>Add Resource</strong> in the sidebar to open the submission form. 
            You must provide a clear title, select the correct resource type (Video, PDF, Note, etc.), and categorize it under one of our core Engineering subjects.
          </p>
        </section>

        <section>
          <h2 style={{ color: 'var(--accent-primary)', marginBottom: '0.75rem' }}>4. Saving & Bookmarking</h2>
          <p>
            Found a resource useful? Click the <strong>Bookmark Icon</strong> on any resource card to save it. You can instantly retrieve all your saved materials later by visiting the <strong>Saved</strong> tab in the sidebar. This feature requires you to be signed in.
          </p>
        </section>

        <section>
          <h2 style={{ color: 'var(--accent-primary)', marginBottom: '0.75rem' }}>5. Authentication</h2>
          <p>
            NoteVault utilizes a secure, real-time database. Users must create an account and sign in to submit new resources and manage their personal saved collection. Browsing resources is open to everyone.
          </p>
        </section>
      </div>
    </div>
  )
}
