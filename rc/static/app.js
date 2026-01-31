const el = (id) => document.getElementById(id);

let ws = null;
let lastPidFromServer = null;

const canvas = el("map");
const ctx = canvas.getContext("2d");

function fmt(x) {
  if (x === null || x === undefined) return "-";
  if (Number.isNaN(x)) return "-";
  return (Math.round(x * 1000) / 1000).toString();
}

function setBadgeArmed(armed) {
  el("armedState").textContent = armed ? "ARMED" : "DISARMED";
  el("armedState").className = armed ? "badge armed" : "badge";
  el("armBtn").textContent = armed ? "DISARM" : "ARM";
}

function send(obj) {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify(obj));
  }
}

function syncPidSliders(pid) {
  const key = `${pid.kp}|${pid.ki}|${pid.kd}`;
  if (lastPidFromServer === key) return;
  lastPidFromServer = key;

  el("kp").value = pid.kp;
  el("ki").value = pid.ki;
  el("kd").value = pid.kd;

  el("kpVal").textContent = Number(pid.kp).toFixed(2);
  el("kiVal").textContent = Number(pid.ki).toFixed(3);
  el("kdVal").textContent = Number(pid.kd).toFixed(2);
}

function draw(data) {
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  const scale = 120; // px per meter
  const cx = canvas.width / 2;
  const cy = canvas.height / 2;

  // axes
  ctx.beginPath();
  ctx.moveTo(0, cy); ctx.lineTo(canvas.width, cy);
  ctx.moveTo(cx, 0); ctx.lineTo(cx, canvas.height);
  ctx.stroke();

  // car
  ctx.beginPath();
  ctx.moveTo(cx + 15, cy);
  ctx.lineTo(cx - 10, cy - 8);
  ctx.lineTo(cx - 10, cy + 8);
  ctx.closePath();
  ctx.stroke();

  const trail = data.trail_xy || [];
  for (const scan of trail) {
    if (!scan) continue;
    ctx.beginPath();
    for (const p of scan) {
      const x = p[0], y = p[1];
      const px = cx + x * scale;
      const py = cy - y * scale;
      ctx.rect(px, py, 1, 1);
    }
    ctx.stroke();
  }

  const scan = data.scan_xy || [];
  ctx.beginPath();
  for (const p of scan) {
    const x = p[0], y = p[1];
    const px = cx + x * scale;
    const py = cy - y * scale;
    ctx.rect(px, py, 2, 2);
  }
  ctx.stroke();
}

function updateUI(data) {
  el("control_hz").textContent = fmt(data.control_hz);
  el("sensor_hz").textContent = fmt(data.sensor_hz);
  el("last_error").textContent = data.last_error || "-";

  setBadgeArmed(!!data.armed);

  if (data.pid) syncPidSliders(data.pid);

  el("d_left").textContent = fmt(data.d_left);
  el("d_right").textContent = fmt(data.d_right);
  el("min_front").textContent = fmt(data.min_front);
  el("curvature").textContent = fmt(data.curvature);

  el("steer").textContent = fmt(data.steer);
  el("throttle").textContent = fmt(data.throttle);
  el("steering_us").textContent = data.steering_us ?? "-";
  el("esc_us").textContent = data.esc_us ?? "-";

  el("yaw_rate").textContent = fmt(data.yaw_rate);

  draw(data);
}

function setupControls() {
  const onSlider = () => {
    el("kpVal").textContent = Number(el("kp").value).toFixed(2);
    el("kiVal").textContent = Number(el("ki").value).toFixed(3);
    el("kdVal").textContent = Number(el("kd").value).toFixed(2);
  };

  el("kp").addEventListener("input", onSlider);
  el("ki").addEventListener("input", onSlider);
  el("kd").addEventListener("input", onSlider);

  el("armBtn").addEventListener("click", () => {
    const armedNow = (el("armedState").textContent === "ARMED");
    send({ cmd: "arm", value: !armedNow });
  });

  el("applyPidBtn").addEventListener("click", () => {
    send({
      cmd: "pid",
      kp: Number(el("kp").value),
      ki: Number(el("ki").value),
      kd: Number(el("kd").value),
    });
  });

  el("saveBtn").addEventListener("click", () => {
    send({ cmd: "save" });
  });
}

function connect() {
  const proto = (location.protocol === "https:") ? "wss" : "ws";
  ws = new WebSocket(`${proto}://${location.host}/ws`);
  el("status").textContent = "connecting...";

  ws.onopen = () => el("status").textContent = "connected";
  ws.onclose = () => {
    el("status").textContent = "disconnected, retrying...";
    setTimeout(connect, 1000);
  };
  ws.onerror = () => ws.close();

  ws.onmessage = (ev) => {
    try {
      updateUI(JSON.parse(ev.data));
    } catch (e) {}
  };
}

setupControls();
connect();
