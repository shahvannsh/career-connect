// ---------- Auth ----------
const authScreen = document.getElementById("authScreen");
const appEl = document.getElementById("app");
const authError = document.getElementById("authError");

document.querySelectorAll(".auth-tab-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".auth-tab-btn").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".auth-form").forEach(f => f.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById(btn.dataset.form).classList.add("active");
    authError.textContent = "";
  });
});

document.getElementById("loginForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const username = document.getElementById("loginUsername").value.trim();
  const password = document.getElementById("loginPassword").value;
  const res = await fetch("/api/login", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  const data = await res.json();
  if (!res.ok) { authError.textContent = data.error; return; }
  enterApp();
});

document.getElementById("signupForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const username = document.getElementById("signupUsername").value.trim();
  const password = document.getElementById("signupPassword").value;
  const res = await fetch("/api/signup", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  const data = await res.json();
  if (!res.ok) { authError.textContent = data.error; return; }
  enterApp();
});

document.getElementById("logoutBtn").addEventListener("click", async () => {
  await fetch("/api/logout", { method: "POST" });
  location.reload();
});

function enterApp() {
  authScreen.classList.add("hidden");
  appEl.classList.remove("hidden");
  loadJobs();
  loadProfile();
}

async function checkSession() {
  const res = await fetch("/api/me");
  const data = await res.json();
  if (data.loggedIn) enterApp();
}
checkSession();

// ---------- Tabs ----------
const tabBtns = document.querySelectorAll(".tab-btn");
const panels = document.querySelectorAll(".tab-panel");

tabBtns.forEach(btn => {
  btn.addEventListener("click", () => {
    tabBtns.forEach(b => b.classList.remove("active"));
    panels.forEach(p => p.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById(btn.dataset.tab).classList.add("active");
    if (btn.dataset.tab === "matches") loadMatches();
  });
});

function showToast(text) {
  const toast = document.createElement("div");
  toast.className = "toast";
  toast.textContent = text;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 2500);
}

// ---------- Jobs + swipe stack ----------
let allJobs = [];
let stackJobs = [];

async function loadJobs() {
  const res = await fetch("/api/jobs");
  if (!res.ok) return;
  allJobs = await res.json();
  stackJobs = allJobs.filter(j => !j.saved && !j.applied && !j.skipped);
  renderStack();
  renderJobs(allJobs);
}

function renderStack() {
  const stack = document.getElementById("swipeStack");
  stack.innerHTML = "";
  if (stackJobs.length === 0) {
    stack.innerHTML = "<div class='swipe-empty'>No more jobs. Check back later!</div>";
    return;
  }
  // render top 3 cards, topmost last in DOM (on top)
  const visible = stackJobs.slice(0, 3).reverse();
  visible.forEach((job) => {
    const card = buildCard(job);
    stack.appendChild(card);
  });
  attachDrag(stack.lastElementChild, stackJobs[0]);
}

function buildCard(job) {
  const card = document.createElement("div");
  card.className = "swipe-card";
  card.dataset.id = job.id;
  card.innerHTML = `
    <div class="swipe-badge like">LIKE</div>
    <div class="swipe-badge nope">NOPE</div>
    <div>
      <div class="job-logo">${job.logo}</div>
      <p class="job-name">${job.name}</p>
      <p class="job-industry">${job.industry}</p>
      <p class="job-marketcap">Market Cap: ${job.marketCap}</p>
    </div>
    <div>
      <p class="job-salary">${job.salary}</p>
      <p class="job-compat">Compatibility: ${job.compatibility}%</p>
    </div>
  `;
  return card;
}

