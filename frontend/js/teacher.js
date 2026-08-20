const auth = guard("Teacher");
if(auth) document.getElementById("uname").textContent = auth.name;

function badge(status){
  if(status === "Present") return '<span class="badge badge-present">Present</span>';
  if(status === "Manual Override") return '<span class="badge badge-override">Override</span>';
  return '<span class="badge badge-absent">Absent</span>';
}

async function loadRoster(){
  const list = await api("/api/teacher/roster");
  document.getElementById("rosterRows").innerHTML = list.map(s=>`
    <tr><td>${s.roll_number}</td><td>${s.name}</td><td>${s.class_section}</td>
    <td>${badge(s.checkin)}</td><td>${badge(s.checkout)}</td>
    <td>
      <button class="btn btn-sm btn-green" onclick="mark(${s.id},'Check-In')">✓ In</button>
      <button class="btn btn-sm" onclick="mark(${s.id},'Check-Out')">✓ Out</button>
      <button class="btn btn-sm btn-red" onclick="absent(${s.id})">✗ Absent</button>
    </td></tr>`).join("");
}

async function mark(id, session){
  try {
    const r = await api("/api/teacher/mark", { method:"POST", body: JSON.stringify({
      student_id:id, session_type:session, status:"Manual Override" })});
    toast(r.message); loadRoster();
  } catch(e){ toast(e.message, "err"); }
}
async function absent(id){
  try {
    await api("/api/teacher/mark", { method:"POST", body: JSON.stringify({
      student_id:id, session_type:"Check-In", status:"Absent" })});
    toast("Marked Absent"); loadRoster();
  } catch(e){ toast(e.message, "err"); }
}

async function loadLogs(){
  const list = await api("/api/teacher/logs");
  document.getElementById("logRows").innerHTML = list.map(l=>`
    <tr><td>${l.date}</td><td>${l.time}</td><td>${l.roll}</td><td>${l.student}</td>
    <td>${l.session}</td><td>${badge(l.status)}</td><td>${l.marked_by}</td></tr>`).join("");
}

async function exportClass(){
  const a = getAuth();
  const res = await fetch("/api/teacher/export", { headers:{ "Authorization":"Bearer "+a.token }});
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a"); link.href = url; link.download = "Class_Report.xlsx"; link.click();
  toast("Excel downloaded ✅");
}

loadRoster();