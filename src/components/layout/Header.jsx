import { Search, Bell, User } from 'lucide-react'
import { Link } from 'react-router-dom'
import './Layout.css'

export default function Header() {
  return (
    <header className="app-header">
      <div className="search-bar">
        <Search size={18} className="text-secondary" />
        <input type="text" placeholder="Search notes, subjects, resources..." />
      </div>

      <div className="header-actions">
        <button className="btn btn-ghost" title="Notifications">
          <Bell size={20} />
        </button>
        <Link to="/login" className="avatar" title="User Profile">
          <User size={20} className="text-secondary" />
        </Link>
      </div>
    </header>
  )
}
