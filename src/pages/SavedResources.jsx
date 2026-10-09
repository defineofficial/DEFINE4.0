import { useState, useEffect } from 'react'
import { supabase } from '../lib/supabase'
import { ResourceCard } from '../components/ui/ResourceCard'
import { EmptyState } from '../components/ui/EmptyState'
import { useAuth } from '../contexts/AuthContext'
import { SlidersHorizontal } from 'lucide-react'

export default function SavedResources() {
  const { user } = useAuth()
  const [savedResources, setSavedResources] = useState([])
  const [loading, setLoading] = useState(true)

  const [activeFilter, setActiveFilter] = useState('All')
  const filters = ['All', 'note', 'pdf', 'video', 'github', 'textbook']
  
  const filterLabels = {
    'All': 'All Resources',
    'note': 'Notes',
    'pdf': 'PDFs',
    'video': 'Videos',
    'github': 'Repositories',
    'textbook': 'Textbooks'
  }

  useEffect(() => {
    const fetchSavedResources = async () => {
      if (!user) {
        setLoading(false)
        return
      }

      const { data, error } = await supabase
        .from('saved_resources')
        .select(`
          resource_id,
          resources (*)
        `)
        .eq('user_id', user.id)

      if (error) {
        console.error('Error fetching saved resources:', error)
      } else {
        const formattedData = data.map(item => ({
          ...item.resources,
          id: item.resources.id,
          title: item.resources.title,
          type: item.resources.type,
          url: item.resources.url,
          author: item.resources.author_name,
          createdAt: item.resources.created_at,
          isSaved: true
        }))
        setSavedResources(formattedData)
      }
      setLoading(false)
    }

    fetchSavedResources()
  }, [user])

  if (!user) {
    return (
      <EmptyState 
        title="Sign in to save resources" 
        description="You need to be signed in to access and manage your saved resources." 
      />
    )
  }

  const filteredResults = savedResources.filter(res => {
    if (activeFilter === 'All') return true
    return res.type === activeFilter
  })

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem', maxWidth: '1200px', margin: '0 auto', width: '100%' }}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        <div>
          <h1 style={{ marginBottom: '0.5rem', fontSize: '2.5rem' }}>Vault</h1>
          <p className="text-secondary" style={{ fontSize: '1.125rem' }}>
            Your personal collection of bookmarked materials.
          </p>
        </div>

        {!loading && savedResources.length > 0 && (
          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: '1rem', 
            background: 'var(--bg-secondary)', 
            padding: '1rem', 
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-subtle)',
            boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
            overflowX: 'auto'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-secondary)', paddingRight: '1rem', borderRight: '1px solid var(--border-subtle)' }}>
              <SlidersHorizontal size={18} />
              <span style={{ fontWeight: 500, fontSize: '0.875rem' }}>Filters</span>
            </div>
            
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              {filters.map(f => (
                <button
                  key={f}
                  onClick={() => setActiveFilter(f)}
                  style={{
                    padding: '0.4rem 1.25rem',
                    borderRadius: '999px',
                    fontSize: '0.875rem',
                    fontWeight: 500,
                    backgroundColor: activeFilter === f ? 'var(--accent-primary)' : 'transparent',
                    color: activeFilter === f ? 'white' : 'var(--text-secondary)',
                    border: '1px solid',
                    borderColor: activeFilter === f ? 'var(--accent-primary)' : 'var(--border-strong)',
                    transition: 'all 0.2s',
                    whiteSpace: 'nowrap'
                  }}
                >
                  {filterLabels[f]}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {loading ? (
        <div className="text-secondary">Loading saved resources...</div>
      ) : filteredResults.length > 0 ? (
        <div className="grid-cards">
          {filteredResults.map(resource => (
            <ResourceCard key={resource.id} resource={resource} />
          ))}
        </div>
      ) : (
        <EmptyState 
          title={`No ${activeFilter !== 'All' ? filterLabels[activeFilter].toLowerCase() : 'saved resources'} found`} 
          description={activeFilter !== 'All' ? "Try selecting a different filter." : "Browse the library and click the bookmark icon to save resources here."} 
        />
      )}
    </div>
  )
}