function attachDrag(card, job) {
  if (!card) return;
  let startX = 0, startY = 0, curX = 0, dragging = false;
  const likeBadge = card.querySelector(".like");
  const nopeBadge = card.querySelector(".nope");

  function pointerDown(e) {
    dragging = true;
    const p = e.touches ? e.touches[0] : e;
    startX = p.clientX;
    startY = p.clientY;
    card.style.transition = "none";
  }

  function pointerMove(e) {
    if (!dragging) return;
    const p = e.touches ? e.touches[0] : e;
    curX = p.clientX - startX;
    const curY = p.clientY - startY;
    const rotate = curX / 12;
    card.style.transform = `translate(${curX}px, ${curY}px) rotate(${rotate}deg)`;
    likeBadge.style.opacity = Math.min(Math.max(curX / 80, 0), 1);
    nopeBadge.style.opacity = Math.min(Math.max(-curX / 80, 0), 1);
  }

  function pointerUp() {
    if (!dragging) return;
    dragging = false;
    card.style.transition = "transform 0.3s ease";
    if (curX > 100) {
      swipeAway(card, 1, () => handleSwipe(job, "like"));
    } else if (curX < -100) {
      swipeAway(card, -1, () => handleSwipe(job, "skip"));
    } else {
      card.style.transform = "translate(0,0) rotate(0)";
    }
    curX = 0;
  }

  card.addEventListener("mousedown", pointerDown);
  window.addEventListener("mousemove", pointerMove);
  window.addEventListener("mouseup", pointerUp);
  card.addEventListener("touchstart", pointerDown, { passive: true });
  card.addEventListener("touchmove", pointerMove, { passive: true });
  card.addEventListener("touchend", pointerUp);
}

function swipeAway(card, direction, callback) {
  card.style.transform = `translate(${direction * 500}px, -40px) rotate(${direction * 30}deg)`;
  card.style.opacity = "0";
  setTimeout(callback, 250);
}

async function handleSwipe(job, action) {
  stackJobs = stackJobs.filter(j => j.id !== job.id);
  if (action === "like") {
    await fetch(`/api/jobs/${job.id}/save`, { method: "POST" });
    showToast(`Saved ${job.name}`);
  } else {
    await fetch(`/api/jobs/${job.id}/skip`, { method: "POST" });
  }
  renderStack();
}

document.getElementById("likeBtn").addEventListener("click", () => {
  const top = document.querySelector(".swipe-stack .swipe-card:last-child");
  if (top && stackJobs[0]) swipeAway(top, 1, () => handleSwipe(stackJobs[0], "like"));
});

document.getElementById("skipBtn").addEventListener("click", () => {
  const top = document.querySelector(".swipe-stack .swipe-card:last-child");
  if (top && stackJobs[0]) swipeAway(top, -1, () => handleSwipe(stackJobs[0], "skip"));
});

// ---------- Full job list ----------
function renderJobs(jobs) {
  const list = document.getElementById("jobList");
  list.innerHTML = "";
  jobs.forEach(job => {
    const card = document.createElement("div");
    card.className = "job-card";
    card.innerHTML = `
      <div class="job-top">
        <div class="job-info">
          <div class="job-logo">${job.logo}</div>
          <div>
            <p class="job-name">${job.name}</p>
            <p class="job-industry">${job.industry}</p>
          </div>
        </div>
        <div class="job-meta">
          <span class="job-salary">${job.salary}</span>
          <span class="job-compat">Compatibility: ${job.compatibility}%</span>
        </div>
      </div>
      <p class="job-marketcap">Market Cap: ${job.marketCap}</p>
      <div class="job-actions">
        <button class="btn-save ${job.saved ? "saved" : ""}" data-id="${job.id}">
          ${job.saved ? "♥ Saved" : "♡ Save"}
        </button>
        <button class="btn-apply ${job.applied ? "applied" : ""}" data-id="${job.id}" ${job.applied ? "disabled" : ""}>
          ${job.applied ? "✓ Applied" : "➤ Apply"}
        </button>
      </div>
    `;
    list.appendChild(card);
  });

  list.querySelectorAll(".btn-save").forEach(btn => {
    btn.addEventListener("click", async () => {
      await fetch(`/api/jobs/${btn.dataset.id}/save`, { method: "POST" });
      loadJobs();
    });
  });

  list.querySelectorAll(".btn-apply").forEach(btn => {
    btn.addEventListener("click", async () => {
      const res = await fetch(`/api/jobs/${btn.dataset.id}/apply`, { method: "POST" });
      const data = await res.json();
      showToast(data.message || "Applied!");
      loadJobs();
    });
  });
}

