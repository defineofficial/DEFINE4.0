import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { supabase } from '../lib/supabase'
import { useAuth } from '../contexts/AuthContext'

export default function AddResource() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [subjects, setSubjects] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  
  const [formData, setFormData] = useState({
    title: '',
    type: 'note',
    subjectId: '',
    url: '',
    description: ''
  })

  // Fetch subjects for the dropdown on mount
  useEffect(() => {
    const fetchSubjects = async () => {
      const { data, error } = await supabase.from('subjects').select('*').order('name')
      if (error) {
        console.error('Error fetching subjects:', error)
      } else {
        setSubjects(data || [])
      }
    }
    fetchSubjects()
  }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!user) {
      setError("You must be signed in to add a resource.")
      return
    }

    setLoading(true)
    setError(null)

    const { data: defaultSubjects } = await supabase.from('subjects').select('id').limit(1)
    const fallbackSubjectId = defaultSubjects?.[0]?.id

    if (!fallbackSubjectId) {
      setError("Database is missing a default subject to store resources.")
      setLoading(false)
      return
    }

    const { data, error: insertError } = await supabase
      .from('resources')
      .insert([
        {
          title: formData.title,
          type: formData.type,
          url: formData.url,
          description: formData.description,
          subject_id: fallbackSubjectId,
          author_name: user.user_metadata?.full_name || user.email.split('@')[0],
          user_id: user.id
        }
      ])
      .select()
      .single()

    setLoading(false)

    if (insertError) {
      setError(insertError.message)
    } else {
      // Redirect to the newly created resource detail page
      if (data && data.id) {
        navigate(`/resources/${data.id}`)
      } else {
        navigate('/resources')
      }
    }
  }

  return (
    <div style={{ maxWidth: '600px', margin: '0 auto' }}>
      <div style={{ marginBottom: '2rem' }}>
        <h1>Add Resource</h1>
        <p className="text-secondary">Contribute a new learning material to the vault.</p>
      </div>

      <form onSubmit={handleSubmit} style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-subtle)', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)', padding: '2.5rem', borderRadius: 'var(--radius-lg)', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        
        {error && (
          <div style={{ padding: '0.75rem', background: 'rgba(239, 68, 68, 0.1)', color: '#ef4444', borderRadius: 'var(--radius-sm)', fontSize: '0.875rem' }}>
            {error}
          </div>
        )}

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

        <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '1.5rem' }}>
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
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? 'Saving...' : 'Save Resource'}
          </button>
        </div>
      </form>
    </div>
  )
}
