import React, { useState } from 'react';
import { FLASHCARD_DATA } from '../data/mockData';
import { Flashcard } from '../types';

interface FlashcardQuizModalProps {
  isOpen: boolean;
  onClose: () => void;
  onShowToast: (msg: string) => void;
}

export const FlashcardQuizModal: React.FC<FlashcardQuizModalProps> = ({
  isOpen,
  onClose,
  onShowToast
}) => {
  const [deck, setDeck] = useState<Flashcard[]>([...FLASHCARD_DATA]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);
  const [showingHint, setShowingHint] = useState(false);
  const [ratings, setRatings] = useState({ hard: 0, good: 0, easy: 0 });
  const [isComplete, setIsComplete] = useState(false);

  if (!isOpen) return null;

  const currentCard = deck[currentIndex];
  const total = deck.length;

  const handleCardFlip = () => {
    setIsFlipped(!isFlipped);
  };

  const handleRating = (rating: 'hard' | 'good' | 'easy') => {
    setRatings(prev => ({ ...prev, [rating]: prev[rating] + 1 }));
    
    const feedbackMap = {
      hard: 'Marked as Hard. Queued for recall!',
      good: 'Marked Good. Retained in working memory.',
      easy: 'Mastered! Excellent algorithmic depth.'
    };
    onShowToast(feedbackMap[rating]);

    setTimeout(() => {
      if (currentIndex < total - 1) {
        setCurrentIndex(prev => prev + 1);
        setIsFlipped(false);
        setShowingHint(false);
      } else {
        setIsComplete(true);
      }
    }, 180);
  };

  const handleShuffle = () => {
    const shuffled = [...deck];
    for (let i = shuffled.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
    }
    setDeck(shuffled);
    setCurrentIndex(0);
    setIsFlipped(false);
    setShowingHint(false);
    setIsComplete(false);
    onShowToast('Deck shuffled! Random order applied.');
  };

  const handleReset = () => {
    setCurrentIndex(0);
    setIsFlipped(false);
    setShowingHint(false);
    setRatings({ hard: 0, good: 0, easy: 0 });
    setIsComplete(false);
    onShowToast('Quiz reset to Card 1.');
  };

  const currentStep = currentIndex + 1;
  const progressPct = Math.round((currentStep / total) * 100);

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-[#131c2a]/65 backdrop-blur-md transition-opacity"
        onClick={onClose}
      />

      {/* Modal Container */}
      <div className="relative z-10 w-full max-w-lg bg-[#F7F5F0] rounded-t-[32px] sm:rounded-3xl max-h-[92vh] flex flex-col overflow-hidden shadow-2xl border-t sm:border border-white/40">
        {/* Handle bar on mobile */}
        <div className="w-12 h-1.5 rounded-full bg-gray-300 mx-auto mt-3 mb-1 flex-shrink-0 sm:hidden" />

        {/* Header */}
        <div className="px-5 pt-2 pb-3 flex items-center justify-between border-b border-black/[0.05] bg-white/70 backdrop-blur-md flex-shrink-0">
          <div className="flex flex-col">
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full bg-[#E5EEE6] text-[#243B29] font-label-sm text-[11px] font-bold uppercase tracking-wider border border-[#d2ded3]">
                CS204 · Graphs
              </span>
              <span className="text-[11px] font-semibold text-[#3f4dbf] flex items-center gap-1">
                <span className="material-symbols-outlined text-[14px]">psychology</span>
                <span>{ratings.easy}/{total} Mastered</span>
              </span>
            </div>
            <h3 className="font-headline text-lg text-[#131c2a] font-bold mt-1">
              DSA Quick Recall Sprint
            </h3>
          </div>

          <div className="flex items-center gap-1.5">
            <button
              onClick={handleShuffle}
              className="w-9 h-9 rounded-full bg-white border border-black/[0.08] flex items-center justify-center text-[#58605a] hover:text-[#131c2a] active-haptic"
              title="Shuffle Deck"
            >
              <span className="material-symbols-outlined text-[18px]">shuffle</span>
            </button>
            <button
              onClick={onClose}
              className="w-9 h-9 rounded-full bg-white border border-black/[0.08] flex items-center justify-center text-[#58605a] hover:text-[#131c2a] active-haptic"
            >
              <span className="material-symbols-outlined text-[20px]">close</span>
            </button>
          </div>
        </div>

        {/* Progress Bar & Step Tracker */}
        {!isComplete && (
          <div className="px-5 py-2.5 bg-white/40 flex items-center justify-between border-b border-black/[0.03] flex-shrink-0">
            <div className="flex items-center gap-2 flex-1 mr-4">
              <div className="flex-1 bg-black/10 h-2 rounded-full overflow-hidden">
                <div
                  className="bg-[#3f4dbf] h-full rounded-full transition-all duration-300"
                  style={{ width: `${progressPct}%` }}
                />
              </div>
            </div>
            <span className="font-label-md text-xs font-bold text-[#131c2a] flex-shrink-0">
              Card {currentStep} of {total}
            </span>
          </div>
        )}

        {/* Main Body */}
        {!isComplete ? (
          <div className="flex-1 overflow-y-auto px-5 py-4 flex flex-col justify-between">
            {/* 3D Perspective Card Container */}
            <div
              className="perspective-1000 w-full min-h-[340px] my-auto cursor-pointer"
              onClick={handleCardFlip}
            >
              <div className={`flashcard-inner relative w-full h-[340px] rounded-2xl shadow-md ${isFlipped ? 'flipped' : ''}`}>
                {/* CARD FRONT (QUESTION) */}
                <div className="flashcard-face absolute inset-0 w-full h-full bg-white rounded-2xl p-5 border border-black/[0.06] flex flex-col justify-between select-none">
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <span className="px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider bg-[#dfe0ff] text-[#000a64]">
                        {currentCard.badge}
                      </span>
                      <span className="text-xs font-semibold text-[#58605a] flex items-center gap-1">
                        <span className="material-symbols-outlined text-[15px]">touch_app</span>
                        Tap to flip
                      </span>
                    </div>
                    <p className="text-xs uppercase tracking-wider text-[#58605a] font-bold">
                      {currentCard.topic}
                    </p>
                    <h4 className="font-headline text-lg sm:text-xl text-[#131c2a] font-semibold mt-2 leading-snug">
                      {currentCard.question}
                    </h4>
                  </div>

                  {/* Hint Toggle */}
                  <div className="mt-4 pt-3 border-t border-black/[0.05]">
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-[#58605a] font-medium">Need a clue before answering?</span>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setShowingHint(!showingHint);
                        }}
                        className="px-2.5 py-1 rounded-lg bg-[#F7F5F0] hover:bg-[#dfe8fd] text-[#3f4dbf] text-xs font-bold flex items-center gap-1 active-haptic transition-colors"
                      >
                        <span className="material-symbols-outlined text-[15px]">lightbulb</span>
                        <span>{showingHint ? 'Hide Hint' : 'Show Hint'}</span>
                      </button>
                    </div>

                    {showingHint && (
                      <div className="mt-2 p-2.5 rounded-xl bg-[#F0F3FF] border border-[#3f4dbf]/20 text-xs text-[#131c2a] leading-relaxed animate-fadeIn">
                        {currentCard.hint}
                      </div>
                    )}
                  </div>

                  <div className="mt-2 flex items-center justify-center gap-1.5 text-[#58605a] text-xs font-medium">
                    <span className="material-symbols-outlined text-[16px] text-[#3f4dbf]">sync</span>
                    <span>Tap card or press button below to reveal answer</span>
                  </div>
                </div>

                {/* CARD BACK (ANSWER) */}
                <div className="flashcard-face flashcard-back absolute inset-0 w-full h-full bg-[#1e2736] text-white rounded-2xl p-5 border border-white/10 flex flex-col justify-between select-none">
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                        Verified Solution
                      </span>
                      <span className="text-xs text-[#bcc2ff] font-mono bg-white/10 px-2 py-0.5 rounded">
                        {currentCard.complexity}
                      </span>
                    </div>

                    <h4 className="font-headline text-base sm:text-lg text-white font-bold leading-snug">
                      {currentCard.answerTitle}
                    </h4>

                    <div className="mt-2 text-xs sm:text-sm text-gray-200 space-y-1.5 leading-relaxed">
                      {currentCard.details.map((detail, idx) => (
                        <p key={idx}>{detail}</p>
                      ))}
                    </div>
                  </div>

                  {/* Formula Snippet */}
                  <div className="mt-2 p-2.5 rounded-xl bg-black/30 border border-white/10 font-mono text-[11px] text-[#bcc2ff]">
                    {currentCard.formula}
                  </div>

                  <div className="mt-1 flex items-center justify-center gap-1.5 text-gray-400 text-xs">
                    <span className="material-symbols-outlined text-[15px]">360</span>
                    <span>Tap card to return to question</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Rating / Spaced Repetition Controls */}
            <div className="mt-4 pt-3 border-t border-black/[0.06] flex flex-col gap-2.5 flex-shrink-0">
              <div className="flex items-center justify-between text-xs text-[#58605a] font-semibold px-1">
                <span>Rate your recall to schedule next review:</span>
                <button
                  onClick={handleCardFlip}
                  className="text-[#3f4dbf] hover:underline flex items-center gap-1 active-haptic"
                >
                  <span className="material-symbols-outlined text-[15px]">swap_horiz</span>
                  <span>{isFlipped ? 'Show Question' : 'Reveal Answer'}</span>
                </button>
              </div>

              {/* 3 Repetition Choices */}
              <div className="grid grid-cols-3 gap-2">
                <button
                  onClick={() => handleRating('hard')}
                  className="flex flex-col items-center justify-center py-2 px-1 rounded-xl bg-red-50 hover:bg-red-100 border border-red-200 text-[#ba1a1a] active-haptic transition-all"
                >
                  <span className="material-symbols-outlined text-[18px]">sentiment_very_dissatisfied</span>
                  <span className="font-label-md text-xs font-bold mt-0.5">Again / Hard</span>
                  <span className="text-[10px] text-[#58605a] font-normal">&lt; 10 min</span>
                </button>

                <button
                  onClick={() => handleRating('good')}
                  className="flex flex-col items-center justify-center py-2 px-1 rounded-xl bg-amber-50 hover:bg-amber-100 border border-amber-200 text-amber-700 active-haptic transition-all"
                >
                  <span className="material-symbols-outlined text-[18px]">sentiment_satisfied</span>
                  <span className="font-label-md text-xs font-bold mt-0.5">Good</span>
                  <span className="text-[10px] text-[#58605a] font-normal">1 day</span>
                </button>

                <button
                  onClick={() => handleRating('easy')}
                  className="flex flex-col items-center justify-center py-2 px-1 rounded-xl bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 text-emerald-700 active-haptic transition-all"
                >
                  <span className="material-symbols-outlined text-[18px]">sentiment_very_satisfied</span>
                  <span className="font-label-md text-xs font-bold mt-0.5">Mastered</span>
                  <span className="text-[10px] text-[#58605a] font-normal">4 days</span>
                </button>
              </div>

              {/* Step Navigation Arrows */}
              <div className="flex items-center justify-between pt-1">
                <button
                  disabled={currentIndex === 0}
                  onClick={() => {
                    setCurrentIndex(prev => Math.max(0, prev - 1));
                    setIsFlipped(false);
                    setShowingHint(false);
                  }}
                  className="px-3 py-1.5 rounded-xl border border-black/[0.1] bg-white text-[#131c2a] text-xs font-semibold flex items-center gap-1 active-haptic disabled:opacity-40"
                >
                  <span className="material-symbols-outlined text-[16px]">chevron_left</span>
                  <span>Previous</span>
                </button>

                <button
                  onClick={handleReset}
                  className="text-[#58605a] hover:text-[#131c2a] text-xs font-semibold active-haptic"
                >
                  Restart Deck
                </button>

                <button
                  onClick={() => {
                    if (currentIndex < total - 1) {
                      setCurrentIndex(prev => prev + 1);
                      setIsFlipped(false);
                      setShowingHint(false);
                    } else {
                      setIsComplete(true);
                    }
                  }}
                  className="px-3.5 py-1.5 rounded-xl bg-[#3f4dbf] text-white text-xs font-semibold flex items-center gap-1 active-haptic shadow-sm"
                >
                  <span>Next</span>
                  <span className="material-symbols-outlined text-[16px]">chevron_right</span>
                </button>
              </div>
            </div>
          </div>
        ) : (
          /* Completion Screen */
          <div className="flex-1 overflow-y-auto px-5 py-6 flex flex-col items-center justify-center text-center">
            <div className="w-20 h-20 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center shadow-inner mb-3">
              <span className="material-symbols-outlined text-4xl">workspace_premium</span>
            </div>
            <span className="px-3 py-1 rounded-full bg-emerald-50 text-emerald-700 font-label-sm text-xs font-bold uppercase tracking-wider mb-2">
              Drill Complete
            </span>
            <h3 className="font-headline text-2xl text-[#131c2a] font-bold">
              {total}/{total} Cards Reviewed!
            </h3>
            <p className="font-body text-sm text-[#58605a] mt-1 max-w-xs">
              Great session! You reviewed all {total} core algorithm cards. Estimated retention index is {Math.min(95, Math.max(70, Math.round(((ratings.easy * 1 + ratings.good * 0.7) / total) * 100)))}%.
            </p>

            {/* Score Breakdown */}
            <div className="w-full bg-white rounded-2xl p-4 shadow-sm border border-black/[0.05] mt-5 grid grid-cols-3 gap-2">
              <div className="p-2.5 rounded-xl bg-[#F7F5F0]">
                <span className="text-xl font-bold text-emerald-600">{ratings.easy}</span>
                <p className="text-[10px] text-[#58605a] uppercase font-semibold mt-0.5">Mastered</p>
              </div>
              <div className="p-2.5 rounded-xl bg-[#F7F5F0]">
                <span className="text-xl font-bold text-amber-600">{ratings.good}</span>
                <p className="text-[10px] text-[#58605a] uppercase font-semibold mt-0.5">Good</p>
              </div>
              <div className="p-2.5 rounded-xl bg-[#F7F5F0]">
                <span className="text-xl font-bold text-[#ba1a1a]">{ratings.hard}</span>
                <p className="text-[10px] text-[#58605a] uppercase font-semibold mt-0.5">Again / Hard</p>
              </div>
            </div>

            {/* Recommendation */}
            <div className="w-full bg-[#dfe0ff]/50 rounded-xl p-3 text-left mt-4 border border-[#3f4dbf]/20">
              <div className="flex items-center gap-1.5 text-[#000a64] text-xs font-bold">
                <span className="material-symbols-outlined text-[16px]">psychology_alt</span>
                <span>Spaced Repetition Schedule</span>
              </div>
              <p className="text-xs text-[#58605a] mt-1">
                Cards marked <em>Again/Hard</em> will re-appear tomorrow before your DSA Exam on 18 Oct.
              </p>
            </div>

            <div className="w-full mt-6 space-y-2">
              <button
                onClick={handleReset}
                className="w-full py-3 rounded-xl bg-[#3f4dbf] text-white font-label-lg font-bold flex items-center justify-center gap-2 active-haptic shadow-md"
              >
                <span className="material-symbols-outlined text-[18px]">replay</span>
                <span>Practice Deck Again</span>
              </button>
              <button
                onClick={onClose}
                className="w-full py-2.5 rounded-xl bg-white border border-black/[0.1] text-[#131c2a] text-sm font-semibold active-haptic"
              >
                Return to Dashboard
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
