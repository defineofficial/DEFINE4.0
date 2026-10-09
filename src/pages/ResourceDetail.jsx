import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { supabase } from '../lib/supabase'
import { ArrowLeft, ExternalLink, Bookmark } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'

export default function ResourceDetail() {
  const { id } = useParams()
  const { user } = useAuth()
  const [resource, setResource] = useState(null)
  const [isSaved, setIsSaved] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchResource = async () => {
      const { data, error } = await supabase
        .from('resources')
        .select('*, saved_resources(id)')
        .eq('id', id)
        .single()
        
      if (data) {
        setResource(data)
        setIsSaved(data.saved_resources && data.saved_resources.length > 0)
      }
      setLoading(false)
    }

    fetchResource()
  }, [id])

  const toggleSave = async () => {
    if (!user) return alert('Please sign in to save resources.')
    
    if (isSaved) {
      await supabase.from('saved_resources').delete().match({ user_id: user.id, resource_id: id })
      setIsSaved(false)
    } else {
      await supabase.from('saved_resources').insert({ user_id: user.id, resource_id: id })
      setIsSaved(true)
    }
  }

  if (loading) return <div>Loading resource...</div>
  if (!resource) return <div>Resource not found.</div>

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto' }}>
      <Link to="/resources" className="btn btn-ghost" style={{ marginBottom: '1.5rem', padding: '0.5rem 0' }}>
        <ArrowLeft size={16} /> Back to Library
      </Link>
      
      <div className="glass-panel" style={{ padding: '3rem', borderRadius: 'var(--radius-lg)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.5rem' }}>
          <div>
            <span style={{ color: 'var(--accent-primary)', textTransform: 'uppercase', fontSize: '0.875rem', fontWeight: 600 }}>
              {resource.type}
            </span>
            <h1 style={{ marginTop: '0.5rem', marginBottom: '0.5rem' }}>{resource.title}</h1>
            <div className="text-secondary">
              Added by {resource.author_name} on {new Date(resource.created_at).toLocaleDateString()}
            </div>
            {resource.description && (
              <p style={{ marginTop: '1rem', color: 'var(--text-secondary)' }}>{resource.description}</p>
            )}
          </div>
          <button onClick={toggleSave} className={`btn btn-ghost ${isSaved ? 'text-primary' : ''}`} title="Save">
            <Bookmark size={24} fill={isSaved ? "var(--accent-primary)" : "none"} color={isSaved ? "var(--accent-primary)" : "currentColor"} />
          </button>
        </div>

        <div style={{ 
          background: 'var(--bg-primary)', 
          padding: '2rem', 
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-subtle)',
          minHeight: '200px',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '1rem',
          textAlign: 'center'
        }}>
          <p className="text-secondary">
            Content preview is not available directly.<br/>
            Click the link below to access the resource.
          </p>
          <a href={resource.url} target="_blank" rel="noopener noreferrer" className="btn btn-primary">
            Open Resource <ExternalLink size={16} />
          </a>
        </div>
      </div>
    </div>
  )
}
