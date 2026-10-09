import { useState } from "react";

/* ---------- styles ---------- */
const css = `
:root{--ink:#14202B;--mut:#5B6B77;--teal:#2DD7C0;--mint:#E4F7F5;--line:#E3E7EA;--bg:#F1F3F4;--red:#C0233B;--redbg:#FDE8EC;--amb:#8A5A00;--ambbg:#FFF3D6;--grn:#176B3A;--grnbg:#E7F4EA}
*{box-sizing:border-box}body{margin:0}
.k{font-family:Inter,system-ui,sans-serif;color:var(--ink);background:#fff;min-height:100vh}

/* Top Navigation / Breadcrumbs */
.top-bar{display:flex;justify-content:space-between;align-items:center;padding:12px 24px;background:var(--ink);color:#fff;border-bottom:1px solid #263544;position:sticky;top:0;z-index:90}
.top-brand{display:flex;align-items:center;gap:12px;font-size:16px;font-weight:700}
.top-brand span{color:var(--teal)}
.top-right{display:flex;align-items:center;gap:12px}
.user-pill{display:flex;align-items:center;gap:8px;background:#1e2d3a;padding:5px 12px;border-radius:20px;font-size:12px;color:#cfd8dc;border:1px solid #334454}
.user-dot{width:8px;height:8px;background:var(--teal);border-radius:50%}
.btn-sm{padding:6px 12px;font-size:12px;border-radius:6px;border:1px solid #3a4854;background:#1e2d3a;color:#fff;cursor:pointer;font-weight:600}
.btn-sm:hover{background:#2a3c4c}

/* Home / Login Screen */
.home-wrap{min-height:100vh;background:linear-gradient(135deg,#0d151c 0%,#16232e 50%,#0c2a32 100%);color:#fff;display:flex;flex-direction:column}
.home-nav{display:flex;justify-content:space-between;align-items:center;padding:24px 48px;border-bottom:1px solid rgba(255,255,255,0.08)}
.home-logo{font-size:24px;font-weight:800;color:#fff;display:flex;align-items:center;gap:8px}
.home-logo b{color:var(--teal)}
.home-grid{flex:1;display:grid;grid-template-columns:1.2fr 0.9fr;gap:56px;align-items:center;padding:64px 48px;max-width:1200px;margin:0 auto;width:100%}
@media(max-width:900px){.home-grid{grid-template-columns:1fr;padding:32px 24px}}
.home-hero h1{font-size:48px;line-height:1.15;margin:16px 0;letter-spacing:-0.02em}
.home-hero h1 span{background:linear-gradient(90deg,#fff,#2DD7C0);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.home-hero p{font-size:17px;color:#9fb3c4;line-height:1.6;margin-bottom:28px}
.home-tags{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:32px}
.home-tags span{background:rgba(45,215,192,0.12);color:var(--teal);border:1px solid rgba(45,215,192,0.25);padding:6px 14px;border-radius:99px;font-size:12px;font-weight:600}
.home-card{background:#fff;color:var(--ink);border-radius:18px;padding:36px;box-shadow:0 24px 48px rgba(0,0,0,0.4);border:1px solid rgba(255,255,255,0.2)}
.home-card h2{margin:0 0 8px;font-size:24px}
.home-card p{color:var(--mut);font-size:14px;margin-top:0;margin-bottom:24px}

/* Headers & Layout */
.hd{display:flex;justify-content:space-between;align-items:center;padding:14px 32px;border-bottom:1px solid var(--line)}
.hd small{display:block;color:var(--mut);font-size:11px}
.lang{display:flex;border:1px solid var(--line);border-radius:10px;padding:4px;gap:4px}
.lang span{padding:8px 22px;border-radius:8px;font-size:13px;cursor:pointer}.lang .on{background:var(--mint);font-weight:600}
.hero{background:linear-gradient(120deg,#2b2623,#1d3a42);color:#fff;padding:48px 32px}
.hero b{color:var(--teal);font-size:11px;letter-spacing:.04em}.hero h1{font-size:34px;margin:8px 0}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:28px;padding:32px;max-width:1100px;margin:auto}
@media(max-width:800px){.grid{grid-template-columns:1fr}}
.card{border:1px solid var(--line);border-radius:12px;padding:22px;background:#fff}
.mint{background:var(--mint);border-radius:10px;padding:16px}
.row{display:flex;justify-content:space-between;gap:12px;padding:9px 0;border-bottom:1px solid var(--line);font-size:14px}
.row span:first-child{color:var(--mut)}
.f{margin:14px 0}.f label{display:block;font-weight:600;font-size:14px;margin-bottom:6px}
.f input,.f select,.f textarea{width:100%;padding:11px 12px;border:1px solid var(--line);border-radius:8px;font:inherit;font-size:14px;background:#fff}
.f input[readonly]{background:#F3F4F6}.f.err input{border-color:var(--red)}
.hint{font-size:12px;color:var(--mut);margin-top:4px}.hint.e{color:var(--red)}
.btn{display:block;width:100%;padding:12px;border-radius:8px;border:1px solid var(--line);background:#fff;font:inherit;font-weight:600;cursor:pointer;margin-top:10px;text-align:center}
.btn.p{background:var(--teal);border-color:var(--teal);color:var(--ink)}.btn:disabled{opacity:.6;cursor:wait}
.al{border-radius:10px;padding:14px;margin:14px 0;font-size:14px}.al b{display:block;margin-bottom:2px}
.al.e{background:var(--redbg);color:var(--red)}.al.w{background:var(--ambbg);color:var(--amb)}.al.g{background:var(--grnbg);color:var(--grn)}
.pill{display:inline-block;font-size:11px;font-weight:600;padding:4px 10px;border-radius:99px;margin-right:6px}
.pill.g{background:var(--grnbg);color:var(--grn)}.pill.w{background:var(--ambbg);color:var(--amb)}.pill.e{background:var(--redbg);color:var(--red)}
.tabs{display:flex;border:1px solid var(--line);border-radius:10px;padding:4px;margin:14px 0}
.tabs span{flex:1;text-align:center;padding:9px;border-radius:8px;font-size:14px;cursor:pointer}.tabs .on{background:var(--mint);font-weight:600}
.ag{display:flex;gap:28px;padding:12px 0;border-bottom:1px solid var(--line);font-size:14px}.ag b{width:80px}.ag span{color:var(--mut)}
.big{font-size:34px;font-weight:700}
.msg{max-width:440px;margin:28px auto;border:1px solid var(--line);border-radius:14px;overflow:hidden;background:#fff}
.msg .body{padding:20px}.msg h2{margin:0 0 8px;font-size:20px}
.wrap{background:var(--bg);padding:1px 0}

/* Wizard */
.wiz-container{max-width:1000px;margin:32px auto;padding:0 20px}
.wiz-hdr{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px}
.wiz{background:#E0FAF7;min-height:560px;padding:32px;border-radius:16px;box-shadow:0 12px 30px rgba(0,0,0,0.06)}
.steps{display:flex;justify-content:space-between;margin-bottom:28px}
.steps div{text-align:center;font-size:13px;flex:1}.steps i{display:block;width:34px;height:34px;border-radius:50%;border:1px solid #7a8b8b;margin:0 auto 6px;background:#fff}
.steps .on i{background:#3DE0D0}.steps .on{font-weight:700}
.tpl{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}.tpl div{background:#fff;border:1px solid var(--ink);border-radius:14px;padding:30px 8px;text-align:center}
.tpl .on{background:#3DE0D0}
table{width:100%;border-collapse:collapse;font-size:13px}th{background:var(--ink);color:#fff;text-align:left;padding:10px}td{padding:10px;border-bottom:1px solid var(--line)}

/* Dashboard & Side Navigation */
.dash{display:grid;grid-template-columns:250px 1fr;min-height:calc(100vh - 56px)}
@media(max-width:850px){.dash{grid-template-columns:1fr}}
.side{background:#16202B;color:#cfd8dc;padding:24px 16px;font-size:14px;display:flex;flex-direction:column}
.side-title{font-size:11px;font-weight:700;color:#607d8b;letter-spacing:0.05em;margin:16px 0 8px 8px}
.side-item{padding:10px 14px;border-radius:8px;cursor:pointer;margin-bottom:4px;display:flex;justify-content:space-between;align-items:center;transition:background 0.15s}
.side-item:hover{background:#1e2d3b}
.side-item.on{background:#233544;color:#fff;font-weight:600}
.side-item.on .dot{background:var(--teal)}
.dot{width:8px;height:8px;border-radius:50%;background:#455a64}
.side-sub{margin:4px 0 12px 14px;border-left:2px solid #2e4354;padding-left:10px;display:flex;flex-direction:column;gap:3px}
.sub-link{padding:7px 10px;border-radius:6px;font-size:13px;color:#9fb3c4;cursor:pointer;transition:all .15s}
.sub-link:hover{background:#1f2e3d;color:#fff}
.sub-link.on{background:var(--teal);color:var(--ink);font-weight:700}
.side-btn{margin:12px 0 20px}

/* Sub-page Switcher Bar */
.sub-bar{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;padding-bottom:14px;border-bottom:1px solid var(--line);flex-wrap:wrap;gap:12px}
.pill-group{display:flex;gap:6px;flex-wrap:wrap}
.state-pill{font-size:12px;padding:6px 12px;border-radius:20px;border:1px solid var(--line);background:#fff;cursor:pointer;color:var(--mut);font-weight:500}
.state-pill.on{background:var(--ink);color:#fff;border-color:var(--ink);font-weight:600}

.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:16px 0}.stats .mint .big{font-size:28px}
@media(max-width:1100px){.stats{grid-template-columns:repeat(2,1fr)}}
.bar{height:8px;background:#DFF5F2;border-radius:9px;margin:6px 0}.bar i{display:block;height:100%;background:#3DE0D0;border-radius:9px}
.qr{width:180px;height:180px;margin:12px auto;background:repeating-conic-gradient(var(--ink) 0 25%,#fff 0 50%) 0 0/30px 30px;border:8px solid #fff;outline:1px solid var(--line)}
.scan{background:var(--ink);color:#fff;border-radius:12px;height:300px;display:grid;place-items:center}
`;

