// PulsePoint CareOS - Modern Clinical AI & Operations Controller

const API_BASE = window.location.protocol === "file:" ? "http://127.0.0.1:8000/api/v1" : "/api/v1";
let frontendOnlyMode = false;
let offlineNoticeShown = false;

const demoData = {
  doctors: [
    { id: 1, name: "Ava Bennett", specialization: "Cardiology", department_id: 1, department: { name: "Cardiology" }, email: "ava.bennett@pulsepoint.health", phone: "+1 555 0101" },
    { id: 2, name: "Noah Williams", specialization: "Internal Medicine", department_id: 2, department: { name: "Internal Medicine" }, email: "noah.williams@pulsepoint.health", phone: "+1 555 0102" },
    { id: 3, name: "Mia Patel", specialization: "Pediatrics", department_id: 3, department: { name: "Pediatrics" }, email: "mia.patel@pulsepoint.health", phone: "+1 555 0103" },
  ],
  departments: [
    { id: 1, name: "Cardiology", description: "Heart and cardiovascular care, diagnostics, and follow-up services.", is_active: true },
    { id: 2, name: "Internal Medicine", description: "Comprehensive care for adult health and chronic conditions.", is_active: true },
    { id: 3, name: "Pediatrics", description: "Specialized medical care for infants, children, and adolescents.", is_active: true },
  ],
  patients: [{ id: 1, name: "Demo Patient", gender: "Other", date_of_birth: "1990-01-01", phone: "+1 555 0199", email: "patient@hospital.com" }],
  appointments: [],
  documents: [
    { id: 1, title: "Visiting Hours", filename: "visiting_hours.md", file_type: "md", status: "indexed", indexed_at: new Date().toISOString() },
    { id: 2, title: "Emergency Procedures", filename: "emergency_procedures.md", file_type: "md", status: "indexed", indexed_at: new Date().toISOString() },
  ],
};

function demoResponse(data, status = 200) {
  return { ok: status >= 200 && status < 300, status, json: async () => data };
}

function demoChatAnswer(question) {
  const normalized = question.toLowerCase();
  const emergency = /chest pain|can't breathe|cannot breathe|difficulty breathing|trouble breathing|shortness of breath|suicide|kill myself|overdose|stroke|face droop|unconscious|not breathing|severe bleeding|heavy bleeding|anaphylaxis|heart attack|seizure|choking|poison|\b911\b|medical emergency|emergency (right now|help)|call (an )?emergency (number|services)/.test(normalized);
  if (emergency) {
    return { emergency: true, answer: "This sounds like a medical emergency. Call your local emergency number (for example 911) or go to the nearest Emergency Department immediately. Do not wait for a chatbot answer. If you are with the person, stay with them and follow instructions from emergency dispatchers.", sources: [] };
  }
  let answer = "PulsePoint CareOS clinical guidance is available from the verified policy repository.";
  let document = "Visiting Hours";
  if (/where.*emergency|emergency department/.test(normalized)) { answer = "The Emergency Department is on the Ground Floor in the Emergency Wing. Call +91 33 4000 2199 for emergency assistance."; document = "Emergency Procedures"; }
  else if (/open|hospital hour/.test(normalized)) answer = "The Emergency Department operates 24 hours a day. Most outpatient departments operate Monday through Saturday during their listed clinic hours.";
  else if (/book.*phone|appointment.*phone/.test(normalized)) { answer = "Appointments can be booked through the Appointment Desk at +91 33 4000 2205."; document = "Appointment Policy"; }
  else if (/general visiting/.test(normalized)) answer = "General inpatient visiting hours are 11:00 AM-1:00 PM and 4:00 PM-7:00 PM.";
  else if (/visit|icu/.test(normalized)) answer = "ICU visiting hours are 11:00 AM-12:00 PM and 5:00 PM-6:00 PM. A maximum of two visitors may enter at one time.";
  else if (/mri/.test(normalized)) { answer = "Yes. The Diagnostic Center has a 1.5 Tesla MRI scanner."; document = "Diagnostic Center"; }
  else if (/ct scanner|ct scan/.test(normalized)) { answer = "Yes. The hospital has a 128-slice CT scanner."; document = "Diagnostic Center"; }
  else if (/pharmacy/.test(normalized)) { answer = "Yes. The pharmacy is on the Ground Floor in the Main Lobby and is open from 7:00 AM to 11:00 PM."; document = "Pharmacy Policy"; }
  else if (/how many beds|capacity/.test(normalized)) answer = "The hospital has 350 beds.";
  else if (/icu bed|have an icu/.test(normalized)) answer = "Yes. The ICU has 25 beds.";
  else if (/pediatric|pediatrics/.test(normalized)) { answer = "Yes. Pediatrics is located on the 2nd Floor of the Children's Wing."; document = "Pediatrics Department"; }
  else if (/maternity|obstetrics/.test(normalized)) { answer = "Yes. Obstetrics and Gynecology operates a 30-bed maternity unit."; document = "Maternity Services"; }
  else if (/medical record/.test(normalized)) { answer = "Medical records can be requested from the Records Office on the Ground Floor, Monday-Friday, 9:00 AM-5:00 PM."; document = "Medical Records Policy"; }
  else if (/laboratory|lab report/.test(normalized)) { answer = "Yes. Selected laboratory reports can be viewed through the PulsePoint patient portal."; document = "Patient Portal"; }
  else if (/department|service|doctor|special/.test(normalized)) { answer = "Our current departments include Cardiology, Internal Medicine, and Pediatrics."; document = "Cardiology Department"; }
  else if (/opd|consult/.test(normalized)) { answer = "Most outpatient departments operate Monday through Saturday during their listed clinic hours."; document = "Appointment Policy"; }
  else if (/appointment|schedule|cancel/.test(normalized)) { answer = "Appointments can be scheduled from the Appointments section. Please cancel or reschedule as early as possible so the slot can be offered to another patient."; document = "Appointment Policy"; }
  return { emergency: false, answer, sources: [{ document, chunk: 0, score: 0.98, excerpt: answer }] };
}

