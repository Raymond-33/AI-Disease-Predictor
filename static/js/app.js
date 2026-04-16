/**
 * MediSense AI — Frontend Application
 * Handles form submission, API calls, result rendering, and animations.
 */

"use strict";

// ── DOM References ──────────────────────────────────────────────────────────
const form        = document.getElementById("symptom-form");
const textarea    = document.getElementById("symptom-input");
const analyzeBtn  = document.getElementById("analyze-btn");
const clearBtn    = document.getElementById("clear-btn");
const charCount   = document.getElementById("char-count");
const resultsArea = document.getElementById("results-area");
const exPills     = document.getElementById("example-pills");

// ── Constants ───────────────────────────────────────────────────────────────
const API_URL     = "/api/predict";
const EXAMPLES_URL = "/api/examples";
const MAX_CHARS   = 1000;

// Emergency keywords — triggers extra warning
const EMERGENCY_KEYWORDS = [
  "chest pain", "heart attack", "stroke", "cannot breathe", "can't breathe",
  "unconscious", "seizure", "suicidal", "overdose", "severe bleeding",
  "sudden numbness", "vision lost", "losing vision",
];

// Severity → CSS class mapping
const SEVERITY_CLASS = {
  "mild":                  "tag-severity-mild",
  "mild-to-moderate":     "tag-severity-mild",
  "moderate":              "tag-severity-moderate",
  "moderate-to-moderate": "tag-severity-moderate",
  "moderate-to-severe":   "tag-severity-moderate",
  "chronic/manageable":   "tag-severity-chronic",
  "chronic/serious":      "tag-severity-severe",
  "chronic/variable":     "tag-severity-chronic",
  "variable":              "tag-severity-chronic",
  "variable (mild to severe)": "tag-severity-moderate",
  "serious (requires professional treatment)": "tag-severity-severe",
  "serious (potentially life-threatening)":    "tag-severity-severe",
  "serious (requires emergency surgery)":      "tag-severity-severe",
  "life-threatening (emergency)":              "tag-severity-severe",
};

// Rank labels
const RANK_LABEL = ["#1", "#2"];

// ── Fetch and Render Examples ────────────────────────────────────────────────
async function loadExamples() {
  try {
    const res = await fetch(EXAMPLES_URL);
    if (!res.ok) return;
    const data = await res.json();
    const examples = data.examples || [];

    // Show a subset (5 random)
    const shuffled = examples.sort(() => Math.random() - 0.5).slice(0, 5);

    shuffled.forEach((ex, i) => {
      const pill = document.createElement("button");
      pill.type = "button";
      pill.className = "example-pill";
      pill.id = `example-pill-${i}`;
      // Truncate display text
      pill.textContent = ex.length > 48 ? ex.slice(0, 47) + "…" : ex;
      pill.setAttribute("aria-label", `Use example: ${ex}`);
      pill.title = ex;
      pill.addEventListener("click", () => {
        textarea.value = ex;
        updateCharCount();
        textarea.focus();
        textarea.scrollIntoView({ behavior: "smooth", block: "center" });
      });
      exPills.appendChild(pill);
    });
  } catch (_) { /* silently ignore */ }
}

// ── Character Counter ────────────────────────────────────────────────────────
function updateCharCount() {
  const len = textarea.value.length;
  charCount.textContent = `${len} / ${MAX_CHARS}`;
  charCount.classList.toggle("near-limit", len > MAX_CHARS * 0.8 && len <= MAX_CHARS * 0.95);
  charCount.classList.toggle("at-limit",   len > MAX_CHARS * 0.95);
}

textarea.addEventListener("input", updateCharCount);

// ── Emergency Detection ──────────────────────────────────────────────────────
function hasEmergencyKeyword(query) {
  const lower = query.toLowerCase();
  return EMERGENCY_KEYWORDS.some(kw => lower.includes(kw));
}

// ── Form Submit ──────────────────────────────────────────────────────────────
form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const query = textarea.value.trim();

  if (!query) {
    shakeInput();
    return;
  }
  if (query.length < 5) {
    showError("Please describe your symptoms in more detail.");
    return;
  }

  await runAnalysis(query);
});

clearBtn.addEventListener("click", () => {
  textarea.value = "";
  updateCharCount();
  resultsArea.innerHTML = "";
  textarea.focus();
  analyzeBtn.disabled = false;
  setLoading(false);
});

