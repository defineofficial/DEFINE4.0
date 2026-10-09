import { Routes, Route, Navigate } from 'react-router-dom'
import AppLayout from './components/layout/AppLayout'
import Dashboard from './pages/Dashboard'
import ResourceLibrary from './pages/ResourceLibrary'
import Subjects from './pages/Subjects'
import SubjectDetail from './pages/SubjectDetail'
import AddResource from './pages/AddResource'
import ResourceDetail from './pages/ResourceDetail'
import SavedResources from './pages/SavedResources'
import SignIn from './pages/auth/SignIn'
import SignUp from './pages/auth/SignUp'

function App() {
  return (
    <Routes>
      <Route path="/login" element={<SignIn />} />
      <Route path="/register" element={<SignUp />} />
      
      <Route path="/" element={<AppLayout />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="resources" element={<ResourceLibrary />} />
        <Route path="resources/new" element={<AddResource />} />
        <Route path="resources/:id" element={<ResourceDetail />} />
        <Route path="subjects" element={<Subjects />} />
        <Route path="subjects/:id" element={<SubjectDetail />} />
        <Route path="saved" element={<SavedResources />} />
      </Route>
    </Routes>
  )
}

export default App
