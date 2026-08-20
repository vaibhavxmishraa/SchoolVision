const auth = guard("Admin");
if(auth) document.getElementById("uname").textContent = auth.name;

// ---- Dashboard ----
async function loadStats(){
  try {
    const s = await api("/api/admin/stats");
    document.getElementById("statCards").innerHTML = `
      <div class="stat-card"><div class="num">${s.students}</div><div class="label">Total Students</div></div>
      <div class="stat-card"><div class="num">${s.teachers}</div><div class="label">Teachers</div></div>
      <div class="stat-card"><div class="num">${s.parents}</div><div class="label">Parents</div></div>
      <div class="stat-card"><div class="num">${s.today_present}</div><div class="label">Present Today</div></div>`;
  } catch(e){ toast(e.message, "err"); }
}
async function exportExcel(){
  const a = getAuth();
  const res = await fetch("/api/admin/export", { headers:{ "Authorization":"Bearer "+a.token }});
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a"); link.href = url;
  link.download = "EduvisionAI_Report.xlsx"; link.click();
  toast("Excel report downloaded ✅");
}

// ---- Students ----
async function loadStudents(){
  document.getElementById("pageTitle").textContent = "Students";
  const list = await api("/api/admin/students");
  document.getElementById("studentRows").innerHTML = list.map(s=>`
    <tr><td>${s.roll_number}</td><td>${s.name}</td><td>${s.class_section}</td>
    <td>${s.parent_name}</td><td>${s.face_samples} 📸</td>
    <td><button class="btn btn-sm btn-red" onclick="delStudent(${s.id})">Delete</button></td></tr>`).join("");
}
async function delStudent(id){
  if(!confirm("Delete this student?")) return;
  await api("/api/admin/students/"+id, { method:"DELETE" });
  toast("Student deleted"); loadStudents();
}

let capturedFaces = [], enrollStream = null;
async function openStudentModal(){
  const parents = await api("/api/admin/parents");
  document.getElementById("s_parent").innerHTML =
    '<option value="">Select Parent</option>' +
    parents.map(p=>`<option value="${p.id}">${p.full_name} (${p.username})</option>`).join("");
  capturedFaces = []; document.getElementById("faceThumbs").innerHTML = "";
  document.getElementById("studentModal").classList.add("show");
  try {
    enrollStream = await navigator.mediaDevices.getUserMedia({ video:true });
    document.getElementById("enrollVid").srcObject = enrollStream;
  } catch(e){ toast("Webcam access nahi mila (face upload skip hoga)", "warn"); }
}
function closeStudentModal(){
  document.getElementById("studentModal").classList.remove("show");
  if(enrollStream){ enrollStream.getTracks().forEach(t=>t.stop()); enrollStream = null; }
}
function capFace(){
  const v = document.getElementById("enrollVid");
  if(!v.videoWidth){ toast("Camera ready nahi hai", "warn"); return; }
  const c = document.createElement("canvas");
  c.width = v.videoWidth; c.height = v.videoHeight;
  c.getContext("2d").drawImage(v, 0, 0);
  const data = c.toDataURL("image/jpeg", 0.85);
  capturedFaces.push(data);
  const img = document.createElement("img"); img.src = data;
  document.getElementById("faceThumbs").appendChild(img);
  toast(`Face ${capturedFaces.length} captured 📸`);
}
async function saveStudent(){
  const body = {
    name: document.getElementById("s_name").value.trim(),
    roll_number: document.getElementById("s_roll").value.trim(),
    class_section: document.getElementById("s_class").value.trim(),
    parent_id: parseInt(document.getElementById("s_parent").value),
    face_images: capturedFaces
  };
  if(!body.name || !body.roll_number || !body.parent_id){ toast("Name, Roll & Parent zaroori hai", "err"); return; }
  try {
    const r = await api("/api/admin/students", { method:"POST", body: JSON.stringify(body) });
    toast(r.message); closeStudentModal(); loadStudents();
  } catch(e){ toast(e.message, "err"); }
}

// ---- Teachers / Parents ----
async function loadTeachers(){
  document.getElementById("pageTitle").textContent = "Teachers";
  const list = await api("/api/admin/teachers");
  document.getElementById("teacherRows").innerHTML = list.map(t=>
    `<tr><td>${t.full_name}</td><td>${t.username}</td><td>${t.phone_number||"-"}</td></tr>`).join("");
}
function openTeacherModal(){ document.getElementById("teacherModal").classList.add("show"); }
async function saveTeacher(){
  try {
    await api("/api/admin/teachers", { method:"POST", body: JSON.stringify({
      full_name: t_name.value, username: t_user.value, password: t_pass.value, phone_number: t_phone.value })});
    toast("Teacher added"); document.getElementById("teacherModal").classList.remove("show"); loadTeachers();
  } catch(e){ toast(e.message, "err"); }
}
async function loadParents(){
  document.getElementById("pageTitle").textContent = "Parents";
  const list = await api("/api/admin/parents");
  document.getElementById("parentRows").innerHTML = list.map(p=>
    `<tr><td>${p.full_name}</td><td>${p.username}</td><td>${p.phone_number||"-"}</td></tr>`).join("");
}
function openParentModal(){ document.getElementById("parentModal").classList.add("show"); }
async function saveParent(){
  try {
    await api("/api/admin/parents", { method:"POST", body: JSON.stringify({
      full_name: p_name.value, username: p_user.value, password: p_pass.value, phone_number: p_phone.value })});
    toast("Parent added"); document.getElementById("parentModal").classList.remove("show"); loadParents();
  } catch(e){ toast(e.message, "err"); }
}

// ---- Live CCTV ----
let camStream = null, scanTimer = null;
async function startCam(){
  document.getElementById("pageTitle").textContent = "Live CCTV";
  if(camStream) return;
  try {
    camStream = await navigator.mediaDevices.getUserMedia({ video:true });
    document.getElementById("video").srcObject = camStream;
  } catch(e){ toast("Webcam nahi mila", "err"); }
}
function grabFrame(){
  const v = document.getElementById("video");
  if(!v.videoWidth) return null;
  const c = document.getElementById("snap");
  c.width = v.videoWidth; c.height = v.videoHeight;
  c.getContext("2d").drawImage(v, 0, 0);
  return c.toDataURL("image/jpeg", 0.8);
}
async function scanOnce(){
  const img = grabFrame();
  if(!img){ toast("Camera ready nahi", "warn"); return; }
  try {
    const r = await api("/api/attendance/recognize", { method:"POST", body: JSON.stringify({ image: img })});
    logCam(r);
    if(r.status === "success") toast(r.message);
    else if(r.status === "duplicate") toast(r.message, "warn");
  } catch(e){ toast(e.message, "err"); }
}
function toggleScan(){
  const btn = document.getElementById("scanBtn");
  if(scanTimer){ clearInterval(scanTimer); scanTimer = null; btn.textContent = "▶ Start Auto-Scan"; btn.classList.add("btn-green"); }
  else { scanTimer = setInterval(scanOnce, 4000); btn.textContent = "⏸ Stop Auto-Scan"; btn.classList.remove("btn-green"); toast("Auto-scan started (har 4s)"); }
}
function logCam(r){
  const icons = { success:"✅", duplicate:"🔁", unknown:"❓", no_face:"👤", closed:"⏰" };
  const item = document.createElement("div");
  item.className = "log-item";
  item.innerHTML = `${icons[r.status]||"ℹ"} <b>${new Date().toLocaleTimeString()}</b> — ${r.message}`;
  const log = document.getElementById("camLog");
  log.insertBefore(item, log.firstChild);
}

loadStats();