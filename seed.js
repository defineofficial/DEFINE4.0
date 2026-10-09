import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';
dotenv.config();

const supabase = createClient(process.env.VITE_SUPABASE_URL, process.env.VITE_SUPABASE_ANON_KEY);

async function seedSubjects() {
  console.log('Seeding subjects...');
  const { data, error } = await supabase.from('subjects').insert([
    { name: 'Computer Science', code: 'CS101', description: 'Intro to algorithms and data structures' },
    { name: 'Physics', code: 'PHY201', description: 'Quantum mechanics basics' },
    { name: 'Mathematics', code: 'MATH301', description: 'Linear algebra and calculus' }
  ]).select();

  if (error) {
    console.error('Error inserting subjects:', error);
  } else {
    console.log('Successfully inserted subjects:', data);
  }
}

seedSubjects();
