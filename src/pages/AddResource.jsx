import { useState } from 'react'
import { MOCK_SUBJECTS } from '../data/mockData'

export default function AddResource() {
  const [formData, setFormData] = useState({
    title: '',
    type: 'note',
    subjectId: '',
    url: '',
    description: ''
  })

  const handleSubmit = (e) => {
    e.preventDefault()
    alert('Resource submission is not yet connected to the backend.')
  }

  return (
    <div style={{ maxWidth: '600px', margin: '0 auto' }}>
      <div style={{ marginBottom: '2rem' }}>
        <h1>Add Resource</h1>
        <p className="text-secondary">Contribute a new learning material to the vault.</p>
      </div>

      <form onSubmit={handleSubmit} className="glass-panel" style={{ padding: '2rem', borderRadius: 'var(--radius-lg)', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <label htmlFor="title">Resource Title</label>
          <input 
            type="text" 
            id="title" 
            placeholder="e.g. Intro to Machine Learning" 
            value={formData.title}
            onChange={(e) => setFormData({...formData, title: e.target.value})}
            required
          />
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <label htmlFor="type">Resource Type</label>
            <select 
              id="type"
              value={formData.type}
              onChange={(e) => setFormData({...formData, type: e.target.value})}
            >
              <option value="note">Note / Text</option>
              <option value="pdf">PDF Document</option>
              <option value="video">Video</option>
              <option value="github">GitHub Repo</option>
            </select>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <label htmlFor="subject">Subject</label>
            <select 
              id="subject"
              value={formData.subjectId}
              onChange={(e) => setFormData({...formData, subjectId: e.target.value})}
              required
            >
              <option value="">Select a subject...</option>
              {MOCK_SUBJECTS.map(s => (
                <option key={s.id} value={s.id}>{s.name}</option>
              ))}
            </select>
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <label htmlFor="url">URL / Link</label>
          <input 
            type="url" 
            id="url" 
            placeholder="https://..." 
            value={formData.url}
            onChange={(e) => setFormData({...formData, url: e.target.value})}
            required
          />
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <label htmlFor="desc">Description (Optional)</label>
          <textarea 
            id="desc" 
            rows="3" 
            placeholder="Briefly describe this resource..."
            value={formData.description}
            onChange={(e) => setFormData({...formData, description: e.target.value})}
          />
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem', marginTop: '1rem' }}>
          <button type="button" className="btn btn-ghost" onClick={() => window.history.back()}>Cancel</button>
          <button type="submit" className="btn btn-primary">Save Resource</button>
        </div>
      </form>
    </div>
  )
}
