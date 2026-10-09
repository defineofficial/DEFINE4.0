import React, { useState } from 'react';
import { Resource } from '../types';

interface AddResourceViewProps {
  onCancel: () => void;
  onSaveResource: (newRes: Resource) => void;
  onShowToast: (msg: string) => void;
}

export const AddResourceView: React.FC<AddResourceViewProps> = ({
  onCancel,
  onSaveResource,
  onShowToast
}) => {
  const [sourceTab, setSourceTab] = useState<'url' | 'upload'>('url');
  const [url, setUrl] = useState('https://www.youtube.com/watch?v=XB4MlexJyY0');
  const [title, setTitle] = useState('Dijkstra · Visual walkthrough');
  const [selectedFormat, setSelectedFormat] = useState('YouTube video');
  const [subject, setSubject] = useState('Data Structures & Algorithms');
  const [topic, setTopic] = useState('Graphs');
  const [tags, setTags] = useState<string[]>(['shortest paths', 'revision']);
  const [addToExamPrep, setAddToExamPrep] = useState(true);
  const [autoExtract, setAutoExtract] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  const handleAddTag = () => {
    const newTag = prompt('Enter a new tag name:');
    if (newTag && newTag.trim()) {
      setTags([...tags, newTag.trim().toLowerCase()]);
      onShowToast(`Added tag #${newTag.trim()}`);
    }
  };

  const handleRemoveTag = (t: string) => {
    setTags(tags.filter((tag) => tag !== t));
  };

  const handleSave = () => {
    setIsSaving(true);
    setTimeout(() => {
      const newRes: Resource = {
        id: 'res-' + Date.now(),
        title: title || 'Dijkstra · Visual walkthrough',
        type: 'video',
        typeBadge: 'VIDEO',
        subject: 'CS204',
        subjectName: subject,
        topic: topic,
        author: 'Abdul Bari',
        meta: '18 mins · 1080p HD · Added today',
        progress: 0,
        isPending: true,
        saved: true,
        imageUrl:
          'https://lh3.googleusercontent.com/aida-public/AB6AXuBll6nrCz0mrYVkun1fIxqxJzoViKbJGH0s8DY2kVcI7LXoYfBE2QfQrkACGlIuXZHmOKnwQ93Pgyotjly43fq1PU5_CSb85lQVrNUHQgWiqpOANE1g2uxHBNn_U1wvgsLj8elBKWhCVyAzIVK0sZ6D6HRW1U3RJ3yxQ72YAdkP3CgMFEMX1CjwpnV1f4RtkK5FHjDVv7BAVCynCDN4fN6eNCyNaxj6YYQvZ1bPhDXh-GdULmQxlpYj6c_iZql4kPA7',
        colorClass: 'bg-[#ffdad6] text-[#ba1a1a]',
        spineGradient: 'from-[#ba1a1a] via-[#ffdad6] to-white',
        icon: 'play_circle',
        duration: '18 mins',
        updatedAt: 'Added just now',
        highlights: [
          'Dijkstra Single-Source Shortest Path visual traces',
          'Priority Queue decrease-key analysis',
          'Exam review questions and recurrence relations'
        ]
      };

      onSaveResource(newRes);
      onShowToast(`Saved "${newRes.title}" to NoteVault!`);
      setIsSaving(false);
    }, 700);
  };

  return (
    <div className="flex flex-col w-full pb-10 space-y-4 animate-fadeIn">
      {/* Top Utility Context & Stepper */}
      <div className="flex items-center justify-between py-1">
        <button
          onClick={onCancel}
          className="font-label-lg text-xs font-semibold text-[#58605a] hover:text-[#131c2a] py-1 active-haptic"
        >
          Cancel
        </button>
        <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#dfe8fd]">
          <span className="w-2 h-2 rounded-full bg-[#3f4dbf] animate-pulse" />
          <span className="font-label-sm text-[11px] font-bold text-[#3f4dbf] tracking-wide uppercase font-mono">
            Step 1 of 3
          </span>
        </div>
        <button
          onClick={handleSave}
          className="font-label-lg text-xs text-[#3f4dbf] hover:text-[#5967d9] py-1 font-bold active-haptic"
        >
          Save
        </button>
      </div>

      {/* Stepper Breadcrumb Track */}
      <div className="bg-white rounded-2xl p-3 shadow-xs border border-black/[0.04]">
        <div className="flex items-center justify-between text-center gap-1">
          <div className="flex-1 flex flex-col items-center">
            <div className="flex items-center gap-1">
              <span className="w-5 h-5 rounded-full bg-[#3f4dbf] text-white font-label-sm text-[10px] flex items-center justify-center font-bold">
                1
              </span>
              <span className="font-label-md text-xs text-[#131c2a] font-bold">Source</span>
            </div>
            <span className="w-full h-1 bg-[#3f4dbf] rounded-full mt-1.5" />
          </div>
          <div className="flex-1 flex flex-col items-center opacity-70">
            <div className="flex items-center gap-1">
              <span className="w-5 h-5 rounded-full bg-gray-100 text-[#58605a] font-label-sm text-[10px] flex items-center justify-center">
                2
              </span>
              <span className="font-label-md text-xs text-[#58605a]">Organise</span>
            </div>
            <span className="w-full h-1 bg-gray-200 rounded-full mt-1.5" />
          </div>
          <div className="flex-1 flex flex-col items-center opacity-70">
            <div className="flex items-center gap-1">
              <span className="w-5 h-5 rounded-full bg-gray-100 text-[#58605a] font-label-sm text-[10px] flex items-center justify-center">
                3
              </span>
              <span className="font-label-md text-xs text-[#58605a]">Save</span>
            </div>
            <span className="w-full h-1 bg-gray-200 rounded-full mt-1.5" />
          </div>
        </div>
      </div>

      {/* Source Selector Switcher Tabs */}
      <div className="p-1 bg-[#e7eeff] rounded-2xl flex items-center gap-1 shadow-inner">
        <button
          onClick={() => setSourceTab('url')}
          className={`flex-1 py-2 px-3 rounded-xl font-label-md text-xs font-semibold flex items-center justify-center gap-1.5 transition-all ${
            sourceTab === 'url' ? 'bg-white text-[#3f4dbf] shadow-xs' : 'text-[#58605a] hover:text-[#131c2a]'
          }`}
        >
          <span className="material-symbols-outlined text-[18px]">link</span>
          <span>Import a URL</span>
        </button>
        <button
          onClick={() => setSourceTab('upload')}
          className={`flex-1 py-2 px-3 rounded-xl font-label-md text-xs font-semibold flex items-center justify-center gap-1.5 transition-all ${
            sourceTab === 'upload' ? 'bg-white text-[#3f4dbf] shadow-xs' : 'text-[#58605a] hover:text-[#131c2a]'
          }`}
        >
          <span className="material-symbols-outlined text-[18px]">upload_file</span>
          <span>Upload a file</span>
        </button>
      </div>

      {sourceTab === 'upload' && (
        <div className="p-6 rounded-2xl bg-white border-2 border-dashed border-gray-300 text-center space-y-2">
          <span className="material-symbols-outlined text-4xl text-[#3f4dbf]">cloud_upload</span>
          <p className="font-headline text-sm font-bold text-[#131c2a]">Drag & drop course PDF, DOCX, or EPUB</p>
          <p className="text-xs text-[#58605a]">Accepts academic course files up to 50MB</p>
          <button
            onClick={() => onShowToast('File browser opened for document selection')}
            className="px-4 py-2 rounded-xl bg-[#dfe0ff] text-[#000a64] text-xs font-bold"
          >
            Browse Local Device
          </button>
        </div>
      )}

      {/* URL Input Panel */}
      {sourceTab === 'url' && (
        <div className="bg-white rounded-2xl p-4 shadow-xs border border-black/[0.04]">
          <label className="block font-label-md text-xs font-bold text-[#58605a] mb-1.5">
            Resource Web Address
          </label>
          <div className="relative flex items-center">
            <div className="absolute left-3 text-[#3f4dbf] flex items-center pointer-events-none">
              <span className="material-symbols-outlined text-[20px]">smart_display</span>
            </div>
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              className="w-full bg-[#F0F3FF] text-[#131c2a] pl-10 pr-10 py-2.5 rounded-xl font-body text-xs outline-none focus:bg-white focus:ring-2 focus:ring-[#3f4dbf]/30"
            />
            <div className="absolute right-3 flex items-center text-emerald-600">
              <span className="material-symbols-outlined text-[20px] fill-icon">check_circle</span>
            </div>
          </div>

          {/* Status Metadata Feedback */}
          <div className="flex items-center justify-between mt-2.5 pt-2 bg-[#F7F5F0] px-3 py-1.5 rounded-xl">
            <div className="flex items-center gap-1.5 min-w-0">
              <span className="w-2 h-2 rounded-full bg-[#3f4dbf] flex-shrink-0 animate-pulse" />
              <span className="font-body text-xs text-[#58605a] truncate">
                Title and video details detected
              </span>
            </div>
            <button
              onClick={() => onShowToast('URL validator active')}
              className="text-[#3f4dbf] font-label-sm text-xs font-semibold whitespace-nowrap ml-2 hover:underline"
            >
              Change URL
            </button>
          </div>
        </div>
      )}

      {/* Rich Live Resource Preview Card */}
      <div className="relative bg-white rounded-2xl p-4 shadow-xs border border-black/[0.04] overflow-hidden">
        <div className="flex items-center justify-between mb-3">
          <span className="font-label-sm text-[11px] uppercase tracking-wider text-[#58605a] font-bold flex items-center gap-1">
            <span className="material-symbols-outlined text-[15px] text-[#3f4dbf]">visibility</span>
            <span>Live Resource Preview</span>
          </span>
          <a
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className="font-label-md text-xs text-[#3f4dbf] hover:underline flex items-center gap-0.5 font-semibold"
          >
            <span>Open original</span>
            <span className="material-symbols-outlined text-[16px]">open_in_new</span>
          </a>
        </div>

        {/* Video Preview Bento Block */}
        <div className="relative rounded-xl overflow-hidden bg-[#d1daee] aspect-video mb-3 shadow-xs">
          <img
            src="https://lh3.googleusercontent.com/aida-public/AB6AXuBll6nrCz0mrYVkun1fIxqxJzoViKbJGH0s8DY2kVcI7LXoYfBE2QfQrkACGlIuXZHmOKnwQ93Pgyotjly43fq1PU5_CSb85lQVrNUHQgWiqpOANE1g2uxHBNn_U1wvgsLj8elBKWhCVyAzIVK0sZ6D6HRW1U3RJ3yxQ72YAdkP3CgMFEMX1CjwpnV1f4RtkK5FHjDVv7BAVCynCDN4fN6eNCyNaxj6YYQvZ1bPhDXh-GdULmQxlpYj6c_iZql4kPA7"
            alt="Video preview graphic"
            className="w-full h-full object-cover"
            referrerPolicy="no-referrer"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent flex items-end p-3 justify-between">
            <div className="flex items-center gap-1.5">
              <span className="px-2 py-0.5 rounded bg-[#3f4dbf] text-white font-label-sm text-[10px] font-bold flex items-center gap-1 shadow-xs">
                <span className="material-symbols-outlined text-[12px] fill-icon">play_arrow</span>
                <span>18:00</span>
              </span>
              <span className="px-2 py-0.5 rounded bg-black/60 text-white font-label-sm text-[10px] backdrop-blur-sm font-mono">
                1080p HD
              </span>
            </div>
            <span className="w-8 h-8 rounded-full bg-white text-[#3f4dbf] flex items-center justify-center shadow-md">
              <span className="material-symbols-outlined text-[20px] fill-icon">play_arrow</span>
            </span>
          </div>
        </div>

        <div className="min-w-0">
          <h3 className="font-headline text-base font-bold text-[#131c2a] mb-1">
            Dijkstra · Shortest paths, explained
          </h3>
          <div className="flex items-center gap-2 text-[#58605a] font-body text-xs">
            <div className="flex items-center gap-1">
              <span className="material-symbols-outlined text-[16px] text-[#ba1a1a]">subscriptions</span>
              <span className="text-[#131c2a] font-semibold">Abdul Bari</span>
            </div>
            <span>•</span>
            <span>YouTube Channel</span>
            <span>•</span>
            <span className="text-[#3f4dbf] font-semibold">Verified Source</span>
          </div>
        </div>
      </div>

      {/* Resource Categorisation & Tags */}
      <div className="bg-white rounded-2xl p-4 shadow-xs border border-black/[0.04] space-y-4">
        <div className="flex items-center justify-between pb-1">
          <div>
            <h2 className="font-headline text-base font-bold text-[#131c2a]">Organise & Tag</h2>
            <p className="font-body text-xs text-[#58605a]">Tune how this item is filed in NoteVault</p>
          </div>
          <span className="w-8 h-8 rounded-full bg-[#dce5dd] text-[#151d19] flex items-center justify-center">
            <span className="material-symbols-outlined text-[18px]">folder_copy</span>
          </span>
        </div>

        {/* Format Chips */}
        <div>
          <label className="block font-label-md text-xs font-bold text-[#58605a] mb-2">
            Resource Format
          </label>
          <div className="flex flex-wrap gap-1.5">
            {[
              'Notes',
              'PDF',
              'YouTube video',
              'GitHub repository',
              'PYQ',
              'Textbook'
            ].map((fmt) => {
              const isSelected = selectedFormat === fmt;
              return (
                <button
                  key={fmt}
                  type="button"
                  onClick={() => setSelectedFormat(fmt)}
                  className={`px-3 py-1.5 rounded-full font-label-md text-xs font-semibold transition-all active-haptic ${
                    isSelected
                      ? 'bg-[#3f4dbf] text-white shadow-xs flex items-center gap-1'
                      : 'bg-[#F7F5F0] text-[#58605a] hover:text-[#131c2a]'
                  }`}
                >
                  {isSelected && <span className="w-1.5 h-1.5 rounded-full bg-white" />}
                  <span>{fmt}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Title Input */}
        <div>
          <label className="block font-label-md text-xs font-bold text-[#58605a] mb-1.5">
            Vault Display Title
          </label>
          <div className="relative">
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full bg-[#F0F3FF] text-[#131c2a] px-3.5 py-2.5 rounded-xl font-body text-xs sm:text-sm outline-none focus:bg-white focus:ring-2 focus:ring-[#3f4dbf]/30"
            />
            <button
              type="button"
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[#58605a] p-1"
            >
              <span className="material-symbols-outlined text-[18px]">edit</span>
            </button>
          </div>
        </div>

        {/* Subject & Topic Dropdowns */}
        <div className="grid grid-cols-2 gap-2.5">
          <div>
            <label className="block font-label-md text-xs font-bold text-[#58605a] mb-1.5">
              Subject
            </label>
            <select
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              className="w-full bg-[#F0F3FF] text-[#131c2a] px-3 py-2.5 rounded-xl font-body text-xs outline-none truncate"
            >
              <option value="Data Structures & Algorithms">CS204 · DSA</option>
              <option value="Operating Systems">CS206 · OS</option>
              <option value="Linear Algebra">MA202 · Linear Alg</option>
            </select>
          </div>
          <div>
            <label className="block font-label-md text-xs font-bold text-[#58605a] mb-1.5">
              Topic
            </label>
            <select
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              className="w-full bg-[#F0F3FF] text-[#131c2a] px-3 py-2.5 rounded-xl font-body text-xs outline-none truncate"
            >
              <option value="Graphs">Graphs</option>
              <option value="Dynamic Programming">Dynamic Prog</option>
              <option value="Trees">Trees & Heaps</option>
              <option value="Arrays & sorting">Arrays & Sorting</option>
            </select>
          </div>
        </div>

        {/* Categorical Tags */}
        <div>
          <label className="block font-label-md text-xs font-bold text-[#58605a] mb-1.5">
            Categorical Tags
          </label>
          <div className="flex flex-wrap items-center gap-1.5">
            {tags.map((tag) => (
              <span
                key={tag}
                className="inline-flex items-center gap-1 bg-[#dce5dd] text-[#151d19] px-2.5 py-1 rounded-full font-label-sm text-xs"
              >
                <span>{tag}</span>
                <button
                  type="button"
                  onClick={() => handleRemoveTag(tag)}
                  className="hover:text-[#ba1a1a] flex items-center"
                >
                  <span className="material-symbols-outlined text-[14px]">close</span>
                </button>
              </span>
            ))}
            <button
              type="button"
              onClick={handleAddTag}
              className="inline-flex items-center gap-0.5 bg-[#F7F5F0] hover:bg-[#dfe8fd] text-[#3f4dbf] px-2.5 py-1 rounded-full font-label-sm text-xs transition-colors"
            >
              <span className="material-symbols-outlined text-[14px]">add</span>
              <span>Add tag</span>
            </button>
          </div>
        </div>

        {/* Add to DSA exam prep checkbox */}
        <div className="p-3 bg-[#F0F3FF] rounded-2xl">
          <label className="flex items-start gap-3 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={addToExamPrep}
              onChange={(e) => setAddToExamPrep(e.target.checked)}
              className="sr-only"
            />
            <div
              className={`w-5 h-5 mt-0.5 rounded-lg flex items-center justify-center flex-shrink-0 transition-colors ${
                addToExamPrep ? 'bg-[#3f4dbf] text-white' : 'bg-gray-200 text-transparent'
              }`}
            >
              <span className="material-symbols-outlined text-[16px]">check</span>
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-1.5">
                <span className="font-headline text-xs font-bold text-[#131c2a]">
                  Also add to DSA exam prep
                </span>
                <span className="material-symbols-outlined text-[14px] text-[#58605a]">lock</span>
              </div>
              <p className="font-body text-xs text-[#58605a] mt-0.5 leading-snug">
                Private collection · 12 resources now, <span className="text-[#3f4dbf] font-bold">13 after saving</span>
              </p>
            </div>
          </label>
        </div>
      </div>

      {/* AI Companion Micro-Callout */}
      <div className="p-4 rounded-2xl bg-[#dfe8fd]/70 shadow-xs border border-[#3f4dbf]/20 flex items-center gap-3">
        <div className="w-9 h-9 rounded-full bg-[#5967d9] text-white flex items-center justify-center flex-shrink-0 shadow-xs">
          <span className="material-symbols-outlined text-[20px]">auto_awesome</span>
        </div>
        <div className="flex-1 min-w-0">
          <h4 className="font-headline text-xs font-bold text-[#131c2a]">
            Auto-extract flashcards?
          </h4>
          <p className="font-body text-xs text-[#58605a]">
            AI Study Guide will generate key revision cards after saving.
          </p>
        </div>
        <input
          type="checkbox"
          checked={autoExtract}
          onChange={(e) => setAutoExtract(e.target.checked)}
          className="w-4 h-4 text-[#3f4dbf] rounded"
        />
      </div>

      {/* Bottom Action Group */}
      <div className="pt-2 flex items-center gap-3">
        <button
          type="button"
          onClick={onCancel}
          className="flex-1 py-3 px-4 rounded-2xl bg-white text-[#58605a] hover:text-[#131c2a] font-label-lg text-xs font-bold text-center transition-colors shadow-xs border border-black/[0.04]"
        >
          Cancel
        </button>
        <button
          type="button"
          onClick={handleSave}
          disabled={isSaving}
          className="flex-[2] py-3 px-4 rounded-2xl bg-[#3f4dbf] text-white font-label-lg text-xs sm:text-sm font-bold flex items-center justify-center gap-2 shadow-md hover:bg-[#5967d9] active-haptic transition-all"
        >
          {isSaving ? (
            <>
              <span className="material-symbols-outlined text-[18px] animate-spin">
                progress_activity
              </span>
              <span>Saving to Vault...</span>
            </>
          ) : (
            <>
              <span className="material-symbols-outlined text-[18px] fill-icon">bookmark</span>
              <span>Save resource</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
};