async function demoApiFetch(endpoint, options = {}) {
  const method = (options.method || "GET").toUpperCase();
  const body = options.body && typeof options.body === "string" ? JSON.parse(options.body) : {};
  if (endpoint === "/auth/login" && method === "POST") {
    const isAdmin = body.email === "admin@admin.com" || body.email === "admin@pulsepoint.health" || body.email?.toLowerCase().includes("admin");
    return demoResponse({ access_token: `demo-token-${isAdmin ? "admin" : "patient"}`, email: body.email || (isAdmin ? "admin@pulsepoint.health" : "patient@hospital.com"), role: isAdmin ? "admin" : "patient", user_id: isAdmin ? 1 : 2 });
  }
  if (endpoint === "/auth/register" && method === "POST") return demoResponse({ id: 2 });
  if (endpoint === "/chat" && method === "POST") return demoResponse(demoChatAnswer(body.question || body.message || ""));
  if (endpoint === "/doctors" && method === "GET") return demoResponse(demoData.doctors);
  if (endpoint === "/departments" && method === "GET") return demoResponse(demoData.departments);
  if (endpoint === "/departments" && method === "POST") {
    const department = { ...body, id: demoData.departments.length + 1, created_at: new Date().toISOString() };
    demoData.departments.push(department);
    return demoResponse(department, 201);
  }
  const departmentMatch = endpoint.match(/^\/departments\/(\d+)$/);
  if (departmentMatch && (method === "PUT" || method === "PATCH")) {
    const department = demoData.departments.find(item => item.id === Number(departmentMatch[1]));
    if (!department) return demoResponse({ detail: "Department not found" }, 404);
    Object.assign(department, body);
    return demoResponse(department);
  }
  if (departmentMatch && method === "DELETE") {
    const index = demoData.departments.findIndex(item => item.id === Number(departmentMatch[1]));
    if (index < 0) return demoResponse({ detail: "Department not found" }, 404);
    demoData.departments.splice(index, 1);
    return demoResponse({}, 204);
  }
  if (endpoint === "/doctors" && method === "POST") {
    const doctor = { ...body, id: demoData.doctors.length + 1, created_at: new Date().toISOString() };
    demoData.doctors.push(doctor);
    return demoResponse(doctor, 201);
  }
  if (endpoint === "/patients" && method === "GET") return demoResponse(demoData.patients);
  if (endpoint === "/patients" && method === "POST") {
    const patient = { ...body, id: demoData.patients.length + 1 };
    demoData.patients.push(patient);
    return demoResponse(patient, 201);
  }
  const patientMatch = endpoint.match(/^\/patients\/(\d+)$/);
  if (patientMatch && method === "DELETE") {
    const index = demoData.patients.findIndex(item => item.id === Number(patientMatch[1]));
    if (index < 0) return demoResponse({ detail: "Patient not found" }, 404);
    demoData.patients.splice(index, 1);
    return demoResponse({}, 204);
  }
  const doctorMatch = endpoint.match(/^\/doctors\/(\d+)$/);
  if (doctorMatch && (method === "PUT" || method === "PATCH")) {
    const doctor = demoData.doctors.find(item => item.id === Number(doctorMatch[1]));
    if (!doctor) return demoResponse({ detail: "Doctor not found" }, 404);
    Object.assign(doctor, body);
    return demoResponse(doctor);
  }
  if (doctorMatch && method === "DELETE") {
    const index = demoData.doctors.findIndex(item => item.id === Number(doctorMatch[1]));
    if (index < 0) return demoResponse({ detail: "Doctor not found" }, 404);
    demoData.doctors.splice(index, 1);
    return demoResponse({}, 204);
  }
  if (endpoint === "/appointments" && method === "GET") return demoResponse(demoData.appointments);
  if (endpoint === "/appointments" && method === "POST") {
    const appointment = { ...body, id: demoData.appointments.length + 1, status: "scheduled", doctor: demoData.doctors.find(d => d.id === body.doctor_id), patient: demoData.patients.find(p => p.id === body.patient_id) };
    demoData.appointments.push(appointment);
    return demoResponse(appointment, 201);
  }
  const appointmentMatch = endpoint.match(/^\/appointments\/(\d+)(?:\/status)?$/);
  if (appointmentMatch && method === "PATCH") {
    const appointment = demoData.appointments.find(item => item.id === Number(appointmentMatch[1]));
    if (!appointment) return demoResponse({ detail: "Appointment not found" }, 404);
    appointment.status = body.status;
    return demoResponse(appointment);
  }
  if (appointmentMatch && method === "DELETE") {
    const index = demoData.appointments.findIndex(item => item.id === Number(appointmentMatch[1]));
    if (index < 0) return demoResponse({ detail: "Appointment not found" }, 404);
    demoData.appointments.splice(index, 1);
    return demoResponse({}, 204);
  }
  if (endpoint === "/documents" && method === "GET") return demoResponse(demoData.documents);
  if (endpoint === "/documents/upload" && method === "POST") {
    const file = options.body instanceof FormData ? options.body.get("file") : null;
    const title = options.body instanceof FormData ? options.body.get("title") : "";
    const filename = file && file.name ? file.name : "uploaded-document.txt";
    const extension = filename.includes(".") ? filename.split(".").pop().toLowerCase() : "text";
    const document = {
      id: demoData.documents.length + 1,
      title: title || filename,
      filename,
      file_type: extension,
      status: "indexed",
      chunk_count: 1,
      indexed_at: new Date().toISOString(),
    };
    demoData.documents.unshift(document);
    return demoResponse(document, 201);
  }
  const documentMatch = endpoint.match(/^\/documents\/(\d+)$/);
  if (documentMatch && method === "DELETE") {
    const index = demoData.documents.findIndex(item => item.id === Number(documentMatch[1]));
    if (index < 0) return demoResponse({ detail: "Document not found" }, 404);
    demoData.documents.splice(index, 1);
    return demoResponse({}, 204);
  }
  return demoResponse({ detail: "Demo mode: endpoint unavailable" }, 404);
}

// State
let authToken = localStorage.getItem("hospital_jwt") || "";
let currentUser = null;
try {
  currentUser = JSON.parse(localStorage.getItem("hospital_user") || "null");
} catch {
  currentUser = null;
}
let selfPatientRecord = null;
const appointmentLookup = { doctors: new Map(), patients: new Map() };

