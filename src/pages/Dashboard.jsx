import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { supabase } from '../lib/supabase'
import { ResourceCard } from '../components/ui/ResourceCard'
import { BookOpen, ExternalLink, Bookmark, FileText } from 'lucide-react'

export default function Dashboard() {
  const [recentResources, setRecentResources] = useState([])
  const [categoryResources, setCategoryResources] = useState([])
  const [activeCategory, setActiveCategory] = useState('All')
  const [loading, setLoading] = useState(true)
  const [featuredResource, setFeaturedResource] = useState(null)
  const navigate = useNavigate()

  const categories = ['All', 'Notes', 'PDFs', 'Videos', 'GitHub', 'Textbooks']

  useEffect(() => {
    const fetchDashboardData = async () => {
      const { data: resourcesResponse } = await supabase
        .from('resources')
        .select('*, saved_resources(id)')
        .order('created_at', { ascending: false })
        .limit(10)

      if (resourcesResponse) {
        const formattedRes = resourcesResponse.map(res => ({
          ...res,
          author: res.author_name,
          createdAt: res.created_at,
          isSaved: res.saved_resources && res.saved_resources.length > 0
        }))
        setRecentResources(formattedRes.slice(0, 4))
        setCategoryResources(formattedRes)
        if (formattedRes.length > 0) {
          setFeaturedResource(formattedRes[0])
        }
      }
      setLoading(false)
    }
    fetchDashboardData()
  }, [])

  const filteredCategories = categoryResources.filter(res => {
    if (activeCategory === 'All') return true
    if (activeCategory === 'Notes') return res.type === 'note'
    if (activeCategory === 'PDFs') return res.type === 'pdf'
    if (activeCategory === 'Videos') return res.type === 'video'
    if (activeCategory === 'GitHub') return res.type === 'github'
    if (activeCategory === 'Textbooks') return res.type === 'textbook'
    return true
  })

  return (
    <div style={{ display: 'flex', gap: '2rem', height: '100%' }}>
      {/* Main Content Area */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '2.5rem', minWidth: 0 }}>
        
        <section>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
            <h2 style={{ fontSize: '1.25rem' }}>Recommended</h2>
            <Link to="/resources" className="text-sm" style={{ color: 'var(--accent-primary)', fontWeight: 600 }}>See All &rsaquo;</Link>
          </div>
          
          {loading ? (
            <div className="text-secondary">Loading...</div>
          ) : (
            <div style={{ display: 'flex', gap: '1rem', overflowX: 'auto', paddingBottom: '0.5rem' }}>
              {recentResources.map(resource => (
                <div key={resource.id} onClick={() => setFeaturedResource(resource)} style={{ cursor: 'pointer', minWidth: '220px', flex: '0 0 auto' }}>
                  <ResourceCard resource={resource} compact={true} />
                </div>
              ))}
            </div>
          )}
        </section>

        <section>
          <div style={{ marginBottom: '1.25rem' }}>
            <h2 style={{ fontSize: '1.25rem', marginBottom: '1rem' }}>Categories</h2>
            <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
              {categories.map(cat => (
                <button
                  key={cat}
                  onClick={() => setActiveCategory(cat)}
                  style={{
                    padding: '0.4rem 1rem',
                    borderRadius: 'var(--radius-xl)',
                    fontSize: '0.875rem',
                    fontWeight: 500,
                    backgroundColor: activeCategory === cat ? 'var(--accent-primary)' : 'var(--bg-secondary)',
                    color: activeCategory === cat ? 'white' : 'var(--text-secondary)',
                    border: '1px solid',
                    borderColor: activeCategory === cat ? 'var(--accent-primary)' : 'var(--border-subtle)',
                    transition: 'all 0.2s'
                  }}
                >
                  {cat}
                </button>
              ))}
            </div>
          </div>
          
          <div className="grid-cards" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))' }}>
            {filteredCategories.map(resource => (
              <div key={resource.id} onClick={() => setFeaturedResource(resource)} style={{ cursor: 'pointer' }}>
                <ResourceCard resource={resource} compact={true} />
              </div>
            ))}
            {filteredCategories.length === 0 && !loading && (
              <p className="text-secondary">No resources in this category yet.</p>
            )}
          </div>
        </section>
      </div>

      {/* Right Focus Panel */}
      <div style={{ 
        width: '340px', 
        backgroundColor: '#0a192f', 
        borderRadius: 'var(--radius-lg)',
        padding: '2rem',
        color: 'white',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        flexShrink: 0
      }}>
        {featuredResource ? (
          <>
            <div style={{ 
              width: '200px', 
              height: '280px', 
              backgroundColor: 'white', 
              borderRadius: 'var(--radius-md)',
              marginBottom: '1.5rem',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--text-primary)',
              padding: '1.5rem',
              textAlign: 'center',
              boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.3)'
            }}>
              <h3 style={{ fontSize: '1.25rem', marginBottom: '1rem', lineHeight: 1.2 }}>
                {featuredResource.title}
              </h3>
              <span className="text-secondary text-sm">{featuredResource.author || 'Unknown'}</span>
            </div>
            
            <h2 style={{ fontSize: '1.25rem', color: 'white', textAlign: 'center', marginBottom: '0.25rem' }}>
              {featuredResource.title}
            </h2>
            <p style={{ color: '#94a3b8', fontSize: '0.875rem', marginBottom: '2rem' }}>
              {featuredResource.author || 'Unknown'}
            </p>

            <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%', borderTop: '1px solid rgba(255,255,255,0.1)', borderBottom: '1px solid rgba(255,255,255,0.1)', padding: '1rem 0', marginBottom: '2rem' }}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '1.125rem', fontWeight: 600 }}>{featuredResource.type.toUpperCase()}</div>
                <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Format</div>
              </div>
              <div style={{ textAlign: 'center', borderLeft: '1px solid rgba(255,255,255,0.1)', borderRight: '1px solid rgba(255,255,255,0.1)', padding: '0 1.5rem' }}>
                <div style={{ fontSize: '1.125rem', fontWeight: 600 }}>{new Date(featuredResource.createdAt).getFullYear() || '-'}</div>
                <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Added</div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '1.125rem', fontWeight: 600 }}>{featuredResource.isSaved ? 'Yes' : 'No'}</div>
                <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Saved</div>
              </div>
            </div>

            <p style={{ fontSize: '0.875rem', color: '#cbd5e1', lineHeight: 1.6, marginBottom: '2rem', textAlign: 'center', display: '-webkit-box', WebkitLineClamp: 4, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
              {featuredResource.description || 'No description available for this resource. Explore to learn more.'}
            </p>

            <a 
              href={featuredResource.url} 
              target="_blank" 
              rel="noopener noreferrer"
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '0.5rem',
                backgroundColor: 'var(--accent-primary)',
                color: 'white',
                width: '100%',
                padding: '0.875rem',
                borderRadius: 'var(--radius-md)',
                fontWeight: 600,
                marginTop: 'auto',
                transition: 'background-color 0.2s'
              }}
              onMouseOver={(e) => e.currentTarget.style.backgroundColor = 'var(--accent-hover)'}
              onMouseOut={(e) => e.currentTarget.style.backgroundColor = 'var(--accent-primary)'}
            >
              Open Resource <ExternalLink size={18} />
            </a>
          </>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', opacity: 0.5 }}>
            <BookOpen size={48} style={{ marginBottom: '1rem' }} />
            <p>Select a resource to view details</p>
          </div>
        )}
      </div>
    </div>
  )
}
