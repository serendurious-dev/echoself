// the front of the conversation. it holds nothing - every word lives in the core,
// in memory only, and is dropped when the talk ends. this just gives her a face.

const thread = document.getElementById("thread");
const form   = document.getElementById("say");
const box    = document.getElementById("box");
const send   = document.getElementById("send");
const here   = document.getElementById("here");
const face   = document.getElementById("face");

let sessionId = null;
let busy      = false;
let faceEmotion = "neutral";

// let her expression follow how the talk feels. cross-fade so it never snaps -
// she settles into the new feeling the way a face does, not like a slideshow.
function setFace(emotion) {
  if (!face || emotion === faceEmotion) return;
  faceEmotion = emotion;
  const next = new Image();
  next.onload = () => { face.src = next.src; face.classList.remove("settling"); };
  face.classList.add("settling");
  next.src = "/api/face?emotion=" + encodeURIComponent(emotion) + "&h=320&t=" + Date.now();
}

async function api(path, body) {
  const opt = { method: body ? "POST" : "GET" };
  if (body) { opt.headers = { "Content-Type": "application/json" }; opt.body = JSON.stringify(body); }
  const r = await fetch(path, opt);
  return r.json();
}

function addLine(text, who, care) {
  const el = document.createElement("div");
  el.className = "line " + who + (care ? " care" : "");
  el.textContent = text;
  thread.appendChild(el);
  thread.scrollTop = thread.scrollHeight;
  return el;
}

function showThinking() {
  const el = document.createElement("div");
  el.className = "line her thinking";
  el.innerHTML = '<span class="pip"></span><span class="pip"></span><span class="pip"></span>';
  thread.appendChild(el);
  thread.scrollTop = thread.scrollHeight;
  return el;
}

// give her a beat before she answers - reading should feel met, not auto-replied.
// longer for heavier, shorter replies, capped so it never drags.
function pause(reply) {
  const base = 550 + Math.min((reply || "").length * 9, 1100);
  return new Promise(res => setTimeout(res, base));
}

function grow() {
  box.style.height = "auto";
  box.style.height = Math.min(box.scrollHeight, 140) + "px";
}

async function open() {
  try {
    const today = await api("/api/today");
    const name = today && (today.her_name || today.name);
    if (name) here.textContent = name + " is here";
  } catch (e) { /* the header is just a grace note - never block on it */ }

  const t = showThinking();
  try {
    const s = await api("/api/session/start", {});
    sessionId = s.session_id;
    await pause(s.opener);
    t.remove();
    addLine(s.opener || "i'm here.", "her");
  } catch (e) {
    t.remove();
    addLine("i'm here, even if the line to me is quiet right now.", "her");
  }
}

async function say(text) {
  if (busy || !text.trim()) return;
  busy = true; send.disabled = true;

  addLine(text, "you");
  box.value = ""; grow();
  const t = showThinking();

  try {
    const res = sessionId
      ? await api("/api/session/say", { session_id: sessionId, text })
      : await api("/api/respond", { text });
    await pause(res.reply);
    t.remove();
    if (res.emotion) setFace(res.emotion);
    addLine(res.reply || "i'm still here.", "her", res.crisis);
  } catch (e) {
    t.remove();
    addLine("something got in the way of my answer - but i'm still with you.", "her");
  } finally {
    busy = false; send.disabled = false;
    box.focus();
  }
}

// the portrait room - what she's gathered about you, each line yours to drop.
const panel      = document.getElementById("panel");
const memBtn     = document.getElementById("memBtn");
const panelClose = document.getElementById("panelClose");
const factsEl    = document.getElementById("facts");

function renderFacts(facts) {
  factsEl.innerHTML = "";
  if (!facts || !facts.length) {
    const empty = document.createElement("p");
    empty.className = "facts-empty";
    empty.textContent = "nothing yet - we're still getting to know each other. what i learn shows up here, and it stays yours.";
    factsEl.appendChild(empty);
    return;
  }
  for (const f of facts) {
    const row = document.createElement("div");
    row.className = "fact";
    const txt = document.createElement("span");
    txt.textContent = f.text || "";
    const x = document.createElement("button");
    x.className = "fact-forget";
    x.setAttribute("aria-label", "forget this");
    x.onclick = async () => {
      await api("/api/portrait/forget", { fact_id: f.id });
      row.remove();
      if (!factsEl.querySelector(".fact")) renderFacts([]);
    };
    row.append(txt, x);
    factsEl.appendChild(row);
  }
}

