/**
 * EventReach API Client
 * Connects React Frontend to FastAPI backend at http://127.0.0.1:8000
 * Gracefully falls back to mock responses if backend is offline.
 *
 * Every failed call now shows a red box at the bottom right of the page (see reportError),
 * so a fallback to sample data is never silent.
 */

const API_BASE = ""; // Uses Vite reverse-proxy (/auth, /campaigns, /r, etc.)

let lastMsg = "", lastAt = 0;
function reportError(what, status, detail) {
  console.error("[EventReach API]", what, status, detail);
  try {
    const text = `${what} failed${status ? " (" + status + ")" : ""}: ${detail}`;
    if (text === lastMsg && Date.now() - lastAt < 5000) return;
    lastMsg = text; lastAt = Date.now();
    let box = document.getElementById("er-api-errors");
    if (!box) {
      box = document.createElement("div");
      box.id = "er-api-errors";
      box.style.cssText = "position:fixed;right:12px;bottom:12px;z-index:99999;display:flex;flex-direction:column;gap:6px;max-width:380px;font:13px system-ui";
      document.body.appendChild(box);
    }
    const d = document.createElement("div");
    d.style.cssText = "background:#8a1c1c;color:#fff;padding:10px 12px;border-radius:8px;box-shadow:0 2px 10px rgba(0,0,0,.3)";
    d.textContent = text;
    box.appendChild(d);
    setTimeout(() => d.remove(), 9000);
  } catch { /* ignore */ }
}

let token = localStorage.getItem("eventreach_token") || null;

export function setAuthToken(newToken) {
  token = newToken;
  if (newToken) {
    localStorage.setItem("eventreach_token", newToken);
  } else {
    localStorage.removeItem("eventreach_token");
  }
}

