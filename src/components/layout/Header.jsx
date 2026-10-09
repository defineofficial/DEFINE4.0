import { Search, Bell, User } from 'lucide-react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import './Layout.css'

export default function Header() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const { user } = useAuth()

  // Keep input synced with URL
  useEffect(() => {
    setQuery(searchParams.get('q') || '')
  }, [searchParams])

  const handleSearch = (e) => {
    e.preventDefault()
    if (query.trim()) {
      navigate(`/search?q=${encodeURIComponent(query)}`)
    }
  }

  return (
    <header className="app-header">
      <form className="search-bar" onSubmit={handleSearch} style={{ margin: 0 }}>
        <Search size={18} className="text-secondary" />
        <input 
          type="text" 
          placeholder="Search notes, github repos, textbooks..." 
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </form>

      <div className="header-actions">
        <button className="btn btn-ghost" title="Notifications">
          <Bell size={20} />
        </button>
        <Link to={user ? "/profile" : "/login"} className="avatar" title="User Profile">
          <User size={20} className="text-secondary" />
        </Link>
      </div>
    </header>
  )
}
