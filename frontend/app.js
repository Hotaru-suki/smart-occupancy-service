const BACKEND_BASE =
  window.location.port === "8000"
    ? window.location.origin
    : `http://${window.location.hostname}:8000`;
const WS_BASE = BACKEND_BASE.replace(/^http/, "ws");

const authState = {
  mode: "login",
  registerRole: "viewer",
  authenticated: false,
  toastTimer: null,
  realtimeSocket: null,
  reconnectTimer: null,
  peerConnection: null,
  supportsVideo: false,
  webrtcStarted: false,
  webrtcNegotiating: false
};

const ui = {
  toast: document.getElementById("toast"),
  authStage: document.getElementById("authStage"),
  authEyebrow: document.getElementById("authEyebrow"),
  authTitle: document.getElementById("authTitle"),
  backendInfo: document.getElementById("backendInfo"),
  loginForm: document.getElementById("loginForm"),
  registerForm: document.getElementById("registerForm"),
  openRegisterButton: document.getElementById("openRegisterButton"),
  backToLoginButton: document.getElementById("backToLoginButton"),
  viewerRoleButton: document.getElementById("viewerRoleButton"),
  adminRoleButton: document.getElementById("adminRoleButton"),
  adminRegistrationCodeGroup: document.getElementById("adminRegistrationCodeGroup"),
  loginUsername: document.getElementById("loginUsername"),
  loginPassword: document.getElementById("loginPassword"),
  registerUsername: document.getElementById("registerUsername"),
  registerPassword: document.getElementById("registerPassword"),
  adminRegistrationCode: document.getElementById("adminRegistrationCode"),
  dashboard: document.getElementById("dashboard"),
  sessionInfo: document.getElementById("sessionInfo"),
  sessionRole: document.getElementById("sessionRole"),
  realtimeState: document.getElementById("realtimeState"),
  accessScope: document.getElementById("accessScope"),
  connectButton: document.getElementById("connectButton"),
  logoutButton: document.getElementById("logoutButton"),
  video: document.getElementById("video"),
  videoPlaceholder: document.getElementById("videoPlaceholder"),
  eventsPanel: document.getElementById("eventsPanel"),
  eventsList: document.getElementById("eventsList"),
  adminPanel: document.getElementById("adminPanel"),
  cleanupTestUsersButton: document.getElementById("cleanupTestUsersButton"),
  passwordForm: document.getElementById("passwordForm"),
  currentPassword: document.getElementById("currentPassword"),
  newPassword: document.getElementById("newPassword"),
  roiForm: document.getElementById("roiForm"),
  roiX1: document.getElementById("roiX1"),
  roiY1: document.getElementById("roiY1"),
  roiX2: document.getElementById("roiX2"),
  roiY2: document.getElementById("roiY2"),
  userList: document.getElementById("userList")
};

const statusFieldIds = [
  "mock",
  "supports_video",
  "status",
  "occupied",
  "current_people",
  "occupied_duration_sec",
  "today_total_occupied_sec",
  "max_people_today",
  "camera_ok",
  "detector_ok",
  "running",
  "last_frame_time",
  "last_error"
];

ui.backendInfo.textContent = `后端地址：${BACKEND_BASE}`;
if (window.location.search.includes("debug=1")) {
  ui.backendInfo.hidden = false;
}

function setText(id, value) {
  const node = document.getElementById(id);
  node.textContent = value ?? "-";
}

function setStateText(id, ok, okText = "正常", badText = "异常") {
  const node = document.getElementById(id);
  node.textContent = ok ? okText : badText;
  node.className = `status-card__value ${ok ? "ok" : "bad"}`;
}

function resetStatusBoard() {
  statusFieldIds.forEach((id) => setText(id, "-"));
}

function updateRealtimeState(text) {
  ui.realtimeState.textContent = text;
}

