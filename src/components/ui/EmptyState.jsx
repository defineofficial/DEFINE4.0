import { FileQuestion } from 'lucide-react'

export function EmptyState({ title, description, action }) {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '4rem 2rem',
      textAlign: 'center',
      background: 'var(--bg-secondary)',
      borderRadius: 'var(--radius-lg)',
      border: '1px dashed var(--border-strong)'
    }}>
      <div style={{ 
        width: '64px', height: '64px', 
        borderRadius: '50%', background: 'var(--bg-tertiary)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        marginBottom: '1.5rem', color: 'var(--text-muted)'
      }}>
        <FileQuestion size={32} />
      </div>
      <h3 style={{ marginBottom: '0.5rem' }}>{title}</h3>
      <p className="text-secondary" style={{ marginBottom: '1.5rem', maxWidth: '400px' }}>
        {description}
      </p>
      {action && action}
    </div>
  )
}
