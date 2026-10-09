import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { supabase } from '../lib/supabase'
import { searchGithub } from '../lib/providers/githubProvider'
import { searchTextbooks } from '../lib/providers/openLibraryProvider'
import { searchArxiv } from '../lib/providers/arxivProvider'
import { searchWikipedia } from '../lib/providers/wikipediaProvider'
import { ResourceCard } from '../components/ui/ResourceCard'
import { EmptyState } from '../components/ui/EmptyState'
import { Loader2, SlidersHorizontal } from 'lucide-react'

export default function SearchResults() {
  const [searchParams] = useSearchParams()
  const query = searchParams.get('q') || ''
  
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  
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
    const fetchResults = async () => {
      if (!query.trim()) {
        setResults([])
        setLoading(false)
        return
      }

      setLoading(true)
      setError(null)

      try {
        const { data: internalData, error: dbError } = await supabase
          .from('resources')
          .select('*, saved_resources(id)')
          .ilike('title', `%${query}%`)
          .limit(10)

        if (dbError) throw dbError

        const formattedInternal = (internalData || []).map(res => ({
          ...res,
          author: res.author_name,
          createdAt: res.created_at,
          isSaved: res.saved_resources && res.saved_resources.length > 0,
          isExternal: false
        }))

        const [githubData, textbookData, arxivData, wikiData] = await Promise.all([
          searchGithub(query),
          searchTextbooks(query),
          searchArxiv(query),
          searchWikipedia(query)
        ])

        setResults([...formattedInternal, ...textbookData, ...githubData, ...arxivData, ...wikiData])
      } catch (err) {
        console.error('Search failed:', err)
        setError('Failed to fetch search results. Please try again.')
      } finally {
        setLoading(false)
      }
    }

    fetchResults()
  }, [query])

  const filteredResults = results.filter(res => {
    if (activeFilter === 'All') return true
    return res.type === activeFilter
  })

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem', maxWidth: '1200px', margin: '0 auto', width: '100%' }}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        <div>
          <h1 style={{ marginBottom: '0.5rem', fontSize: '2.5rem' }}>
            {query ? `Results for "${query}"` : 'Library Search'}
          </h1>
          <p className="text-secondary" style={{ fontSize: '1.125rem' }}>
            {query ? `Found ${results.length} resources across NoteVault, GitHub, and Open Library.` : 'Enter a query in the header to discover resources.'}
          </p>
        </div>

        {results.length > 0 && (
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
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '4rem', gap: '1rem', color: 'var(--text-secondary)' }}>
          <Loader2 className="animate-spin" size={28} color="var(--accent-primary)" /> 
          <span style={{ fontSize: '1.125rem' }}>Scanning global resources...</span>
        </div>
      ) : error ? (
        <div style={{ padding: '1rem', background: 'rgba(239, 68, 68, 0.1)', color: '#ef4444', borderRadius: 'var(--radius-sm)' }}>
          {error}
        </div>
      ) : filteredResults.length > 0 ? (
        <div className="grid-cards">
          {filteredResults.map(resource => (
            <ResourceCard key={resource.id} resource={resource} />
          ))}
        </div>
      ) : query ? (
        <EmptyState 
          title="No results found" 
          description={`We couldn't find any ${activeFilter !== 'All' ? filterLabels[activeFilter].toLowerCase() : 'resources'} matching "${query}".`} 
        />
      ) : (
        <div style={{ padding: '4rem 0', textAlign: 'center', opacity: 0.5 }}>
          <p>Search for a topic to start discovering.</p>
        </div>
      )}
    </div>
  )
}
