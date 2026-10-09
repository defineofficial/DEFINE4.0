import { MOCK_RESOURCES } from '../data/mockData'
import { ResourceCard } from '../components/ui/ResourceCard'
import { EmptyState } from '../components/ui/EmptyState'

export default function SavedResources() {
  const savedResources = MOCK_RESOURCES.filter(r => r.isSaved)

  return (
    <div>
      <div style={{ marginBottom: '2rem' }}>
        <h1>Saved Resources</h1>
        <p className="text-secondary">Your personal collection of bookmarked materials.</p>
      </div>

      {savedResources.length > 0 ? (
        <div className="grid-cards">
          {savedResources.map(resource => (
            <ResourceCard key={resource.id} resource={resource} />
          ))}
        </div>
      ) : (
        <EmptyState 
          title="No saved resources" 
          description="You haven't bookmarked any resources yet. Click the bookmark icon on any resource card to save it here." 
        />
      )}
    </div>
  )
}
