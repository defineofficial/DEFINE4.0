import React, { useState } from 'react';

interface TestSolutionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onShowToast: (msg: string) => void;
}

export const TestSolutionModal: React.FC<TestSolutionModalProps> = ({
  isOpen,
  onClose,
  onShowToast
}) => {
  const [answer, setAnswer] = useState('A, B, C, D, E, F');
  const [status, setStatus] = useState<'idle' | 'checking' | 'correct' | 'incorrect'>('idle');
  const [stepExplanation, setStepExplanation] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleVerify = () => {
    setStatus('checking');
    setTimeout(() => {
      const cleanAns = answer.replace(/\s+/g, '').toUpperCase();
      if (cleanAns.includes('A,B,C,D,E,F') || cleanAns === 'ABCDEF') {
        setStatus('correct');
        setStepExplanation(
          '✓ Vertex discovery order: [A] -> neighbors [B, C] in alphabetical order -> explore B: discovers [D] -> explore C: discovers [E] -> explore D/E: discovers [F]. FIFO Queue state after C is processed: [D, E].'
        );
        onShowToast('Full 10 Marks Awarded! Discovery sequence verified.');
      } else {
        setStatus('incorrect');
        setStepExplanation(
          'Notice that at vertex A, adjacent choices B and C must be visited in strict alphabetical order (B first, then C).'
        );
      }
    }, 600);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-[#283140]/50 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative z-10 bg-white w-full max-w-md rounded-2xl p-5 shadow-2xl space-y-4 border border-black/[0.06]">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-[#3f4dbf] text-[24px]">verified</span>
            <h3 className="font-headline text-lg font-bold text-[#131c2a]">
              Solution Verification: Question 7
            </h3>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center text-[#58605a] hover:text-[#131c2a] active-haptic"
          >
            <span className="material-symbols-outlined text-[18px]">close</span>
          </button>
        </div>

        <p className="font-body text-sm text-[#131c2a] leading-relaxed">
          Enter your BFS discovery order for Figure 7.1 starting from Vertex <strong>A</strong>:
        </p>

        <div className="relative">
          <input
            type="text"
            value={answer}
            onChange={(e) => {
              setAnswer(e.target.value);
              setStatus('idle');
            }}
            placeholder="e.g., A, B, C, D, E, F"
            className="w-full px-4 py-3 rounded-xl bg-[#F0F3FF] text-[#131c2a] font-medium text-sm outline-none focus:bg-white focus:ring-2 focus:ring-[#3f4dbf]/40 shadow-inner"
          />
        </div>

        {/* Feedback box */}
        {status === 'checking' && (
          <div className="p-3 rounded-xl bg-blue-50 text-blue-700 text-xs flex items-center gap-2 animate-pulse">
            <span className="material-symbols-outlined text-[16px] animate-spin">progress_activity</span>
            <span>Simulating BFS traversal and queue states...</span>
          </div>
        )}

        {status === 'correct' && (
          <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs leading-relaxed space-y-1 animate-fadeIn">
            <div className="font-bold flex items-center gap-1 text-emerald-700">
              <span className="material-symbols-outlined text-[16px]">check_circle</span>
              <span>Correct Sequence: A, B, C, D, E, F!</span>
            </div>
            <p>{stepExplanation}</p>
          </div>
        )}

        {status === 'incorrect' && (
          <div className="p-3 rounded-xl bg-red-50 border border-red-200 text-red-800 text-xs leading-relaxed space-y-1 animate-fadeIn">
            <div className="font-bold flex items-center gap-1 text-red-700">
              <span className="material-symbols-outlined text-[16px]">cancel</span>
              <span>Sequence does not match alphabetized BFS.</span>
            </div>
            <p>{stepExplanation}</p>
          </div>
        )}

        {/* Buttons */}
        <div className="flex items-center justify-end gap-2 pt-2">
          <button
            onClick={onClose}
            className="px-4 py-2.5 rounded-xl text-[#58605a] text-xs font-semibold hover:bg-gray-100 active-haptic"
          >
            Cancel
          </button>
          <button
            onClick={handleVerify}
            className={`px-4 py-2.5 rounded-xl text-white text-xs font-bold shadow-sm active-haptic transition-all ${
              status === 'correct' ? 'bg-emerald-600' : 'bg-[#3f4dbf] hover:bg-[#5967d9]'
            }`}
          >
            {status === 'correct' ? 'Done' : 'Verify Traversal'}
          </button>
        </div>
      </div>
    </div>
  );
};
