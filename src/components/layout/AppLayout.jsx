import { Outlet } from 'react-router-dom'
import AppSidebar from './AppSidebar'
import Header from './Header'

export default function AppLayout() {
  return (
    <div className="app-layout">
      <AppSidebar />
      <main className="main-content">
        <Header />
        <div className="scroll-area">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