export async function ensureAuth() {
  if (!token) {
    try {
      const res = await fetch(`${API_BASE}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: "organizer@example.com", password: "password123" }),
      });
      if (res.ok) {
        const data = await res.json();
        if (data.access_token) {
          setAuthToken(data.access_token);
        }
      }
    } catch {
      // offline / mock mode fallback
    }
  }
  return token;
}

async function request(endpoint, options = {}) {
  await ensureAuth();
  const headers = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };

  const config = {
    ...options,
    headers,
  };

  let response;
  try {
    response = await fetch(`${API_BASE}${endpoint}`, config);
  } catch (e) {
    reportError(`${options.method || "GET"} ${endpoint}`, 0, "cannot reach the backend");
    throw e;
  }
  if (!response.ok) {
    let errDetail = response.statusText;
    try {
      const errJson = await response.json();
      errDetail = errJson.detail || JSON.stringify(errJson);
    } catch {
      // ignore
    }
    reportError(`${options.method || "GET"} ${endpoint}`, response.status, errDetail);
    const err = new Error(errDetail);
    err.status = response.status;
    throw err;
  }

  // Handle SVG, ICS or JSON
  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    return await response.json();
  }
  return await response.text();
}

export const api = {
  // Health
  checkHealth: async () => {
    try {
      const res = await fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(2000) });
      if (res.ok) return await res.json();
      return null;
    } catch {
      return null;
    }
  },

  // Auth
  login: async (email, password) => {
    try {
      const data = await request("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      if (data.access_token) {
        setAuthToken(data.access_token);
      }
      return data;
    } catch (err) {
      console.warn("Backend auth failed, using mock auth:", err.message);
      return { access_token: "mock-token" };
    }
  },

  getMe: async () => {
    try {
      return await request("/me");
    } catch {
      return { id: "org_001", name: "Asha Thomas", email: "organizer@example.com", role: "organizer" };
    }
  },

  // Templates
  getTemplates: async () => {
    try {
      return await request("/templates");
    } catch {
      return null;
    }
  },

  // Campaigns
  getCampaigns: async () => {
    try {
      return await request("/campaigns");
    } catch {
      return null;
    }
  },

  createCampaign: async (name, template_key) => {
    try {
      return await request("/campaigns", {
        method: "POST",
        body: JSON.stringify({ name, template_key }),
      });
    } catch (err) {
      console.warn("Backend createCampaign failed:", err.message);
      return null;
    }
  },

  // Analytics & Contacts
  getFunnel: async (campaignId) => {
    try {
      return await request(`/campaigns/${campaignId}/analytics/funnel`);
    } catch {
      return null;
    }
  },

  getContacts: async (campaignId) => {
    try {
      return await request(`/campaigns/${campaignId}/contacts`);
    } catch {
      return null;
    }
  },

  // Dispatch & Retries
  testCall: async (campaignId, phone, language = "ml") => {
    try {
      return await request(`/campaigns/${campaignId}/test-call`, {
        method: "POST",
        body: JSON.stringify({ phone, language }),
      });
    } catch {
      return { status: "queued", message: "Mock test call simulated." };
    }
  },

  retryOutreach: async (campaignId, target = "non_responders") => {
    try {
      return await request(`/campaigns/${campaignId}/retry`, {
        method: "POST",
        body: JSON.stringify({ target }),
      });
    } catch {
      return { queued: 412, skipped_opted_out: 14, skipped_max_attempts: 28 };
    }
  },

  // File Uploads
  uploadPoster: async (campaignId, file) => {
    try {
      await ensureAuth();
      const formData = new FormData();
      formData.append("file", file);
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      const res = await fetch(`${API_BASE}/campaigns/${campaignId}/poster`, {
        method: "POST",
        headers,
        body: formData,
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Poster upload failed");
      }
      return await res.json();
    } catch (err) {
      reportError("Poster upload", 0, err.message);
      console.warn("Poster upload warning:", err.message);
      return { poster_url: URL.createObjectURL(file) };
    }
  },

  uploadVoiceNote: async (campaignId, file) => {
    try {
      await ensureAuth();
      const formData = new FormData();
      formData.append("file", file);
      const customKey = localStorage.getItem("eventreach_ai_key") || "";
      const customProvider = localStorage.getItem("eventreach_ai_provider") || "";
      const headers = {
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(customKey ? { "X-AI-Key": customKey } : {}),
        ...(customProvider ? { "X-AI-Provider": customProvider } : {}),
      };
      const res = await fetch(`${API_BASE}/campaigns/${campaignId}/voice-note`, {
        method: "POST",
        headers,
        body: formData,
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Voice note extraction failed");
      }
      return await res.json();
    } catch (err) {
      reportError("Voice note extraction", 0, err.message + " (showing a SAMPLE result, not your audio)");
      console.warn("Voice extraction warning:", err.message);
      return {
        transcript: "Join us for the Define Healthcare & AI Seminar on October 23, 2026 at Grand Hall, Kochi. Registration fee is 500 rupees.",
        detected_language: "en",
        event: {
          title: "Define Healthcare & AI Seminar",
          venue: "Grand Hall, Block A",
          city: "Kochi",
          fee_inr: 500,
          starts_at: "2026-10-23T10:00:00+05:30",
        },
        needs_review: [],
      };
    }
  },

  importAudience: async (campaignId, file, defaultLanguage = "en") => {
    try {
      await ensureAuth();
      const formData = new FormData();
      formData.append("file", file);
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      const res = await fetch(`${API_BASE}/campaigns/${campaignId}/audience?default_language=${defaultLanguage}`, {
        method: "POST",
        headers,
        body: formData,
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Audience import failed");
      }
      return await res.json();
    } catch (err) {
      reportError("CSV import", 0, err.message + " (showing SAMPLE counts, nothing was imported)");
      console.warn("Audience import warning:", err.message);
      return {
        total_rows: 50,
        imported: 50,
        skipped: 0,
        errors: [],
        warnings: [],
        languages_found: { ml: 25, en: 15, hi: 10 },
        segments_found: { Faculty: 20, Students: 30 },
      };
    }
  },

  saveEvent: async (campaignId, eventDetails) => {
    try {
      await ensureAuth();
      let startsAtIso = "2026-10-23T10:00:00+05:30";
      if (eventDetails?.starts_at) {
        const d = new Date(eventDetails.starts_at);
        if (!isNaN(d.getTime())) {
          startsAtIso = d.toISOString();
        } else if (typeof eventDetails.starts_at === "string" && eventDetails.starts_at.includes("T")) {
          startsAtIso = eventDetails.starts_at;
        }
      }

      const payload = {
        title: eventDetails?.title || "Community Outreach Event",
        description: eventDetails?.description || `Outreach campaign for ${eventDetails?.title || "event"}`,
        starts_at: startsAtIso,
        venue: eventDetails?.venue || "Grand Hall",
        city: eventDetails?.city || "Kochi",
        fee_inr: parseInt(eventDetails?.fee_inr, 10) || 0,
      };

      return await request(`/campaigns/${campaignId}/event`, {
        method: "PUT",
        body: JSON.stringify(payload),
      });
    } catch (err) {
      console.warn("Failed to persist event to backend:", err.message);
      return null;
    }
  },

  launchCampaign: async (campaignId) => {
    try {
      await ensureAuth();
      return await request(`/campaigns/${campaignId}/launch`, {
        method: "POST",
      });
    } catch {
      return { status: "running", queued_contacts: 50 };
    }
  },

  // Translations
  getTranslations: async (campaignId) => {
    try {
      await ensureAuth();
      return await request(`/campaigns/${campaignId}/translations`);
    } catch {
      return null;
    }
  },

  generateTranslations: async (campaignId) => {
    try {
      await ensureAuth();
      return await request(`/campaigns/${campaignId}/translations/generate`, {
        method: "POST",
      });
    } catch {
      return null;
    }
  },

  saveTranslation: async (campaignId, language, translationData) => {
    try {
      await ensureAuth();
      return await request(`/campaigns/${campaignId}/translations/${language}`, {
        method: "PUT",
        body: JSON.stringify(translationData),
      });
    } catch {
      return null;
    }
  },

  // AI Configuration
  getAISettings: async () => {
    try {
      return await request("/settings/ai");
    } catch {
      return { provider: "gemini", has_key: false };
    }
  },

  setAISettings: async (provider, apiKey) => {
    localStorage.setItem("eventreach_ai_provider", provider);
    localStorage.setItem("eventreach_ai_key", apiKey);
    try {
      return await request("/settings/ai", {
        method: "POST",
        body: JSON.stringify({ provider, api_key: apiKey }),
      });
    } catch {
      return { status: "ok", provider };
    }
  },

  // QR Check-in
  checkInAttendee: async (token) => {
    try {
      return await request(`/r/${token}/check-in`, { method: "POST" });
    } catch (err) {
      return { status: "error", message: err.message };
    }
  },
};