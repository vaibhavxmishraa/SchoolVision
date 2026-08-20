async function doLogin(){
  const username = document.getElementById("username").value.trim();
  const password = document.getElementById("password").value.trim();
  if(!username || !password){ toast("Username & password daaliye", "err"); return; }
  try {
    const d = await api("/api/auth/login", { method:"POST",
      body: JSON.stringify({ username, password }) });
    saveAuth(d);
    toast("Welcome " + d.name + "!");
    setTimeout(()=>{
      if(d.role === "Admin") location.href = "admin.html";
      else if(d.role === "Teacher") location.href = "teacher.html";
      else location.href = "parent.html";
    }, 600);
  } catch(e){ toast(e.message, "err"); }
}
document.getElementById("password").addEventListener("keydown", e=>{ if(e.key==="Enter") doLogin(); });