// ── Main Analysis Flow ───────────────────────────────────────────────────────
async function runAnalysis(query) {
  setLoading(true);
  showSkeletons();

  // Check for emergency keywords before API call
  const emergency = hasEmergencyKeyword(query);

  try {
    const response = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query }),
    });

    const data = await response.json();

    if (!response.ok || !data.success) {
      showError(data.error || "Something went wrong. Please try again.");
      return;
    }

    renderResults(data, emergency);

  } catch (err) {
    showError("Unable to connect to the analysis server. Please try again.");
    console.error("API error:", err);
  } finally {
    setLoading(false);
  }
}

// ── Render Results ───────────────────────────────────────────────────────────
function renderResults(data, emergency) {
  resultsArea.innerHTML = "";

  // 1. Emergency banner
  if (emergency) {
    const banner = document.createElement("div");
    banner.className = "emergency-banner";
    banner.setAttribute("role", "alert");
    banner.innerHTML = `
      <span aria-hidden="true">🚨</span>
      <span><strong>Possible Medical Emergency:</strong> Based on keywords in your description, please call emergency services or go to your nearest emergency room immediately. Do not delay seeking professional help.</span>
    `;
    resultsArea.appendChild(banner);
  }



  // 3. No match
  if (!data.predictions || data.predictions.length === 0) {
    const noMatch = document.createElement("div");
    noMatch.className = "no-match-card glass-card";
    noMatch.setAttribute("role", "status");
    noMatch.innerHTML = `
      <span class="no-match-icon" aria-hidden="true">🤔</span>
      <h3 class="no-match-title">No Close Match Found</h3>
      <p class="no-match-text">
        ${data.message || "Please describe your symptoms in more detail. Try mentioning specific body parts, duration, and severity."}
      </p>
    `;
    resultsArea.appendChild(noMatch);
    return;
  }

  // 4. Render each prediction card
  const template = document.getElementById("result-card-template");

  data.predictions.forEach((pred, index) => {
    const clone = template.content.cloneNode(true);
    const card  = clone.querySelector(".result-card");

    // Rank badge
    const rankBadge = card.querySelector(".result-rank-badge");
    rankBadge.textContent = RANK_LABEL[index] || `#${pred.rank}`;
    rankBadge.classList.add(`rank-${pred.rank}`);
    rankBadge.setAttribute("aria-label", `Rank ${pred.rank}`);

    // Disease name
    card.querySelector(".result-disease-name").textContent = pred.disease;

    // Category tag
    const catTag = card.querySelector(".result-category");
    catTag.textContent = pred.category;
    catTag.classList.add("tag-category");

    // Severity tag
    const sevTag = card.querySelector(".result-severity");
    sevTag.textContent = pred.severity;
    const sevClass = getSeverityClass(pred.severity);
    sevTag.classList.add(sevClass);

    // Confidence ring animation
    const ringFill = card.querySelector(".ring-fill");
    const confVal  = card.querySelector(".confidence-val");

    // Add gradient def inline
    const svgEl = card.querySelector(".confidence-ring");
    const defs = document.createElementNS("http://www.w3.org/2000/svg", "defs");
    const grad  = document.createElementNS("http://www.w3.org/2000/svg", "linearGradient");
    grad.id = `ringGrad-${index}`;
    grad.setAttribute("x1", "0%"); grad.setAttribute("y1", "0%");
    grad.setAttribute("x2", "100%"); grad.setAttribute("y2", "100%");
    const s1 = document.createElementNS("http://www.w3.org/2000/svg", "stop");
    s1.setAttribute("offset", "0%"); s1.setAttribute("stop-color", "#6ee7f7");
    const s2 = document.createElementNS("http://www.w3.org/2000/svg", "stop");
    s2.setAttribute("offset", "100%"); s2.setAttribute("stop-color", "#a78bfa");
    grad.appendChild(s1); grad.appendChild(s2);
    defs.appendChild(grad);
    svgEl.insertBefore(defs, svgEl.firstChild);
    ringFill.setAttribute("stroke", `url(#ringGrad-${index})`);

    // Animate confidence ring after mount
    const circumference = 201;
    ringFill.style.strokeDashoffset = circumference;
    confVal.textContent = "0";

    resultsArea.appendChild(clone);

    // Trigger animation next frame
    requestAnimationFrame(() => {
      setTimeout(() => {
        const offset = circumference * (1 - pred.confidence / 100);
        ringFill.style.strokeDashoffset = offset;
        animateCount(confVal, 0, pred.confidence, 1200);
      }, 100 + index * 120);
    });

    // Description
    card.querySelector(".description-content").textContent = pred.description;

    // Diagnosis
    card.querySelector(".diagnosis-content").textContent = pred.diagnosis;

    // Treatment
    const treatDiv = card.querySelector(".treatment-content");
    treatDiv.innerHTML = `<strong>Recommended Treatment:</strong> ${escapeHtml(pred.treatment)}`;

    // When to see doctor
    const doctorDiv = card.querySelector(".doctor-content");
    doctorDiv.innerHTML = `<strong>⚠️ Seek medical attention:</strong> ${escapeHtml(pred.when_to_see_doctor)}`;
  });

  // Need to re-attach card refs (clone appended above in loop; find them now)
  const allCards = resultsArea.querySelectorAll(".result-card");
  allCards.forEach(card => {
    // Access ring fills already set above — no extra loop needed
  });
}