function showToast(message, tone = "ok", autoHide = true) {
  ui.toast.hidden = false;
  ui.toast.textContent = message;
  ui.toast.className = `toast ${tone}`;

  if (authState.toastTimer) {
    clearTimeout(authState.toastTimer);
    authState.toastTimer = null;
  }

  if (autoHide) {
    authState.toastTimer = window.setTimeout(() => {
      ui.toast.hidden = true;
      authState.toastTimer = null;
    }, 1800);
  }
}

function parseErrorMessage(statusCode, text) {
  try {
    const payload = JSON.parse(text);
    if (payload.retry_after_sec) {
      return `登录失败，请在 ${payload.retry_after_sec} 秒后重试`;
    }
    if (typeof payload.remaining_attempts === "number" && payload.remaining_attempts >= 0) {
      return `登录失败，还可尝试 ${payload.remaining_attempts} 次`;
    }
    if (payload.detail) {
      return payload.detail;
    }
  } catch (error) {
    return `请求失败 ${statusCode}: ${text}`;
  }
  return `请求失败 ${statusCode}: ${text}`;
}

async function requestJson(path, options = {}) {
  const response = await fetch(`${BACKEND_BASE}${path}`, {
    credentials: "include",
    ...options
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(parseErrorMessage(response.status, text));
  }

  return response.json();
}

function setAuthMode(mode) {
  authState.mode = mode;
  const isLogin = mode === "login";
  ui.authEyebrow.textContent = isLogin ? "账号登录" : "账号注册";
  ui.authTitle.textContent = isLogin ? "登录系统" : "创建账号";
  ui.loginForm.hidden = !isLogin;
  ui.registerForm.hidden = isLogin;
  syncRegisterRole();
}

function setRegisterRole(role) {
  authState.registerRole = role;
  syncRegisterRole();
}

function syncRegisterRole() {
  const isAdmin = authState.registerRole === "admin";
  ui.viewerRoleButton.classList.toggle("is-active", !isAdmin);
  ui.adminRoleButton.classList.toggle("is-active", isAdmin);
  ui.adminRegistrationCodeGroup.hidden = !(authState.mode === "register" && isAdmin);
}

function hideDashboard() {
  authState.authenticated = false;
  ui.authStage.hidden = false;
  ui.dashboard.hidden = true;
  ui.eventsPanel.hidden = true;
  ui.adminPanel.hidden = true;
  ui.sessionInfo.textContent = "未登录";
  ui.sessionRole.textContent = "-";
  ui.accessScope.textContent = "-";
  updateRealtimeState("未连接");
  resetStatusBoard();
  resetRealtimeConnection();
  resetVideoConnection();
  renderEvents([]);
  renderUsers([]);
  showVideoPlaceholder("等待视频接入");
}

function showDashboard(session) {
  authState.authenticated = true;
  ui.authStage.hidden = true;
  ui.dashboard.hidden = false;
  ui.dashboard.classList.remove("is-entering");
  void ui.dashboard.offsetWidth;
  ui.dashboard.classList.add("is-entering");
  ui.sessionInfo.textContent = `${session.username} 已登录`;
  ui.sessionRole.textContent = session.role === "admin" ? "管理员" : "普通用户";
  ui.accessScope.textContent = session.role === "admin" ? "读写" : "只读";
  updateRealtimeState("连接中");
  ui.eventsPanel.hidden = session.role !== "admin";
  ui.adminPanel.hidden = session.role !== "admin";
}

function showVideoPlaceholder(message) {
  ui.video.style.display = "none";
  ui.videoPlaceholder.style.display = "block";
  ui.videoPlaceholder.textContent = message;
}

function showVideoElement() {
  ui.videoPlaceholder.style.display = "none";
  ui.video.style.display = "block";
}

function renderStatus(status) {
  authState.supportsVideo = Boolean(status.supports_video);
  setText("mock", status.mock ? "Mock" : "Real");
  setText("supports_video", status.supports_video ? "支持" : "不支持");
  setText("status", status.status);
  setText("occupied", status.occupied ? "有人" : "无人");
  setText("current_people", status.current_people);
  setText("occupied_duration_sec", status.occupied_duration_sec);
  setText("today_total_occupied_sec", status.today_total_occupied_sec);
  setText("max_people_today", status.max_people_today);
  setText("last_frame_time", status.last_frame_time || "-");
  setText("last_error", status.last_error || "无");
  setStateText("camera_ok", status.camera_ok);
  setStateText("detector_ok", status.detector_ok);
  setStateText("running", status.running, "运行中", "已停止");
  fillROIForm(status.roi);

  if (!status.supports_video) {
    showVideoPlaceholder("当前模式不提供视频流");
  }
}

function renderEvents(events) {
  if (ui.eventsPanel.hidden) {
    return;
  }

  ui.eventsList.innerHTML = "";
  if (!events || events.length === 0) {
    ui.eventsList.innerHTML = '<div class="empty-text">暂无事件</div>';
    return;
  }

  events.slice().reverse().forEach((eventItem) => {
    const item = document.createElement("div");
    item.className = "list-item";
    item.innerHTML = `
      <div><strong>时间：</strong>${eventItem.timestamp}</div>
      <div><strong>事件：</strong>${eventItem.event}</div>
      <div><strong>人数：</strong>${eventItem.people_count}</div>
    `;
    ui.eventsList.appendChild(item);
  });
}

function renderUsers(users) {
  if (ui.adminPanel.hidden) {
    return;
  }

  ui.userList.innerHTML = "";
  if (!users || users.length === 0) {
    ui.userList.innerHTML = '<div class="empty-text">暂无用户数据</div>';
    return;
  }

  users.forEach((user) => {
    const item = document.createElement("div");
    item.className = "user-row";
    item.innerHTML = `
      <span>${user.username}</span>
      <select class="role-select" data-username="${user.username}">
        <option value="viewer"${user.role === "viewer" ? " selected" : ""}>viewer</option>
        <option value="admin"${user.role === "admin" ? " selected" : ""}>admin</option>
      </select>
      <button class="inline-button" type="button" data-save-role="${user.username}">保存</button>
      <button class="danger-button" type="button" data-delete-user="${user.username}">删除</button>
    `;
    ui.userList.appendChild(item);
  });
}

function fillROIForm(roi) {
  if (!roi || ui.adminPanel.hidden) {
    return;
  }

  ui.roiX1.value = roi.x1;
  ui.roiY1.value = roi.y1;
  ui.roiX2.value = roi.x2;
  ui.roiY2.value = roi.y2;
}

async function loadAdminData() {
  if (ui.adminPanel.hidden) {
    return;
  }

  const [users, region] = await Promise.all([
    requestJson("/api/admin/users"),
    requestJson("/api/admin/regions/default")
  ]);

  renderUsers(users.items);
  fillROIForm(region.roi);
}

async function hydrateDashboard(session) {
  const tasks = [requestJson("/api/status").then((status) => renderStatus(status))];

  if (session.role === "admin") {
    tasks.push(
      requestJson("/api/events?limit=10").then((payload) => renderEvents(payload.events)),
      loadAdminData(),
    );
  }

  await Promise.all(tasks);
}

function resetRealtimeConnection() {
  if (authState.reconnectTimer) {
    clearTimeout(authState.reconnectTimer);
    authState.reconnectTimer = null;
  }

  if (!authState.realtimeSocket) {
    return;
  }

  authState.realtimeSocket.onopen = null;
  authState.realtimeSocket.onmessage = null;
  authState.realtimeSocket.onerror = null;
  authState.realtimeSocket.onclose = null;
  authState.realtimeSocket.close();
  authState.realtimeSocket = null;
}

function scheduleRealtimeReconnect() {
  if (authState.reconnectTimer || !authState.authenticated) {
    return;
  }

  authState.reconnectTimer = window.setTimeout(() => {
    authState.reconnectTimer = null;
    connectRealtime();
  }, 1600);
}

function connectRealtime() {
  if (!authState.authenticated || authState.realtimeSocket) {
    return;
  }

  updateRealtimeState("连接中");
  const socket = new WebSocket(`${WS_BASE}/api/realtime`);
  authState.realtimeSocket = socket;

  socket.onopen = () => {
    updateRealtimeState("已连接");
  };

  socket.onmessage = (event) => {
    const payload = JSON.parse(event.data);
    if (payload.type === "status") {
      renderStatus(payload.data);
      if (payload.data.supports_video && !authState.webrtcStarted && !authState.webrtcNegotiating) {
        startVideoConnection().catch(() => {});
      }
      return;
    }

    if (payload.type === "events") {
      renderEvents(payload.data.events);
    }
  };

  socket.onerror = () => {
    updateRealtimeState("连接异常");
  };

  socket.onclose = (event) => {
    authState.realtimeSocket = null;
    if (event.code === 4401) {
      hideDashboard();
      showToast("登录态已失效，请重新登录", "bad", false);
      return;
    }
    updateRealtimeState("重连中");
    scheduleRealtimeReconnect();
  };
}

function resetVideoConnection() {
  if (!authState.peerConnection) {
    authState.webrtcStarted = false;
    authState.webrtcNegotiating = false;
    return;
  }

  try {
    authState.peerConnection.close();
  } catch (error) {
    console.warn("关闭 WebRTC 连接失败:", error);
  }

  authState.peerConnection = null;
  authState.webrtcStarted = false;
  authState.webrtcNegotiating = false;
}

async function startVideoConnection() {
  if (authState.webrtcStarted || authState.webrtcNegotiating || !authState.supportsVideo) {
    return;
  }

  authState.webrtcNegotiating = true;
  resetVideoConnection();
  authState.webrtcNegotiating = true;

  try {
    const peerConnection = new RTCPeerConnection({
      iceServers: [{ urls: ["stun:stun.l.google.com:19302"] }]
    });
    authState.peerConnection = peerConnection;

    peerConnection.ontrack = (event) => {
      if (event.streams && event.streams[0]) {
        ui.video.srcObject = event.streams[0];
        showVideoElement();
      }
    };

    peerConnection.onconnectionstatechange = () => {
      if (peerConnection.connectionState === "connected") {
        authState.webrtcStarted = true;
      }

      if (["failed", "disconnected", "closed"].includes(peerConnection.connectionState)) {
        authState.webrtcStarted = false;
        showVideoPlaceholder(`视频连接状态异常：${peerConnection.connectionState}`);
      }
    };

    peerConnection.addTransceiver("video", { direction: "recvonly" });

    const offer = await peerConnection.createOffer();
    await peerConnection.setLocalDescription(offer);

    const answer = await requestJson("/api/webrtc-offer", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        sdp: peerConnection.localDescription.sdp,
        type: peerConnection.localDescription.type
      })
    });

    await peerConnection.setRemoteDescription(answer);
    authState.webrtcStarted = true;
  } catch (error) {
    showToast(`视频连接失败: ${error.message}`, "bad", false);
    showVideoPlaceholder(`视频连接失败：${error.message}`);
    resetVideoConnection();
  } finally {
    authState.webrtcNegotiating = false;
  }
}

