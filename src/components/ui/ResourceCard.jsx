import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Bookmark, FileText, Video, Github, Book, Link as LinkIcon, HelpCircle } from 'lucide-react'
import { supabase } from '../../lib/supabase'
import { useAuth } from '../../contexts/AuthContext'
import './Cards.css'

export function ResourceCard({ resource }) {
  const { user } = useAuth()
  const [isSaved, setIsSaved] = useState(resource.isSaved)

  const toggleSave = async (e) => {
    e.preventDefault() // prevent routing when clicking the button
    if (!user) return alert('Please sign in to save resources.')

    const previousState = isSaved
    setIsSaved(!isSaved) // Optimistic UI update

    let targetResourceId = resource.id

    try {
      if (resource.isExternal && !previousState) {
        // We are saving a discovery result for the first time. We must import it.
        // 1. Fetch a fallback subject_id since the DB requires it
        const { data: subjects } = await supabase.from('subjects').select('id').limit(1)
        const fallbackSubjectId = subjects?.[0]?.id

        if (!fallbackSubjectId) {
          throw new Error('No subjects found in database to attach resource to.')
        }

        // 2. Insert into resources
        const { data: newResource, error: insertError } = await supabase
          .from('resources')
          .insert({
            title: resource.title,
            type: resource.type,
            url: resource.url,
            description: resource.description,
            author_name: resource.author_name || resource.author || 'Unknown',
            subject_id: fallbackSubjectId,
            user_id: user.id
          })
          .select()
          .single()

        if (insertError) throw insertError
        targetResourceId = newResource.id // Use the new real UUID for bookmarking
        
        // Mutate the local resource object so it's no longer 'external'
        resource.id = targetResourceId
        resource.isExternal = false 
      }

      // Handle the bookmark logic
      if (previousState) {
        await supabase.from('saved_resources').delete().match({ user_id: user.id, resource_id: targetResourceId })
      } else {
        await supabase.from('saved_resources').insert({ user_id: user.id, resource_id: targetResourceId })
      }
    } catch (err) {
      console.error('Failed to save resource:', err)
      setIsSaved(previousState) // Revert UI if failed
      alert('Failed to save resource: ' + err.message)
    }
  }

  const getTypeIcon = (type) => {
    switch (type) {
      case 'video': return <Video size={14} />
      case 'pdf': return <FileText size={14} />
      case 'github': return <Github size={14} />
      case 'note': return <FileText size={14} />
      case 'textbook': return <Book size={14} />
      case 'pyq': return <HelpCircle size={14} />
      default: return <LinkIcon size={14} />
    }
  }

  const isExternalUrl = resource.isExternal

  if (isExternalUrl) {
    return (
      <a href={resource.url} target="_blank" rel="noopener noreferrer" className="card glass-panel" style={{ textDecoration: 'none', color: 'inherit' }} tabIndex="0">
        <div className="card-header">
          <div className={`badge badge-${resource.type || 'note'}`}>
            {getTypeIcon(resource.type)} {resource.type}
          </div>
          <button 
            onClick={toggleSave} 
            className="btn-icon" 
            aria-label={isSaved ? "Unsave resource" : "Save resource"}
            title={isSaved ? "Unsave" : "Save"}
          >
            <Bookmark size={18} fill={isSaved ? "var(--accent-primary)" : "none"} color={isSaved ? "var(--accent-primary)" : "currentColor"} />
          </button>
        </div>
        <div className="card-body">
          <h3>{resource.title}</h3>
          <p className="text-secondary text-sm">
            {resource.author || resource.author_name} • Discovery Result
          </p>
        </div>
      </a>
    )
  }

  return (
    <Link to={`/resources/${resource.id}`} className="card glass-panel" style={{ textDecoration: 'none', color: 'inherit' }} tabIndex="0">
      <div className="card-header">
        <div className={`badge badge-${resource.type || 'note'}`}>
          {getTypeIcon(resource.type)} {resource.type}
        </div>
        <button 
          onClick={toggleSave} 
          className="btn-icon" 
          aria-label={isSaved ? "Unsave resource" : "Save resource"}
          title={isSaved ? "Unsave" : "Save"}
        >
          <Bookmark size={18} fill={isSaved ? "var(--accent-primary)" : "none"} color={isSaved ? "var(--accent-primary)" : "currentColor"} />
        </button>
      </div>
      <div className="card-body">
        <h3>{resource.title}</h3>
        <p className="text-secondary text-sm">
          {resource.author || resource.author_name} • {new Date(resource.createdAt || resource.created_at).toLocaleDateString()}
        </p>
      </div>
    </Link>
  )
}