async function openPanel() {
  panel.hidden = false;
  try {
    const data = await api("/api/portrait");
    renderFacts(data.facts);
  } catch (e) {
    renderFacts([]);
  }
}

memBtn.addEventListener("click", openPanel);
panelClose.addEventListener("click", () => { panel.hidden = true; });

// the echo-distance room - how far apart we are, across four ways of being. the gap
// is 1 - closeness, so the shape reaching outward means we're closer. same four axes
// and colours the window uses, in gentler words.
const echoPanel = document.getElementById("echoPanel");
const echoBtn   = document.getElementById("echoBtn");
const echoClose = document.getElementById("echoClose");
const echoEl    = document.getElementById("echo");

const ECHO_AXES = [
  { key: "mental",     name: "mind",       color: "#8ab0e0", deg: -90 },
  { key: "behavioral", name: "showing up", color: "#e0b884", deg: 0 },
  { key: "emotional",  name: "feeling",    color: "#d88aa8", deg: 90 },
  { key: "learning",   name: "growing",    color: "#7bb5a8", deg: 180 },
];

function closenessOf(dist, key) {
  const d = (dist && typeof dist[key] === "number") ? dist[key] : 0.5;
  return Math.max(0, Math.min(1, 1 - d));
}

function radarSVG(dist) {
  const cx = 150, cy = 130, R = 84;
  const pt = (deg, r) => {
    const a = deg * Math.PI / 180;
    return [cx + r * Math.cos(a), cy + r * Math.sin(a)];
  };
  let g = "";
  for (const f of [0.25, 0.5, 0.75, 1]) {
    g += `<circle cx="${cx}" cy="${cy}" r="${(R * f).toFixed(1)}" fill="none" stroke="rgba(255,255,255,0.08)"/>`;
  }
  const poly = [];
  for (const ax of ECHO_AXES) {
    const [tx, ty] = pt(ax.deg, R);
    g += `<line x1="${cx}" y1="${cy}" x2="${tx.toFixed(1)}" y2="${ty.toFixed(1)}" stroke="rgba(255,255,255,0.08)"/>`;
    const [lx, ly] = pt(ax.deg, R + 16);
    g += `<text x="${lx.toFixed(1)}" y="${(ly + 4).toFixed(1)}" fill="${ax.color}" font-size="12" text-anchor="middle">${ax.name}</text>`;
    const [px, py] = pt(ax.deg, closenessOf(dist, ax.key) * R);
    poly.push(`${px.toFixed(1)},${py.toFixed(1)}`);
  }
  const shape = `<polygon points="${poly.join(" ")}" fill="rgba(123,181,168,0.28)" stroke="#7bb5a8" stroke-width="2"/>`;
  return `<svg viewBox="0 0 300 280" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="echo distance radar">${g}${shape}</svg>`;
}

function renderEcho(dist) {
  let legend = '<div class="echo-legend">';
  for (const ax of ECHO_AXES) {
    const pct = Math.round(closenessOf(dist, ax.key) * 100);
    legend += `<div class="echo-axis">
      <span class="echo-dot" style="background:${ax.color}"></span>
      <span class="echo-name">${ax.name}</span>
      <span class="echo-bar"><span class="echo-fill" style="width:${pct}%;background:${ax.color}"></span></span>
      <span class="echo-pct">${pct}%</span>
    </div>`;
  }
  legend += "</div>";
  echoEl.innerHTML = radarSVG(dist) + legend;
}

async function openEcho() {
  echoPanel.hidden = false;
  try {
    renderEcho(await api("/api/echo-distance"));
  } catch (e) {
    echoEl.innerHTML = '<p class="facts-empty">the distance fills in as the days do.</p>';
  }
}

echoBtn.addEventListener("click", openEcho);
echoClose.addEventListener("click", () => { echoPanel.hidden = true; });

form.addEventListener("submit", e => { e.preventDefault(); say(box.value); });
box.addEventListener("input", grow);
box.addEventListener("keydown", e => {
  if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); say(box.value); }
});

// let her go first.
open();
box.focus();