// ==========================================
// Toast Notification Utility
// ==========================================
function showToast(message, type = "info") {
  const container = document.getElementById("toastContainer");
  if (!container) return;
  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transition = "opacity 0.3s";
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// ==========================================
// API Request Helper
// ==========================================
async function apiFetch(endpoint, options = {}) {
  const headers = options.headers || {};
  if (authToken && !headers["Authorization"]) {
    headers["Authorization"] = `Bearer ${authToken}`;
  }
  if (!(options.body instanceof FormData) && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }
  options.headers = headers;

  if (frontendOnlyMode) return demoApiFetch(endpoint, options);

  let res;
  try {
    res = await fetch(`${API_BASE}${endpoint}`, options);
  } catch (error) {
    frontendOnlyMode = true;
    if (!offlineNoticeShown) {
      offlineNoticeShown = true;
      showToast("Backend unavailable. Running in browser demo mode.", "info");
    }
    return demoApiFetch(endpoint, options);
  }
  if (res.status === 401 && authToken && endpoint !== "/auth/login") {
    showToast("Session expired. Please sign in again.", "error");
    logout();
  }
  return res;
}

// ==========================================
// Authentication & RBAC
// ==========================================
const authModal = document.getElementById("authModal");
const loginModalBtn = document.getElementById("loginModalBtn");
const closeAuthModalBtn = document.getElementById("closeAuthModalBtn");
const signInForm = document.getElementById("signInForm");
const inputEmail = document.getElementById("inputEmail");
const inputPassword = document.getElementById("inputPassword");
const userProfileWidget = document.getElementById("userProfileWidget");
const userEmailLabel = document.getElementById("userEmailLabel");
const userRoleBadge = document.getElementById("userRoleBadge");
const logoutBtn = document.getElementById("logoutBtn");
const authStatusIndicator = document.getElementById("authStatusIndicator");
const demoLoginAdminBtn = document.getElementById("demoLoginAdminBtn");
const demoLoginPatientBtn = document.getElementById("demoLoginPatientBtn");

const adminPatientSelectGroup = document.getElementById("adminPatientSelectGroup");
const patientSelfSelectGroup = document.getElementById("patientSelfSelectGroup");
const patientSelfDisplay = document.getElementById("patientSelfDisplay");

function getCurrentUserRole() {
  if (!authToken || !currentUser) return "guest";
  return (currentUser.role || "user").toLowerCase();
}

function isAdminOrStaff() {
  const role = getCurrentUserRole();
  return role === "admin" || role === "staff";
}

function applyRolePermissions() {
  const role = getCurrentUserRole();
  const adminStaff = isAdminOrStaff();

  // 1. Hide/Show sidebar navigation items restricted to admin/staff
  document.querySelectorAll("[data-roles]").forEach(el => {
    const allowed = el.dataset.roles.split(",").map(r => r.trim().toLowerCase());
    if (allowed.includes(role)) {
      el.style.display = "";
    } else {
      el.style.display = "none";
    }
  });

  // 2. Adjust Appointment booking form based on role
  if (adminStaff) {
    if (adminPatientSelectGroup) adminPatientSelectGroup.style.display = "";
    if (patientSelfSelectGroup) patientSelfSelectGroup.style.display = "none";
  } else {
    // PATIENT / GUEST: Never show other patients in dropdown
    if (adminPatientSelectGroup) adminPatientSelectGroup.style.display = "none";
    if (patientSelfSelectGroup) patientSelfSelectGroup.style.display = "";
  }

  // 3. Prevent patient from viewing admin-only panels if currently selected
  const activeNav = document.querySelector(".nav-item.active[data-view]");
  if (activeNav) {
    const activeView = activeNav.dataset.view;
    if ((activeView === "patients" || activeView === "knowledge") && !adminStaff) {
      switchView("assistant");
    }
  }
}

function updateAuthDisplay() {
  const role = getCurrentUserRole();

  if (authToken && currentUser) {
    if (userProfileWidget) userProfileWidget.style.display = "flex";
    if (loginModalBtn) loginModalBtn.style.display = "none";
    if (userEmailLabel) userEmailLabel.textContent = currentUser.email;
    if (userRoleBadge) {
      userRoleBadge.textContent = role.toUpperCase();
      userRoleBadge.className = `role-pill role-${role}`;
    }
    if (authStatusIndicator) {
      if (role === "admin") {
        authStatusIndicator.textContent = `👑 Clinical Administrator: ${currentUser.email}`;
        authStatusIndicator.style.color = "var(--emergency-red)";
      } else if (role === "staff") {
        authStatusIndicator.textContent = `🩺 Clinical Staff: ${currentUser.email}`;
        authStatusIndicator.style.color = "var(--warning)";
      } else {
        authStatusIndicator.textContent = `👤 Patient Portal: ${currentUser.email}`;
        authStatusIndicator.style.color = "var(--primary)";
      }
    }
  } else {
    if (userProfileWidget) userProfileWidget.style.display = "none";
    if (loginModalBtn) loginModalBtn.style.display = "block";
    if (authStatusIndicator) {
      authStatusIndicator.textContent = "Guest Mode (Sign in for appointments and full medical records)";
      authStatusIndicator.style.color = "var(--text-muted)";
    }
  }

  applyRolePermissions();
}

function openModal() {
  authModal.classList.remove("hidden");
  inputEmail.focus();
}

function closeModal() {
  authModal.classList.add("hidden");
}

function logout() {
  authToken = "";
  currentUser = null;
  selfPatientRecord = null;
  localStorage.removeItem("hospital_jwt");
  localStorage.removeItem("hospital_user");
  updateAuthDisplay();
  showToast("Signed out successfully.", "info");
  switchView("assistant");
}

async function performLogin(email, password, silent = false) {
  try {
    const res = await apiFetch("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Invalid login credentials");
    }

    const data = await res.json();
    authToken = data.access_token;
    currentUser = {
      email: data.email,
      role: data.role,
      user_id: data.user_id,
    };

    localStorage.setItem("hospital_jwt", authToken);
    localStorage.setItem("hospital_user", JSON.stringify(currentUser));

    updateAuthDisplay();
    closeModal();
    showToast(`Logged in as ${data.email} (${(data.role || "user").toUpperCase()})`, "success");

    // Load patient record if logged in as patient
    if (data.role === "patient" || data.role === "user") {
      await resolvePatientSelfRecord();
    }

    refreshActiveView();
    return true;
  } catch (err) {
    if (!silent) {
      showToast(err.message, "error");
    }
    return false;
  }
}

async function resolvePatientSelfRecord() {
  try {
    const res = await apiFetch("/patients");
    if (res.ok) {
      const list = await res.json();
      if (list && list.length > 0) {
        selfPatientRecord = list[0];
        if (patientSelfDisplay) {
          patientSelfDisplay.innerHTML = `👤 Booking for: <strong>${escapeHtml(selfPatientRecord.name)}</strong> (Patient #${selfPatientRecord.id})`;
        }
      } else {
        // Patient has no linked record yet; use account info
        selfPatientRecord = { id: 1, name: currentUser ? currentUser.email : "Patient" };
        if (patientSelfDisplay) {
          patientSelfDisplay.innerHTML = `👤 Booking for: <strong>${escapeHtml(selfPatientRecord.name)}</strong>`;
        }
      }
    }
  } catch (err) {
    console.error("Failed to resolve self patient record:", err);
  }
}

// ==========================================
// Navigation & Views
// ==========================================
const navItems = document.querySelectorAll(".nav-item[data-view]");
const viewPanels = document.querySelectorAll(".view-panel");
const viewTitle = document.getElementById("viewTitle");

const viewTitles = {
  assistant: "AI Knowledge Assistant",
  appointments: "Appointments & Care Scheduling",
  directory: "Care Team & Clinical Departments",
  patients: "Patient Medical Records Registry",
  knowledge: "Clinical Knowledge Hub & Ingestion",
};

