import { useParams, Link } from 'react-router-dom'
import { MOCK_SUBJECTS, MOCK_RESOURCES } from '../data/mockData'
import { ResourceCard } from '../components/ui/ResourceCard'
import { ArrowLeft } from 'lucide-react'

export default function SubjectDetail() {
  const { id } = useParams()
  const subject = MOCK_SUBJECTS.find(s => s.id === id)
  const resources = MOCK_RESOURCES.filter(r => r.subjectId === id)

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
