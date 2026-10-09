import React, { useState, useEffect } from 'react';

interface PyqDrillModalProps {
  isOpen: boolean;
  onClose: () => void;
  onShowToast: (msg: string) => void;
}

const DRILL_QUESTIONS = [
  {
    id: 1,
    q: 'In a connected undirected graph with 7 vertices and 11 edges, how many edges must be removed to create a spanning tree?',
    options: ['4 edges', '5 edges', '6 edges', '7 edges'],
    correct: 1, // 11 - (7-1) = 11 - 6 = 5 edges
    explanation: 'A spanning tree for V=7 vertices requires exactly V - 1 = 6 edges. Removing 11 - 6 = 5 edges breaks all fundamental cycles without disconnecting the graph.'
  },
  {
    id: 2,
    q: 'What is the tightest time complexity to compute Single-Source Shortest Paths in a Directed Acyclic Graph (DAG) with arbitrary (including negative) weights?',
    options: ['O(V²)', 'O(V + E)', 'O(V · E)', 'O((V + E) log V)'],
    correct: 1, // O(V + E) by topological sorting!
    explanation: 'By performing a topological sort in O(V + E) time, we can relax outgoing edges in topological order in single pass, achieving exact O(V + E) even with negative edge weights!'
  },
  {
    id: 3,
    q: 'Which graph traversal property distinguishes BFS from DFS when visiting unweighted graph vertices from origin s?',
    options: [
      'DFS discovers nodes in non-decreasing order of distance from s',
      'BFS guarantees shortest path in terms of hop count',
      'BFS requires O(1) auxiliary working memory',
      'DFS visits all cross edges before back edges'
    ],
    correct: 1,
    explanation: 'Because BFS processes vertices level-by-level using a FIFO queue, the first time vertex v is dequeued, the discovery path represents the minimum hop path from s.'
  }
];

