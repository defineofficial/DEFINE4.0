import { NavLink } from 'react-router-dom'
import { LayoutDashboard, Library, BookOpen, Bookmark, PlusCircle, BookText } from 'lucide-react'
import './Layout.css'

export default function AppSidebar() {
  const navItems = [
    { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { name: 'Library', path: '/resources', icon: Library },
    { name: 'Saved', path: '/saved', icon: Bookmark },
    { name: 'Docs', path: '/docs', icon: BookText },
  ]

  return (
    <aside className="app-sidebar">
      <div className="sidebar-brand">
        <div className="brand-logo">N</div>
        <h2>NoteVault</h2>
      </div>
      
      <nav className="sidebar-nav">
        {navItems.map((item) => (
          <NavLink 
            key={item.path} 
            to={item.path}
            className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
          >
            <item.icon size={20} />
            <span>{item.name}</span>
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-footer">
        <NavLink to="/resources/new" className="btn btn-primary w-full">
          <PlusCircle size={18} />
          <span>Add Resource</span>
        </NavLink>
      </div>
    </aside>
  )
}
