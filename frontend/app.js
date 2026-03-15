const BACKEND_BASE =
  window.location.hostname === "127.0.0.1" || window.location.hostname === "localhost"
    ? "http://127.0.0.1:8000"
    : `http://${window.location.hostname}:8000`;

let pc = null;
let statusTimer = null;
let eventsTimer = null;
let currentSupportsVideo = false;
let webrtcStarted = false;
let webrtcNegotiating = false;

const videoEl = document.getElementById("video");
const videoPlaceholderEl = document.getElementById("videoPlaceholder");
const backendInfoEl = document.getElementById("backendInfo");

backendInfoEl.textContent = `后端地址：${BACKEND_BASE}`;

function setText(id, value) {
  document.getElementById(id).textContent = value ?? "-";
}

function setStateText(id, ok, okText = "正常", badText = "异常") {
  const el = document.getElementById(id);
  el.textContent = ok ? okText : badText;
  el.className = "card-value " + (ok ? "ok" : "bad");
}

function showVideoMessage(message) {
  videoEl.style.display = "none";
  videoPlaceholderEl.style.display = "block";
  videoPlaceholderEl.textContent = message;
}

function showVideoElement() {
  videoPlaceholderEl.style.display = "none";
  videoEl.style.display = "block";
}

async function fetchJson(path, options = {}) {
  const res = await fetch(`${BACKEND_BASE}${path}`, options);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`请求失败 ${res.status}: ${text}`);
  }
  return await res.json();
}

function renderStatus(data) {
  currentSupportsVideo = !!data.supports_video;

  setText("mock", data.mock ? "Mock" : "Real");
  setText("supports_video", data.supports_video ? "支持" : "不支持");
  setText("status", data.status);
  setText("occupied", data.occupied ? "有人" : "无人");
  setText("current_people", data.current_people);
  setText("occupied_duration_sec", data.occupied_duration_sec);
  setText("today_total_occupied_sec", data.today_total_occupied_sec);
  setText("max_people_today", data.max_people_today);

  setStateText("camera_ok", data.camera_ok);
  setStateText("detector_ok", data.detector_ok);
  setStateText("running", data.running, "运行中", "已停止");

  setText("last_frame_time", data.last_frame_time || "-");
  setText("last_error", data.last_error || "无");

  if (!data.supports_video) {
    showVideoMessage("当前模式不提供视频流（通常为 Mock 模式）");
  }
}

function renderEvents(events) {
  const list = document.getElementById("eventsList");
  list.innerHTML = "";

  if (!events || events.length === 0) {
    list.innerHTML = '<div class="muted">暂无事件</div>';
    return;
  }

  const reversed = [...events].reverse();
  reversed.forEach(item => {
    const div = document.createElement("div");
    div.className = "list-item";
    div.innerHTML = `
      <div><strong>时间：</strong>${item.timestamp}</div>
      <div><strong>事件：</strong>${item.event}</div>
      <div><strong>人数：</strong>${item.people_count}</div>
    `;
    list.appendChild(div);
  });
}

async function refreshStatus() {
  try {
    const data = await fetchJson("/api/status");
    renderStatus(data);

    if (data.supports_video && !webrtcStarted && !webrtcNegotiating) {
      await startWebRTC();
    }
  } catch (err) {
    console.error("refreshStatus error:", err);
    setText("last_error", err.message);
    showVideoMessage("状态接口访问失败，请检查后端是否启动");
  }
}

async function refreshEvents() {
  try {
    const data = await fetchJson("/api/events?limit=10");
    renderEvents(data.events);
  } catch (err) {
    console.error("refreshEvents error:", err);
  }
}

function cleanupPeerConnection() {
  if (pc) {
    try {
      pc.ontrack = null;
      pc.onconnectionstatechange = null;
      pc.oniceconnectionstatechange = null;
      pc.onsignalingstatechange = null;
      pc.close();
    } catch (e) {
      console.warn("关闭旧 WebRTC 连接失败:", e);
    }
    pc = null;
  }
  webrtcStarted = false;
  webrtcNegotiating = false;
}

async function startWebRTC() {
  if (webrtcStarted) return;
  if (webrtcNegotiating) return;
  if (!currentSupportsVideo) return;

  webrtcNegotiating = true;
  cleanupPeerConnection();
  webrtcNegotiating = true;

  try {
    pc = new RTCPeerConnection({
      iceServers: [{ urls: ["stun:stun.l.google.com:19302"] }]
    });

    pc.ontrack = (event) => {
      console.log("收到远端视频轨道:", event);
      if (event.streams && event.streams[0]) {
        videoEl.srcObject = event.streams[0];
        showVideoElement();
      }
    };

    pc.onconnectionstatechange = () => {
      console.log("WebRTC connectionState:", pc.connectionState);

      if (pc.connectionState === "connected") {
        console.log("WebRTC 视频连接成功");
        webrtcStarted = true;
      }

      if (
        pc.connectionState === "failed" ||
        pc.connectionState === "disconnected" ||
        pc.connectionState === "closed"
      ) {
        showVideoMessage(`视频连接状态异常：${pc.connectionState}`);
        webrtcStarted = false;
      }
    };

    pc.oniceconnectionstatechange = () => {
      console.log("WebRTC iceConnectionState:", pc.iceConnectionState);
    };

    pc.onsignalingstatechange = () => {
      console.log("WebRTC signalingState:", pc.signalingState);
    };

    pc.addTransceiver("video", { direction: "recvonly" });

    const offer = await pc.createOffer();
    await pc.setLocalDescription(offer);

    console.log("本地 offer 已创建");

    const answer = await fetchJson("/api/webrtc-offer", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        sdp: pc.localDescription.sdp,
        type: pc.localDescription.type
      })
    });

    console.log("收到服务端 answer");

    if (pc.signalingState !== "have-local-offer") {
      throw new Error(`当前 signalingState=${pc.signalingState}，不能设置 answer`);
    }

    await pc.setRemoteDescription(answer);
    webrtcStarted = true;
  } catch (err) {
    console.error("startWebRTC error:", err);
    showVideoMessage("视频连接失败：" + err.message);
    cleanupPeerConnection();
  } finally {
    webrtcNegotiating = false;
  }
}

async function init() {
  await refreshStatus();
  await refreshEvents();

  statusTimer = setInterval(refreshStatus, 1000);
  eventsTimer = setInterval(refreshEvents, 2000);
}

document.getElementById("connectBtn").addEventListener("click", async () => {
  await refreshStatus();
  if (currentSupportsVideo && !webrtcStarted && !webrtcNegotiating) {
    await startWebRTC();
  }
});

document.getElementById("refreshBtn").addEventListener("click", async () => {
  await refreshStatus();
  await refreshEvents();
});

window.addEventListener("beforeunload", () => {
  if (statusTimer) clearInterval(statusTimer);
  if (eventsTimer) clearInterval(eventsTimer);
  cleanupPeerConnection();
});

init();