/* ---------- shared bits ---------- */
const Row = ({ k, v }) => <div className="row"><span>{k}</span><b>{v}</b></div>;
const Alert = ({ t, title, children }) => <div className={`al ${t}`}><b>{title}</b>{children}</div>;
const Field = ({ label, hint, err, ...p }) => (
  <div className={`f ${err ? "err" : ""}`}><label>{label}</label><input {...p} />
    <div className={`hint ${err ? "e" : ""}`}>{err || hint}</div></div>
);
const Hdr = ({ right }) => (
  <div className="hd"><div><b style={{ fontSize: 20 }}>koodal</b><small>Bring people together.</small></div>{right}</div>
);
const Lang = () => <div className="lang"><span className="on">✓ English</span><span>हिन्दी</span><span>മലയാളം</span></div>;
const Hero = ({ sub = "A day to connect, share ideas and shape what comes next." }) => (
  <div className="hero"><b>KOODAL EVENTS PRESENTS</b><h1>Define</h1><div>{sub}</div>
    <p><b style={{ color: "#fff", fontSize: 13 }}>23 October 2026 · Kochi</b></p></div>
);
const Invite = () => (
  <div>
    <div className="mint"><small>YOUR PERSONAL INVITATION</small><h3>An invitation to Define</h3>
      <div style={{ color: "var(--mut)", fontSize: 14 }}>Friday 23 October 2026 · 10:00 AM to 4:00 PM IST<br />Grand Hall, Kochi</div>
      <p style={{ fontSize: 14 }}>Join us for a day of conversations, interactive discussions and a practical afternoon workshop.</p>
      <b style={{ fontSize: 14 }}>Organized by Koodal Events</b><div className="hint">₹500 per seat · choose 1–4 seats</div></div>
    <h3>Your day at a glance</h3>
    {[["10:00 AM", "Check-in"], ["10:30 AM", "Opening session"], ["11:00 AM", "Interactive discussions"], ["12:30 PM", "Lunch"], ["1:30 PM", "Afternoon workshop"], ["3:45 PM", "Closing · finishes by 4:00 PM"]]
      .map(([t, a]) => <div className="ag" key={t}><b>{t}</b><span>{a}</span></div>)}
    <div className="hint">Agenda is an example programme. All times are in IST.</div>
  </div>
);
const Page = ({ left, right, hero = true, hdr = <Lang /> }) => (
  <><Hdr right={hdr} />{hero && <Hero />}<div className="grid"><div>{left}</div><div>{right}</div></div>
    <div className="hd" style={{ borderTop: "1px solid var(--line)", borderBottom: 0, fontSize: 12, color: "var(--mut)" }}>
      <span>Koodal Events · Personal invitations, thoughtful gatherings.</span><span>Your details are used only for this event.</span></div></>
);

