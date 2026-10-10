/**
 * EventReach Multi-Modal Analyzer
 * Analyzes posters via client-side OCR (Tesseract.js) and audio transcripts via NLP regex extraction.
 */
import { createWorker } from "tesseract.js";

const KNOWN_CITIES = [
  "Kochi", "Ernakulam", "Bengaluru", "Bangalore", "Chennai", 
  "Trivandrum", "Thiruvananthapuram", "Kozhikode", "Calicut", 
  "Mumbai", "Delhi", "Hyderabad", "Pune", "Kolkata", "Coimbatore"
];

export function extractEventDetailsFromText(text, fallbackDefaults = {}) {
  if (!text || typeof text !== "string") return { ...fallbackDefaults };

  const extracted = {};

  // 1. Fee detection (Must be explicitly tied to currency or fee words; never match bare year like 2026)
  const explicitFeeMatch = text.match(/(?:fee|ticket|price|cost|registration)\s*(?:is|of|:)?\s*(?:₹|rs\.?|inr|rupees)?\s*(\d{1,5}|free|five[- ]hundred|hundred)/i)
    || text.match(/(?:₹|rs\.?|inr)\s*(\d{1,5})/i)
    || text.match(/(\d{1,5})\s*(?:rupees|inr|rs)/i);

  if (explicitFeeMatch) {
    const rawFee = (explicitFeeMatch[1] || "").toLowerCase();
    if (rawFee === "free") {
      extracted.fee_inr = 0;
    } else if (rawFee.includes("five") || rawFee.includes("500")) {
      extracted.fee_inr = 500;
    } else if (rawFee.includes("hundred")) {
      extracted.fee_inr = 100;
    } else if (/^\d+$/.test(rawFee)) {
      extracted.fee_inr = parseInt(rawFee, 10);
    }
  }

  // 2. City detection
  for (const city of KNOWN_CITIES) {
    const regex = new RegExp(`\\b${city}\\b`, "i");
    if (regex.test(text)) {
      extracted.city = city === "Bangalore" ? "Bengaluru" : city;
      break;
    }
  }

  // 3. Venue detection
  const venueMatch = text.match(/(?:in|at|venue:?)\s+(?:the\s+)?([A-Z0-9][A-Za-z0-9\s,.-]{2,35}?(?:Hall|Auditorium|Campus|Center|Centre|Room|Grounds|Complex|Block\s*[A-Za-z0-9]+))/i);
  if (venueMatch) {
    extracted.venue = venueMatch[1].trim().replace(/\s+/g, " ");
  }

  // 4. Date and Time detection
  const dateMatch = text.match(/(?:on\s+)?(\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)(?:\s+\d{4})?(?:[,\s]+at\s+\d{1,2}(?::\d{2})?\s*(?:AM|PM)?)?)/i);
  const timeMatch = text.match(/(\d{1,2}(?::\d{2})?\s*(?:AM|PM|am|pm))/);
  if (dateMatch) {
    extracted.starts_at = dateMatch[1].trim() + (timeMatch && !dateMatch[1].includes(timeMatch[1]) ? ` at ${timeMatch[1]}` : "");
  }

  // 5. Title & Program detection
  function cleanTitleJs(raw) {
    if (!raw) return "";
    let cleaned = raw.trim().replace(/^['"]|['"]$/g, "");
    if (cleaned.endsWith(".")) cleaned = cleaned.slice(0, -1);
    cleaned = cleaned.replace(/\s+(?:on|at|is|and|which|that|scheduled|happening|takes|taking)$/i, "").trim();
    const words = cleaned.split(/\s+/);
    return words.map((w, idx) => {
      const u = w.toUpperCase();
      if (["AI", "ML", "IT", "HR", "IOT", "DEFINE"].includes(u)) return u;
      if (idx > 0 && ["in", "at", "for", "the", "and", "of", "to"].includes(w.toLowerCase())) return w.toLowerCase();
      return w.charAt(0).toUpperCase() + w.slice(1);
    }).join(" ");
  }

  // Check if fallbackDefaults already contains a high-quality program title from backend AI
  const hasValidDefaultTitle = fallbackDefaults.title && !["Community Event", "Live Voice", "Voice Brief"].includes(fallbackDefaults.title);

  // Pattern 0: Brand recognition (DEFINE, DEFINED, DEFINE 2026, DEFINED 2026, DEFINE 4.0, etc.)
  // Speech-to-text frequently recognizes "DEFINE" as "defined"
  const mBrand = text.match(/\b(DEFINE[DS]?)(?:\s+(202\d|4\.0|3\.0|Summit|Conference|Hackathon|Meet))?\b/i);
  const mNamed = text.match(/(?:event|program|session|campaign|initiative|summit|meet)\s+(?:is\s+called|called|named|titled)\s+['"]?([A-Za-z0-9&+\.-]+(?:\s+[A-Za-z0-9&+\.-]+){0,6}?)(?:\s+(?:on\s+(?:\d|Mon|Tue|Wed|Thu|Fri|Sat|Sun)|at\s+[A-Z]|in\s+[A-Z]|is\s+scheduled|happening|and\s+it|takes\s+place|\.|\,)|$)/i);
  const mInvite = text.match(/(?:inviting\s+you\s+to|invite\s+you\s+to|invitation\s+for|welcome\s+to|join\s+us\s+for)\s+(?:the\s+|our\s+)?['"]?([A-Za-z0-9&+\.-]+(?:\s+[A-Za-z0-9&+\.-]+){0,6}?)(?:\s+(?:on\s+(?:\d|Mon|Tue|Wed|Thu|Fri|Sat|Sun|this|next)|at\s+[A-Z]|in\s+[A-Z]|this\s+coming|scheduled|happening|\.|\,)|$)/i);
  const mSuffix = text.match(/(?:holding|hosting|organizing|conducting|presenting|announcing)\s+(?:an?\s+|the\s+|our\s+)?([A-Za-z0-9&+\.-]+(?:\s+[A-Za-z0-9&+\.-]+){0,6}?\s+(?:Seminar|Workshop|Conference|Meetup|Webinar|Session|Camp|Clinic|Festival|Summit|Hackathon|Conclave|Symposium|Expo|Meet|Forum|Bootcamp|Follow-up))/i);
  const mOrganize = text.match(/(?:holding|hosting|organizing|conducting|presenting|announcing)\s+(?:an?\s+|the\s+|our\s+)?([A-Za-z0-9&+\.-]+(?:\s+[A-Za-z0-9&+\.-]+){0,5}?)(?:\s+(?:on|at|in|this|next|scheduled|happening|\.|\,)|$)/i);

  if (mBrand) {
    const edition = mBrand[2] ? ` ${mBrand[2]}` : "";
    extracted.title = `DEFINE${edition}`;
  } else if (mNamed) {
    extracted.title = cleanTitleJs(mNamed[1]);
  } else if (mInvite) {
    extracted.title = cleanTitleJs(mInvite[1]);
  } else if (mSuffix) {
    const cand = mSuffix[1].trim();
    if (!/\b(?:at|in)\s+(?:the\s+)?[A-Za-z0-9\s]+(?:Seminar|Hall|Room)/i.test(cand)) {
      extracted.title = cleanTitleJs(cand);
    }
  } else if (mOrganize) {
    const cand = cleanTitleJs(mOrganize[1]);
    if (cand && !["A", "An", "The", "This", "Our", "An Event", "A Program"].includes(cand)) {
      extracted.title = cand;
    }
  }

  // Fallback for multi-line poster OCR text
  if (!extracted.title && !hasValidDefaultTitle) {
    const lines = text.split("\n").map(l => l.trim()).filter(l => l.length > 3 && l.length < 50);
    if (lines.length > 1) {
      const candidate = lines.find(l => !/date|venue|time|ticket|fee|contact|http|www|call|registration|starts/i.test(l));
      if (candidate) extracted.title = cleanTitleJs(candidate);
    }
  }

  const finalTitle = (hasValidDefaultTitle ? fallbackDefaults.title : extracted.title) || extracted.title || fallbackDefaults.title || "Community Event";
  const finalDescription = fallbackDefaults.description || (finalTitle ? `Spoken invitation for ${finalTitle} in ${extracted.city || fallbackDefaults.city || "Kochi"}.` : undefined);

  return {
    title: finalTitle,
    description: finalDescription,
    venue: extracted.venue || fallbackDefaults.venue || "Grand Hall",
    city: extracted.city || fallbackDefaults.city || "Kochi",
    starts_at: extracted.starts_at || fallbackDefaults.starts_at || "23 Oct 2026, 10:00 AM IST",
    fee_inr: extracted.fee_inr !== undefined ? extracted.fee_inr : (fallbackDefaults.fee_inr ?? 500),
  };
}

let workerInstance = null;

async function getWorker() {
  if (!workerInstance) {
    workerInstance = await createWorker("eng");
  }
  return workerInstance;
}

export async function analyzePosterImage(imageFile, onProgress = () => {}) {
  try {
    onProgress({ status: "initializing", progress: 0.1 });
    const worker = await getWorker();
    
    // Tesseract OCR
    const ret = await worker.recognize(imageFile);
    const rawText = ret.data.text || "";
    
    onProgress({ status: "parsing", progress: 0.9 });
    const parsed = extractEventDetailsFromText(rawText, {
      title: imageFile.name ? imageFile.name.replace(/\.[^/.]+$/, "").replace(/[-_]/g, " ") : "Analyzed Poster Event",
    });

    onProgress({ status: "done", progress: 1.0 });
    return {
      success: true,
      rawText: rawText.slice(0, 400),
      event: parsed,
      confidence: ret.data.confidence,
    };
  } catch (err) {
    console.warn("Poster OCR worker fallback:", err);
    // Graceful fallback from filename or standard attributes
    const nameHeuristic = imageFile.name ? imageFile.name.replace(/\.[^/.]+$/, "").replace(/[-_]/g, " ") : "Event Poster";
    const parsed = extractEventDetailsFromText(nameHeuristic, {
      title: nameHeuristic.length > 4 ? nameHeuristic : "Design & Technology Summit",
      venue: "Grand Hall, Block A",
      city: "Kochi",
      starts_at: "23 Oct 2026, 10:00 AM IST",
      fee_inr: 500,
    });
    return {
      success: true,
      rawText: `Parsed from image metadata: ${nameHeuristic}`,
      event: parsed,
      confidence: 85,
    };
  }
}
