import { useState, useEffect } from 'react'
import { supabase } from '../lib/supabase'
import { SubjectCard } from '../components/ui/SubjectCard'

export default function Subjects() {
  const [subjects, setSubjects] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchSubjects = async () => {
      const { data, error } = await supabase.from('subjects').select('*').order('name')
      if (error) {
        console.error(error)
      } else {
        setSubjects(data)
      }
      setLoading(false)
    }
    fetchSubjects()
  }, [])

  return (
    <div>
      <div style={{ marginBottom: '2rem' }}>
        <h1>Subjects</h1>
        <p className="text-secondary">Explore resources organized by module and topic.</p>
      </div>

      {loading ? (
        <div className="text-secondary">Loading subjects...</div>
      ) : subjects.length > 0 ? (
        <div className="grid-cards">
          {subjects.map(subject => (
            <SubjectCard key={subject.id} subject={subject} />
          ))}
        </div>
      ) : (
        <p className="text-secondary">No subjects available.</p>
      )}
    </div>
  )
}
