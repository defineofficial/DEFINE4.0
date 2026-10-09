import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { User, LogOut, Mail, Calendar } from 'lucide-react'
import { EmptyState } from '../components/ui/EmptyState'

export default function Profile() {
  const { user, signOut } = useAuth()
  const navigate = useNavigate()

  const handleSignOut = async () => {
    await signOut()
    navigate('/')
  }

  if (!user) {
    return (
      <EmptyState 
        title="Not signed in" 
        description="Please sign in to view your profile." 
      />
    )
  }

  return (
    <div style={{ maxWidth: '600px', margin: '0 auto' }}>
      <div style={{ marginBottom: '2rem' }}>
        <h1>My Profile</h1>
        <p className="text-secondary">Manage your account and settings.</p>
      </div>

      <div className="glass-panel" style={{ padding: '2rem', borderRadius: 'var(--radius-lg)', display: 'flex', flexDirection: 'column', gap: '2rem' }}>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
          <div style={{ 
            width: '80px', height: '80px', borderRadius: '50%', 
            background: 'var(--accent-primary)', display: 'flex', 
            alignItems: 'center', justifyContent: 'center' 
          }}>
            <User size={40} color="white" />
          </div>
          <div>
            <h2 style={{ marginBottom: '0.25rem' }}>
              {user.user_metadata?.full_name || 'Student'}
            </h2>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-secondary)' }}>
              <Mail size={14} />
              {user.email}
            </div>
          </div>
        </div>

        <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '2rem' }}>
          <h3 style={{ marginBottom: '1rem', fontSize: '1.1rem' }}>Account Details</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-secondary)' }}>
              <Calendar size={16} />
              Joined: {new Date(user.created_at).toLocaleDateString()}
            </div>
          </div>
        </div>

        <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '2rem', display: 'flex', justifyContent: 'flex-end' }}>
          <button onClick={handleSignOut} className="btn btn-ghost" style={{ color: '#ef4444' }}>
            <LogOut size={18} style={{ marginRight: '0.5rem' }} />
            Sign Out
          </button>
        </div>
      </div>
    </div>
  )
}