export const PyqDrillModal: React.FC<PyqDrillModalProps> = ({
  isOpen,
  onClose,
  onShowToast
}) => {
  const [currentQ, setCurrentQ] = useState(0);
  const [selectedAnswers, setSelectedAnswers] = useState<Record<number, number>>({});
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [secondsLeft, setSecondsLeft] = useState(900); // 15:00 mins

  useEffect(() => {
    if (!isOpen || isSubmitted) return;
    const interval = setInterval(() => {
      setSecondsLeft((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);
    return () => clearInterval(interval);
  }, [isOpen, isSubmitted]);

  if (!isOpen) return null;

  const formatTimer = (sec: number) => {
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  const handleSelect = (optionIdx: number) => {
    if (isSubmitted) return;
    setSelectedAnswers({ ...selectedAnswers, [currentQ]: optionIdx });
  };

  const calculateScore = () => {
    let score = 0;
    DRILL_QUESTIONS.forEach((q, idx) => {
      if (selectedAnswers[idx] === q.correct) score++;
    });
    return score;
  };

  const qData = DRILL_QUESTIONS[currentQ];

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-[#283140]/65 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />

      {/* Container */}
      <div className="relative z-10 w-full max-w-lg bg-white rounded-t-[32px] sm:rounded-3xl p-5 shadow-2xl flex flex-col max-h-[90vh] overflow-y-auto border-t border-black/[0.05]">
        <div className="w-12 h-1.5 rounded-full bg-gray-300 mx-auto mb-4 sm:hidden" />

        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-black/[0.05]">
          <div className="flex items-center gap-2">
            <span className="w-8 h-8 rounded-lg bg-[#3f4dbf] text-white flex items-center justify-center">
              <span className="material-symbols-outlined text-[18px]">quiz</span>
            </span>
            <div>
              <h3 className="font-headline text-base font-bold text-[#131c2a]">
                CS204 PYQ Timed Drill
              </h3>
              <p className="text-[11px] text-[#58605a]">University Exam Simulator</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="px-2.5 py-1 rounded-full bg-[#ffdad6] text-[#ba1a1a] text-xs font-mono font-bold flex items-center gap-1">
              <span className="material-symbols-outlined text-[14px]">timer</span>
              <span>{formatTimer(secondsLeft)}</span>
            </span>
            <button
              onClick={onClose}
              className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center text-[#58605a] active-haptic"
            >
              <span className="material-symbols-outlined text-[18px]">close</span>
            </button>
          </div>
        </div>

        {!isSubmitted ? (
          <div className="py-4 space-y-4">
            <div className="flex items-center justify-between text-xs text-[#58605a]">
              <span>Question {currentQ + 1} of {DRILL_QUESTIONS.length}</span>
              <span className="font-semibold text-[#3f4dbf]">5 Marks Each</span>
            </div>

            <h4 className="font-headline text-base font-semibold text-[#131c2a] leading-relaxed">
              {qData.q}
            </h4>

            {/* Options */}
            <div className="space-y-2 pt-1">
              {qData.options.map((opt, idx) => {
                const isChosen = selectedAnswers[currentQ] === idx;
                return (
                  <button
                    key={idx}
                    onClick={() => handleSelect(idx)}
                    className={`w-full p-3 rounded-xl text-left text-xs sm:text-sm font-medium flex items-center gap-3 transition-all active-haptic ${
                      isChosen
                        ? 'bg-[#dfe0ff] text-[#000a64] border border-[#3f4dbf]'
                        : 'bg-[#F7F5F0] hover:bg-gray-100 text-[#131c2a] border border-transparent'
                    }`}
                  >
                    <span
                      className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                        isChosen ? 'bg-[#3f4dbf] text-white' : 'bg-white text-[#58605a]'
                      }`}
                    >
                      {String.fromCharCode(65 + idx)}
                    </span>
                    <span className="flex-1">{opt}</span>
                  </button>
                );
              })}
            </div>

            {/* Stepper Buttons */}
            <div className="flex items-center justify-between pt-4 border-t border-black/[0.05]">
              <button
                disabled={currentQ === 0}
                onClick={() => setCurrentQ((p) => Math.max(0, p - 1))}
                className="px-3 py-2 rounded-xl text-xs font-semibold text-[#58605a] hover:bg-gray-100 disabled:opacity-40"
              >
                Previous
              </button>

              {currentQ < DRILL_QUESTIONS.length - 1 ? (
                <button
                  onClick={() => setCurrentQ((p) => p + 1)}
                  className="px-4 py-2 rounded-xl bg-[#3f4dbf] text-white text-xs font-bold active-haptic shadow-sm"
                >
                  Next Question
                </button>
              ) : (
                <button
                  onClick={() => {
                    setIsSubmitted(true);
                    onShowToast('Drill evaluated! Review your score.');
                  }}
                  className="px-4 py-2 rounded-xl bg-emerald-600 text-white text-xs font-bold active-haptic shadow-sm"
                >
                  Submit Exam Drill
                </button>
              )}
            </div>
          </div>
        ) : (
          /* Results Summary */
          <div className="py-4 space-y-4">
            <div className="text-center p-4 bg-[#F7F5F0] rounded-2xl">
              <span className="text-xs uppercase tracking-wider font-bold text-[#3f4dbf]">
                Exam Readiness Score
              </span>
              <h3 className="text-3xl font-headline font-bold text-[#131c2a] mt-1">
                {calculateScore()} / {DRILL_QUESTIONS.length} Correct
              </h3>
              <p className="text-xs text-[#58605a] mt-1">
                Performance: {Math.round((calculateScore() / DRILL_QUESTIONS.length) * 100)}% (Benchmarked in Top 8% of CS204 students)
              </p>
            </div>

            <div className="space-y-3">
              <h5 className="font-headline text-xs font-bold uppercase text-[#131c2a]">
                Detailed Solutions:
              </h5>
              {DRILL_QUESTIONS.map((q, idx) => {
                const userChoice = selectedAnswers[idx];
                const isCorrect = userChoice === q.correct;
                return (
                  <div key={idx} className="p-3 rounded-xl bg-[#F0F3FF] text-xs space-y-1">
                    <div className="flex items-center justify-between font-bold">
                      <span>Q{idx + 1}: {isCorrect ? '✓ Correct' : '✗ Incorrect'}</span>
                      <span className={isCorrect ? 'text-emerald-700' : 'text-[#ba1a1a]'}>
                        Correct: {String.fromCharCode(65 + q.correct)} ({q.options[q.correct]})
                      </span>
                    </div>
                    <p className="text-[#58605a]">{q.explanation}</p>
                  </div>
                );
              })}
            </div>

            <div className="pt-2 flex gap-2">
              <button
                onClick={() => {
                  setIsSubmitted(false);
                  setCurrentQ(0);
                  setSelectedAnswers({});
                  setSecondsLeft(900);
                }}
                className="flex-1 py-2.5 rounded-xl border border-black/[0.1] text-xs font-bold text-[#131c2a]"
              >
                Retake Drill
              </button>
              <button
                onClick={onClose}
                className="flex-1 py-2.5 rounded-xl bg-[#3f4dbf] text-white text-xs font-bold shadow-sm"
              >
                Back to Dashboard
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
