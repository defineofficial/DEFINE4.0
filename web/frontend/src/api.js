/**
 * EventReach API Client
 * Connects React Frontend to FastAPI backend at http://127.0.0.1:8000
 * Gracefully falls back to mock responses if backend is offline.
 */

const API_BASE = ""; // Uses Vite reverse-proxy (/auth, /campaigns, /r, etc.)

let token = localStorage.getItem("eventreach_token") || null;

export function setAuthToken(newToken) {
  token = newToken;
  if (newToken) {
    localStorage.setItem("eventreach_token", newToken);
  } else {
    localStorage.removeItem("eventreach_token");
  }
}

export function getAuthToken() {
  return token;
}

async function request(endpoint, options = {}) {
  const headers = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };

  const config = {
    ...options,
    headers,
  };

  const response = await fetch(`${API_BASE}${endpoint}`, config);
  if (!response.ok) {
    let errDetail = response.statusText;
    try {
      const errJson = await response.json();
      errDetail = errJson.detail || JSON.stringify(errJson);
    } catch {
      // ignore
    }
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

  // Translations
  getTranslations: async (campaignId) => {
    try {
      return await request(`/campaigns/${campaignId}/translations`);
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

  // QR Check-in
  checkInAttendee: async (token) => {
    try {
      return await request(`/r/${token}/check-in`, { method: "POST" });
    } catch (err) {
      return { status: "error", message: err.message };
    }
  },
};