async function submitLogin(username, password) {
  const session = await requestJson("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password })
  });

  showDashboard(session);
  await hydrateDashboard(session);
  connectRealtime();
  showToast("登录成功", "ok", true);
}

async function submitRegister(username, password) {
  const payload = {
    username,
    password,
    role: authState.registerRole
  };

  if (authState.registerRole === "admin") {
    payload.admin_registration_code = ui.adminRegistrationCode.value;
  }

  await requestJson("/api/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  await submitLogin(username, password);
  showToast("注册成功", "ok", true);
}

async function restoreSession() {
  const session = await requestJson("/api/auth/session");
  if (!session.authenticated) {
    return;
  }

  showDashboard(session);
  await hydrateDashboard(session);
  connectRealtime();
}

async function logout() {
  await requestJson("/api/auth/logout", { method: "POST" });
  hideDashboard();
  setAuthMode("login");
  showToast("已退出登录", "ok", true);
}

async function changePassword(currentPassword, newPassword) {
  await requestJson("/api/auth/password", {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      current_password: currentPassword,
      new_password: newPassword
    })
  });
}

ui.openRegisterButton.addEventListener("click", () => setAuthMode("register"));
ui.backToLoginButton.addEventListener("click", () => setAuthMode("login"));
ui.viewerRoleButton.addEventListener("click", () => setRegisterRole("viewer"));
ui.adminRoleButton.addEventListener("click", () => setRegisterRole("admin"));

