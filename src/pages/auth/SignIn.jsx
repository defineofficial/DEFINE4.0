import { Link } from 'react-router-dom'

export default function SignIn() {
  const handleSubmit = (e) => {
    e.preventDefault()
    window.location.href = '/dashboard'
  }

  return (
    <div style={{ display: 'flex', height: '100vh', alignItems: 'center', justifyContent: 'center', padding: '2rem' }}>
      <div className="glass-panel" style={{ width: '100%', maxWidth: '400px', padding: '2.5rem', borderRadius: 'var(--radius-lg)' }}>
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <div style={{ width: '48px', height: '48px', background: 'var(--accent-primary)', borderRadius: 'var(--radius-sm)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.5rem', fontWeight: 700, margin: '0 auto 1rem' }}>
            N
          </div>
          <h2>Welcome to NoteVault</h2>
          <p className="text-secondary" style={{ marginTop: '0.5rem' }}>Sign in to access your resources</p>
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <label htmlFor="email">Email</label>
            <input type="email" id="email" placeholder="you@example.com" required />
          </div>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <label htmlFor="password">Password</label>
              <a href="#" className="text-sm" style={{ color: 'var(--accent-primary)' }}>Forgot password?</a>
            </div>
            <input type="password" id="password" placeholder="••••••••" required />
          </div>

          <button type="submit" className="btn btn-primary" style={{ marginTop: '0.5rem', width: '100%' }}>
            Sign In
          </button>
        </form>

        <p className="text-secondary text-sm" style={{ textAlign: 'center', marginTop: '2rem' }}>
          Don't have an account? <Link to="/register" style={{ color: 'var(--accent-primary)', fontWeight: 500 }}>Sign up</Link>
        </p>
      </div>
    </div>
  )
}
