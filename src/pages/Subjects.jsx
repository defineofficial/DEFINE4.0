import { MOCK_SUBJECTS } from '../data/mockData'
import { SubjectCard } from '../components/ui/SubjectCard'

export default function Subjects() {
  return (
    <div>
      <div style={{ marginBottom: '2rem' }}>
        <h1>Subjects</h1>
        <p className="text-secondary">Explore resources organized by module and topic.</p>
      </div>

      <div className="grid-cards">
        {MOCK_SUBJECTS.map(subject => (
          <SubjectCard key={subject.id} subject={subject} />
        ))}
      </div>
    </div>
  )
}
