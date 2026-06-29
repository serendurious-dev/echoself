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

form.addEventListener("submit", e => { e.preventDefault(); say(box.value); });
box.addEventListener("input", grow);
box.addEventListener("keydown", e => {
  if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); say(box.value); }
});

// let her go first.
open();
box.focus();
