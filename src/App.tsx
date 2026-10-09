import React, { useState } from 'react';
import { Resource, ScreenType } from './types';
import { INITIAL_RESOURCES, WORKSPACES } from './data/mockData';
import { Header } from './components/Header';
import { BottomNav } from './components/BottomNav';
import { FlashcardQuizModal } from './components/FlashcardQuizModal';
import { TestSolutionModal } from './components/TestSolutionModal';
import { AiSolverDrawer } from './components/AiSolverDrawer';
import { WorkspaceModal } from './components/WorkspaceModal';
import { ResourceDetailModal } from './components/ResourceDetailModal';
import { PyqDrillModal } from './components/PyqDrillModal';
import { DashboardView } from './views/DashboardView';
import { SubjectView } from './views/SubjectView';
import { DocumentReaderView } from './views/DocumentReaderView';
import { LibraryView } from './views/LibraryView';
import { AddResourceView } from './views/AddResourceView';
import { SavedView } from './views/SavedView';
import { ProfileView } from './views/ProfileView';

export default function App() {
  const [currentScreen, setCurrentScreen] = useState<ScreenType>('dashboard');
  const [resources, setResources] = useState<Resource[]>(INITIAL_RESOURCES);
  const [activeSubject, setActiveSubject] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [activeWorkspace, setActiveWorkspace] = useState(WORKSPACES[0]);

  // Modals & Drawers state
  const [selectedResource, setSelectedResource] = useState<Resource | null>(null);
  const [isFlashcardsOpen, setIsFlashcardsOpen] = useState(false);
  const [isTestSolutionOpen, setIsTestSolutionOpen] = useState(false);
  const [isAiSolverOpen, setIsAiSolverOpen] = useState(false);
  const [isWorkspaceModalOpen, setIsWorkspaceModalOpen] = useState(false);
  const [isPyqDrillOpen, setIsPyqDrillOpen] = useState(false);

  // Toast feedback state
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => {
      setToastMessage(null);
    }, 2400);
  };

  const handleToggleSave = (id: string) => {
    setResources((prev) =>
      prev.map((item) => {
        if (item.id === id) {
          const nextSaved = !item.saved;
          showToast(nextSaved ? `Pinned "${item.title}" to Saved Vault` : `Removed "${item.title}" from Saved Vault`);
          return { ...item, saved: nextSaved };
        }
        return item;
      })
    );
  };

  const handleSaveNewResource = (newRes: Resource) => {
    setResources((prev) => [newRes, ...prev]);
    setCurrentScreen('dashboard');
    showToast(`Added "${newRes.title}" to ${activeWorkspace.shortName}`);
  };

  return (
    <div className="min-h-screen bg-[#F7F5F0] text-[#131c2a] flex flex-col font-body selection:bg-[#3f4dbf]/20">
      {/* Global Navigation Header (hidden when in deep document reading mode) */}
      {currentScreen !== 'reader' && (
        <Header
          currentScreen={currentScreen}
          workspaceName={activeWorkspace.shortName}
          onOpenWorkspaceModal={() => setIsWorkspaceModalOpen(true)}
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
          onSelectScreen={setCurrentScreen}
          onShowToast={showToast}
        />
      )}

      {/* Main Screen Container */}
      <main className={`flex-1 w-full max-w-lg mx-auto px-4 ${currentScreen === 'reader' ? 'pt-4' : 'pt-20'} pb-24`}>
        {currentScreen === 'dashboard' && (
          <DashboardView
            resources={resources}
            activeSubject={activeSubject}
            onSelectResource={(res) => setSelectedResource(res)}
            onToggleSave={handleToggleSave}
            onOpenFlashcards={() => setIsFlashcardsOpen(true)}
            onOpenDrill={() => setIsPyqDrillOpen(true)}
            onOpenAiSolver={() => setIsAiSolverOpen(true)}
            onSelectSubject={(subj) => {
              setActiveSubject(subj);
              if (subj === 'CS204') {
                setCurrentScreen('collections');
              } else {
                showToast(`Filtered to ${subj}`);
              }
            }}
            onSelectScreen={setCurrentScreen}
            onShowToast={showToast}
          />
        )}

        {currentScreen === 'collections' && (
          <SubjectView
            resources={resources}
            onSelectResource={(res) => setSelectedResource(res)}
            onToggleSave={handleToggleSave}
            onOpenReader={() => setCurrentScreen('reader')}
            onOpenAddModal={() => setCurrentScreen('add')}
            onSelectScreen={setCurrentScreen}
            onShowToast={showToast}
          />
        )}

        {currentScreen === 'reader' && (
          <DocumentReaderView
            onBack={() => setCurrentScreen('collections')}
            onOpenTestModal={() => setIsTestSolutionOpen(true)}
            onShowToast={showToast}
          />
        )}

        {currentScreen === 'library' && (
          <LibraryView
            resources={resources}
            searchQuery={searchQuery}
            onSearchChange={setSearchQuery}
            onSelectResource={(res) => setSelectedResource(res)}
            onToggleSave={handleToggleSave}
            onOpenFlashcards={() => setIsFlashcardsOpen(true)}
            onShowToast={showToast}
          />
        )}

        {currentScreen === 'add' && (
          <AddResourceView
            onCancel={() => setCurrentScreen('dashboard')}
            onSaveResource={handleSaveNewResource}
            onShowToast={showToast}
          />
        )}

        {currentScreen === 'saved' && (
          <SavedView
            resources={resources}
            onSelectResource={(res) => setSelectedResource(res)}
            onToggleSave={handleToggleSave}
            onOpenReader={() => setCurrentScreen('reader')}
            onShowToast={showToast}
          />
        )}

        {currentScreen === 'profile' && (
          <ProfileView
            onSelectScreen={setCurrentScreen}
            onOpenWorkspaceModal={() => setIsWorkspaceModalOpen(true)}
            onOpenFlashcards={() => setIsFlashcardsOpen(true)}
            onShowToast={showToast}
          />
        )}
      </main>

      {/* Global Bottom Navigation (hidden when in deep document reading mode) */}
      {currentScreen !== 'reader' && (
        <BottomNav
          currentScreen={currentScreen}
          onSelectScreen={(scr) => {
            setCurrentScreen(scr);
            window.scrollTo({ top: 0, behavior: 'smooth' });
          }}
        />
      )}

      {/* Interactive 3D Flashcard Quiz Modal */}
      <FlashcardQuizModal
        isOpen={isFlashcardsOpen}
        onClose={() => setIsFlashcardsOpen(false)}
        onShowToast={showToast}
      />

      {/* Test Question 7 Solution Modal */}
      <TestSolutionModal
        isOpen={isTestSolutionOpen}
        onClose={() => setIsTestSolutionOpen(false)}
        onShowToast={showToast}
      />

      {/* AI Mathematical Proof Drawer */}
      <AiSolverDrawer
        isOpen={isAiSolverOpen}
        onClose={() => setIsAiSolverOpen(false)}
        onShowToast={showToast}
      />

      {/* Workspace Switcher Modal */}
      <WorkspaceModal
        isOpen={isWorkspaceModalOpen}
        activeId={activeWorkspace.id}
        onSelect={(ws) => {
          setActiveWorkspace(ws);
          showToast(`Switched workspace to: ${ws.shortName}`);
        }}
        onClose={() => setIsWorkspaceModalOpen(false)}
      />

      {/* Resource Detail Sheet */}
      <ResourceDetailModal
        resource={selectedResource}
        isOpen={!!selectedResource}
        onClose={() => setSelectedResource(null)}
        onToggleSave={handleToggleSave}
        onOpenReader={(res) => {
          setSelectedResource(null);
          if (res.type === 'pyq') {
            setCurrentScreen('reader');
          } else {
            showToast(`Opening "${res.title}"...`);
          }
        }}
        onShowToast={showToast}
      />

      {/* Timed PYQ Examination Drill Modal */}
      <PyqDrillModal
        isOpen={isPyqDrillOpen}
        onClose={() => setIsPyqDrillOpen(false)}
        onShowToast={showToast}
      />

      {/* Toast Feedback Notification Banner */}
      {toastMessage && (
        <div className="fixed bottom-20 left-1/2 -translate-x-1/2 z-50 flex items-center gap-2 px-4 py-2.5 rounded-full bg-[#202938] text-white shadow-xl text-xs font-semibold animate-slideUp">
          <span className="material-symbols-outlined text-[18px] text-emerald-400">check_circle</span>
          <span>{toastMessage}</span>
        </div>
      )}
    </div>
  );
}
