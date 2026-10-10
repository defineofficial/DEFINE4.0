// The real guest page: opened from a personal link like /r/<token>.
// Loads the person and event from the API, registers them, takes a (test) payment, collects feedback.
// Self-contained: needs only React. It does not depend on KoodalApp.jsx or its CSS.
import { useEffect, useState } from "react";

const TOKEN = () => decodeURIComponent(window.location.pathname.split("/").filter(Boolean)[1] || "");

async function call(method, path, body) {
  const res = await fetch(path, {
    method,
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  let data = null;
  try { data = await res.json(); } catch { /* no body */ }
  if (!res.ok) {
    const d = data && data.detail;
    throw new Error(typeof d === "string" ? d : "Something went wrong. Please check your details and try again.");
  }
  return data;
}

const fmtWhen = (iso) => {
  try {
    return new Date(iso).toLocaleString("en-IN", {
      timeZone: "Asia/Kolkata", weekday: "long", day: "numeric", month: "long", year: "numeric",
      hour: "numeric", minute: "2-digit",
    }) + " IST";
  } catch { return iso; }
};

const S = {
  page: { minHeight: "100vh", background: "#f3f5f7", display: "flex", justifyContent: "center", padding: "24px 16px", fontFamily: "system-ui, Segoe UI, Arial, sans-serif", color: "#14202b" },
  card: { width: "100%", maxWidth: 520, background: "#fff", borderRadius: 14, boxShadow: "0 2px 14px rgba(0,0,0,.08)", overflow: "hidden", alignSelf: "flex-start" },
  body: { padding: "22px 22px 26px" },
  h1: { margin: "0 0 6px", fontSize: 24, lineHeight: 1.25 },
  muted: { color: "#5a6a78", fontSize: 14, margin: "4px 0" },
  row: { display: "flex", justifyContent: "space-between", gap: 12, padding: "9px 0", borderBottom: "1px solid #e8edf1", fontSize: 15 },
  label: { display: "block", fontSize: 14, fontWeight: 600, margin: "14px 0 6px" },
  input: { width: "100%", boxSizing: "border-box", padding: "11px 12px", fontSize: 16, border: "1px solid #b9c4cd", borderRadius: 8 },
  btn: { width: "100%", marginTop: 18, padding: "13px 16px", fontSize: 16, fontWeight: 700, color: "#fff", background: "#0b7a75", border: 0, borderRadius: 8, cursor: "pointer" },
  btnGhost: { width: "100%", marginTop: 10, padding: "12px 16px", fontSize: 15, fontWeight: 600, color: "#0b7a75", background: "#fff", border: "1px solid #0b7a75", borderRadius: 8, cursor: "pointer" },
  ok: { background: "#e6f6ee", border: "1px solid #9bd8b8", color: "#0d5c36", padding: "12px 14px", borderRadius: 8, margin: "14px 0", fontSize: 15 },
  warn: { background: "#fff6e0", border: "1px solid #f0d28a", color: "#6b4a00", padding: "12px 14px", borderRadius: 8, margin: "14px 0", fontSize: 15 },
  err: { background: "#fdeaea", border: "1px solid #f0a8a8", color: "#8a1c1c", padding: "12px 14px", borderRadius: 8, margin: "14px 0", fontSize: 15 },
};

function Frame({ children, poster }) {
  return (
    <div style={S.page}>
      <div style={S.card}>
        {poster && <img src={poster} alt="Event poster" style={{ width: "100%", display: "block", maxHeight: 320, objectFit: "cover" }} onError={(e) => { e.currentTarget.style.display = "none"; }} />}
        <div style={S.body}>{children}</div>
      </div>
    </div>
  );
}

function Details({ ev, fee, seats }) {
  const total = (fee || 0) * (seats || 1);
  return (
    <div style={{ margin: "12px 0" }}>
      <div style={S.row}><span>When</span><b style={{ textAlign: "right" }}>{fmtWhen(ev.starts_at)}</b></div>
      <div style={S.row}><span>Where</span><b style={{ textAlign: "right" }}>{ev.venue}, {ev.city}</b></div>
      <div style={S.row}><span>Fee</span><b>{fee ? `Rs ${fee} per seat` : "Free"}</b></div>
      {seats > 1 && fee > 0 && <div style={S.row}><span>Total for {seats} seats</span><b>Rs {total}</b></div>}
    </div>
  );
}

function Feedback({ token }) {
  const [rating, setRating] = useState(0);
  const [comment, setComment] = useState("");
  const [state, setState] = useState("idle");
  const [error, setError] = useState("");
  const send = async () => {
    if (!rating) { setError("Please choose a rating from 1 to 5."); return; }
    setState("sending"); setError("");
    try {
      await call("POST", `/r/${encodeURIComponent(token)}/feedback`, { rating, comment: comment.trim() || null });
      setState("done");
    } catch (e) { setError(e.message); setState("idle"); }
  };
  if (state === "done") return <div style={S.ok}>Thank you. Your feedback was received.</div>;
  return (
    <div style={{ marginTop: 22 }}>
      <h2 style={{ fontSize: 18, margin: "0 0 4px" }}>How was the event?</h2>
      <div role="radiogroup" aria-label="Rating" style={{ display: "flex", gap: 6, margin: "8px 0" }}>
        {[1, 2, 3, 4, 5].map((n) => (
          <button key={n} type="button" role="radio" aria-checked={rating === n} aria-label={`${n} star${n > 1 ? "s" : ""}`}
            onClick={() => setRating(n)}
            style={{ flex: 1, padding: "10px 0", fontSize: 22, borderRadius: 8, cursor: "pointer", border: "1px solid #b9c4cd", background: n <= rating ? "#0b7a75" : "#fff", color: n <= rating ? "#fff" : "#5a6a78" }}>
            {n <= rating ? "★" : "☆"}
          </button>
        ))}
      </div>
      <label htmlFor="fb-comment" style={S.label}>Comments (optional)</label>
      <textarea id="fb-comment" rows={3} value={comment} maxLength={1000} onChange={(e) => setComment(e.target.value)} style={{ ...S.input, fontFamily: "inherit" }} />
      {error && <div style={S.err} role="alert">{error}</div>}
      <button type="button" style={S.btn} onClick={send} disabled={state === "sending"}>{state === "sending" ? "Sending..." : "Submit feedback"}</button>
    </div>
  );
}

export default function LiveGuest() {
  const token = TOKEN();
  const feedbackOnly = new URLSearchParams(window.location.search).has("feedback");
  const [page, setPage] = useState(null);          // GET /r/{token}
  const [phase, setPhase] = useState("loading");   // loading | form | registered | paid | missing
  const [seats, setSeats] = useState(1);
  const [form, setForm] = useState({ name: "", email: "", party_size: 1, consent: false });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [note, setNote] = useState("");

  useEffect(() => {
    let live = true;
    call("GET", `/r/${encodeURIComponent(token)}`)
      .then((p) => {
        if (!live) return;
        setPage(p);
        setForm((f) => ({ ...f, name: p.first_name || "" }));
        if (p.stage === "paid" || p.stage === "attended") setPhase("paid");
        else if (p.already_registered) setPhase("registered");
        else setPhase("form");
      })
      .catch((e) => { if (live) { setError(e.message); setPhase("missing"); } });
    return () => { live = false; };
  }, [token]);

  const fee = page ? page.fee_inr || 0 : 0;

  const register = async (e) => {
    e.preventDefault();
    setError("");
    if (!form.name.trim()) { setError("Please enter your name."); return; }
    if (form.email && !/^\S+@\S+\.\S+$/.test(form.email)) { setError("That email address does not look right."); return; }
    if (!form.consent) { setError("Please tick the box to agree before registering."); return; }
    setBusy(true);
    try {
      const r = await call("POST", `/r/${encodeURIComponent(token)}/register`, {
        name: form.name.trim(), email: form.email.trim() || null, party_size: Number(form.party_size), consent: true,
      });
      setSeats(Number(form.party_size));
      setPhase(r.stage === "paid" ? "paid" : "registered");
    } catch (err) { setError(err.message); }
    setBusy(false);
  };

  const pay = async () => {
    setBusy(true); setError(""); setNote("");
    try {
      const order = await call("POST", `/r/${encodeURIComponent(token)}/pay`);
      // Test gateway: the real checkout would open here with order.order_id and order.gateway_key_id.
      await call("POST", "/webhooks/payment", { order_id: order.order_id, status: "paid" });
      setNote("Test payment received. No real money was charged.");
      setPhase("paid");
    } catch (err) { setError(err.message); }
    setBusy(false);
  };

  if (phase === "loading") return <Frame><p style={S.muted}>Loading your invitation...</p></Frame>;
  if (phase === "missing") return (
    <Frame>
      <h1 style={S.h1}>This link did not work</h1>
      <div style={S.err} role="alert">{error || "We could not find this invitation."}</div>
      <p style={S.muted}>Please ask the organizer to send you a new link.</p>
    </Frame>
  );

  const ev = page.event;
  if (feedbackOnly) return (
    <Frame poster={page.poster_url}>
      <h1 style={S.h1}>{ev.title}</h1>
      <p style={S.muted}>Thank you for being part of it, {page.first_name}.</p>
      <Feedback token={token} />
    </Frame>
  );

  return (
    <Frame poster={page.poster_url}>
      <p style={{ ...S.muted, margin: 0 }}>Hello {page.first_name}, you are invited to</p>
      <h1 style={S.h1}>{ev.title}</h1>
      {ev.description && <p style={S.muted}>{ev.description}</p>}
      <Details ev={ev} fee={fee} seats={phase === "form" ? Number(form.party_size) : seats} />

      {phase === "form" && (
        <form onSubmit={register} noValidate>
          <label htmlFor="g-name" style={S.label}>Your name</label>
          <input id="g-name" style={S.input} value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} autoComplete="name" />
          <label htmlFor="g-email" style={S.label}>Email (for your confirmation)</label>
          <input id="g-email" type="email" style={S.input} value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} autoComplete="email" />
          <label htmlFor="g-seats" style={S.label}>Number of seats</label>
          <select id="g-seats" style={S.input} value={form.party_size} onChange={(e) => setForm({ ...form, party_size: e.target.value })}>
            {[1, 2, 3, 4, 5].map((n) => <option key={n} value={n}>{n}</option>)}
          </select>
          <label style={{ display: "flex", gap: 10, alignItems: "flex-start", marginTop: 16, fontSize: 14 }}>
            <input type="checkbox" checked={form.consent} onChange={(e) => setForm({ ...form, consent: e.target.checked })} style={{ marginTop: 3, width: 18, height: 18 }} />
            <span>I agree that my name, phone number and email are stored to manage this event, and used to contact me about it. I can ask to be removed at any time.</span>
          </label>
          {error && <div style={S.err} role="alert">{error}</div>}
          <button type="submit" style={S.btn} disabled={busy}>{busy ? "Registering..." : "Register now"}</button>
        </form>
      )}

      {phase === "registered" && (
        <>
          <div style={S.ok}>You are registered{fee > 0 ? ", pending payment." : "."} A confirmation was sent{form.email ? ` to ${form.email}` : ""} if an email was given.</div>
          {fee > 0 && (
            <>
              <div style={S.warn}>Payment due: <b>Rs {fee * seats}</b> for {seats} seat{seats > 1 ? "s" : ""}. Unpaid seats are released after a short hold.</div>
              {error && <div style={S.err} role="alert">{error}</div>}
              <button type="button" style={S.btn} onClick={pay} disabled={busy}>{busy ? "Processing..." : `Pay Rs ${fee * seats} (test payment)`}</button>
              <p style={{ ...S.muted, fontSize: 12 }}>This is a test checkout. No real money is charged.</p>
            </>
          )}
        </>
      )}

      {phase === "paid" && (
        <>
          <div style={S.ok}>{fee > 0 ? "Payment received. Your seat is confirmed." : "Your seat is confirmed."} {note}</div>
          <Feedback token={token} />
        </>
      )}
    </Frame>
  );
}
