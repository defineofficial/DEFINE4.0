import { Link } from 'react-router-dom'
import { Bookmark, FileText, Video, Github, BookOpen } from 'lucide-react'
import './Cards.css'

const typeConfig = {
  video: { icon: Video, class: 'badge-video', label: 'Video' },
  pdf: { icon: BookOpen, class: 'badge-pdf', label: 'PDF' },
  note: { icon: FileText, class: 'badge-note', label: 'Note' },
  github: { icon: Github, class: 'badge-github', label: 'GitHub' },
}

export function ResourceCard({ resource }) {
  const config = typeConfig[resource.type] || typeConfig.note
  const Icon = config.icon

  return (
    <div className="resource-card">
      <div className="resource-card-header">
        <div className={`resource-type-badge ${config.class}`}>
          <Icon size={14} />
          {config.label}
        </div>
        <button className={`save-btn ${resource.isSaved ? 'saved' : ''}`} title="Save Resource">
          <Bookmark size={20} fill={resource.isSaved ? "currentColor" : "none"} />
        </button>
      </div>
      
      <Link to={`/resources/${resource.id}`}>
        <h3 className="resource-title">{resource.title}</h3>
      </Link>
      
      <div className="resource-meta">
        <span>By {resource.author}</span>
        <span>{new Date(resource.createdAt).toLocaleDateString()}</span>
      </div>
    </div>
  )
}
