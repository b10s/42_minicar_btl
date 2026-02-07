const el = (id) => document.getElementById(id);

let ws = null;
let lastPidFromServer = null;
let showTrail = true;
let trailHistory = [];
const trailMax = 25;
let lastMsgT = 0;
let wsHzEma = null;

const canvas = el("map");
const ctx = canvas.getContext("2d");
let scale = 120; // px per meter

function fmt(x) {
  if (x === null || x === undefined) return "-";
  if (Number.isNaN(x)) return "-";
  return (Math.round(x * 1000) / 1000).toString();
}

function angleInSector(deg, sector) {
  let [a, b] = sector;
  deg = ((deg % 360) + 360) % 360;
  a = ((a % 360) + 360) % 360;
  b = ((b % 360) + 360) % 360;
  if (a <= b) return deg >= a && deg <= b;
  return deg >= a || deg <= b;
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

  if (showTrail) {
    for (const scan of trailHistory) {
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
  }

  const scan = data.scan_xy || [];
  const leftSector = data.left_sector_deg || null;
  const rightSector = data.right_sector_deg || null;
  const frontSector = data.front_sector_deg || null;
  const leftFiltered = data.left_xy || [];
  const rightFiltered = data.right_xy || [];
  const frontFiltered = data.front_xy || [];

  for (const p of scan) {
    const x = p[0], y = p[1];
    const px = cx + x * scale;
    const py = cy - y * scale;
    const ang = (Math.atan2(y, x) * 180) / Math.PI;
    const angDeg = (ang + 360) % 360;

    let color = "#666";
    if (leftSector && angleInSector(angDeg, leftSector)) color = "#e85d5d";
    if (rightSector && angleInSector(angDeg, rightSector)) color = "#4c9be8";
    if (frontSector && angleInSector(angDeg, frontSector)) color = "#4caf50";

    ctx.fillStyle = color;
    ctx.fillRect(px, py, 2, 2);
  }

  const drawFiltered = (pts, color) => {
    ctx.fillStyle = color;
    for (const p of pts) {
      const x = p[0], y = p[1];
      const px = cx + x * scale;
      const py = cy - y * scale;
      ctx.fillRect(px - 1, py - 1, 4, 4);
    }
  };

  drawFiltered(leftFiltered, "#ff3b3b");
  drawFiltered(rightFiltered, "#2f7bff");
  drawFiltered(frontFiltered, "#34c759");

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
  el("left_points").textContent = data.left_points ?? "-";
  el("right_points").textContent = data.right_points ?? "-";
  el("left_inliers").textContent = data.left_inliers ?? "-";
  el("right_inliers").textContent = data.right_inliers ?? "-";

  el("steer").textContent = fmt(data.steer);
  el("throttle").textContent = fmt(data.throttle);
  el("steering_us").textContent = data.steering_us ?? "-";
  el("esc_us").textContent = data.esc_us ?? "-";

  el("yaw_rate").textContent = fmt(data.yaw_rate);

  const scan = data.scan_xy || [];
  if (scan.length > 0) {
    trailHistory.push(scan);
    if (trailHistory.length > trailMax) {
      trailHistory.shift();
    }
  }

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

  const scaleEl = el("scale");
  const scaleValEl = el("scaleVal");
  const onScale = () => {
    scale = Number(scaleEl.value);
    scaleValEl.textContent = scale;
  };
  scaleEl.addEventListener("input", onScale);
  onScale();

  const trailToggle = el("trailToggle");
  const onTrail = () => {
    showTrail = !!trailToggle.checked;
  };
  trailToggle.addEventListener("change", onTrail);
  onTrail();

}

function connect() {
  const proto = (location.protocol === "https:") ? "wss" : "ws";
  ws = new WebSocket(`${proto}://${location.host}/ws`);
  el("status").textContent = "connecting...";

  ws.onopen = () => el("status").textContent = "connected";
  ws.onclose = () => {
    el("status").textContent = "disconnected, retrying...";
    trailHistory = [];
    lastMsgT = 0;
    wsHzEma = null;
    el("web_hz").textContent = "-";
    setTimeout(connect, 1000);
  };
  ws.onerror = () => ws.close();

  ws.onmessage = (ev) => {
    try {
      const now = performance.now() / 1000;
      if (lastMsgT > 0) {
        const dt = now - lastMsgT;
        if (dt > 0) {
          const hz = 1.0 / dt;
          if (wsHzEma === null) wsHzEma = hz;
          else wsHzEma = 0.85 * wsHzEma + 0.15 * hz;
          el("web_hz").textContent = fmt(wsHzEma);
        }
      }
      lastMsgT = now;
      updateUI(JSON.parse(ev.data));
    } catch (e) {}
  };
}

setupControls();
connect();
