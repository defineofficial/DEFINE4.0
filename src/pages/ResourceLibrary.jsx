import { useState, useEffect } from 'react'
import { supabase } from '../lib/supabase'
import { ResourceCard } from '../components/ui/ResourceCard'
import { EmptyState } from '../components/ui/EmptyState'
import { SlidersHorizontal } from 'lucide-react'

export default function ResourceLibrary() {
  const [resources, setResources] = useState([])
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
    const fetchResources = async () => {
      const { data, error } = await supabase
        .from('resources')
        .select(`
          *,
          saved_resources ( id )
        `)
        .order('created_at', { ascending: false })

      if (error) {
        console.error('Error fetching resources:', error)
      } else {
        const formattedData = data.map(res => ({
          ...res,
          id: res.id,
          title: res.title,
          type: res.type,
          url: res.url,
          author: res.author_name,
          createdAt: res.created_at,
          isSaved: res.saved_resources && res.saved_resources.length > 0
        }))
        setResources(formattedData)
      }
      setLoading(false)
    }

    fetchResources()
  }, [])

  const filteredResults = resources.filter(res => {
    if (activeFilter === 'All') return true
    return res.type === activeFilter
  })

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem', maxWidth: '1200px', margin: '0 auto', width: '100%' }}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        <div>
          <h1 style={{ marginBottom: '0.5rem', fontSize: '2.5rem' }}>Library</h1>
          <p className="text-secondary" style={{ fontSize: '1.125rem' }}>
            Browse and discover materials uploaded by the community.
          </p>
        </div>

        {!loading && resources.length > 0 && (
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
        <div className="text-secondary">Loading resources...</div>
      ) : filteredResults.length > 0 ? (
        <div className="grid-cards">
          {filteredResults.map(resource => (
            <ResourceCard key={resource.id} resource={resource} />
          ))}
        </div>
      ) : (
        <EmptyState 
          title={`No ${activeFilter !== 'All' ? filterLabels[activeFilter].toLowerCase() : 'resources'} found`} 
          description="Try selecting a different filter or add a new resource to the library." 
        />
      )}
    </div>
  )
}
