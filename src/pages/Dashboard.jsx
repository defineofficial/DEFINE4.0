import { MOCK_RESOURCES, MOCK_SUBJECTS } from '../data/mockData'
import { ResourceCard } from '../components/ui/ResourceCard'
import { SubjectCard } from '../components/ui/SubjectCard'

export default function Dashboard() {
  const recentResources = MOCK_RESOURCES.slice(0, 3);
  const featuredSubjects = MOCK_SUBJECTS.slice(0, 3);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '3rem' }}>
      <div>
        <h1 style={{ marginBottom: '0.5rem' }}>Welcome back, Student!</h1>
        <p className="text-secondary">Here's an overview of your learning resources.</p>
      </div>

      <section>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
          <h2>Continue Learning</h2>
        </div>
        <div className="grid-cards">
          {recentResources.map(resource => (
            <ResourceCard key={resource.id} resource={resource} />
          ))}
        </div>
      </section>

      <section>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
          <h2>Your Subjects</h2>
        </div>
        <div className="grid-cards">
          {featuredSubjects.map(subject => (
            <SubjectCard key={subject.id} subject={subject} />
          ))}
        </div>
      </section>
    </div>
  )
}
