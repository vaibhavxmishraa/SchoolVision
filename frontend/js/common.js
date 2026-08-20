const API = "";  // same origin

function saveAuth(d){ localStorage.setItem("eduvision", JSON.stringify(d)); }
function getAuth(){ try { return JSON.parse(localStorage.getItem("eduvision")); } catch(e){ return null; } }
function logout(){ localStorage.removeItem("eduvision"); location.href = "index.html"; }

function guard(role){
  const a = getAuth();
  if(!a || a.role !== role){ location.href = "index.html"; return null; }
  return a;
}

async function api(path, opts = {}){
  const a = getAuth();
  opts.headers = opts.headers || {};
  opts.headers["Content-Type"] = "application/json";
  if(a) opts.headers["Authorization"] = "Bearer " + a.token;
  const res = await fetch(API + path, opts);
  if(res.status === 401){ logout(); throw new Error("Session expired"); }
  if(!res.ok){ const e = await res.json().catch(()=>({detail:"Error"})); throw new Error(e.detail || "Error"); }
  return res.json();
}

function toast(msg, type = ""){
  let area = document.getElementById("toast-area");
  if(!area){ area = document.createElement("div"); area.id = "toast-area"; document.body.appendChild(area); }
  const t = document.createElement("div");
  t.className = "toast " + type; t.textContent = msg;
  area.appendChild(t);
  setTimeout(()=>{ t.style.opacity = "0"; setTimeout(()=>t.remove(), 300); }, 3500);
}

function switchSection(id, el){
  document.querySelectorAll(".section").forEach(s=>s.classList.remove("active"));
  document.querySelectorAll(".nav-item").forEach(n=>n.classList.remove("active"));
  document.getElementById(id).classList.add("active");
  if(el) el.classList.add("active");
}