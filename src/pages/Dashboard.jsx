import { useState, useEffect } from 'react'
import { supabase } from '../lib/supabase'
import { ResourceCard } from '../components/ui/ResourceCard'
import { SubjectCard } from '../components/ui/SubjectCard'

export default function Dashboard() {
  const [recentResources, setRecentResources] = useState([])
  const [featuredSubjects, setFeaturedSubjects] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchDashboardData = async () => {
      const { data: resourcesResponse } = await supabase
        .from('resources')
        .select('*, saved_resources(id)')
        .order('created_at', { ascending: false })
        .limit(6)

      if (resourcesResponse) {
        const formattedRes = resourcesResponse.map(res => ({
          ...res,
          author: res.author_name,
          createdAt: res.created_at,
          isSaved: res.saved_resources && res.saved_resources.length > 0
        }))
        setRecentResources(formattedRes)
      }
      
      setLoading(false)
    }

    fetchDashboardData()
  }, [])

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '3rem' }}>
      <div>
        <h1 style={{ marginBottom: '0.5rem' }}>Welcome to NoteVault</h1>
        <p className="text-secondary">Discover notes, repos, and books matching your search.</p>
      </div>

      <section>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
          <h2>Recent Additions</h2>
        </div>
        {loading ? (
          <div className="text-secondary">Loading...</div>
        ) : recentResources.length > 0 ? (
          <div className="grid-cards">
            {recentResources.map(resource => (
              <ResourceCard key={resource.id} resource={resource} />
            ))}
          </div>
        ) : (
          <p className="text-secondary">No resources found.</p>
        )}
      </section>
    </div>
  )
}
