import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { supabase } from '../lib/supabase'
import { ArrowLeft, ExternalLink, Bookmark, Clock, User, Calendar } from 'lucide-react'
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

  const getYoutubeEmbedUrl = (url) => {
    const regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|&v=)([^#&?]*).*/;
    const match = url.match(regExp);
    return (match && match[2].length === 11)
      ? `https://www.youtube.com/embed/${match[2]}`
      : null;
  }

  if (loading) {
    return <div style={{ padding: '4rem', textAlign: 'center', color: 'var(--text-secondary)' }}>Loading resource...</div>
  }
  
  if (!resource) {
    return <div style={{ padding: '4rem', textAlign: 'center' }}>Resource not found.</div>
  }

  const youtubeEmbedUrl = resource.type === 'video' ? getYoutubeEmbedUrl(resource.url) : null;

  return (
    <div style={{ maxWidth: '1000px', margin: '0 auto', paddingBottom: '4rem' }}>
      <Link to="/resources" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-secondary)', marginBottom: '2rem', fontWeight: 500, textDecoration: 'none' }}>
        <ArrowLeft size={16} /> Back to Library
      </Link>
      
      <div style={{ display: 'flex', gap: '3rem', alignItems: 'flex-start' }}>
        {/* Main Content Area */}
        <div style={{ flex: '1', display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem' }}>
              <span style={{ 
                background: 'var(--accent-transparent)', 
                color: 'var(--accent-primary)', 
                padding: '0.25rem 0.75rem', 
                borderRadius: '999px', 
                fontSize: '0.75rem', 
                fontWeight: 600, 
                textTransform: 'uppercase',
                letterSpacing: '0.05em'
              }}>
                {resource.type}
              </span>
              {isSaved && <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>★ Saved in your vault</span>}
            </div>
            <h1 style={{ fontSize: '2.5rem', lineHeight: 1.2, marginBottom: '1rem' }}>{resource.title}</h1>
            <p style={{ fontSize: '1.125rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
              {resource.description || 'No detailed description provided for this resource.'}
            </p>
          </div>

          <div style={{ 
            background: 'var(--bg-secondary)', 
            borderRadius: 'var(--radius-lg)',
            border: '1px solid var(--border-subtle)',
            overflow: 'hidden',
            boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)'
          }}>
            {youtubeEmbedUrl ? (
              <div style={{ position: 'relative', paddingBottom: '56.25%', height: 0 }}>
                <iframe 
                  src={youtubeEmbedUrl}
                  style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', border: 'none' }}
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                  allowFullScreen
                />
              </div>
            ) : (
              <div style={{ padding: '4rem 2rem', textAlign: 'center', background: 'var(--bg-tertiary)' }}>
                <div style={{ width: '80px', height: '100px', background: 'white', borderRadius: '4px', margin: '0 auto 1.5rem auto', boxShadow: '0 4px 6px rgba(0,0,0,0.1)', border: '1px solid var(--border-subtle)' }} />
                <h3 style={{ marginBottom: '0.5rem' }}>External Resource</h3>
                <p className="text-secondary" style={{ marginBottom: '1.5rem', maxWidth: '400px', margin: '0 auto 1.5rem auto' }}>
                  This {resource.type} is hosted externally. Click below to open it in a new tab.
                </p>
                <a href={resource.url} target="_blank" rel="noopener noreferrer" className="btn btn-primary">
                  Open {resource.type.toUpperCase()} <ExternalLink size={16} />
                </a>
              </div>
            )}
          </div>
          
        </div>

        {/* Right Sidebar Metadata */}
        <div style={{ 
          width: '300px', 
          background: 'var(--bg-secondary)', 
          padding: '2rem', 
          borderRadius: 'var(--radius-lg)',
          border: '1px solid var(--border-subtle)',
          display: 'flex',
          flexDirection: 'column',
          gap: '2rem',
          flexShrink: 0
        }}>
          
          <button 
            onClick={toggleSave} 
            style={{ 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'center', 
              gap: '0.5rem', 
              width: '100%', 
              padding: '0.75rem', 
              borderRadius: 'var(--radius-md)',
              border: `1px solid ${isSaved ? 'var(--accent-primary)' : 'var(--border-strong)'}`,
              background: isSaved ? 'var(--accent-transparent)' : 'transparent',
              color: isSaved ? 'var(--accent-primary)' : 'var(--text-primary)',
              fontWeight: 600,
              transition: 'all 0.2s'
            }}
          >
            <Bookmark size={18} fill={isSaved ? "var(--accent-primary)" : "none"} />
            {isSaved ? 'Saved to Vault' : 'Save Resource'}
          </button>

          <div>
            <h3 style={{ fontSize: '0.875rem', textTransform: 'uppercase', color: 'var(--text-muted)', letterSpacing: '0.05em', marginBottom: '1rem' }}>
              About this Resource
            </h3>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <User size={18} color="var(--text-secondary)" />
                <div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Author / Source</div>
                  <div style={{ fontWeight: 500 }}>{resource.author_name || 'Unknown'}</div>
                </div>
              </div>
              
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <Calendar size={18} color="var(--text-secondary)" />
                <div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Date Added</div>
                  <div style={{ fontWeight: 500 }}>{new Date(resource.created_at).toLocaleDateString()}</div>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <ExternalLink size={18} color="var(--text-secondary)" />
                <div style={{ overflow: 'hidden' }}>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Source Link</div>
                  <a href={resource.url} target="_blank" rel="noopener noreferrer" style={{ fontWeight: 500, color: 'var(--accent-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', display: 'block' }}>
                    {new URL(resource.url).hostname}
                  </a>
                </div>
              </div>
            </div>
          </div>
          
        </div>
      </div>
    </div>
  )
}