function switchView(viewName) {
  // Enforce RBAC guard on view switching
  if ((viewName === "patients" || viewName === "knowledge") && !isAdminOrStaff()) {
    showToast("Access Restricted: Staff or Administrator role required.", "error");
    return;
  }

  navItems.forEach(item => {
    item.classList.toggle("active", item.dataset.view === viewName);
  });

  viewPanels.forEach(panel => {
    panel.classList.toggle("active", panel.id === `panel-${viewName}`);
  });

  if (viewTitle) {
    viewTitle.textContent = viewTitles[viewName] || "PulsePoint CareOS";
  }

  if (directoryAdminTools) {
    directoryAdminTools.style.display = viewName === "directory" && isAdminOrStaff() ? "grid" : "none";
  }

  if (viewName === "appointments") {
    loadDoctorsAndPatientsForAppt().then(loadAppointments);
  } else if (viewName === "directory") {
    loadDepartments();
    loadDoctors();
    if (isAdminOrStaff()) loadDepartmentOptions();
  } else if (viewName === "patients" && isAdminOrStaff()) {
    loadPatients();
  } else if (viewName === "knowledge" && isAdminOrStaff()) {
    loadKnowledgeDocs();
  }
}

function refreshActiveView() {
  const activeNav = document.querySelector(".nav-item.active[data-view]");
  if (activeNav) {
    switchView(activeNav.dataset.view);
  }
}

// ==========================================
// AI Knowledge Assistant (RAG Chat)
// ==========================================
const chatMessagesPane = document.getElementById("chatMessagesPane");
const chatQuestionInput = document.getElementById("chatQuestionInput");
const chatSendBtn = document.getElementById("chatSendBtn");
const modeSelect = document.getElementById("modeSelect");
const sourcesList = document.getElementById("sourcesList");

function appendChatMessage(sender, text, isEmergency = false) {
  const bubble = document.createElement("div");
  bubble.className = `msg-bubble ${
    sender === "User" ? "msg-user" : isEmergency ? "msg-emergency" : "msg-assistant"
  }`;

  if (isEmergency) {
    const alertTag = document.createElement("div");
    alertTag.className = "emergency-alert-tag";
    alertTag.textContent = "🚨 MEDICAL EMERGENCY DETECTED";
    bubble.appendChild(alertTag);
  }

  const content = document.createElement("div");
  content.innerHTML = `<strong>${sender}:</strong> ${escapeHtml(text)}`;
  bubble.appendChild(content);

  chatMessagesPane.appendChild(bubble);
  chatMessagesPane.scrollTop = chatMessagesPane.scrollHeight;
}

function renderSources(sources) {
  sourcesList.innerHTML = "";
  if (!sources || sources.length === 0) {
    sourcesList.innerHTML =
      '<div class="empty-state">No sources retrieved for this response.<br>Ask a specific clinical or policy question.</div>';
    return;
  }

  sources.forEach((src, idx) => {
    const item = document.createElement("div");
    item.className = "source-item";

    const title = document.createElement("div");
    title.className = "source-title";
    const scoreVal = typeof src.score === "number" ? src.score.toFixed(4) : "N/A";
    title.innerHTML = `<span>Source #${idx + 1}: ${escapeHtml(src.document || src.filename || "Knowledge Doc")}</span>
                       <span style="font-size:0.75rem; color:var(--text-muted);">Score: ${scoreVal}</span>`;
    item.appendChild(title);

    const meta = document.createElement("div");
    meta.className = "source-meta";
    meta.textContent = `Chunk #${src.chunk ?? src.chunk_index ?? 0}`;
    item.appendChild(meta);

    if (src.excerpt) {
      const excerpt = document.createElement("div");
      excerpt.className = "source-excerpt";
      excerpt.textContent = `"${src.excerpt}"`;
      item.appendChild(excerpt);
    }

    sourcesList.appendChild(item);
  });
}

async function sendChatQuery(customQuery) {
  const query = customQuery || chatQuestionInput.value.trim();
  if (!query) return;

  if (!authToken) {
    showToast("Please sign in or use 1-click Demo Login to ask questions.", "info");
    openModal();
    return;
  }

  chatQuestionInput.value = "";
  appendChatMessage("User", query);
  chatSendBtn.disabled = true;
  chatSendBtn.textContent = "Thinking...";

  const payload = {
    message: query,
    mode: modeSelect.value,
    top_k: 3,
  };

  try {
    const res = await apiFetch("/chat", {
      method: "POST",
      body: JSON.stringify(payload),
    });

    if (res.status === 401) {
      appendChatMessage("PulsePoint Assistant", "Authentication required. Please sign in to continue.");
      renderSources([]);
      return;
    }

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      appendChatMessage("PulsePoint Assistant", `Error: ${err.detail || "Unable to retrieve response from assistant."}`);
      renderSources([]);
      return;
    }

    const data = await res.json();
    appendChatMessage("PulsePoint Assistant", data.answer, data.emergency);
    renderSources(data.sources);

  } catch (err) {
    appendChatMessage("PulsePoint Assistant", `Connection error: ${err.message}. Ensure backend is running.`);
    renderSources([]);
  } finally {
    chatSendBtn.disabled = false;
    chatSendBtn.textContent = "Send";
    chatQuestionInput.focus();
  }
}

// ==========================================
// Appointments Management
// ==========================================
const apptDoctor = document.getElementById("apptDoctor");
const apptPatient = document.getElementById("apptPatient");
const appointmentsTableBody = document.getElementById("appointmentsTableBody");
const bookApptForm = document.getElementById("bookApptForm");
const refreshApptsBtn = document.getElementById("refreshApptsBtn");

async function loadDoctorsAndPatientsForAppt() {
  try {
    const docRes = await apiFetch("/doctors");
    if (docRes.ok) {
      const doctors = await docRes.json();
      appointmentLookup.doctors.clear();
      apptDoctor.innerHTML = '<option value="">-- Choose a Doctor --</option>';
      doctors.forEach(d => {
        appointmentLookup.doctors.set(String(d.id), d);
        const opt = document.createElement("option");
        opt.value = d.id;
        opt.textContent = `Dr. ${d.name} (${d.specialization || "General"})`;
        apptDoctor.appendChild(opt);
      });
    }

    // Only load all hospital patients if Admin or Staff
    if (isAdminOrStaff()) {
      const patRes = await apiFetch("/patients");
      if (patRes.ok) {
        const patients = await patRes.json();
        appointmentLookup.patients.clear();
        apptPatient.innerHTML = '<option value="">-- Choose a Patient --</option>';
        patients.forEach(p => {
          appointmentLookup.patients.set(String(p.id), p);
          const opt = document.createElement("option");
          opt.value = p.id;
          opt.textContent = `${p.name} (ID #${p.id}, ${p.gender || "N/A"})`;
          apptPatient.appendChild(opt);
        });
      }
    } else {
      // Patient role: Resolve and lock to self
      await resolvePatientSelfRecord();
    }
  } catch (err) {
    console.error("Error loading dropdown data:", err);
  }
}

