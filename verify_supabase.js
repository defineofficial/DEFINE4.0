import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';
dotenv.config();

async function checkConnection() {
  console.log('--- STARTING SUPABASE CHECKER ---');
  
  if (!process.env.VITE_SUPABASE_URL || !process.env.VITE_SUPABASE_ANON_KEY) {
    console.log('❌ ERROR: Missing URL or Anon Key in .env file!');
    return;
  }
  
  console.log('✅ Keys found in .env');
  console.log(`URL: ${process.env.VITE_SUPABASE_URL}`);
  
  const supabase = createClient(process.env.VITE_SUPABASE_URL, process.env.VITE_SUPABASE_ANON_KEY);
  
  try {
    console.log('Testing connection to subjects table...');
    const { data, error } = await supabase.from('subjects').select('*').limit(1);
    
    if (error) {
      console.log('❌ ERROR connecting to database:', error.message);
      if (error.code === '42P01') {
         console.log('👉 FIX: The "subjects" table does not exist. You need to run the SQL schema in Supabase!');
      }
    } else {
      console.log('✅ SUCCESS: Database connected and subjects table exists!');
      console.log(`Found ${data.length} subjects in the table.`);
      if (data.length === 0) {
        console.log('⚠️ WARNING: The subjects table is empty. You need to insert the Engineering subjects.');
      }
    }
  } catch (err) {
    console.log('❌ FATAL ERROR:', err.message);
  }
}

checkConnection();
