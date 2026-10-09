import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { supabase } from '../lib/supabase'
import { ResourceCard } from '../components/ui/ResourceCard'
import { ArrowLeft } from 'lucide-react'

export default function SubjectDetail() {
  const { id } = useParams()
  const [subject, setSubject] = useState(null)
  const [resources, setResources] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchSubjectData = async () => {
      const [subjectRes, resourcesRes] = await Promise.all([
        supabase.from('subjects').select('*').eq('id', id).single(),
        supabase.from('resources').select('*, saved_resources(id)').eq('subject_id', id)
      ])

      if (subjectRes.data) setSubject(subjectRes.data)
      if (resourcesRes.data) {
        const formattedRes = resourcesRes.data.map(res => ({
          ...res,
          author: res.author_name,
          createdAt: res.created_at,
          isSaved: res.saved_resources && res.saved_resources.length > 0
        }))
        setResources(formattedRes)
      }
      setLoading(false)
    }

    fetchSubjectData()
  }, [id])

  if (loading) return <div>Loading...</div>
  if (!subject) return <div>Subject not found.</div>

  return (
    <div>
      <Link to="/subjects" className="btn btn-ghost" style={{ marginBottom: '1.5rem', padding: '0.5rem 0' }}>
        <ArrowLeft size={16} /> Back to Subjects
      </Link>
      
      <div style={{ marginBottom: '2rem', padding: '2rem', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-lg)' }}>
        <div style={{ color: 'var(--accent-primary)', fontWeight: 600, marginBottom: '0.5rem' }}>
          {subject.code}
        </div>
        <h1>{subject.name}</h1>
        <p className="text-secondary" style={{ marginTop: '0.5rem', maxWidth: '600px' }}>
          {subject.description}
        </p>
      </div>

      <h2 style={{ marginBottom: '1.5rem' }}>Resources ({resources.length})</h2>
      <div className="grid-cards">
        {resources.map(resource => (
          <ResourceCard key={resource.id} resource={resource} />
        ))}
      </div>
    </div>
  )
}