// ── UI State Helpers ─────────────────────────────────────────────────────────
function setLoading(isLoading) {
  analyzeBtn.disabled = isLoading;
  analyzeBtn.classList.toggle("loading", isLoading);
  analyzeBtn.querySelector(".btn-text").textContent = isLoading ? "Analyzing…" : "Analyze Symptoms";
}

function showSkeletons() {
  resultsArea.innerHTML = "";
  for (let i = 0; i < 2; i++) {
    const sk = document.createElement("div");
    sk.className = "skeleton skeleton-card glass-card";
    sk.setAttribute("aria-hidden", "true");
    sk.style.animationDelay = `${i * 0.1}s`;
    resultsArea.appendChild(sk);
  }
}

function showError(message) {
  resultsArea.innerHTML = "";
  const err = document.createElement("div");
  err.className = "error-card";
  err.setAttribute("role", "alert");
  err.innerHTML = `
    <span class="error-icon" aria-hidden="true">⚠️</span>
    <span>${escapeHtml(message)}</span>
  `;
  resultsArea.appendChild(err);
}

function shakeInput() {
  textarea.style.animation = "none";
  textarea.offsetHeight; // reflow
  textarea.style.animation = "shake 0.4s ease";
  textarea.focus();

  let style = document.getElementById("shake-style");
  if (!style) {
    style = document.createElement("style");
    style.id = "shake-style";
    style.textContent = `
      @keyframes shake {
        0%,100%{transform:translateX(0)}
        20%{transform:translateX(-6px)}
        40%{transform:translateX(6px)}
        60%{transform:translateX(-4px)}
        80%{transform:translateX(4px)}
      }
    `;
    document.head.appendChild(style);
  }
}

// ── Animated Number Counter ──────────────────────────────────────────────────
function animateCount(el, from, to, duration) {
  const start = performance.now();
  function step(now) {
    const elapsed = now - start;
    const progress = Math.min(elapsed / duration, 1);
    const ease = 1 - Math.pow(1 - progress, 3); // ease-out-cubic
    const current = Math.round(from + (to - from) * ease);
    el.textContent = current;
    if (progress < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

// ── Severity CSS Class ───────────────────────────────────────────────────────
function getSeverityClass(severity) {
  if (!severity) return "tag-severity-mild";
  const lower = severity.toLowerCase();
  if (SEVERITY_CLASS[lower]) return SEVERITY_CLASS[lower];
  if (lower.includes("life-threatening") || lower.includes("emergency") ||
      lower.includes("serious") || lower.includes("severe")) return "tag-severity-severe";
  if (lower.includes("moderate")) return "tag-severity-moderate";
  if (lower.includes("chronic")) return "tag-severity-chronic";
  return "tag-severity-mild";
}

// ── HTML Escape ──────────────────────────────────────────────────────────────
function escapeHtml(str = "") {
  const div = document.createElement("div");
  div.appendChild(document.createTextNode(str));
  return div.innerHTML;
}

// ── Smooth scroll for nav links ──────────────────────────────────────────────
document.querySelectorAll('a[href^="#"]').forEach(link => {
  link.addEventListener("click", (e) => {
    const target = document.querySelector(link.getAttribute("href"));
    if (target) {
      e.preventDefault();
      target.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  });
});

// ── Init ─────────────────────────────────────────────────────────────────────
loadExamples();
updateCharCount();