async function loadAppointments() {
  appointmentsTableBody.innerHTML = '<tr><td colspan="6" class="empty-state">Loading appointments...</td></tr>';
  try {
    const res = await apiFetch("/appointments");
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      appointmentsTableBody.innerHTML = `<tr><td colspan="6" class="empty-state">${err.detail || "Sign in to view appointments"}</td></tr>`;
      return;
    }

    const list = await res.json();
    if (list.length === 0) {
      const msg = isAdminOrStaff() ? "No appointments booked in the system." : "You have no scheduled appointments.";
      appointmentsTableBody.innerHTML = `<tr><td colspan="6" class="empty-state">${msg}</td></tr>`;
      return;
    }

    appointmentsTableBody.innerHTML = "";
    list.forEach(a => {
      const tr = document.createElement("tr");
      const doctor = a.doctor || appointmentLookup.doctors.get(String(a.doctor_id));
      const patient = a.patient || appointmentLookup.patients.get(String(a.patient_id));
      const docName = doctor ? `Dr. ${doctor.name}` : `Doctor #${a.doctor_id}`;
      const patName = patient ? patient.name : `Patient #${a.patient_id}`;
      const statusClass = `status-${(a.status || "scheduled").toLowerCase()}`;

      tr.innerHTML = `
        <td>#${a.id}</td>
        <td><strong>${escapeHtml(docName)}</strong></td>
        <td>${escapeHtml(patName)}</td>
        <td>${escapeHtml(a.appointment_date)} at ${escapeHtml(a.appointment_time)}</td>
        <td><span class="status-badge ${statusClass}">${escapeHtml(a.status)}</span></td>
        <td>
          ${
            a.status === "scheduled"
              ? `<button class="btn btn-outline btn-sm" onclick="cancelAppointment(${a.id})">Cancel</button>
                 <button class="btn btn-danger btn-sm" onclick="deleteAppointment(${a.id})">Delete</button>`
              : `<button class="btn btn-danger btn-sm" onclick="deleteAppointment(${a.id})">Delete</button>`
          }
        </td>
      `;
      appointmentsTableBody.appendChild(tr);
    });
  } catch (err) {
    appointmentsTableBody.innerHTML = `<tr><td colspan="6" class="empty-state">Error: ${err.message}</td></tr>`;
  }
}

async function cancelAppointment(id) {
  if (!confirm(`Cancel appointment #${id}?`)) return;
  try {
    const res = await apiFetch(`/appointments/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ status: "cancelled" }),
    });
    if (res.ok) {
      showToast(`Appointment #${id} cancelled.`, "info");
      await loadAppointments();
    } else {
      const err = await res.json().catch(() => ({}));
      showToast(err.detail || "Failed to cancel", "error");
    }
  } catch (err) {
    showToast(err.message, "error");
  }
}
window.cancelAppointment = cancelAppointment;

async function deleteRecord(endpoint, label, refresh) {
  if (!confirm(`Delete ${label}? This action cannot be undone.`)) return;
  try {
    const res = await apiFetch(endpoint, { method: "DELETE" });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      showToast(err.detail || `Failed to delete ${label.toLowerCase()}.`, "error");
      return;
    }
    showToast(`${label} deleted successfully.`, "success");
    await refresh();
  } catch (err) {
    showToast(`Delete failed: ${err.message}`, "error");
  }
}

function deleteAppointment(id) {
  return deleteRecord(`/appointments/${id}`, `Appointment #${id}`, loadAppointments);
}
window.deleteAppointment = deleteAppointment;

// ==========================================
// Directory: Departments & Doctors
// ==========================================
const departmentsGrid = document.getElementById("departmentsGrid");
const doctorsGrid = document.getElementById("doctorsGrid");
const directoryAdminTools = document.getElementById("directoryAdminTools");
const departmentForm = document.getElementById("departmentForm");
const departmentFormTitle = document.getElementById("departmentFormTitle");
const departmentNameInput = document.getElementById("departmentNameInput");
const departmentDescriptionInput = document.getElementById("departmentDescriptionInput");
const departmentActiveInput = document.getElementById("departmentActiveInput");
const departmentSubmitBtn = document.getElementById("departmentSubmitBtn");
const departmentCancelBtn = document.getElementById("departmentCancelBtn");
const doctorForm = document.getElementById("doctorForm");
const doctorFormTitle = document.getElementById("doctorFormTitle");
const doctorNameInput = document.getElementById("doctorNameInput");
const doctorSpecializationInput = document.getElementById("doctorSpecializationInput");
const doctorDepartmentInput = document.getElementById("doctorDepartmentInput");
const doctorLicenseInput = document.getElementById("doctorLicenseInput");
const doctorEmailInput = document.getElementById("doctorEmailInput");
const doctorPhoneInput = document.getElementById("doctorPhoneInput");
const doctorActiveInput = document.getElementById("doctorActiveInput");
const doctorSubmitBtn = document.getElementById("doctorSubmitBtn");
const doctorCancelBtn = document.getElementById("doctorCancelBtn");
let editingDepartmentId = null;
let editingDoctorId = null;

function resetDepartmentForm() {
  editingDepartmentId = null;
  departmentForm.reset();
  departmentActiveInput.checked = true;
  departmentFormTitle.textContent = "Add Department";
  departmentSubmitBtn.textContent = "Add Department";
  departmentCancelBtn.style.display = "none";
}

function editDepartment(department) {
  editingDepartmentId = department.id;
  departmentNameInput.value = department.name;
  departmentDescriptionInput.value = department.description || "";
  departmentActiveInput.checked = department.is_active !== false;
  departmentFormTitle.textContent = `Edit Department #${department.id}`;
  departmentSubmitBtn.textContent = "Save Department";
  departmentCancelBtn.style.display = "inline-flex";
  departmentNameInput.focus();
}

function resetDoctorForm() {
  editingDoctorId = null;
  doctorForm.reset();
  doctorActiveInput.checked = true;
  doctorFormTitle.textContent = "Add Doctor";
  doctorSubmitBtn.textContent = "Add Doctor";
  doctorCancelBtn.style.display = "none";
}