document.getElementById("searchInput").addEventListener("input", (e) => {
  const q = e.target.value.toLowerCase();
  renderJobs(allJobs.filter(j =>
    j.name.toLowerCase().includes(q) || j.industry.toLowerCase().includes(q)
  ));
});

// ---------- Profile ----------
const nameInput = document.getElementById("nameInput");
const titleInput = document.getElementById("titleInput");
const bioInput = document.getElementById("bioInput");
const photoInput = document.getElementById("photoInput");
const resumeInput = document.getElementById("resumeInput");
const photoPreview = document.getElementById("photoPreview");
const photoFileName = document.getElementById("photoFileName");
const resumeFileName = document.getElementById("resumeFileName");
const linkedinBtn = document.getElementById("linkedinBtn");
const saveProfileBtn = document.getElementById("saveProfileBtn");
const skillsBox = document.getElementById("skillsBox");

async function loadProfile() {
  const res = await fetch("/api/profile");
  if (!res.ok) return;
  const profile = await res.json();
  nameInput.value = profile.name || "";
  titleInput.value = profile.title || "";
  bioInput.value = profile.bio || "";
  if (profile.photo) {
    photoPreview.src = `/uploads/photos/${profile.photo}`;
    photoFileName.textContent = profile.photo;
  }
  if (profile.resume) resumeFileName.textContent = profile.resume;
  renderSkills(profile.skills || []);
  updateLinkedinBtn(profile.linkedin_connected);
}

function renderSkills(skills) {
  skillsBox.innerHTML = skills.length
    ? skills.map(s => `<span class="skill-chip">${s}</span>`).join("")
    : "<span style='color:#999;font-size:13px;'>No skills detected yet — add a bio or upload a resume.</span>";
}

function updateLinkedinBtn(connected) {
  linkedinBtn.classList.toggle("connected", connected);
  linkedinBtn.textContent = connected ? "LinkedIn Connected" : "Connect LinkedIn";
}

photoInput.addEventListener("change", () => {
  const file = photoInput.files[0];
  if (file) {
    photoFileName.textContent = file.name;
    photoPreview.src = URL.createObjectURL(file);
  }
});

resumeInput.addEventListener("change", () => {
  const file = resumeInput.files[0];
  if (file) resumeFileName.textContent = file.name;
});

linkedinBtn.addEventListener("click", async () => {
  const res = await fetch("/api/profile/linkedin", { method: "POST" });
  const data = await res.json();
  updateLinkedinBtn(data.linkedInConnected);
  showToast(data.message);
});

saveProfileBtn.addEventListener("click", async () => {
  const formData = new FormData();
  formData.append("name", nameInput.value);
  formData.append("title", titleInput.value);
  formData.append("bio", bioInput.value);
  if (photoInput.files[0]) formData.append("photo", photoInput.files[0]);
  if (resumeInput.files[0]) formData.append("resume", resumeInput.files[0]);

  const res = await fetch("/api/profile", { method: "POST", body: formData });
  const data = await res.json();
  renderSkills(data.skills || []);
  showToast("Profile saved!");
  loadJobs();
});

// ---------- Matches ----------
async function loadMatches() {
  const res = await fetch("/api/matches");
  const matches = await res.json();
  const list = document.getElementById("matchList");
  list.innerHTML = "";
  if (matches.length === 0) {
    list.innerHTML = "<li>No matches yet. Apply to jobs in Discover!</li>";
    return;
  }
  matches.forEach(m => {
    const li = document.createElement("li");
    li.textContent = m.name;
    list.appendChild(li);
  });
}
