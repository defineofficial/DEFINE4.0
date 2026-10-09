import { useState, useEffect } from 'react'
import { supabase } from '../lib/supabase'
import { ResourceCard } from '../components/ui/ResourceCard'
import { EmptyState } from '../components/ui/EmptyState'

export default function ResourceLibrary() {
  const [resources, setResources] = useState([])
  const [loading, setLoading] = useState(true)

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
        // Map the saved_resources relationship to a simple boolean for the UI
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

  return (
    <div>
      <div style={{ marginBottom: '2rem' }}>
        <h1>Resource Library</h1>
        <p className="text-secondary">Browse all notes, videos, and materials.</p>
      </div>

      {loading ? (
        <div className="text-secondary">Loading resources...</div>
      ) : resources.length > 0 ? (
        <div className="grid-cards">
          {resources.map(resource => (
            <ResourceCard key={resource.id} resource={resource} />
          ))}
        </div>
      ) : (
        <EmptyState 
          title="No resources found" 
          description="It looks like there are no resources available yet. Be the first to add one!" 
        />
      )}
    </div>
  )
}
