import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { supabase } from '../lib/supabase'
import { searchGithub } from '../lib/providers/githubProvider'
import { searchTextbooks } from '../lib/providers/openLibraryProvider'
import { ResourceCard } from '../components/ui/ResourceCard'
import { EmptyState } from '../components/ui/EmptyState'
import { Loader2 } from 'lucide-react'

export default function SearchResults() {
  const [searchParams] = useSearchParams()
  const query = searchParams.get('q') || ''
  
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

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
        // 1. Fetch internal resources (ilike for case-insensitive partial match)
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

        // 2. Fetch external resources in parallel (GitHub + OpenLibrary)
        const [githubData, textbookData] = await Promise.all([
          searchGithub(query),
          searchTextbooks(query)
        ])

        // 3. Merge and set state (Internal first, then textbooks, then code repos)
        setResults([...formattedInternal, ...textbookData, ...githubData])

      } catch (err) {
        console.error('Search failed:', err)
        setError('Failed to fetch search results. Please try again.')
      } finally {
        setLoading(false)
      }
    }

    fetchResults()
  }, [query])

  return (
    <div>
      <div style={{ marginBottom: '2rem' }}>
        <h1>Search Results</h1>
        <p className="text-secondary">
          {query ? `Showing results for "${query}" across NoteVault and GitHub.` : 'Enter a query in the header to discover resources.'}
        </p>
      </div>

      {loading ? (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-secondary)' }}>
          <Loader2 className="animate-spin" size={20} /> Fetching discovery results...
        </div>
      ) : error ? (
        <div style={{ padding: '1rem', background: 'rgba(239, 68, 68, 0.1)', color: '#ef4444', borderRadius: 'var(--radius-sm)' }}>
          {error}
        </div>
      ) : results.length > 0 ? (
        <div className="grid-cards">
          {results.map(resource => (
            <ResourceCard key={resource.id} resource={resource} />
          ))}
        </div>
      ) : (
        <EmptyState 
          title="No results found" 
          description={`We couldn't find anything matching "${query}". Try different keywords.`} 
        />
      )}
    </div>
  )
}
