import re

path = r"c:\Users\giris\Desktop\projects\DEFINE\DEFINE4.0_Untitled-5-\web\frontend\src\KoodalApp.jsx"

with open(path, "r", encoding="utf-8") as f:
    text = f.read()

# 1. Update Wizard initCampaign to start fresh for a new campaign
old_wizard_init = """  // Persistent Campaign & Event State (PostgreSQL)
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

new_wizard_init = """  // Persistent Campaign & Event State (PostgreSQL)
  const [campaignId, setCampaignId] = useState(null);
  const [isSavingEvent, setIsSavingEvent] = useState(false);
  const [saveEventStatus, setSaveEventStatus] = useState(null);

  const templateKeys = ["seminar_invite", "clinic_reminder", "school_notice", "payment_reminder"];
  const defaultTitles = [
    "Healthcare & AI Seminar 2026",
    "Cardiology Clinic Appointment Reminder",
    "St. Mary's School Parent-Teacher Notice",
    "Annual Membership Fee Payment Reminder"
  ];

  const handleSaveEventToDB = async () => {
    setIsSavingEvent(true);
    setSaveEventStatus(null);
    try {
      let cid = campaignId;
      if (!cid) {
        const created = await api.createCampaign(eventData.title || "New Campaign", templateKeys[tpl]);
        if (created?.id) {
          cid = created.id;
          setCampaignId(cid);
        }
      }
      if (cid) {
        const res = await api.saveEvent(cid, eventData);
        if (res) {
          setSaveEventStatus({ type: "success", msg: "✓ Event saved permanently to PostgreSQL database!" });
        } else {
          setSaveEventStatus({ type: "error", msg: "Failed to persist event details." });
        }
      }
    } catch (err) {
      setSaveEventStatus({ type: "error", msg: err.message });
    } finally {
      setIsSavingEvent(false);
    }
  };"""

assert old_wizard_init in text, "old_wizard_init not found"
text = text.replace(old_wizard_init, new_wizard_init, 1)

# 2. Update Step 1 in Wizard to include template click title update and Campaign Title Input
old_step1 = """    <>
      <h3>1. Choose an event template</h3>
      <div className="tpl">
        {["Seminar Invite", "Clinic Reminder", "School Notice", "Payment Reminder"].map((x, n) => (
          <div key={x} className={tpl === n ? "on" : ""} onClick={() => setTpl(n)} style={{ cursor: "pointer" }}>
            <b>{x}</b>
            <div className="hint" style={{ marginTop: 8 }}>
              {n === 0 && "Seminar RSVPs & passes"}
              {n === 1 && "Appointments & reschedule"}
              {n === 2 && "Parent-teacher meetings"}
              {n === 3 && "Fees with personal links"}
            </div>
          </div>
        ))}
      </div>
      <p><b>Each preset includes a call script, voicemail, email and WhatsApp copy.</b></p>
    </>,"""

new_step1 = """    <>
      <h3>1. Choose an event template</h3>
      <div className="tpl">
        {["Seminar Invite", "Clinic Reminder", "School Notice", "Payment Reminder"].map((x, n) => (
          <div
            key={x}
            className={tpl === n ? "on" : ""}
            onClick={() => {
              setTpl(n);
              if (!eventData.title || defaultTitles.includes(eventData.title)) {
                setEventData((prev) => ({ ...prev, title: defaultTitles[n] }));
              }
            }}
            style={{ cursor: "pointer" }}
          >
            <b>{x}</b>
            <div className="hint" style={{ marginTop: 8 }}>
              {n === 0 && "Seminar RSVPs & passes"}
              {n === 1 && "Appointments & reschedule"}
              {n === 2 && "Parent-teacher meetings"}
              {n === 3 && "Fees with personal links"}
            </div>
          </div>
        ))}
      </div>

      {/* Explicit User Input for Campaign / Event Name */}
      <div className="f" style={{ marginTop: 20, background: "#fff", padding: 18, borderRadius: 12, border: "1px solid var(--line)" }}>
        <label style={{ fontSize: 14, fontWeight: 700, color: "var(--ink)" }}>Campaign & Event Title</label>
        <input
          value={eventData.title}
          placeholder="e.g. Healthcare Innovation Summit 2026"
          style={{ fontSize: 14, fontWeight: 600, padding: 10, marginTop: 6 }}
          onChange={(e) => setEventData({ ...eventData, title: e.target.value })}
        />
        <div className="hint" style={{ marginTop: 4 }}>
          This title will identify your event on the organizer dashboard sidebar and on all invitations.
        </div>
      </div>
      <p><b>Each preset includes a call script, voicemail, email and WhatsApp copy.</b></p>
    </>,"""

assert old_step1 in text, "old_step1 not found"
text = text.replace(old_step1, new_step1, 1)

# 3. Update Step 8 Launch in Wizard to create campaign if not yet created and pass full campaign object
old_step_nav = """            onClick={async () => {
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
            }}"""

new_step_nav = """            onClick={async () => {
              if (i === 2) {
                // Auto-save event details to PostgreSQL database when continuing past Step 3
                try {
                  let cid = campaignId;
                  if (!cid) {
                    const created = await api.createCampaign(eventData.title || "New Campaign", templateKeys[tpl]);
                    if (created?.id) {
                      cid = created.id;
                      setCampaignId(cid);
                    }
                  }
                  if (cid) {
                    await api.saveEvent(cid, eventData);
                  }
                } catch (e) {
                  console.warn("Auto-save error:", e);
                }
                setI(3);
              } else if (i === 7) {
                // Launch campaign in database
                setIsSavingEvent(true);
                try {
                  let cid = campaignId;
                  if (!cid) {
                    const created = await api.createCampaign(eventData.title || "New Campaign", templateKeys[tpl]);
                    if (created?.id) cid = created.id;
                  }
                  if (cid) {
                    await api.saveEvent(cid, eventData);
                    await api.launchCampaign(cid);
                  }
                  const newCampObj = {
                    id: cid || `cmp_${Date.now()}`,
                    name: eventData.title || "New Campaign",
                    template_key: templateKeys[tpl],
                    status: "running",
                    event: { ...eventData },
                    contact_count: contactsList.length || 50,
                  };
                  onLaunch(newCampObj);
                } catch (err) {
                  console.warn("Launch error:", err);
                  onLaunch({
                    id: campaignId || `cmp_${Date.now()}`,
                    name: eventData.title || "New Campaign",
                    template_key: templateKeys[tpl],
                    status: "running",
                    event: { ...eventData },
                    contact_count: 50,
                  });
                } finally {
                  setIsSavingEvent(false);
                }
              } else {
                setI(Math.min(7, i + 1));
              }
            }}"""

assert old_step_nav in text, "old_step_nav not found"
text = text.replace(old_step_nav, new_step_nav, 1)

# 4. Update Dashboard component with rich sidebar cards and event details
old_dash_start = """function Dashboard({ onNewCampaign, onSignOut, user, onOpenAISettings }) {
  const [activeCampaign, setActiveCampaign] = useState("Define");
  const [activeSection, setActiveSection] = useState("overview");

  // Sub-states for interactive previewing within sections
  const [payState, setPayState] = useState("form");
  const [guestState, setGuestState] = useState("form");
  const [checkinState, setCheckinState] = useState("ok");
  const [msgKey, setMsgKey] = useState("Invite");
  const [channel, setChannel] = useState("Email");
  const [feedbackState, setFeedbackState] = useState("form");

  const [dashContacts, setDashContacts] = useState(null);
  const [serverCampaigns, setServerCampaigns] = useState([]);

  useEffect(() => {
    api.getCampaigns().then((res) => {
      if (res && res.length > 0) setServerCampaigns(res);
    });
    api.getContacts("cmp_001").then((res) => {
      if (res?.items && res.items.length > 0) setDashContacts(res.items);
    });
  }, []);

  const defaultCampaigns = ["Define", "Future of Work Summit", "SALT", "Relevant"];
  const campaigns = Array.from(new Set([...defaultCampaigns, ...serverCampaigns.map((c) => c.name)]));

  const subsections = [
    { id: "overview", label: "📊 Overview" },
    { id: "payments", label: "💳 Payments" },
    { id: "registration", label: "📝 Guest Registration" },
    { id: "tickets", label: "🎟️ Tickets & Check-in" },
    { id: "messages", label: "💬 Message Previews" },
    { id: "feedback", label: "⭐ Event Feedback" },
  ];"""

new_dash_start = """function Dashboard({
  onNewCampaign,
  onSignOut,
  user,
  onOpenAISettings,
  campaignsList = [],
  setCampaignsList,
  activeCampaignId,
  setActiveCampaignId,
}) {
  const [activeSection, setActiveSection] = useState("overview");

  // Sub-states for interactive previewing within sections
  const [payState, setPayState] = useState("form");
  const [guestState, setGuestState] = useState("form");
  const [checkinState, setCheckinState] = useState("ok");
  const [msgKey, setMsgKey] = useState("Invite");
  const [channel, setChannel] = useState("Email");
  const [feedbackState, setFeedbackState] = useState("form");

  const [dashContacts, setDashContacts] = useState(null);
  const [serverCampaigns, setServerCampaigns] = useState([]);

  useEffect(() => {
    api.getCampaigns().then((res) => {
      if (res && res.length > 0) {
        setServerCampaigns(res);
        if (setCampaignsList) setCampaignsList(res);
      }
    });
    api.getContacts("cmp_001").then((res) => {
      if (res?.items && res.items.length > 0) setDashContacts(res.items);
    });
  }, []);

  const fallbackCampaigns = [
    {
      id: "cmp_demo_1",
      name: "Define Healthcare & AI Seminar",
      template_key: "seminar_invite",
      status: "running",
      event: {
        title: "Define Healthcare & AI Seminar",
        starts_at: "23 Oct 2026, 10:00 AM IST",
        venue: "Grand Hall, Block A",
        city: "Kochi",
        fee_inr: 500,
        description: "A day of conversations and interactive discussions on AI in Healthcare.",
      },
      contact_count: 50,
    },
    {
      id: "cmp_demo_2",
      name: "Future of Work Summit",
      template_key: "seminar_invite",
      status: "draft",
      event: {
        title: "Future of Work Summit",
        starts_at: "15 Nov 2026, 09:30 AM IST",
        venue: "Infopark Auditorium",
        city: "Kochi",
        fee_inr: 750,
        description: "Leadership symposium on remote collaboration and intelligent automation.",
      },
      contact_count: 42,
    },
    {
      id: "cmp_demo_3",
      name: "City Health Clinic Follow-up",
      template_key: "clinic_reminder",
      status: "running",
      event: {
        title: "City Health Clinic Follow-up",
        starts_at: "28 Oct 2026, 11:00 AM IST",
        venue: "City Wellness Clinic",
        city: "Kochi",
        fee_inr: 0,
        description: "Preventive cardiology check-up and doctor consultation.",
      },
      contact_count: 35,
    },
  ];

  // Merge database campaigns with fallbacks
  const combinedList = [...(campaignsList && campaignsList.length > 0 ? campaignsList : serverCampaigns)];
  fallbackCampaigns.forEach((fb) => {
    if (!combinedList.some((c) => c.id === fb.id || c.name === fb.name)) {
      combinedList.push(fb);
    }
  });

  const currentCamp = combinedList.find((c) => c.id === activeCampaignId || c.name === activeCampaignId) || combinedList[0] || fallbackCampaigns[0];
  const activeEventTitle = currentCamp.event?.title || currentCamp.name;
  const activeEventVenue = currentCamp.event?.venue || "Grand Hall";
  const activeEventCity = currentCamp.event?.city || "Kochi";
  const activeEventDate = currentCamp.event?.starts_at ? (typeof currentCamp.event.starts_at === "string" ? currentCamp.event.starts_at : new Date(currentCamp.event.starts_at).toLocaleString()) : "23 Oct 2026, 10:00 AM IST";
  const activeEventFee = currentCamp.event?.fee_inr !== undefined ? currentCamp.event.fee_inr : 500;

  const subsections = [
    { id: "overview", label: "📊 Overview" },
    { id: "payments", label: "💳 Payments" },
    { id: "registration", label: "📝 Guest Registration" },
    { id: "tickets", label: "🎟️ Tickets & Check-in" },
    { id: "messages", label: "💬 Message Previews" },
    { id: "feedback", label: "⭐ Event Feedback" },
  ];"""

assert old_dash_start in text, "old_dash_start not found"
text = text.replace(old_dash_start, new_dash_start, 1)

# 5. Update Sidebar rendering to show rich event data provided by user
old_side_render = """        <div className="side-title">CAMPAIGNS</div>
        {campaigns.map((name) => {
          const isSelected = activeCampaign === name;
          return (
            <div key={name}>
              <div
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
              </div>

              {/* Subsections appear inside sidebar when campaign is active */}
              {isSelected && (
                <div className="side-sub">
                  {subsections.map((sub) => (
                    <div
                      key={sub.id}
                      className={`sub-link ${activeSection === sub.id ? "on" : ""}`}
                      onClick={(e) => {
                        e.stopPropagation();
                        setActiveSection(sub.id);
                      }}
                    >
                      {sub.label}
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}"""

new_side_render = """        <div className="side-title">CAMPAIGNS & EVENTS ({combinedList.length})</div>
        {combinedList.map((c) => {
          const isSelected = (c.id === currentCamp.id || c.name === currentCamp.name);
          const cTitle = c.event?.title || c.name;
          const cCity = c.event?.city || "Kochi";
          const cDate = c.event?.starts_at ? (typeof c.event.starts_at === "string" ? c.event.starts_at.slice(0, 16) : new Date(c.event.starts_at).toLocaleDateString()) : "Upcoming";
          const cFee = c.event?.fee_inr !== undefined ? (c.event.fee_inr === 0 ? "Free" : `₹${c.event.fee_inr}`) : "₹500";
          const isRunning = c.status === "running";

          return (
            <div key={c.id || c.name} style={{ marginBottom: 8 }}>
              <div
                className={`side-item ${isSelected ? "on" : ""}`}
                style={{
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "stretch",
                  padding: "10px 12px",
                  borderRadius: 10,
                  background: isSelected ? "#233544" : "rgba(255,255,255,0.03)",
                  border: isSelected ? "1px solid var(--teal)" : "1px solid rgba(255,255,255,0.08)",
                  cursor: "pointer",
                  transition: "all 0.15s"
                }}
                onClick={() => {
                  if (setActiveCampaignId) setActiveCampaignId(c.id || c.name);
                  if (!isSelected) setActiveSection("overview");
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 6 }}>
                  <span style={{ fontWeight: 700, fontSize: 13, color: isSelected ? "#fff" : "#cfd8dc", lineHeight: 1.3 }}>
                    {cTitle}
                  </span>
                  <span
                    className={`pill ${isRunning ? "g" : "w"}`}
                    style={{ fontSize: 9, padding: "2px 6px", margin: 0, flexShrink: 0 }}
                  >
                    {isRunning ? "RUNNING" : "DRAFT"}
                  </span>
                </div>

                {/* Event data provided by the user reflected directly on sidebar item */}
                <div style={{ fontSize: 11, color: isSelected ? "#a0c4db" : "#78909c", marginTop: 5, display: "flex", flexWrap: "wrap", gap: 8 }}>
                  <span>📅 {cDate}</span>
                  <span>📍 {cCity}</span>
                  <span>🎟️ {cFee}</span>
                </div>
              </div>

              {/* Subsections appear under active event in sidebar */}
              {isSelected && (
                <div className="side-sub" style={{ marginTop: 4 }}>
                  {subsections.map((sub) => (
                    <div
                      key={sub.id}
                      className={`sub-link ${activeSection === sub.id ? "on" : ""}`}
                      onClick={(e) => {
                        e.stopPropagation();
                        setActiveSection(sub.id);
                      }}
                    >
                      {sub.label}
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}"""

assert old_side_render in text, "old_side_render not found"
text = text.replace(old_side_render, new_side_render, 1)

# 6. Update Dashboard header & Overview to display active event data card
old_sub_bar = """        {/* Breadcrumb Header */}
        <div className="sub-bar">
          <div>
            <div style={{ fontSize: 12, color: "var(--mut)", textTransform: "uppercase", letterSpacing: ".05em" }}>
              Campaigns / {activeCampaign} / <b style={{ color: "var(--ink)" }}>{activeSection}</b>
            </div>
            <h1 style={{ margin: "4px 0 0", fontSize: 26 }}>{activeCampaign}</h1>
          </div>
          <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
            <span className="pill g">● Active Campaign</span>
            <button className="btn p" style={{ width: "auto", margin: 0, padding: "8px 16px" }} onClick={onNewCampaign}>
              + New Campaign
            </button>
          </div>
        </div>

        {/* 1. OVERVIEW SUBSECTION */}
        {activeSection === "overview" && (
          <div>
            <small style={{ color: "var(--mut)" }}>Real-time analytics and response telemetry</small>"""

new_sub_bar = """        {/* Breadcrumb Header */}
        <div className="sub-bar">
          <div>
            <div style={{ fontSize: 12, color: "var(--mut)", textTransform: "uppercase", letterSpacing: ".05em" }}>
              Campaigns / {activeEventTitle} / <b style={{ color: "var(--ink)" }}>{activeSection}</b>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 12, marginTop: 4 }}>
              <h1 style={{ margin: 0, fontSize: 26 }}>{activeEventTitle}</h1>
              <span className={`pill ${currentCamp.status === "running" ? "g" : "w"}`} style={{ fontSize: 11, margin: 0 }}>
                ● {currentCamp.status ? currentCamp.status.toUpperCase() : "ACTIVE"}
              </span>
            </div>
          </div>
          <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
            <button className="btn p" style={{ width: "auto", margin: 0, padding: "8px 16px" }} onClick={onNewCampaign}>
              + New Campaign
            </button>
          </div>
        </div>

        {/* 1. OVERVIEW SUBSECTION */}
        {activeSection === "overview" && (
          <div>
            {/* User-Provided Event Summary Card */}
            <div style={{
              background: "#fff",
              borderRadius: 14,
              padding: "16px 20px",
              border: "1px solid var(--line)",
              boxShadow: "0 2px 10px rgba(0,0,0,0.04)",
              marginBottom: 20
            }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <span style={{ fontSize: 20 }}>📌</span>
                  <b style={{ fontSize: 15, color: "var(--ink)" }}>Event Details Provided by User</b>
                </div>
                <span className="pill g" style={{ fontSize: 11 }}>
                  {currentCamp.status === "running" ? "🚀 Live Campaign Dispatched" : "📝 Saved in PostgreSQL"}
                </span>
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 14 }}>
                <div style={{ background: "#F8FAFB", padding: 12, borderRadius: 8, border: "1px solid var(--line)" }}>
                  <small style={{ color: "var(--mut)", fontSize: 11, fontWeight: 700 }}>EVENT TITLE</small>
                  <div style={{ fontWeight: 700, fontSize: 14, color: "var(--ink)", marginTop: 4 }}>
                    {activeEventTitle}
                  </div>
                </div>
                <div style={{ background: "#F8FAFB", padding: 12, borderRadius: 8, border: "1px solid var(--line)" }}>
                  <small style={{ color: "var(--mut)", fontSize: 11, fontWeight: 700 }}>DATE & TIME</small>
                  <div style={{ fontWeight: 700, fontSize: 14, color: "var(--ink)", marginTop: 4 }}>
                    {activeEventDate}
                  </div>
                </div>
                <div style={{ background: "#F8FAFB", padding: 12, borderRadius: 8, border: "1px solid var(--line)" }}>
                  <small style={{ color: "var(--mut)", fontSize: 11, fontWeight: 700 }}>VENUE & LOCATION</small>
                  <div style={{ fontWeight: 700, fontSize: 14, color: "var(--ink)", marginTop: 4 }}>
                    {activeEventVenue}, {activeEventCity}
                  </div>
                </div>
                <div style={{ background: "#F8FAFB", padding: 12, borderRadius: 8, border: "1px solid var(--line)" }}>
                  <small style={{ color: "var(--mut)", fontSize: 11, fontWeight: 700 }}>REGISTRATION PASS</small>
                  <div style={{ fontWeight: 700, fontSize: 14, color: "var(--ink)", marginTop: 4 }}>
                    {activeEventFee === 0 ? "Free Access" : `₹${activeEventFee} per seat`}
                  </div>
                </div>
              </div>
            </div>

            <small style={{ color: "var(--mut)" }}>Real-time analytics and response telemetry</small>"""

assert old_sub_bar in text, "old_sub_bar not found"
text = text.replace(old_sub_bar, new_sub_bar, 1)

# 7. Update root KoodalApp component to pass campaignsList, activeCampaignId, and handleCampaignLaunch
old_root_setup = """export default function KoodalApp() {
  // Views: "home" (default landing/login) | "dashboard" | "wizard"
  const [view, setView] = useState("home");
  const [user, setUser] = useState({ name: "Asha Thomas", email: "organizer@example.com", role: "organizer" });
  const [backendStatus, setBackendStatus] = useState("checking");
  const [showAISettings, setShowAISettings] = useState(false);
  const [activeAIProvider, setActiveAIProvider] = useState(localStorage.getItem("eventreach_ai_provider") || "gemini");

  useEffect(() => {
    // Check backend health immediately on mount
    api.checkHealth().then((res) => {
      setBackendStatus(res ? "connected" : "offline");
    });

    // Re-check every 8 seconds
    const interval = setInterval(() => {
      api.checkHealth().then((res) => {
        setBackendStatus(res ? "connected" : "offline");
      });
    }, 8000);
    return () => clearInterval(interval);
  }, []);"""

new_root_setup = """export default function KoodalApp() {
  // Views: "home" (default landing/login) | "dashboard" | "wizard"
  const [view, setView] = useState("home");
  const [user, setUser] = useState({ name: "Asha Thomas", email: "organizer@example.com", role: "organizer" });
  const [backendStatus, setBackendStatus] = useState("checking");
  const [showAISettings, setShowAISettings] = useState(false);
  const [activeAIProvider, setActiveAIProvider] = useState(localStorage.getItem("eventreach_ai_provider") || "gemini");

  // Global campaigns list & active selected campaign
  const [campaignsList, setCampaignsList] = useState([]);
  const [activeCampaignId, setActiveCampaignId] = useState(null);

  const refreshCampaigns = async () => {
    try {
      const res = await api.getCampaigns();
      if (res && res.length > 0) {
        setCampaignsList(res);
        if (!activeCampaignId) setActiveCampaignId(res[0].id || res[0].name);
      }
    } catch {}
  };

  useEffect(() => {
    refreshCampaigns();
    api.checkHealth().then((res) => {
      setBackendStatus(res ? "connected" : "offline");
    });

    const interval = setInterval(() => {
      api.checkHealth().then((res) => {
        setBackendStatus(res ? "connected" : "offline");
      });
    }, 8000);
    return () => clearInterval(interval);
  }, []);

  const handleCampaignLaunch = (newCamp) => {
    setCampaignsList((prev) => [newCamp, ...prev.filter((c) => c.id !== newCamp.id && c.name !== newCamp.name)]);
    setActiveCampaignId(newCamp.id || newCamp.name);
    setView("dashboard");
    refreshCampaigns();
  };"""

assert old_root_setup in text, "old_root_setup not found"
text = text.replace(old_root_setup, new_root_setup, 1)

# 8. Update root KoodalApp route calls
old_root_routes = """      {/* 2. Campaign Wizard Flow */}
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

new_root_routes = """      {/* 2. Campaign Wizard Flow */}
      {view === "wizard" && (
        <Wizard
          onCancel={() => setView("dashboard")}
          onOpenAISettings={() => setShowAISettings(true)}
          activeAIProvider={activeAIProvider}
          onLaunch={handleCampaignLaunch}
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
          campaignsList={campaignsList}
          setCampaignsList={setCampaignsList}
          activeCampaignId={activeCampaignId}
          setActiveCampaignId={setActiveCampaignId}
        />
      )}"""

assert old_root_routes in text, "old_root_routes not found"
text = text.replace(old_root_routes, new_root_routes, 1)

with open(path, "w", encoding="utf-8") as f:
    f.write(text)

print("KoodalApp.jsx successfully patched with new campaign sidebar flow!")