/* ---------- guest registration (all states) ---------- */
const reg = (rest) => (
  <div className="card">{rest}</div>
);
function Guest({ s }) {
  const full = s === "full", saving = s === "saving", bad = s === "error";
  const summary = (title, intro, banner, pill) => reg(<>
    <h2>{title}</h2><p>{intro}</p>{banner}<span className="pill g">✓ REGISTERED</span><span className="pill w">! PAYMENT PENDING</span>
    <Row k="Guest name" v="Anjali Menon" /><Row k="Phone number" v="+91 •••••• 4321" /><Row k="Email address" v="anjali.menon@example.org" />
    <Row k="Seats and language" v="1 seat · English" /><Row k="Date and time" v="Fri 23 Oct 2026, 10:00 AM to 4:00 PM IST" />
    <Row k="Venue" v="Grand Hall, Kochi" /><Row k="Registration ID" v="KDL-DEF-2026-004321" />
    <div className="mint" style={{ marginTop: 14 }}>1 seat × ₹500 <b style={{ float: "right" }}>Payable ₹500</b><div className="hint">Payment has not been received.</div></div>
    <p className="hint">Your registration is saved. Complete the ₹500 payment separately; this summary is not proof of payment.</p>
    <button className="btn p">Pay now ₹500</button>{pill}</>);

  if (s === "success") return <Page left={<Invite />} right={summary("You're registered, Anjali", "We look forward to welcoming you to Define. Keep this summary for your records.",
    <Alert t="g" title="Your registration is confirmed">1 seat registered for Define. The ₹500 payment is still pending.</Alert>, <button className="btn">Add to calendar</button>)} />;
  if (s === "existing") return <Page left={<Invite />} right={summary("You're already on the list", "Welcome back, Anjali. We found your existing registration; there's no need to register again.",
    <Alert t="g" title="Your existing registration is safe">The same 1-seat registration is shown below. Payment is still pending.</Alert>, <button className="btn">View registration</button>)} />;
  if (s === "expired") return <Page left={<Invite />} right={reg(<>
    <h2>This personal link has expired</h2><p>For your privacy, guest details are hidden. You can request a fresh invitation from Koodal Events.</p>
    <Alert t="w" title="A new link is needed">This link can no longer be used to register for Define.</Alert>
    <button className="btn p">Request a new link</button><div className="hint">If you no longer have access to that number, contact Koodal Events using the number in your original SMS.</div></>)} />;
  if (s === "waitlisted") return <Page left={<Invite />} right={reg(<>
    <h2>You're on the waitlist, Anjali</h2><p>We've received your request for one seat.</p><span className="pill g">✓ On the waitlist</span>
    <div className="mint" style={{ margin: "14px 0" }}>Your queue position:<div className="big">12</div><b>1 seat requested</b><div className="hint">Example queue position · not a verified live position.</div></div>
    <Alert t="g" title="Your waitlist request is received">No charge has been made. Joining is not a registration and does not guarantee a seat.</Alert>
    <Row k="Waitlist reference" v="WL-DEF-004321" /><h3>What happens next</h3>
    <p style={{ fontSize: 14 }}><b>Watch for your offer.</b> We'll send a personal seat offer by email or WhatsApp.<br /><b>Claim within 30 minutes.</b> The window starts when the offer is issued.<br /><b>Confirm and pay after claiming.</b></p>
    <button className="btn p">View waitlist status</button></>)} />;
  if (s === "offer-expired") return <Page left={<Invite />} right={reg(<>
    <h2>Your seat offer has expired</h2><p>Anjali, the 30-minute claim window for this Define seat offer has ended.</p><span className="pill e">× Offer expired</span>
    <Alert t="w" title="00:00 · Offer ended">Deadline: 22 October 2026 · 10:30 AM IST</Alert>
    <Alert t="e" title="This offer can no longer be claimed.">We couldn't reserve this seat after the 30-minute deadline.</Alert>
    <Row k="Waitlist reference" v="WL-DEF-004321" /><button className="btn p">View waitlist status</button></>)} />;

  return <Page left={<Invite />} right={reg(<>
    <h2>{saving ? "Saving your registration" : bad ? "Let's check your details" : full ? "Define is currently full" : "Register for Define"}</h2>
    <p>{saving ? "Your details are being submitted. Please keep this page open." : bad ? "Your entries are still here. Correct the highlighted fields and try again."
      : full ? "Join the waitlist and we'll contact you if a place becomes available." : "Thanks for speaking with us. Complete your details below to join us in Kochi."}</p>
    {bad && <Alert t="e" title="Registration was not saved">Fix your email and give consent, then select Register again.</Alert>}
    {full && <Alert t="w" title="No seats are available right now">The waitlist does not guarantee a seat. No registration or payment is completed by joining.</Alert>}
    <Field label="Guest name · read-only" value="Anjali Menon" readOnly hint="Provided by Koodal Events after your phone call." />
    <Field label="Phone number · read-only" value="+91 •••••• 4321" readOnly hint="Tied to your personal SMS link; these details cannot be edited." />
    <Field label="Email address" defaultValue={saving ? "anjali.menon@example.org" : bad ? "anjali.menon@" : ""} err={bad && "Enter a valid email address, such as anjali.menon@example.org."} readOnly={saving} hint="For your registration summary and event updates." />
    <div className="f"><label>Number of seats</label><select disabled={saving}><option>1</option><option>2</option><option>3</option><option>4</option></select><div className="hint">Choose 1, 2, 3 or 4 seats · ₹500 per seat.</div></div>
    <div className="f"><label>Language preference</label><select disabled={saving}><option>English</option><option>हिन्दी</option><option>മലയാളം</option></select></div>
    <div className="mint">1 seat × ₹500 <b style={{ float: "right" }}>Total ₹500</b><div className="hint">{full ? "No payment to join." : "Payment follows registration."}</div></div>
    <label style={{ display: "flex", gap: 10, margin: "16px 0", fontSize: 14 }}><input type="checkbox" defaultChecked={saving} /> I agree to receive event updates and to the processing of my data</label>
    {bad && <div className="hint e">Please agree to event updates and data processing to continue.</div>}
    <button className="btn p" disabled={saving}>{saving ? "Registering…" : full ? "Join the waitlist" : "Register"}</button>
    <div className="hint">{saving ? "Please wait while we save your registration. Do not submit again." : "Your personal invitation is private. Please do not forward this link."}</div></>)} />;
}

