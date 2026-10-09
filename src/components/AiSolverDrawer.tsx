import React from 'react';

interface AiSolverDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  onShowToast: (msg: string) => void;
}

export const AiSolverDrawer: React.FC<AiSolverDrawerProps> = ({
  isOpen,
  onClose,
  onShowToast
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-[#283140]/60 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />

      {/* Drawer */}
      <div className="relative z-10 w-full max-w-lg bg-white rounded-t-[28px] p-5 shadow-2xl flex flex-col max-h-[85vh] overflow-y-auto animate-slideUp border-t border-black/[0.05]">
        <div className="w-12 h-1.5 rounded-full bg-gray-300 mx-auto mb-3 flex-shrink-0" />

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-[#5967d9] text-[22px]">auto_awesome</span>
            <h3 className="font-headline text-lg font-bold text-[#131c2a]">NoteVault AI Proof Solver</h3>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center text-[#58605a] active-haptic"
          >
            <span className="material-symbols-outlined text-[18px]">close</span>
          </button>
        </div>

        <div className="mt-3 p-3 rounded-xl bg-[#F0F3FF]">
          <span className="text-[11px] font-bold text-[#3f4dbf] uppercase tracking-wider">
            Target Proof: Question 7
          </span>
          <h4 className="font-headline text-sm text-[#131c2a] font-semibold mt-0.5">
            Dijkstra & BFS Inductive Correctness Theorem
          </h4>
        </div>

        {/* AI Mathematical Walkthrough */}
        <div className="mt-4 space-y-3 text-xs text-[#131c2a]">
          <div className="p-3.5 rounded-xl bg-[#F7F5F0] border border-black/[0.04]">
            <h5 className="font-bold text-[#3f4dbf] text-[13px]">1. Base Case (|S| = 1)</h5>
            <p className="mt-1 text-[#58605a] leading-relaxed">
              The visited frontier set S contains only source vertex {'{s}'}. Since dist[s] = 0 and all edge weights w ≥ 0, dist[s] is trivially the shortest path from s to s.
            </p>
          </div>

          <div className="p-3.5 rounded-xl bg-[#F7F5F0] border border-black/[0.04]">
            <h5 className="font-bold text-[#3f4dbf] text-[13px]">2. Inductive Hypothesis</h5>
            <p className="mt-1 text-[#58605a] leading-relaxed">
              Assume that for all vertices u ∈ S, dist[u] equals the exact shortest path distance δ(s, u) from the root origin s.
            </p>
          </div>

          <div className="p-3.5 rounded-xl bg-[#F7F5F0] border border-black/[0.04]">
            <h5 className="font-bold text-[#3f4dbf] text-[13px]">3. Inductive Step (Greedy Pick v ∉ S)</h5>
            <p className="mt-1 text-[#58605a] leading-relaxed">
              Let v be the next vertex outside S that minimizes dist[v] = min {'{dist[u] + w(u, v)}'}. Any alternative path P from s to v must leave S at some first edge (x, y). Because all edge weights w ≥ 0, the length of P up to y is already ≥ dist[x] + w(x, y) ≥ dist[v]. Therefore, no shorter path to v can exist!
            </p>
          </div>

          <div className="p-3.5 rounded-xl bg-[#ffdad6]/60 border border-[#ba1a1a]/20">
            <h5 className="font-bold text-[#ba1a1a] text-[13px]">4. Edge (B, E) Negative Weight Fallacy</h5>
            <p className="mt-1 text-[#131c2a] leading-relaxed">
              If edge (B, E) has weight -3, the greedy invariant breaks because a path going through B could later reduce the cumulative cost of reaching E after E was already finalized in S.
            </p>
          </div>
        </div>

        <div className="mt-5 pt-2 flex items-center justify-between">
          <button
            onClick={() => {
              onShowToast('Proof annotations copied to your personal study notes!');
              onClose();
            }}
            className="w-full py-3 rounded-xl bg-[#3f4dbf] text-white text-xs font-bold active-haptic shadow-sm flex items-center justify-center gap-2 hover:bg-[#5967d9]"
          >
            <span className="material-symbols-outlined text-[18px]">content_copy</span>
            <span>Copy Proof to My Notes</span>
          </button>
        </div>
      </div>
    </div>
  );
};