ui.loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    await submitLogin(ui.loginUsername.value.trim(), ui.loginPassword.value);
    ui.loginForm.reset();
  } catch (error) {
    showToast(`登录失败: ${error.message}`, "bad", false);
  }
});

ui.registerForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    await submitRegister(ui.registerUsername.value.trim(), ui.registerPassword.value);
    ui.registerForm.reset();
    ui.adminRegistrationCode.value = "";
  } catch (error) {
    showToast(`注册失败: ${error.message}`, "bad", false);
  }
});

ui.connectButton.addEventListener("click", async () => {
  await startVideoConnection();
});

ui.logoutButton.addEventListener("click", async () => {
  try {
    await logout();
  } catch (error) {
    showToast(`退出失败: ${error.message}`, "bad", false);
  }
});

ui.passwordForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    await changePassword(ui.currentPassword.value, ui.newPassword.value);
    ui.passwordForm.reset();
    showToast("密码修改成功", "ok", true);
  } catch (error) {
    showToast(`密码修改失败: ${error.message}`, "bad", false);
  }
});

ui.cleanupTestUsersButton.addEventListener("click", async () => {
  if (!window.confirm("确认清理所有 tester_ 前缀测试账号吗？此操作不可撤销。")) {
    return;
  }

  try {
    const result = await requestJson("/api/admin/users", {
      method: "DELETE"
    });
    await loadAdminData();
    showToast(`已清理 ${result.deleted_count} 个测试账号`, "ok", true);
  } catch (error) {
    showToast(`清理测试账号失败: ${error.message}`, "bad", false);
  }
});

