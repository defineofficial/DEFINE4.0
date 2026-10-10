import re
import os

target_path = r"c:\Users\giris\Desktop\projects\DEFINE\DEFINE4.0_Untitled-5-\web\frontend\src\KoodalApp.jsx"

with open(target_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update Home component header & nav
old_home_sig = "function Home({ onLogin, backendStatus }) {"
new_home_sig = "function Home({ onLogin, backendStatus, onOpenAISettings }) {"
assert old_home_sig in content, "old_home_sig not found"
content = content.replace(old_home_sig, new_home_sig, 1)

old_nav_buttons = """        <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
          <span
            className={`pill ${backendStatus === "connected" ? "g" : "w"}`}"""
new_nav_buttons = """        <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
          <button
            className="btn-sm"
            onClick={onOpenAISettings}
            style={{ display: "flex", alignItems: "center", gap: 6, background: "#1b3542", borderColor: "var(--teal)", color: "#fff" }}
            title="Configure Gemini, Groq, or OpenAI API key for real voice processing"
          >
            <span>⚙️</span> AI API Settings
          </button>
          <span
            className={`pill ${backendStatus === "connected" ? "g" : "w"}`}"""
assert old_nav_buttons in content, "old_nav_buttons not found"
content = content.replace(old_nav_buttons, new_nav_buttons, 1)


# 2. Add AISettingsModal component right before Wizard Flow
ai_modal_code = """/* ---------- AI Settings Modal ---------- */
function AISettingsModal({ isOpen, onClose, onSaved }) {
  const [provider, setProvider] = useState(localStorage.getItem("eventreach_ai_provider") || "gemini");
  const [apiKey, setApiKey] = useState(localStorage.getItem("eventreach_ai_key") || "");
  const [showKey, setShowKey] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState(null);

  useEffect(() => {
    if (isOpen) {
      api.getAISettings().then((settings) => {
        if (settings?.provider) setProvider(settings.provider);
      });
      const storedKey = localStorage.getItem("eventreach_ai_key") || "";
      if (storedKey) setApiKey(storedKey);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSave = async (e) => {
    e?.preventDefault();
    setSaving(true);
    setSaveStatus(null);
    try {
      await api.setAISettings(provider, apiKey);
      setSaveStatus({ type: "success", msg: "✓ AI settings saved! Audio voice notes will now be transcribed and extracted using real AI." });
      if (onSaved) onSaved(provider, apiKey);
      setTimeout(() => {
        onClose();
      }, 1000);
    } catch (err) {
      setSaveStatus({ type: "error", msg: "Failed to save: " + err.message });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={{
      position: "fixed",
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: "rgba(10, 20, 30, 0.75)",
      backdropFilter: "blur(4px)",
      zIndex: 9999,
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      padding: 20
    }}>
      <div style={{
        background: "#fff",
        borderRadius: 16,
        maxWidth: 520,
        width: "100%",
        padding: 28,
        boxShadow: "0 20px 50px rgba(0,0,0,0.3)",
        position: "relative"
      }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <span style={{ fontSize: 24 }}>⚙️</span>
            <div>
              <h3 style={{ margin: 0, fontSize: 18, color: "var(--ink)" }}>AI Voice & Extraction API Settings</h3>
              <small style={{ color: "var(--mut)" }}>Extract event information from real audio voice notes</small>
            </div>
          </div>
          <button
            onClick={onClose}
            style={{ background: "none", border: "none", fontSize: 20, cursor: "pointer", color: "var(--mut)" }}
          >
            ✕
          </button>
        </div>

        <form onSubmit={handleSave}>
          <div className="f">
            <label>Select AI Provider</label>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8, marginTop: 6 }}>
              {[
                { id: "gemini", label: "🌟 Gemini", sub: "1.5 Flash (Audio)" },
                { id: "groq", label: "⚡ Groq", sub: "Whisper-v3" },
                { id: "openai", label: "🤖 OpenAI", sub: "Whisper-1" },
              ].map((p) => (
                <div
                  key={p.id}
                  onClick={() => setProvider(p.id)}
                  style={{
                    border: provider === p.id ? "2px solid var(--teal)" : "1px solid var(--line)",
                    background: provider === p.id ? "var(--mint)" : "#fafafa",
                    borderRadius: 10,
                    padding: "10px 8px",
                    textAlign: "center",
                    cursor: "pointer",
                    transition: "all 0.15s"
                  }}
                >
                  <b style={{ fontSize: 13, display: "block" }}>{p.label}</b>
                  <small style={{ fontSize: 11, color: "var(--mut)" }}>{p.sub}</small>
                </div>
              ))}
            </div>
          </div>

          <div className="f" style={{ marginTop: 16 }}>
            <label style={{ display: "flex", justifyContent: "space-between" }}>
              <span>API Key</span>
              <span
                style={{ fontSize: 12, color: "var(--teal)", cursor: "pointer", fontWeight: 600 }}
                onClick={() => setShowKey(!showKey)}
              >
                {showKey ? "Hide" : "Show"}
              </span>
            </label>
            <input
              type={showKey ? "text" : "password"}
              placeholder={provider === "gemini" ? "AIzaSy..." : provider === "groq" ? "gsk_..." : "sk-..."}
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              style={{ fontFamily: showKey ? "monospace" : "inherit" }}
            />
            <div className="hint" style={{ marginTop: 6, lineHeight: 1.5 }}>
              {provider === "gemini" && (
                <span>
                  Get a free Gemini API key from <a href="https://aistudio.google.com/app/apikey" target="_blank" rel="noreferrer" style={{ color: "var(--teal)", fontWeight: 600 }}>Google AI Studio ↗</a>. Gemini 1.5 Flash natively transcribes audio and extracts structured JSON.
                </span>
              )}
              {provider === "groq" && (
                <span>
                  Get a free Groq API key from <a href="https://console.groq.com/keys" target="_blank" rel="noreferrer" style={{ color: "var(--teal)", fontWeight: 600 }}>Groq Console ↗</a>. Uses whisper-large-v3 with high-speed Llama-3.3 event extraction.
                </span>
              )}
              {provider === "openai" && (
                <span>
                  Use your OpenAI API key from <a href="https://platform.openai.com/api-keys" target="_blank" rel="noreferrer" style={{ color: "var(--teal)", fontWeight: 600 }}>platform.openai.com ↗</a>.
                </span>
              )}
            </div>
          </div>

          {saveStatus && (
            <div className={`al ${saveStatus.type === "success" ? "g" : "e"}`} style={{ padding: "8px 12px", fontSize: 13 }}>
              {saveStatus.msg}
            </div>
          )}

          <div style={{ display: "flex", gap: 10, marginTop: 20 }}>
            <button
              type="button"
              className="btn"
              style={{ flex: 1, margin: 0 }}
              onClick={onClose}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn p"
              style={{ flex: 2, margin: 0 }}
              disabled={saving}
            >
              {saving ? "Saving..." : "Save AI Key & Connect"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

"""

old_wiz_marker = "/* ---------- 2. Organizer Campaign Wizard Flow ---------- */"
assert old_wiz_marker in content, "old_wiz_marker not found"
content = content.replace(old_wiz_marker, ai_modal_code + old_wiz_marker, 1)


# 3. Update Wizard signature & state
old_wiz_start = """function Wizard({ onCancel, onLaunch }) {
  const [i, setI] = useState(0), [tpl, setTpl] = useState(0);
  const [testPhone, setTestPhone] = useState("+91 98000 00000");
  const [testLang, setTestLang] = useState("Malayalam");
  const [testResult, setTestResult] = useState(null);
  const [calling, setCalling] = useState(false);"""

new_wiz_start = """function Wizard({ onCancel, onLaunch, onOpenAISettings, activeAIProvider = "gemini" }) {
  const [i, setI] = useState(0), [tpl, setTpl] = useState(0);
  const [testPhone, setTestPhone] = useState("+91 98000 00000");
  const [testLang, setTestLang] = useState("Malayalam");
  const [testResult, setTestResult] = useState(null);
  const [calling, setCalling] = useState(false);

  // Persistent Campaign & Event State (PostgreSQL)
  const [campaignId, setCampaignId] = useState(null);
  const [isSavingEvent, setIsSavingEvent] = useState(false);
  const [saveEventStatus, setSaveEventStatus] = useState(null);

  useEffect(() => {
    async function initCampaign() {
      try {
        const camps = await api.getCampaigns();
        if (camps && camps.length > 0) {
          const draftCamp = camps.find((c) => c.status === "draft") || camps[0];
          setCampaignId(draftCamp.id);
          if (draftCamp.event) {
            setEventData({
              title: draftCamp.event.title || "Define Healthcare & AI Seminar",
              starts_at: draftCamp.event.starts_at || "23 Oct 2026, 10:00 AM IST",
              venue: draftCamp.event.venue || "Grand Hall, Block A",
              city: draftCamp.event.city || "Kochi",
              fee_inr: draftCamp.event.fee_inr !== undefined ? draftCamp.event.fee_inr : 500,
            });
          }
          return;
        }
        const newCamp = await api.createCampaign("Define Healthcare & AI Seminar", "seminar_invite");
        if (newCamp?.id) setCampaignId(newCamp.id);
      } catch (err) {
        console.warn("Could not init campaign in database:", err);
      }
    }
    initCampaign();
  }, []);

  const handleSaveEventToDB = async () => {
    if (!campaignId) return;
    setIsSavingEvent(true);
    setSaveEventStatus(null);
    try {
      const res = await api.saveEvent(campaignId, eventData);
      if (res) {
        setSaveEventStatus({ type: "success", msg: "✓ Event saved permanently to PostgreSQL database!" });
      } else {
        setSaveEventStatus({ type: "error", msg: "Failed to persist event details." });
      }
    } catch (err) {
      setSaveEventStatus({ type: "error", msg: err.message });
    } finally {
      setIsSavingEvent(false);
    }
  };"""

assert old_wiz_start in content, "old_wiz_start not found"
content = content.replace(old_wiz_start, new_wiz_start, 1)


# 4. Replace cmp_001 calls with campaignId || "cmp_001"
content = content.replace('await api.uploadVoiceNote("cmp_001", file)', 'await api.uploadVoiceNote(campaignId || "cmp_001", file)')
content = content.replace('await api.uploadPoster("cmp_001", file)', 'await api.uploadPoster(campaignId || "cmp_001", file)')
content = content.replace('await api.importAudience("cmp_001", file)', 'await api.importAudience(campaignId || "cmp_001", file)')
content = content.replace('await api.getContacts("cmp_001")', 'await api.getContacts(campaignId || "cmp_001")')
content = content.replace('await api.testCall("cmp_001", testPhone, langCode)', 'await api.testCall(campaignId || "cmp_001", testPhone, langCode)')


# 5. Add AI status badge at top of Step 2
old_step2_hdr = "<h3>2. Upload poster and voice note</h3>"
new_step2_hdr = """<h3>2. Upload poster and voice note</h3>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", background: "#f0fcfb", border: "1px solid #c8f3ed", padding: "10px 14px", borderRadius: 10, marginBottom: 14 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13 }}>
          <span style={{ fontSize: 16 }}>⚡</span>
          <span>
            <b>Real AI Audio Engine:</b> {activeAIProvider === "gemini" ? "Google Gemini 1.5 Flash (Direct Audio)" : activeAIProvider === "groq" ? "Groq Whisper-large-v3 + Llama 3" : "OpenAI Whisper"}
            {localStorage.getItem("eventreach_ai_key") ? " (API Key Connected ✓)" : " (No Key - Fallback Mode)"}
          </span>
        </div>
        <button
          type="button"
          className="btn-sm"
          style={{ background: "#fff", borderColor: "var(--teal)", color: "var(--ink)", padding: "4px 10px" }}
          onClick={() => onOpenAISettings && onOpenAISettings()}
        >
          ⚙️ Configure AI Key
        </button>
      </div>"""
assert old_step2_hdr in content, "old_step2_hdr not found"
content = content.replace(old_step2_hdr, new_step2_hdr, 1)


# 6. Add "Save Event Details to Database" button in Step 3
old_step3_bottom = """        <input
          type="number"
          value={eventData.fee_inr}
          style={{ background: "#f0fcfb" }}
          onChange={(e) => setEventData({ ...eventData, fee_inr: parseInt(e.target.value, 10) || 0 })}
        />
      </div>
    </>,"""

new_step3_bottom = """        <input
          type="number"
          value={eventData.fee_inr}
          style={{ background: "#f0fcfb" }}
          onChange={(e) => setEventData({ ...eventData, fee_inr: parseInt(e.target.value, 10) || 0 })}
        />
      </div>

      <div style={{ display: "flex", gap: 10, alignItems: "center", marginTop: 18, marginBottom: 12 }}>
        <button
          type="button"
          className="btn p"
          style={{ width: "auto", padding: "10px 22px", margin: 0, fontSize: 13 }}
          disabled={isSavingEvent}
          onClick={handleSaveEventToDB}
        >
          {isSavingEvent ? "💾 Saving to PostgreSQL..." : "💾 Save Event Details to Database"}
        </button>
        {saveEventStatus && (
          <span className={`pill ${saveEventStatus.type === "success" ? "g" : "e"}`} style={{ fontSize: 13, padding: "6px 12px" }}>
            {saveEventStatus.msg}
          </span>
        )}
      </div>
    </>,"""
assert old_step3_bottom in content, "old_step3_bottom not found"
content = content.replace(old_step3_bottom, new_step3_bottom, 1)


# 7. Update Wizard Navigation buttons: auto-save on Step 3, save & launch on Step 8
old_nav_buttons_wiz = """          <button
            className="btn p"
            style={{ width: 200, borderRadius: 30 }}
            onClick={() => {
              if (i === 7) {
                onLaunch();
              } else {
                setI(Math.min(7, i + 1));
              }
            }}
          >
            {i === 7 ? "🚀 Launch campaign" : "Continue →"}
          </button>"""

new_nav_buttons_wiz = """          <button
            className="btn p"
            style={{ width: 220, borderRadius: 30 }}
            disabled={isSavingEvent}
            onClick={async () => {
              if (i === 2) {
                // Auto-save event details to PostgreSQL database when continuing past Step 3
                if (campaignId) {
                  await api.saveEvent(campaignId, eventData);
                }
                setI(3);
              } else if (i === 7) {
                // Launch campaign in database
                setIsSavingEvent(true);
                try {
                  if (campaignId) {
                    await api.saveEvent(campaignId, eventData);
                    await api.launchCampaign(campaignId);
                  }
                  onLaunch({ id: campaignId, name: eventData.title, status: "running", event: eventData });
                } finally {
                  setIsSavingEvent(false);
                }
              } else {
                setI(Math.min(7, i + 1));
              }
            }}
          >
            {i === 7 ? (isSavingEvent ? "Launching..." : "🚀 Launch campaign") : "Continue →"}
          </button>"""
assert old_nav_buttons_wiz in content, "old_nav_buttons_wiz not found"
content = content.replace(old_nav_buttons_wiz, new_nav_buttons_wiz, 1)


# 8. Update Dashboard signature and campaign status pill
old_dash_sig = "function Dashboard({ onNewCampaign, onSignOut, user }) {"
new_dash_sig = "function Dashboard({ onNewCampaign, onSignOut, user, onOpenAISettings }) {"
assert old_dash_sig in content, "old_dash_sig not found"
content = content.replace(old_dash_sig, new_dash_sig, 1)

old_side_item = """              <div
                className={`side-item ${isSelected ? "on" : ""}`}
                onClick={() => {
                  setActiveCampaign(name);
                  if (!isSelected) setActiveSection("overview");
                }}
              >
                <span>{name}</span>
                <div className="dot" />
              </div>"""

new_side_item = """              <div
                className={`side-item ${isSelected ? "on" : ""}`}
                onClick={() => {
                  setActiveCampaign(name);
                  if (!isSelected) setActiveSection("overview");
                }}
              >
                <span>{name}</span>
                <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                  {serverCampaigns.find(c => c.name === name)?.status === "running" && (
                    <span className="pill g" style={{ fontSize: 9, padding: "2px 6px", margin: 0 }}>RUNNING</span>
                  )}
                  <div className="dot" />
                </div>
              </div>"""
assert old_side_item in content, "old_side_item not found"
content = content.replace(old_side_item, new_side_item, 1)


# 9. Update Root KoodalApp: add states, AISettingsModal, top-bar button, and route handlers
old_root_sig = """export default function KoodalApp() {
  // Views: "home" (default landing/login) | "dashboard" | "wizard"
  const [view, setView] = useState("home");
  const [user, setUser] = useState({ name: "Asha Thomas", email: "organizer@example.com", role: "organizer" });
  const [backendStatus, setBackendStatus] = useState("checking");"""

new_root_sig = """export default function KoodalApp() {
  // Views: "home" (default landing/login) | "dashboard" | "wizard"
  const [view, setView] = useState("home");
  const [user, setUser] = useState({ name: "Asha Thomas", email: "organizer@example.com", role: "organizer" });
  const [backendStatus, setBackendStatus] = useState("checking");
  const [showAISettings, setShowAISettings] = useState(false);
  const [activeAIProvider, setActiveAIProvider] = useState(localStorage.getItem("eventreach_ai_provider") || "gemini");"""
assert old_root_sig in content, "old_root_sig not found"
content = content.replace(old_root_sig, new_root_sig, 1)

old_top_bar_right = """            <span
              className={`pill ${backendStatus === "connected" ? "g" : "w"}`}
              style={{ fontSize: 11, margin: 0 }}
              title={backendStatus === "connected" ? "Connected to FastAPI at http://localhost:8000" : "FastAPI server offline; running in mock mode"}
            >
              {backendStatus === "connected" ? "● Backend Live :8000" : "○ Demo Mode"}
            </span>"""

new_top_bar_right = """            <span
              className={`pill ${backendStatus === "connected" ? "g" : "w"}`}
              style={{ fontSize: 11, margin: 0 }}
              title={backendStatus === "connected" ? "Connected to FastAPI at http://localhost:8000" : "FastAPI server offline; running in mock mode"}
            >
              {backendStatus === "connected" ? "● Backend Live :8000" : "○ Demo Mode"}
            </span>
            <button
              className="btn-sm"
              onClick={() => setShowAISettings(true)}
              style={{ display: "flex", alignItems: "center", gap: 6, background: "#1b3542", borderColor: "var(--teal)", color: "#fff" }}
              title="Configure Gemini, Groq, or OpenAI API key for real audio processing"
            >
              <span>⚙️</span> AI API Settings
            </button>"""
assert old_top_bar_right in content, "old_top_bar_right not found"
content = content.replace(old_top_bar_right, new_top_bar_right, 1)

old_routes = """      {/* 1. Home / Login Flow */}
      {view === "home" && (
        <Home
          backendStatus={backendStatus}
          onLogin={(userData) => {
            setUser(userData);
            setView("dashboard");
          }}
        />
      )}

      {/* 2. Campaign Wizard Flow */}
      {view === "wizard" && (
        <Wizard
          onCancel={() => setView("dashboard")}
          onLaunch={() => {
            alert("Campaign successfully launched! Returning to your dashboard.");
            setView("dashboard");
          }}
        />
      )}

      {/* 3. Organizer Dashboard Flow */}
      {view === "dashboard" && (
        <Dashboard
          onNewCampaign={() => setView("wizard")}
          onSignOut={() => {
            setAuthToken(null);
            setView("home");
          }}
          user={user}
        />
      )}"""

new_routes = """      {/* AI Settings Modal */}
      <AISettingsModal
        isOpen={showAISettings}
        onClose={() => setShowAISettings(false)}
        onSaved={(p) => setActiveAIProvider(p)}
      />

      {/* 1. Home / Login Flow */}
      {view === "home" && (
        <Home
          backendStatus={backendStatus}
          onOpenAISettings={() => setShowAISettings(true)}
          onLogin={(userData) => {
            setUser(userData);
            setView("dashboard");
          }}
        />
      )}

      {/* 2. Campaign Wizard Flow */}
      {view === "wizard" && (
        <Wizard
          onCancel={() => setView("dashboard")}
          onOpenAISettings={() => setShowAISettings(true)}
          activeAIProvider={activeAIProvider}
          onLaunch={(camp) => {
            alert("Campaign successfully launched and saved to database! Returning to your dashboard.");
            setView("dashboard");
          }}
        />
      )}

      {/* 3. Organizer Dashboard Flow */}
      {view === "dashboard" && (
        <Dashboard
          onNewCampaign={() => setView("wizard")}
          onOpenAISettings={() => setShowAISettings(true)}
          onSignOut={() => {
            setAuthToken(null);
            setView("home");
          }}
          user={user}
        />
      )}"""
assert old_routes in content, "old_routes not found"
content = content.replace(old_routes, new_routes, 1)

with open(target_path, "w", encoding="utf-8") as f:
    f.write(content)

print("KoodalApp.jsx successfully patched!")