/* ---------- payment (all states) ---------- */
function Pay({ s }) {
  const T = {
    form: ["Complete your registration", "Your details are saved, Anjali. Choose a payment method to secure your two seats for Define.", "UPI"],
    verifying: ["We're checking your payment", "Keep this page open while the test payment is verified. Your order is not paid yet.", "Card"],
    success: ["Test payment successful", "Thank you, Anjali. Your two seats are secured in this test result. No money was charged.", "Card"],
    failed: ["Your payment didn't go through", "Your two seats are still on hold. You can try again before the original hold expires.", "Netbanking"],
    expired: ["Your seat hold has expired", "The payment was not completed within the 15-minute hold. Your two seats have been released.", "UPI"],
  }[s] || ["Complete your registration", "Your details are saved, Anjali. Choose a payment method to secure your two seats for Define.", "UPI"];

  const [m, setM] = useState(T[2]);
  const done = s === "success", gone = s === "expired";
  return (<>
    <Hdr right={<span className="pill w">! Test mode</span>} />
    <div style={{ background: "var(--mint)", padding: "28px 32px" }}><h1 style={{ margin: 0 }}>{T[0]}</h1><p style={{ color: "var(--mut)" }}>{T[1]}</p></div>
    <div className="grid">
      <div className="card"><div className="mint"><small>KOODAL EVENTS</small><h2>Define</h2>Friday 23 October 2026 · 10:00 AM–4:00 PM IST<br />Grand Hall, Kochi</div>
        <div className="hint">Order ORD-DEF-2026-004322</div>
        <span className={`pill ${done ? "g" : gone ? "e" : "w"}`}>{done ? "✓ 2 seats secured · test result" : gone ? "× 2 seats released" : "! Payment pending"}</span>
        <Row k="Seats" v="2 × ₹500 each" /><Row k="Subtotal" v="₹1,000" /><Row k="Taxes" v="₹0" />
        <div className="mint" style={{ marginTop: 12 }}><b>Total</b><b style={{ float: "right", fontSize: 22 }}>₹1,000</b></div>
        <p><b>Anjali Menon</b><br />anjali.menon@example.org</p>
        {!done && <div className="mint"><b>{gone ? "Seat hold expired" : "Your seats are on hold"}</b><b style={{ float: "right", fontSize: 22 }}>{gone ? "00:00" : s === "failed" ? "11:48" : "12:34"}</b>
          <div className="hint">Unpaid seats are held for 15 minutes from registration. Changing methods or retrying does not restart the hold.</div></div>}</div>
      <div className="card">
        {gone ? <><h2>Start a new registration</h2><Alert t="e" title="2 seats released">The original 15-minute reservation has ended. No money was charged in test mode.</Alert>
          <p>Register again to check current availability. Seats are not guaranteed.</p><button className="btn p">Register again</button></>
          : done ? <><h2>Your test receipt</h2><Alert t="g" title="Test payment successful">2 seats secured · test result. No money was charged.</Alert>
            <Row k="Receipt" v="RCPT-DEF-2026-004322" /><Row k="Order" v="ORD-DEF-2026-004322" /><Row k="Method" v="Card · test card ending 4242" /><Row k="Demo reference" v="TEST-PAY-DEF-004322" />
            <button className="btn">Download receipt</button></>
            : <><h2>{s === "failed" ? "Try your payment again" : s === "verifying" ? "Card payment in progress" : "Choose how to pay"}</h2>
              {s === "failed" && <Alert t="e" title="Payment cancelled">Payment was cancelled before authorization.</Alert>}
              <div className="tabs">{["UPI", "Card", "Netbanking"].map(x => <span key={x} className={m === x ? "on" : ""} onClick={() => s !== "verifying" && setM(x)} style={{ cursor: "pointer" }}>{m === x && "✓ "}{x}</span>)}</div>
              {m === "UPI" && <Field label="UPI ID" defaultValue="anjali@testbank" hint="Test example only. Enter a test UPI ID in name@bank format." />}
              {m === "Card" && <><Field label="Card number" value="•••• •••• •••• 4242" readOnly hint="Synthetic test card · not a real card" /><Field label="Expiry" value="12/28" readOnly /></>}
              {m === "Netbanking" && <div className="f"><label>Bank</label><select><option>Demo Bank</option></select><div className="hint">Generic test bank only; no live bank connection.</div></div>}
              {s === "verifying" && <Alert t="w" title="Verification is pending">Do not retry or switch methods while we check the result. No real money will be charged.</Alert>}
              <button className="btn p" disabled={s === "verifying"}>{s === "verifying" ? "Processing payment…" : s === "failed" ? "Try again" : "Pay ₹1,000"}</button>
              <div className="hint">This is a simulated checkout, not a live payment gateway. No real money will be charged.</div></>}
      </div></div></>);
}

/* ---------- ticket + staff check-in ---------- */
const Ticket = () => (<><Hdr right={<small>Demo registration</small>} />
  <div style={{ background: "var(--mint)", padding: "28px 32px" }}><span className="pill g">✓ Registration complete · demo</span><h1>Your ticket is ready, Anjali.</h1></div>
  <div className="grid"><div className="card mint"><small>KOODAL EVENTS · EVENT TICKET</small><h2>Define</h2>Friday 23 October 2026 · 10:00 AM–4:00 PM IST<br />Grand Hall, Kochi
    <Row k="Guest name" v="Anjali Menon" /><Row k="Seats" v="2 seats" /><Row k="Demo ticket reference" v="KDL-DEF-004322" /></div>
    <div className="card" style={{ textAlign: "center" }}><span className="pill">Demo ticket</span><div className="qr" /><div className="hint">Demo QR · not valid for admission</div><button className="btn p">Download ticket</button></div></div></>);

function Checkin({ s }) {
  const R = { ok: ["g", "Checked in", "Guest check-in recorded", "Welcome Anjali and her guest to Define."], dup: ["w", "Already checked in", "No additional check-in recorded.", "This ticket has already been used. Do not admit the same seats again."], bad: ["e", "Invalid code", "Ticket not found", "This code does not match a ticket for Define. Try scanning again or search for the guest."] }[s];
  return (<><Hdr right={<span>Staff check-in · Front desk</span>} />
    <div className="grid"><div><h2>Scan a ticket</h2><div className="scan">Position the QR code within the guide</div>
      <Field label="Search by guest name or ticket ID" defaultValue={s === "bad" ? "KDL-UNKNOWN-009999" : "KDL-DEF-004322"} err={s === "bad" && "No matching ticket. Check the ID or search by name."} hint="Search still requires a valid, eligible ticket for this event." /><button className="btn p">Search</button></div>
      <div className="card"><small>TICKET RESULT · DEMO</small><h2 style={{ color: `var(--${R[0] === "g" ? "grn" : R[0] === "w" ? "amb" : "red"})` }}>{R[1]}</h2>
        {s !== "bad" && <div className="mint"><b>Anjali Menon</b><br />KDL-DEF-004322 · 2 seats {s === "ok" ? "admitted" : "· original admission"}</div>}
        <Alert t={R[0]} title={R[2]}>{R[3]}</Alert>
        {s !== "bad" && <><Row k={s === "ok" ? "First check-in" : "Original check-in"} v="10:06 AM IST" />{s === "dup" && <Row k="Seen again" v="10:12 AM IST" />}</>}
        <button className="btn p">Scan next ticket</button></div></div></>);
}

/* ---------- feedback ---------- */
function Feedback({ s }) {
  const [r, setR] = useState(s === "form" ? 0 : 4);
  const stars = (n) => [1, 2, 3, 4, 5].map(i => <button key={i} className="btn" disabled={s !== "form"} onClick={() => setR(i)} style={{ width: 54, display: "inline-block", margin: 3, color: i <= n ? "var(--teal)" : "var(--mut)" }}>{i <= n ? "★" : "☆"}</button>);
  const done = s !== "form" && s !== "submitting";
  return (<Page hdr={<Lang />} hero={false}
    left={<><small>EVENT FEEDBACK</small><h1>Good gatherings start with listening.</h1><p>Thank you for being part of Define. Your perspective helps us shape what comes next.</p></>}
    right={<div className="card">
      {done ? <><span className="pill g">✓ Feedback received</span><h2>{s === "repeat" ? "You've already shared your feedback" : "Thank you"}</h2>
        <Row k="Experience rating" v="★★★★☆ 4 / 5 · Very good" /><Row k="How did you hear?" v="Phone call" /><Row k="Your comment" v="The discussions were thoughtful. A little more time for questions would be helpful." />
        <button className="btn">Back to event</button></>
        : <><h2>How was Define?</h2><div className="hint">Rating and event discovery are required. Your comment is optional.</div>
          <h4>How would you rate your experience?</h4>{stars(r)}
          <h4>How did you hear about this event?</h4>
          {["Phone call", "SMS", "WhatsApp", "Email", "Instagram", "Friend or family", "Other"].map(o => <label key={o} style={{ display: "block", padding: 6, fontSize: 14 }}><input type="radio" name="h" disabled={s === "submitting"} defaultChecked={s === "submitting" && o === "Phone call"} /> {o}</label>)}
          <div className="f"><label>Anything else you'd like to share? · Optional</label><textarea rows={3} disabled={s === "submitting"} placeholder="Share your thoughts…" /></div>
          <button className="btn p" disabled={s === "submitting"}>{s === "submitting" ? "Submitting…" : "Submit feedback"}</button></>}
    </div>} />);
}

