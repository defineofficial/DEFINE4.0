import { Link } from 'react-router-dom'
import { BookOpen } from 'lucide-react'
import './Cards.css'

export function SubjectCard({ subject }) {
  return (
    <Link to={`/subjects/${subject.id}`} className="subject-card">
      <div className="subject-code">{subject.code}</div>
      <h3 className="text-primary">{subject.name}</h3>
      <p className="text-secondary text-sm">{subject.description}</p>
      <div className="resource-meta" style={{ marginTop: '1rem' }}>
        <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
          <BookOpen size={14} />
          {subject.resourceCount} Resources
        </span>
      </div>
    </Link>
  )
}
