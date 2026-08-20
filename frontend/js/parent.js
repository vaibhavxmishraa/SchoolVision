const auth = guard("Parent");
if(auth) document.getElementById("uname").textContent = auth.name;
let children = [];

function badgeClass(b){
  if(b.includes("Dismissed")) return "badge-dismissed";
  if(b.includes("In Class")) return "badge-arrived";
  return "badge-notarrived";
}

async function loadChildren(){
  children = await api("/api/parent/children");
  document.getElementById("childCards").innerHTML = children.map(c=>`
    <div class="stat-card">
      <div style="font-size:18px;font-weight:700;color:var(--primary)">${c.name}</div>
      <div class="label">Roll ${c.roll_number} · Class ${c.class_section}</div>
      <div style="margin:14px 0"><span class="badge ${badgeClass(c.badge)}">${c.badge}</span></div>
      <div style="font-size:13px;color:var(--muted)">
        🎒 Check-In: <b>${c.checkin_time}</b><br>
        🚌 Check-Out: <b>${c.checkout_time}</b></div>
    </div>`).join("");
  document.getElementById("childSelect").innerHTML =
    children.map(c=>`<option value="${c.id}">${c.name}</option>`).join("");
  if(children.length) loadTimeline();
}

async function loadTimeline(){
  const id = document.getElementById("childSelect").value;
  if(!id) return;
  const list = await api("/api/parent/timeline/" + id);
  document.getElementById("timeline").innerHTML = list.length ? list.map(t=>`
    <div class="timeline-item">
      <b>${t.session}</b> — ${t.status}
      <span class="badge ${t.status==='Absent'?'badge-absent':'badge-present'}" style="float:right">${t.status}</span>
      <div style="font-size:12px;color:var(--muted)">${t.date} at ${t.time} · via ${t.marked_by}</div>
    </div>`).join("") : "<p style='color:var(--muted)'>Abhi koi record nahi.</p>";
}

async function loadNotifs(){
  const list = await api("/api/parent/notifications");
  document.getElementById("notifList").innerHTML = list.length ? list.map(n=>`
    <div class="timeline-item" style="border-left-color:${n.is_read?'#cbd5e1':'var(--accent)'}">
      ${n.is_read?'':'🟢 '}${n.message}
      <div style="font-size:12px;color:var(--muted)">${n.time}</div>
    </div>`).join("") : "<p style='color:var(--muted)'>Koi notification nahi.</p>";
  await api("/api/parent/notifications/read", { method:"POST" });
}

loadChildren();
setInterval(loadChildren, 15000); // auto-refresh real-time status