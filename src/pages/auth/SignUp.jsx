import { Link } from 'react-router-dom'

export default function SignUp() {
  const handleSubmit = (e) => {
    e.preventDefault()
    window.location.href = '/dashboard'
  }

  return (
    <div style={{ display: 'flex', height: '100vh', alignItems: 'center', justifyContent: 'center', padding: '2rem' }}>
      <div className="glass-panel" style={{ width: '100%', maxWidth: '400px', padding: '2.5rem', borderRadius: 'var(--radius-lg)' }}>
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <h2>Create an Account</h2>
          <p className="text-secondary" style={{ marginTop: '0.5rem' }}>Join NoteVault to start organizing</p>
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <label htmlFor="name">Full Name</label>
            <input type="text" id="name" placeholder="John Doe" required />
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <label htmlFor="email">Email</label>
            <input type="email" id="email" placeholder="you@example.com" required />
          </div>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <label htmlFor="password">Password</label>
            <input type="password" id="password" placeholder="••••••••" required />
          </div>

          <button type="submit" className="btn btn-primary" style={{ marginTop: '0.5rem', width: '100%' }}>
            Sign Up
          </button>
        </form>

        <p className="text-secondary text-sm" style={{ textAlign: 'center', marginTop: '2rem' }}>
          Already have an account? <Link to="/login" style={{ color: 'var(--accent-primary)', fontWeight: 500 }}>Sign in</Link>
        </p>
      </div>
    </div>
  )
}
