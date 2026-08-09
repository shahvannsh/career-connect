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

let allJobs = [];

async function loadJobs() {
  const res = await fetch("/api/jobs");
  allJobs = await res.json();
  renderJobs(allJobs);
}

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
      const id = btn.dataset.id;
      await fetch(`/api/jobs/${id}/save`, { method: "POST" });
      loadJobs();
    });
  });

  list.querySelectorAll(".btn-apply").forEach(btn => {
    btn.addEventListener("click", async () => {
      const id = btn.dataset.id;
      const res = await fetch(`/api/jobs/${id}/apply`, { method: "POST" });
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

// Profile
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

async function loadProfile() {
  const res = await fetch("/api/profile");
  const profile = await res.json();
  nameInput.value = profile.name || "";
  titleInput.value = profile.title || "";
  bioInput.value = profile.bio || "";
  if (profile.photo) {
    photoPreview.src = `/uploads/photos/${profile.photo}`;
    photoFileName.textContent = profile.photo;
  }
  if (profile.resume) {
    resumeFileName.textContent = profile.resume;
  }
  updateLinkedinBtn(profile.linkedInConnected);
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

  await fetch("/api/profile", { method: "POST", body: formData });
  showToast("Profile saved!");
  loadJobs();
});

// Matches
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

loadJobs();
loadProfile();