ui.roiForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    await requestJson("/api/admin/regions/default/roi", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        x1: Number(ui.roiX1.value),
        y1: Number(ui.roiY1.value),
        x2: Number(ui.roiX2.value),
        y2: Number(ui.roiY2.value)
      })
    });
    showToast("ROI 更新成功", "ok", true);
  } catch (error) {
    showToast(`ROI 更新失败: ${error.message}`, "bad", false);
  }
});

ui.userList.addEventListener("click", async (event) => {
  const username = event.target.dataset.saveRole;
  const deleteUsername = event.target.dataset.deleteUser;

  if (username) {
    const select = ui.userList.querySelector(`[data-username="${username}"]`);
    try {
      await requestJson(`/api/admin/users/${username}/role`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ role: select.value })
      });
      await loadAdminData();
      showToast(`用户 ${username} 角色已更新`, "ok", true);
    } catch (error) {
      showToast(`角色更新失败: ${error.message}`, "bad", false);
    }
    return;
  }

  if (deleteUsername) {
    if (!window.confirm(`确认删除用户 ${deleteUsername} 吗？此操作不可撤销。`)) {
      return;
    }

    try {
      await requestJson(`/api/admin/users/${deleteUsername}`, {
        method: "DELETE"
      });
      await loadAdminData();
      showToast(`用户 ${deleteUsername} 已删除`, "ok", true);
    } catch (error) {
      showToast(`删除用户失败: ${error.message}`, "bad", false);
    }
  }
});

window.addEventListener("beforeunload", () => {
  if (authState.toastTimer) {
    clearTimeout(authState.toastTimer);
  }
  resetRealtimeConnection();
  resetVideoConnection();
});

(async function init() {
  setAuthMode("login");
  setRegisterRole("viewer");
  hideDashboard();
  try {
    await restoreSession();
  } catch (error) {
    showToast("无法读取登录状态，请确认后端已启动", "bad", false);
  }
})();