function editDoctor(doctor) {
  editingDoctorId = doctor.id;
  doctorNameInput.value = doctor.name || doctor.full_name || "";
  doctorSpecializationInput.value = doctor.specialization || "";
  doctorDepartmentInput.value = String(doctor.department_id);
  doctorLicenseInput.value = doctor.license_number || "";
  doctorEmailInput.value = doctor.email || "";
  doctorPhoneInput.value = doctor.phone || "";
  doctorActiveInput.checked = doctor.is_active !== false;
  doctorFormTitle.textContent = `Edit Doctor #${doctor.id}`;
  doctorSubmitBtn.textContent = "Save Doctor";
  doctorCancelBtn.style.display = "inline-flex";
  doctorNameInput.focus();
}

async function loadDepartmentOptions() {
  const res = await apiFetch("/departments");
  if (!res.ok) throw new Error("Unable to load departments");
  const departments = await res.json();
  doctorDepartmentInput.innerHTML = departments.length
    ? departments.map(department => `<option value="${department.id}">${escapeHtml(department.name)}</option>`).join("")
    : '<option value="">Add a department first</option>';
  doctorDepartmentInput.disabled = departments.length === 0;
}

async function submitDepartment(event) {
  event.preventDefault();
  const endpoint = editingDepartmentId ? `/departments/${editingDepartmentId}` : "/departments";
  const method = editingDepartmentId ? "PUT" : "POST";
  try {
    const res = await apiFetch(endpoint, {
      method,
      body: JSON.stringify({
        name: departmentNameInput.value.trim(),
        description: departmentDescriptionInput.value.trim() || null,
        is_active: departmentActiveInput.checked,
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Unable to save department");
    }
    showToast(editingDepartmentId ? "Department updated." : "Department added.", "success");
    resetDepartmentForm();
    await loadDepartments();
    await loadDepartmentOptions();
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function submitDoctor(event) {
  event.preventDefault();
  const endpoint = editingDoctorId ? `/doctors/${editingDoctorId}` : "/doctors";
  const method = editingDoctorId ? "PUT" : "POST";
  try {
    const res = await apiFetch(endpoint, {
      method,
      body: JSON.stringify({
        name: doctorNameInput.value.trim(),
        specialization: doctorSpecializationInput.value.trim(),
        department_id: Number(doctorDepartmentInput.value),
        license_number: doctorLicenseInput.value.trim() || null,
        email: doctorEmailInput.value.trim() || null,
        phone: doctorPhoneInput.value.trim() || null,
        is_active: doctorActiveInput.checked,
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Unable to save doctor");
    }
    showToast(editingDoctorId ? "Doctor updated." : "Doctor added.", "success");
    resetDoctorForm();
    await loadDoctors();
  } catch (err) {
    showToast(err.message, "error");
  }
}

departmentForm.addEventListener("submit", submitDepartment);
departmentCancelBtn.addEventListener("click", resetDepartmentForm);
doctorForm.addEventListener("submit", submitDoctor);
doctorCancelBtn.addEventListener("click", resetDoctorForm);

async function loadDepartments() {
  departmentsGrid.innerHTML = '<div class="empty-state">Loading departments...</div>';
  try {
    const res = await apiFetch("/departments");
    if (!res.ok) {
      departmentsGrid.innerHTML = '<div class="empty-state">Sign in to view departments directory.</div>';
      return;
    }
    const depts = await res.json();
    if (depts.length === 0) {
      departmentsGrid.innerHTML = '<div class="empty-state">No departments recorded.</div>';
      return;
    }
    departmentsGrid.innerHTML = "";
    depts.forEach(d => {
      const card = document.createElement("div");
      card.className = "entity-card";
      card.innerHTML = `
        <h4>${escapeHtml(d.name)}</h4>
        <div style="font-size:0.75rem; color:${d.is_active ? 'var(--success)' : 'var(--emergency-red)'}; margin-bottom:0.4rem;">
          ${d.is_active ? "● Active Department" : "○ Inactive"}
        </div>
        <p>${escapeHtml(d.description || "PulsePoint specialized clinical department.")}</p>
        ${isAdminOrStaff() ? `<div style="display:flex; gap:0.5rem;"><button class="btn btn-outline btn-sm" type="button" data-edit-department="${d.id}">Edit</button><button class="btn btn-danger btn-sm" type="button" onclick="deleteDepartment(${d.id})">Delete</button></div>` : ""}
      `;
      const editButton = card.querySelector("[data-edit-department]");
      if (editButton) editButton.addEventListener("click", () => editDepartment(d));
      departmentsGrid.appendChild(card);
    });
  } catch (err) {
    departmentsGrid.innerHTML = `<div class="empty-state">Error: ${err.message}</div>`;
  }
}

function deleteDepartment(id) {
  return deleteRecord(`/departments/${id}`, `Department #${id}`, loadDepartments);
}
window.deleteDepartment = deleteDepartment;

async function loadDoctors() {
  doctorsGrid.innerHTML = '<div class="empty-state">Loading doctors...</div>';
  try {
    const res = await apiFetch("/doctors");
    if (!res.ok) {
      doctorsGrid.innerHTML = '<div class="empty-state">Sign in to view doctors directory.</div>';
      return;
    }
    const docs = await res.json();
    if (docs.length === 0) {
      doctorsGrid.innerHTML = '<div class="empty-state">No clinicians recorded.</div>';
      return;
    }
    doctorsGrid.innerHTML = "";
    docs.forEach(doc => {
      const card = document.createElement("div");
      card.className = "entity-card";
      const deptName = doc.department ? doc.department.name : `Dept #${doc.department_id}`;
      const displayName = doc.name && /^dr\.\s/i.test(doc.name) ? doc.name : `Dr. ${doc.name}`;
      card.innerHTML = `
        <h4>${escapeHtml(displayName)}</h4>
        <p>Specialty: <strong>${escapeHtml(doc.specialization || "General Practitioner")}</strong></p>
        <p>🏥 <strong>${escapeHtml(deptName)}</strong></p>
        <p>📧 ${escapeHtml(doc.email || "N/A")} | 📞 ${escapeHtml(doc.phone || "N/A")}</p>
        ${isAdminOrStaff() ? `<div style="display:flex; gap:0.5rem;"><button class="btn btn-outline btn-sm" type="button" data-edit-doctor="${doc.id}">Edit</button><button class="btn btn-danger btn-sm" type="button" onclick="deleteDoctor(${doc.id})">Delete</button></div>` : ""}
      `;
      const editButton = card.querySelector("[data-edit-doctor]");
      if (editButton) editButton.addEventListener("click", () => editDoctor(doc));
      doctorsGrid.appendChild(card);
    });
  } catch (err) {
    doctorsGrid.innerHTML = `<div class="empty-state">Error: ${err.message}</div>`;
  }
}

function deleteDoctor(id) {
  return deleteRecord(`/doctors/${id}`, `Doctor #${id}`, loadDoctors);
}
window.deleteDoctor = deleteDoctor;

// ==========================================
// Patients Directory (Admin/Staff Only)
// ==========================================
const patientsTableBody = document.getElementById("patientsTableBody");
const addPatientForm = document.getElementById("addPatientForm");
const refreshPatientsBtn = document.getElementById("refreshPatientsBtn");

async function loadPatients() {
  if (!isAdminOrStaff()) return;
  patientsTableBody.innerHTML = '<tr><td colspan="7" class="empty-state">Loading patients...</td></tr>';
  try {
    const res = await apiFetch("/patients");
    if (!res.ok) {
      patientsTableBody.innerHTML = '<tr><td colspan="7" class="empty-state">Sign in as Staff or Admin to access patient records.</td></tr>';
      return;
    }
    const patients = await res.json();
    if (patients.length === 0) {
      patientsTableBody.innerHTML = '<tr><td colspan="7" class="empty-state">No patient records found.</td></tr>';
      return;
    }
    patientsTableBody.innerHTML = "";
    patients.forEach(p => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>#${p.id}</td>
        <td><strong>${escapeHtml(p.name)}</strong></td>
        <td>${escapeHtml(p.gender || "N/A")}</td>
        <td>${escapeHtml(p.date_of_birth || "N/A")}</td>
        <td>${escapeHtml(p.phone || "N/A")}</td>
        <td>${escapeHtml(p.email || "N/A")}</td>
        <td><button class="btn btn-danger btn-sm" type="button" onclick="deletePatient(${p.id})">Delete</button></td>
      `;
      patientsTableBody.appendChild(tr);
    });
  } catch (err) {
    patientsTableBody.innerHTML = `<tr><td colspan="7" class="empty-state">Error: ${err.message}</td></tr>`;
  }
}

function deletePatient(id) {
  return deleteRecord(`/patients/${id}`, `Patient #${id}`, loadPatients);
}
window.deletePatient = deletePatient;

// ==========================================
// Knowledge Base & Ingestion (Admin/Staff Only)
// ==========================================
const knowledgeDocsTableBody = document.getElementById("knowledgeDocsTableBody");
const uploadKnowledgeForm = document.getElementById("uploadKnowledgeForm");
const docFileInput = document.getElementById("docFileInput");
const docTitleInput = document.getElementById("docTitleInput");
const uploadDocSubmitBtn = document.getElementById("uploadDocSubmitBtn");
const refreshDocsBtn = document.getElementById("refreshDocsBtn");

async function loadKnowledgeDocs() {
  if (!isAdminOrStaff()) return;
  knowledgeDocsTableBody.innerHTML = '<tr><td colspan="6" class="empty-state">Loading knowledge documents...</td></tr>';
  try {
    const res = await apiFetch("/documents");
    if (!res.ok) {
      knowledgeDocsTableBody.innerHTML = '<tr><td colspan="6" class="empty-state">Sign in to view indexed documents.</td></tr>';
      return;
    }
    const docs = await res.json();
    if (docs.length === 0) {
      knowledgeDocsTableBody.innerHTML = '<tr><td colspan="6" class="empty-state">No knowledge documents uploaded yet.</td></tr>';
      return;
    }
    knowledgeDocsTableBody.innerHTML = "";
    docs.forEach(d => {
      const tr = document.createElement("tr");
      const indexedDate = d.indexed_at ? new Date(d.indexed_at).toLocaleString() : "Pending";
      tr.innerHTML = `
        <td>#${d.id}</td>
        <td><strong>${escapeHtml(d.title || d.filename)}</strong></td>
        <td><code>${escapeHtml(d.file_type)}</code></td>
        <td><span class="status-badge status-completed">${escapeHtml(d.status || "indexed")}</span></td>
        <td>${indexedDate}</td>
        <td><button class="btn btn-danger btn-sm" type="button" onclick="deleteDocument(${d.id})">Delete</button></td>
      `;
      knowledgeDocsTableBody.appendChild(tr);
    });
  } catch (err) {
    knowledgeDocsTableBody.innerHTML = `<tr><td colspan="6" class="empty-state">Error: ${err.message}</td></tr>`;
  }
}

function deleteDocument(id) {
  return deleteRecord(`/documents/${id}`, `Document #${id}`, loadKnowledgeDocs);
}
window.deleteDocument = deleteDocument;

// ==========================================
// Initialization & Event Binding
// ==========================================
document.addEventListener("DOMContentLoaded", () => {
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  const apptDate = document.getElementById("apptDate");
  if (apptDate) apptDate.value = tomorrow.toISOString().split("T")[0];
  const apptTime = document.getElementById("apptTime");
  if (apptTime) apptTime.value = "10:00";

  updateAuthDisplay();
  if (currentUser && (currentUser.role === "patient" || currentUser.role === "user")) {
    resolvePatientSelfRecord();
  }

  // Sidebar navigation click
  navItems.forEach(item => {
    item.addEventListener("click", () => switchView(item.dataset.view));
  });

  // Modal controls
  loginModalBtn.addEventListener("click", openModal);
  closeAuthModalBtn.addEventListener("click", closeModal);
  logoutBtn.addEventListener("click", logout);
  authModal.addEventListener("click", e => {
    if (e.target === authModal) closeModal();
  });

  // Demo Login Buttons
  demoLoginAdminBtn.addEventListener("click", async () => {
    demoLoginAdminBtn.disabled = true;
    demoLoginAdminBtn.textContent = "Signing In...";

    try {
      const candidates = [
        { email: "admin@admin.com", pass: "Admin123" },
        { email: "admin@pulsepoint.health", pass: "Admin123" },
        { email: "admin@hospital.com", pass: "Admin123" },
      ];

      let ok = false;
      for (const cand of candidates) {
        inputEmail.value = cand.email;
        inputPassword.value = cand.pass;
        ok = await performLogin(cand.email, cand.pass, true);
        if (ok) break;
      }

      if (!ok) {
        ok = await performLogin("admin@admin.com", "Admin123");
      }

      if (!ok && !authToken) {
        const demoRes = await demoApiFetch("/auth/login", {
          method: "POST",
          body: JSON.stringify({ email: "admin@pulsepoint.health", password: "Admin123" }),
        });
        const demoData = await demoRes.json();
        authToken = demoData.access_token;
        currentUser = {
          email: demoData.email,
          role: "admin",
          user_id: 1,
        };
        localStorage.setItem("hospital_jwt", authToken);
        localStorage.setItem("hospital_user", JSON.stringify(currentUser));
        updateAuthDisplay();
        closeModal();
        showToast("Signed in as Administrator (Instant Demo Access)", "success");
        refreshActiveView();
      }

      if (authToken && currentUser && (currentUser.role === "admin" || currentUser.role === "staff")) {
        switchView("directory");
      }
    } catch (err) {
      showToast(`Admin login error: ${err.message}`, "error");
    } finally {
      demoLoginAdminBtn.disabled = false;
      demoLoginAdminBtn.textContent = "👑 Admin Role";
    }
  });

  demoLoginPatientBtn.addEventListener("click", async () => {
    demoLoginPatientBtn.disabled = true;
    demoLoginPatientBtn.textContent = "Signing In...";
    try {
      inputEmail.value = "patient@hospital.com";
      inputPassword.value = "patient123";
      let ok = await performLogin("patient@hospital.com", "patient123", true);
      if (!ok) {
        try {
          await fetch(`${API_BASE}/auth/register`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              email: "patient@hospital.com",
              password: "patient123",
              full_name: "Demo Patient",
            }),
          });
          ok = await performLogin("patient@hospital.com", "patient123");
        } catch (err) {
          console.error("Auto registration error:", err);
        }
      }
      if (!ok && !authToken) {
        const demoRes = await demoApiFetch("/auth/login", {
          method: "POST",
          body: JSON.stringify({ email: "patient@hospital.com", password: "patient123" }),
        });
        const demoData = await demoRes.json();
        authToken = demoData.access_token;
        currentUser = {
          email: demoData.email,
          role: "patient",
          user_id: 2,
        };
        localStorage.setItem("hospital_jwt", authToken);
        localStorage.setItem("hospital_user", JSON.stringify(currentUser));
        updateAuthDisplay();
        closeModal();
        showToast("Signed in as Patient (Demo Access)", "success");
        refreshActiveView();
      }
      if (authToken && currentUser) {
        switchView("appointments");
      }
    } finally {
      demoLoginPatientBtn.disabled = false;
      demoLoginPatientBtn.textContent = "👤 Patient Role";
    }
  });

  // Sign In Form Submit
  signInForm.addEventListener("submit", e => {
    e.preventDefault();
    performLogin(inputEmail.value.trim(), inputPassword.value);
  });

  // Chat send
  chatSendBtn.addEventListener("click", () => sendChatQuery());
  chatQuestionInput.addEventListener("keydown", e => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendChatQuery();
    }
  });

  // Prompt Chips
  document.querySelectorAll(".prompt-chip").forEach(chip => {
    chip.addEventListener("click", () => {
      const q = chip.dataset.query;
      chatQuestionInput.value = q;
      sendChatQuery(q);
    });
  });

  // Appointment Form Submit
  bookApptForm.addEventListener("submit", async e => {
    e.preventDefault();
    if (!authToken) {
      showToast("Please sign in to schedule an appointment.", "error");
      openModal();
      return;
    }

    const docId = parseInt(apptDoctor.value, 10);
    let patId = null;

    if (isAdminOrStaff()) {
      patId = parseInt(apptPatient.value, 10);
    } else {
      patId = selfPatientRecord ? selfPatientRecord.id : 1;
    }

    const dVal = apptDate.value;
    const tVal = apptTime.value;
    const notesVal = document.getElementById("apptNotes").value.trim();

    if (!docId || !patId || !dVal || !tVal) {
      showToast("Please fill all required appointment fields.", "error");
      return;
    }

    const formattedTime = tVal.length === 5 ? `${tVal}:00` : tVal;
    const payload = {
      doctor_id: docId,
      patient_id: patId,
      appointment_date: dVal,
      appointment_time: formattedTime,
      notes: notesVal || null,
    };

    try {
      const res = await apiFetch("/appointments", {
        method: "POST",
        body: JSON.stringify(payload),
      });

      if (res.status === 409) {
        const err = await res.json().catch(() => ({}));
        showToast(`Conflict: ${err.detail || "Doctor or patient is already booked for this slot."}`, "error");
        return;
      }

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        showToast(err.detail || "Failed to schedule appointment", "error");
        return;
      }

      showToast("Appointment scheduled successfully!", "success");
      bookApptForm.reset();
      apptDate.value = tomorrow.toISOString().split("T")[0];
      apptTime.value = "10:00";
      await loadAppointments();
    } catch (err) {
      showToast(`Network error: ${err.message}`, "error");
    }
  });

  if (refreshApptsBtn) refreshApptsBtn.addEventListener("click", loadAppointments);

  // Add Patient Form Submit (Admin/Staff Only)
  if (addPatientForm) {
    addPatientForm.addEventListener("submit", async e => {
      e.preventDefault();
      if (!isAdminOrStaff()) {
        showToast("Permission denied: Staff or Admin role required.", "error");
        return;
      }

      const payload = {
        name: document.getElementById("patientName").value.trim(),
        date_of_birth: document.getElementById("patientDob").value,
        gender: document.getElementById("patientGender").value,
        phone: document.getElementById("patientPhone").value.trim() || null,
        email: document.getElementById("patientEmail").value.trim() || null,
      };

      try {
        const res = await apiFetch("/patients", {
          method: "POST",
          body: JSON.stringify(payload),
        });

        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          showToast(err.detail || "Failed to create patient record", "error");
          return;
        }

        showToast("Patient record created successfully!", "success");
        addPatientForm.reset();
        loadPatients();
      } catch (err) {
        showToast(`Error: ${err.message}`, "error");
      }
    });
  }

  if (refreshPatientsBtn) refreshPatientsBtn.addEventListener("click", loadPatients);

  // Upload Knowledge Document Form Submit (Admin/Staff Only)
  if (uploadKnowledgeForm) {
    uploadKnowledgeForm.addEventListener("submit", async e => {
      e.preventDefault();
      if (!isAdminOrStaff()) {
        showToast("Permission denied: Staff or Admin role required.", "error");
        return;
      }

      const file = docFileInput.files[0];
      if (!file) {
        showToast("Please select a file to upload.", "error");
        return;
      }

      const formData = new FormData();
      formData.append("file", file);
      if (docTitleInput.value.trim()) {
        formData.append("title", docTitleInput.value.trim());
      }

      uploadDocSubmitBtn.disabled = true;
      uploadDocSubmitBtn.textContent = "Uploading & Indexing...";

      try {
        const res = await apiFetch("/documents/upload", {
          method: "POST",
          body: formData,
        });

        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          showToast(`Upload failed: ${err.detail || "Permission denied"}`, "error");
          return;
        }

        const data = await res.json();
        showToast(`Document uploaded successfully! Chunks created: ${data.chunk_count || 1}`, "success");
        uploadKnowledgeForm.reset();
        await loadKnowledgeDocs();
      } catch (err) {
        showToast(`Upload error: ${err.message}`, "error");
      } finally {
        uploadDocSubmitBtn.disabled = false;
        uploadDocSubmitBtn.textContent = "Upload & Ingest Chunks";
      }
    });
  }

  if (refreshDocsBtn) refreshDocsBtn.addEventListener("click", loadKnowledgeDocs);
});

function escapeHtml(str) {
  if (typeof str !== "string") return String(str ?? "");
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