/* ---------- messages: email / WhatsApp previews ---------- */
const MSG = {
  "Invite": { org: "KOODAL EVENTS PRESENTS", t: "Anjali, you're invited to Define.", b: "Join us for a day of ideas, discussion and new connections in Kochi. Confirm your seat through your personal link.", d: ["Friday 23 October 2026", "10:00 AM–4:00 PM IST", "Grand Hall, Kochi"], cta: "Register now" },
  "Clinic reminder": { org: "CITYCARE CLINIC · KOCHI", t: "Your appointment is coming up, Anjali.", b: "Your routine appointment at CityCare Clinic is on Saturday. Please confirm your attendance and bring your appointment confirmation.", d: ["Saturday 24 October 2026", "10:00 AM–10:30 AM IST", "CityCare Clinic, MG Road, Kochi"], cta: "Register now" },
  "School notice": { org: "SUNRISE PUBLIC SCHOOL", t: "Let's plan the next term together.", b: "Join us for a parent meeting to hear next-term updates and talk with our teachers.", d: ["Monday 26 October 2026", "3:00 PM–4:00 PM IST", "School Auditorium, Sunrise Public School, Kochi"], cta: "Register now" },
  "Payment reminder": { org: "KOODAL EVENTS PRESENTS", t: "A gentle reminder to complete your booking.", b: "Your two-seat booking for Define has ₹1,000 outstanding. Payment due: Thursday 22 October 2026.", d: ["Friday 23 October 2026", "10:00 AM–4:00 PM IST", "Grand Hall, Kochi"], cta: "Register now" },
  "Registration confirmed": { org: "KOODAL EVENTS PRESENTS", t: "You're registered for Define", b: "Your registration is confirmed. Adding this event to your calendar does not confirm payment.", d: ["Friday 23 October 2026", "10:00 AM–4:00 PM IST", "Grand Hall, Kochi"], cta: "Google Calendar", alt: "Apple / Outlook (.ics)" },
  "Waitlist offer": { org: "KOODAL EVENTS PRESENTS", t: "A seat opened up, claim it within 30 minutes.", b: "One seat for Define is available. Claim before 22 October 2026 · 10:30 AM IST. This offer is not a paid registration.", d: ["Friday 23 October 2026", "10:00 AM–4:00 PM IST", "Grand Hall, Kochi"], cta: "Claim seat" },
  "Invite (हिन्दी)": { org: "कूडल इवेंट्स की प्रस्तुति", t: "अंजलि, आप Define में आमंत्रित हैं", b: "कोच्चि में विचारों, चर्चाओं और नए संबंधों से भरे एक दिन के लिए हमारे साथ जुड़ें।", d: ["शुक्रवार, 23 अक्टूबर 2026", "सुबह 10:00 बजे–शाम 4:00 बजे (भारतीय मानक समय)", "ग्रैंड हॉल, कोच्चि"], cta: "अभी पंजीकरण करें" },
  "Invite (മലയാളം)": { org: "കൂടൽ ഇവന്റ്സ് അവതരിപ്പിക്കുന്നു", t: "അഞ്ജലി, Define-ലേക്ക് നിങ്ങളെ ക്ഷണിക്കുന്നു.", b: "ആശയങ്ങളും ചർച്ചകളും പുതിയ സൗഹൃദങ്ങളും നിറഞ്ഞ ഒരു ദിവസത്തിനായി ഞങ്ങളോടൊപ്പം ചേരൂ.", d: ["2026 ഒക്ടോബർ 23, വെള്ളിയാഴ്ച", "രാവിലെ 10:00–വൈകിട്ട് 4:00", "ഗ്രാൻഡ് ഹാൾ, കൊച്ചി"], cta: "ഇപ്പോൾ രജിസ്റ്റർ ചെയ്യൂ" },
};

function Message({ k, ch }) {
  const m = MSG[k] || MSG["Invite"], wa = ch === "WhatsApp";
  return (<div className="wrap"><div className="msg">
    <div className="hero" style={{ padding: 28 }}><b>{m.org}</b><h1 style={{ fontSize: 26 }}>{wa ? m.t.split(",")[0] : "Define"}</h1></div>
    <div className="body">{!wa && <h2>{m.t}</h2>}<p style={{ color: "var(--mut)", fontSize: 14 }}>{m.b}</p>
      <div className="mint" style={{ fontSize: 14 }}>{m.d.map(x => <div key={x}>{x}</div>)}</div>
      <button className="btn p">{m.cta}</button>
      {wa ? ["Confirm", "Decline", "Call me back"].map(x => <button className="btn" key={x}>{x}</button>) : m.alt ? <button className="btn">{m.alt}</button> : <div className="hint" style={{ marginTop: 16 }}>To stop these messages, use the unsubscribe link.</div>}
    </div></div></div>);
}

