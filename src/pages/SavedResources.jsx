import { useState, useEffect } from 'react'
import { supabase } from '../lib/supabase'
import { ResourceCard } from '../components/ui/ResourceCard'
import { EmptyState } from '../components/ui/EmptyState'
import { useAuth } from '../contexts/AuthContext'

export default function SavedResources() {
  const { user } = useAuth()
  const [savedResources, setSavedResources] = useState([])
  const [loading, setLoading] = useState(true)

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

  return (
    <div>
      <div style={{ marginBottom: '2rem' }}>
        <h1>Saved Resources</h1>
        <p className="text-secondary">Your personal collection of bookmarked materials.</p>
      </div>

      {loading ? (
        <div className="text-secondary">Loading saved resources...</div>
      ) : savedResources.length > 0 ? (
        <div className="grid-cards">
          {savedResources.map(resource => (
            <ResourceCard key={resource.id} resource={resource} />
          ))}
        </div>
      ) : (
        <EmptyState 
          title="No saved resources yet" 
          description="Browse the library and click the bookmark icon to save resources here." 
        />
      )}
    </div>
  )
}
