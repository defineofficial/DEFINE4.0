import { MOCK_RESOURCES } from '../data/mockData'
import { ResourceCard } from '../components/ui/ResourceCard'
import { EmptyState } from '../components/ui/EmptyState'

export default function ResourceLibrary() {
  return (
    <div>
      <div style={{ marginBottom: '2rem' }}>
        <h1>Resource Library</h1>
        <p className="text-secondary">Browse all notes, videos, and materials.</p>
      </div>

      {MOCK_RESOURCES.length > 0 ? (
        <div className="grid-cards">
          {MOCK_RESOURCES.map(resource => (
            <ResourceCard key={resource.id} resource={resource} />
          ))}
        </div>
      ) : (
        <EmptyState 
          title="No resources found" 
          description="It looks like there are no resources available yet." 
        />
      )}
    </div>
  )
}