/* ---------- 1. Home / Login Landing Page ---------- */
function Home({ onLogin }) {
  const [email, setEmail] = useState("organizer@example.com");
  const [password, setPassword] = useState("password123");
  const [loading, setLoading] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      onLogin({ name: "Asha Thomas", email, role: "organizer" });
    }, 350);
  };

  return (
    <div className="home-wrap">
      <div className="home-nav">
        <div className="home-logo">
          <span>✳</span> koodal <b>/ EventReach</b>
        </div>
        <div style={{ display: "flex", gap: 12 }}>
          <button className="btn-sm" onClick={() => onLogin({ name: "Asha Thomas", email: "organizer@example.com", role: "organizer" })}>
            Demo Sign In →
          </button>
        </div>
      </div>

      <div className="home-grid">
        <div className="home-hero">
          <div className="home-tags">
            <span>✨ Multilingual Voice AI</span>
            <span>📞 Exotel Calling</span>
            <span>💳 Real-time Payments</span>
            <span>🔒 DPDP Privacy by Design</span>
          </div>
          <h1>
            Turn voice notes into <span>live calling campaigns</span> in minutes.
          </h1>
          <p>
            An organizer uploads an event poster, a voice note and contacts.
            EventReach drafts the event, translates it into Hindi, Malayalam, and Tamil,
            calls attendees with Exotel IVR, and collects online registrations & payments.
          </p>
          <div style={{ display: "flex", gap: 16 }}>
            <div className="mint" style={{ padding: "12px 18px", color: "var(--ink)", borderRadius: 10 }}>
              <div style={{ fontSize: 22, fontWeight: 700 }}>100%</div>
              <small>Automated dispatch</small>
            </div>
            <div className="mint" style={{ padding: "12px 18px", color: "var(--ink)", borderRadius: 10 }}>
              <div style={{ fontSize: 22, fontWeight: 700 }}>4</div>
              <small>Presets supported</small>
            </div>
            <div className="mint" style={{ padding: "12px 18px", color: "var(--ink)", borderRadius: 10 }}>
              <div style={{ fontSize: 22, fontWeight: 700 }}>3 Languages</div>
              <small>Hindi · Malayalam · Tamil</small>
            </div>
          </div>
        </div>

        <div className="home-card">
          <h2>Organizer Sign In</h2>
          <p>Access your campaigns, analytics funnels, and attendee response dashboard.</p>
          <form onSubmit={handleSubmit}>
            <div className="f">
              <label>Work Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="organizer@example.com"
                required
              />
            </div>
            <div className="f">
              <label>Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                required
              />
            </div>
            <button type="submit" className="btn p" disabled={loading} style={{ marginTop: 20 }}>
              {loading ? "Signing in…" : "Sign In to Dashboard"}
            </button>
            <div className="hint" style={{ textAlign: "center", marginTop: 12 }}>
              Default demo organizer: <b>organizer@example.com</b>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

/* ---------- 2. Organizer Campaign Wizard Flow ---------- */
const STEPS = ["Template", "Upload", "Review", "Audience", "Translate", "Channels", "Test Call", "Launch"];

function Wizard({ onCancel, onLaunch }) {
  const [i, setI] = useState(0), [tpl, setTpl] = useState(0);
  const [extracting, setExtracting] = useState(false);

  const body = [
    <>
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
    </>,
    <>
      <h3>2. Upload poster and voice note</h3>
      <div className="tpl" style={{ gridTemplateColumns: "1fr 1fr" }}>
        <div style={{ border: "2px dashed #9fb3c4", background: "#f8fafb" }}>
          <b>Event Poster</b>
          <div className="hint">Drop PNG, JPG or WebP (max 10MB)</div>
          <span className="pill g" style={{ marginTop: 12 }}>✓ sample_poster.png</span>
        </div>
        <div style={{ border: "2px dashed #9fb3c4", background: "#f8fafb" }}>
          <b>Voice Note Audio</b>
          <div className="hint">Drop WAV, MP3, M4A or OGG (max 25MB)</div>
          <span className="pill g" style={{ marginTop: 12 }}>✓ voice_brief.mp3</span>
        </div>
      </div>
      <p>AI pipeline transcribing and extracting structured event details:</p>
      <div className="bar"><i style={{ width: "85%" }} /></div>
      <div className="hint">Guarded by monthly AI budget cap. Audio stored privately with HMAC-signed links.</div>
    </>,
    <>
      <h3>3. Review extracted event details</h3>
      <Field label="Event name" defaultValue="Define Healthcare & AI Seminar" />
      <Field label="Date and time" defaultValue="23 Oct 2026, 10:00 AM IST" />
      <Field label="Venue" defaultValue="Grand Hall, Block A" style={{ background: "#E4F7F5" }} />
      <Field label="City" defaultValue="Kochi" />
      <div className="f"><label>Registration Fee (INR)</label><input type="number" defaultValue="500" /></div>
    </>,
    <>
      <h3>4. Upload audience contacts list</h3>
      <table>
        <thead><tr><th>Name</th><th>Phone</th><th>Language</th><th>Segment</th><th>Status</th></tr></thead>
        <tbody>
          {[
            ["Anjali Menon", "+91 90••• ••011", "Malayalam", "Faculty", "Ready"],
            ["Rahul Nair", "+91 90••• ••012", "Malayalam", "Students", "Ready"],
            ["Fatima Sheikh", "+91 90••• ••013", "Hindi", "Alumni", "Ready"],
            ["Meera Iyer", "+91 90••• ••014", "Tamil", "Faculty", "Ready"],
            ["Arjun Verma", "+91 90••• ••015", "Hindi", "Students", "Ready"],
          ].map((r, n) => <tr key={n}>{r.map((c, j) => <td key={j}>{c}</td>)}</tr>)}
        </tbody>
      </table>
      <p><b>50 contacts imported.</b> Phone numbers encrypted at rest with Fernet AES; masked for display.</p>
    </>,
    <>
      <h3>5. Review multilingual translations</h3>
      <div className="card">Original English TTS script and copy reviewed. Back-translation generated for validation:</div>
      <table style={{ marginTop: 12 }}>
        <thead><tr><th>Language</th><th>Translation Preview</th><th>English Back-Translation</th><th>Action</th></tr></thead>
        <tbody>
          <tr>
            <td><b>Hindi (हिन्दी)</b></td>
            <td>नमस्ते {`{name}`}। आपको 23 अक्टूबर को 'Define' सेमिनार में आमंत्रित किया जाता है...</td>
            <td>Hello {`{name}`}. You are invited to 'Define' seminar on 23 October in Kochi.</td>
            <td><span className="pill g">✓ Approved</span></td>
          </tr>
          <tr>
            <td><b>Malayalam (മലയാളം)</b></td>
            <td>നമസ്കാരം {`{name}`}. ഒക്ടോബർ 23-ന് കൊച്ചിയിൽ നടക്കുന്ന 'Define'-ലേക്ക് ക്ഷണിക്കുന്നു...</td>
            <td>Hello {`{name}`}. Invitation to 'Define' on October 23 in Kochi. Press 1 to confirm.</td>
            <td><span className="pill g">✓ Approved</span></td>
          </tr>
          <tr>
            <td><b>Tamil (தமிழ்)</b></td>
            <td>வணக்கம் {`{name}`}. அக்டோபர் 23 அன்று கொச்சியில் நடைபெறும் 'Define'-ற்கு வருக...</td>
            <td>Hello {`{name}`}. We invite you to 'Define' on October 23 in Kochi.</td>
            <td><span className="pill g">✓ Approved</span></td>
          </tr>
        </tbody>
      </table>
    </>,
    <>
      <h3>6. Channels & Dispatch Configuration</h3>
      {["Voice call (Exotel outbound)", "SMS link (/s/code)", "Email with poster attachment", "WhatsApp message (mock adapter)", "Instagram caption (mock adapter)"].map((c) => (
        <label key={c} style={{ display: "block", padding: 8, fontSize: 14 }}>
          <input type="checkbox" defaultChecked /> {c}
        </label>
      ))}
      <Field label="Start date" defaultValue="23 Oct 2026" />
      <Field label="Calling hours" defaultValue="10:00 AM – 6:00 PM IST (India DND compliant)" readOnly />
      <Field label="Retries" defaultValue="Up to 3 attempts across different times of day" readOnly />
    </>,
    <>
      <h3>7. Preview with a test call</h3>
      <Field label="Phone number for test" placeholder="+91 98000 00000" defaultValue="+91 98000 00000" />
      <div className="f">
        <label>Language</label>
        <select><option>Malayalam</option><option>Hindi</option><option>English</option><option>Tamil</option></select>
      </div>
      <button className="btn p" style={{ width: 220 }}>Place Test Call</button>
      <div className="hint">Test call does not burn production contact credits.</div>
      <Alert t="g" title="Exotel Test Call Status">
        Call placed → Answered → Spoken script played → Keypad '1' pressed → Outcome: Confirmed.
      </Alert>
    </>,
    <>
      <h3>8. Ready to launch campaign</h3>
      <div className="card">
        <Row k="Campaign Name" v="Define Healthcare & AI Seminar" />
        <Row k="Template Preset" v="Seminar invite" />
        <Row k="Audience" v="50 contacts" />
        <Row k="Languages" v="English, Hindi, Malayalam, Tamil" />
        <Row k="Channels" v="Voice Call, SMS Short Link, Email" />
        <Row k="Schedule" v="Immediate dispatch within calling window" />
      </div>
      <Alert t="g" title="Safety Verification Passed">
        AI budget verified, DND numbers filtered, phone numbers encrypted, personal registration tokens generated.
      </Alert>
    </>,
  ][i];

  return (
    <div className="wiz-container">
      <div className="wiz-hdr">
        <div>
          <h2 style={{ margin: 0 }}>Create Outreach Campaign</h2>
          <small style={{ color: "var(--mut)" }}>Step {i + 1} of 8: {STEPS[i]}</small>
        </div>
        <button className="btn-sm" onClick={onCancel}>← Back to Dashboard</button>
      </div>

      <div className="wiz">
        <div className="steps">
          {STEPS.map((s, n) => (
            <div key={s} className={n === i ? "on" : ""}>
              <i />
              {s}
            </div>
          ))}
        </div>

        {body}

        <div style={{ display: "flex", justifyContent: "space-between", marginTop: 32 }}>
          <button className="btn" style={{ width: 140, borderRadius: 30 }} disabled={!i} onClick={() => setI(i - 1)}>
            Back
          </button>
          <button
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
          </button>
        </div>
      </div>
    </div>
  );
}

/* ---------- 3. Organizer Dashboard with Sidebar Subsections ---------- */
const Bar = ({ k, n, p }) => (
  <div style={{ display: "flex", gap: 10, alignItems: "center", fontSize: 13, marginBottom: 8 }}>
    <span style={{ width: 85, color: "var(--mut)" }}>{k}</span>
    <div className="bar" style={{ flex: 1 }}><i style={{ width: p + "%" }} /></div>
    <b style={{ width: 45, textAlign: "right" }}>{n}</b>
    <span style={{ width: 40, textAlign: "right", color: "var(--mut)" }}>{p}%</span>
  </div>
);

function Dashboard({ onNewCampaign, onSignOut, user }) {
  const [activeCampaign, setActiveCampaign] = useState("Define");
  const [activeSection, setActiveSection] = useState("overview");

  // Sub-states for interactive previewing within sections
  const [payState, setPayState] = useState("form");
  const [guestState, setGuestState] = useState("form");
  const [checkinState, setCheckinState] = useState("ok");
  const [msgKey, setMsgKey] = useState("Invite");
  const [channel, setChannel] = useState("Email");
  const [feedbackState, setFeedbackState] = useState("form");

  const campaigns = ["Define", "Future of Work Summit", "SALT", "Relevant"];

  const subsections = [
    { id: "overview", label: "📊 Overview" },
    { id: "payments", label: "💳 Payments" },
    { id: "registration", label: "📝 Guest Registration" },
    { id: "tickets", label: "🎟️ Tickets & Check-in" },
    { id: "messages", label: "💬 Message Previews" },
    { id: "feedback", label: "⭐ Event Feedback" },
  ];

  return (
    <div className="dash">
      {/* Left Sidebar */}
      <div className="side">
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 16 }}>
          <span style={{ fontSize: 20, color: "var(--teal)" }}>✳</span>
          <b style={{ fontSize: 18, color: "#fff" }}>koodal</b>
          <span className="pill w" style={{ marginLeft: "auto", fontSize: 10 }}>LIVE</span>
        </div>

        <button className="btn p side-btn" onClick={onNewCampaign}>
          + Create Campaign
        </button>

        <div className="side-title">CAMPAIGNS</div>
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
                <div className="dot" />
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
        })}

        <div style={{ marginTop: "auto", paddingTop: 20, borderTop: "1px solid #263544" }}>
          <div style={{ fontSize: 13, color: "#fff", fontWeight: 600 }}>{user?.name || "Asha Thomas"}</div>
          <small style={{ color: "#8097a8" }}>Organizer · Kochi</small>
          <button
            className="btn-sm"
            onClick={onSignOut}
            style={{ width: "100%", marginTop: 12, textAlign: "center" }}
          >
            Sign Out
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      <div style={{ padding: "28px 36px", overflowY: "auto", background: "#f8fafb" }}>
        {/* Breadcrumb Header */}
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
            <small style={{ color: "var(--mut)" }}>Real-time analytics and response telemetry</small>
            <div className="stats">
              {[
                ["Confirmed", "1,284", "32.3% of invited"],
                ["Not responded", "1,860", "46.7% of invited"],
                ["Weakest language", "Malayalam", "20.4% response rate"],
                ["Calls remaining", "412", "queued or in progress"],
              ].map(([a, b, c]) => (
                <div className="mint" key={a}>
                  <small>{a}</small>
                  <div className="big">{b}</div>
                  <small>{c}</small>
                </div>
              ))}
            </div>

            <div className="grid" style={{ padding: 0, gridTemplateColumns: "2fr 1fr", margin: "20px 0" }}>
              <div className="card">
                <h3>Funnel and conversion stages</h3>
                <Bar k="Invited" n="3,980" p={100} />
                <Bar k="Responded" n="2,120" p={53.3} />
                <Bar k="Registered" n="1,040" p={26.1} />
                <Bar k="Paid" n="920" p={23.1} />
                <h4 style={{ marginTop: 24 }}>By language response rate</h4>
                <Bar k="English" n="1,400" p={70} />
                <Bar k="Hindi" n="520" p={52} />
                <Bar k="Malayalam" n="200" p={20.4} />
              </div>

              <div className="card">
                <h3>Retry Outreach</h3>
                <div className="big">412</div>
                <p className="hint">
                  This will call 412 non-responders via Exotel. Maximum 3 attempts per contact.
                  Opted-out numbers, DND, and exhausted numbers are strictly skipped.
                </p>
                <button className="btn p">+ Retry non-responders</button>
              </div>
            </div>

            <div className="card" style={{ marginTop: 20 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
                <h3 style={{ margin: 0 }}>Recent Contact Log (E.164 Masked)</h3>
                <small className="hint">Protected under DPDP · Salted HMAC hashes</small>
              </div>
              <table>
                <thead>
                  <tr><th>Contact</th><th>Phone Masked</th><th>Language</th><th>Outcome</th><th>Attempts</th><th>Channel</th></tr>
                </thead>
                <tbody>
                  {[
                    ["Priya Nair", "+91 •••• 4821", "English", "Confirmed", "1 of 3", "Call"],
                    ["Rohan Mehta", "+91 •••• 1187", "Hindi", "Declined", "1 of 3", "Call"],
                    ["Aisha Khan", "+91 •••• 7734", "English", "Callback", "2 of 3", "WhatsApp"],
                    ["Deepak Rao", "+91 •••• 6629", "Malayalam", "No answer", "2 of 3", "Call"],
                    ["Anjali Menon", "+91 •••• 4321", "Malayalam", "Confirmed", "1 of 3", "Call + SMS"],
                  ].map((r, n) => (
                    <tr key={n}>{r.map((c, j) => <td key={j}>{c}</td>)}</tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* 2. PAYMENTS SUBSECTION */}
        {activeSection === "payments" && (
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
              <div>
                <h2 style={{ margin: 0 }}>Payments & Checkout Simulator</h2>
                <small style={{ color: "var(--mut)" }}>Test mode gateway integration · 15-minute hold timer · Webhook signature verified</small>
              </div>
              <div className="pill-group">
                {[
                  ["form", "Choose Method"],
                  ["verifying", "Processing"],
                  ["success", "Test Receipt"],
                  ["failed", "Payment Failed"],
                  ["expired", "Hold Expired"],
                ].map(([st, label]) => (
                  <button
                    key={st}
                    className={`state-pill ${payState === st ? "on" : ""}`}
                    onClick={() => setPayState(st)}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>

            <div style={{ background: "#fff", borderRadius: 12, border: "1px solid var(--line)", overflow: "hidden" }}>
              <Pay s={payState} />
            </div>
          </div>
        )}

        {/* 3. GUEST REGISTRATION SUBSECTION */}
        {activeSection === "registration" && (
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
              <div>
                <h2 style={{ margin: 0 }}>Guest Registration Landing Pages</h2>
                <small style={{ color: "var(--mut)" }}>Public recipient view reached from personal links (/r/{`{token}`})</small>
              </div>
              <div className="pill-group">
                {[
                  ["form", "Form"],
                  ["saving", "Submitting"],
                  ["success", "Confirmed"],
                  ["existing", "Already Registered"],
                  ["full", "Event Full"],
                  ["waitlisted", "Waitlisted"],
                  ["expired", "Link Expired"],
                ].map(([st, label]) => (
                  <button
                    key={st}
                    className={`state-pill ${guestState === st ? "on" : ""}`}
                    onClick={() => setGuestState(st)}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>

            <div style={{ background: "#fff", borderRadius: 12, border: "1px solid var(--line)", overflow: "hidden" }}>
              <Guest s={guestState} />
            </div>
          </div>
        )}

        {/* 4. TICKETS & CHECK-IN SUBSECTION */}
        {activeSection === "tickets" && (
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
              <div>
                <h2 style={{ margin: 0 }}>Admission Tickets & Front-Desk Scanner</h2>
                <small style={{ color: "var(--mut)" }}>QR Pass verification & staff attendance logging (/r/{`{token}`}/check-in)</small>
              </div>
              <div className="pill-group">
                {[
                  ["ticket", "Attendee Ticket Pass"],
                  ["ok", "Check-in: Success"],
                  ["dup", "Check-in: Duplicate"],
                  ["bad", "Check-in: Invalid"],
                ].map(([st, label]) => (
                  <button
                    key={st}
                    className={`state-pill ${checkinState === st ? "on" : ""}`}
                    onClick={() => setCheckinState(st)}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>

            <div style={{ background: "#fff", borderRadius: 12, border: "1px solid var(--line)", overflow: "hidden", padding: 12 }}>
              {checkinState === "ticket" ? <Ticket /> : <Checkin s={checkinState} />}
            </div>
          </div>
        )}

        {/* 5. MESSAGES & CHANNELS SUBSECTION */}
        {activeSection === "messages" && (
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
              <div>
                <h2 style={{ margin: 0 }}>Message & Dispatch Previews</h2>
                <small style={{ color: "var(--mut)" }}>Rendered templates across Email & WhatsApp</small>
              </div>
              <div style={{ display: "flex", gap: 12 }}>
                <select
                  value={channel}
                  onChange={(e) => setChannel(e.target.value)}
                  style={{ padding: "6px 12px", borderRadius: 8, border: "1px solid var(--line)", font: "inherit" }}
                >
                  <option>Email</option>
                  <option>WhatsApp</option>
                </select>
                <select
                  value={msgKey}
                  onChange={(e) => setMsgKey(e.target.value)}
                  style={{ padding: "6px 12px", borderRadius: 8, border: "1px solid var(--line)", font: "inherit" }}
                >
                  {Object.keys(MSG).map((k) => <option key={k}>{k}</option>)}
                </select>
              </div>
            </div>

            <div style={{ background: "#fff", borderRadius: 12, border: "1px solid var(--line)", overflow: "hidden" }}>
              <Message k={msgKey} ch={channel} />
            </div>
          </div>
        )}

        {/* 6. FEEDBACK SUBSECTION */}
        {activeSection === "feedback" && (
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
              <div>
                <h2 style={{ margin: 0 }}>Post-Event Attendee Feedback</h2>
                <small style={{ color: "var(--mut)" }}>3-question feedback collection & sentiment survey</small>
              </div>
              <div className="pill-group">
                {[
                  ["form", "Survey Form"],
                  ["submitting", "Submitting"],
                  ["done", "Completed"],
                  ["repeat", "Already Sent"],
                ].map(([st, label]) => (
                  <button
                    key={st}
                    className={`state-pill ${feedbackState === st ? "on" : ""}`}
                    onClick={() => setFeedbackState(st)}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>

            <div style={{ background: "#fff", borderRadius: 12, border: "1px solid var(--line)", overflow: "hidden" }}>
              <Feedback s={feedbackState} />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

/* ---------- 4. Main Root App Flow Router ---------- */
export default function KoodalApp() {
  // Views: "home" (default landing/login) | "dashboard" | "wizard"
  const [view, setView] = useState("home");
  const [user, setUser] = useState({ name: "Asha Thomas", email: "organizer@example.com", role: "organizer" });

  return (
    <div className="k">
      <style>{css}</style>

      {/* Top Brand Bar visible on authenticated screens */}
      {view !== "home" && (
        <div className="top-bar">
          <div className="top-brand" style={{ cursor: "pointer" }} onClick={() => setView("dashboard")}>
            <span>✳</span> koodal <small style={{ color: "#7a90a2", fontWeight: 400 }}>· EventReach Platform</small>
          </div>
          <div className="top-right">
            <div className="user-pill">
              <div className="user-dot" />
              <span>{user?.name} ({user?.role})</span>
            </div>
            <button className="btn-sm" onClick={() => setView("wizard")}>
              + Create Campaign
            </button>
            <button className="btn-sm" onClick={() => setView("home")}>
              Sign Out
            </button>
          </div>
        </div>
      )}

      {/* 1. Home / Login Flow */}
      {view === "home" && (
        <Home
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
          onSignOut={() => setView("home")}
          user={user}
        />
      )}
    </div>
  );
}
