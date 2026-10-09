import { useParams, Link } from 'react-router-dom'
import { MOCK_RESOURCES } from '../data/mockData'
import { ArrowLeft, ExternalLink, Bookmark } from 'lucide-react'

export default function ResourceDetail() {
  const { id } = useParams()
  const resource = MOCK_RESOURCES.find(r => r.id === id)

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
              Added by {resource.author} on {new Date(resource.createdAt).toLocaleDateString()}
            </div>
          </div>
          <button className={`btn btn-ghost ${resource.isSaved ? 'text-primary' : ''}`} title="Save">
            <Bookmark size={24} fill={resource.isSaved ? "var(--accent-primary)" : "none"} color={resource.isSaved ? "var(--accent-primary)" : "currentColor"} />
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
            Content preview is not available in this mockup.<br/>
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
