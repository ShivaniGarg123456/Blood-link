/* BloodLink alert page: looping siren + vibration + spoken message + Accept / Can't come buttons.
   It uses the backend's own endpoints (GET /donors/me/alerts, POST /alerts/{id}/accept|decline,
   GET /alerts/{id}), so the donor must be logged in. Nothing else to set up on the server.

   Honest limits (say them in the pitch):
   - Works only while this page is open. Sound needs ONE tap first (call enable() from a button).
   - Vibration works on Android Chrome, not on iPhone Safari.
   - The spoken voice uses the phone's built-in voices; a Hindi voice may be missing on some phones.

   Usage (after login):
   <button onclick="BloodLinkSiren.enable(); BloodLinkSiren.start({
        baseUrl: 'http://localhost:8000', getToken: function () { return TOKEN; }, language: 'hi' })">Enable alerts</button>
*/
(function (global) {
  var HI_GROUP = { "A+": "ए पॉज़िटिव", "A-": "ए नेगेटिव", "B+": "बी पॉज़िटिव", "B-": "बी नेगेटिव",
                   "O+": "ओ पॉज़िटिव", "O-": "ओ नेगेटिव", "AB+": "एबी पॉज़िटिव", "AB-": "एबी नेगेटिव" };
  var ctx = null, osc = null, gain = null, timers = [], overlay = null, cfg = null;
  var current = null, deadline = 0, waitTimer = null, pollTimer = null;
  var FINAL = ["confirmed", "standby", "arrived", "declined", "expired", "cancelled", "no_show"];

  function lang() { return (cfg && cfg.language) === "en" ? "en" : "hi"; }

  function voiceText(a) {
    var hi = lang() === "hi";
    var g = hi ? (HI_GROUP[a.blood_group] || a.blood_group)
               : a.blood_group.replace("+", " positive").replace("-", " negative");
    return hi
      ? "आपके पास खून की ज़रूरत है। " + a.hospital + " में " + g + " चाहिए, " + a.distance_km + " किलोमीटर दूर। कृपया स्वीकार करें।"
      : "Blood request near you. " + g + " blood is needed at " + a.hospital + ", " + a.distance_km + " kilometres away. Please accept.";
  }

  function alertText(a) {
    return (lang() === "hi" ? "🩸 आपके पास खून की ज़रूरत है\n" : "🩸 Blood needed near you\n") +
      a.blood_group + " · " + a.distance_km + " km\n" + a.hospital;
  }

  function api(path, method) {
    return fetch(cfg.baseUrl + path, { method: method || "GET", headers: { Authorization: "Bearer " + cfg.getToken() } })
      .then(function (r) { return r.json().then(function (j) { return { ok: r.ok, status: r.status, body: j }; }); });
  }

  function enable() {
    var AC = global.AudioContext || global.webkitAudioContext;
    if (AC) { ctx = ctx || new AC(); if (ctx.state === "suspended") ctx.resume(); }
    if (global.speechSynthesis) global.speechSynthesis.getVoices();
    if (navigator.wakeLock) navigator.wakeLock.request("screen").catch(function () {});
  }

  function startSiren() {
    if (!ctx || osc) return;
    osc = ctx.createOscillator(); gain = ctx.createGain();
    osc.type = "square"; gain.gain.value = 0.25;
    osc.connect(gain); gain.connect(ctx.destination); osc.start();
    var high = false;
    timers.push(setInterval(function () { high = !high; osc.frequency.value = high ? 950 : 650; }, 450));
  }

  function startVibration() {
    if (!navigator.vibrate) return;
    var buzz = function () { navigator.vibrate([700, 200, 700, 200, 700]); };
    buzz(); timers.push(setInterval(buzz, 3000));
  }

  function speak() {
    if (!global.speechSynthesis || !current) return;
    var u = new SpeechSynthesisUtterance(voiceText(current));
    u.lang = lang() === "hi" ? "hi-IN" : "en-IN"; u.rate = 0.95;
    global.speechSynthesis.cancel(); global.speechSynthesis.speak(u);
  }

  function stopAlarm() {
    timers.forEach(clearInterval); timers = [];
    if (osc) { try { osc.stop(); } catch (e) {} osc = null; }
    if (navigator.vibrate) navigator.vibrate(0);
    if (global.speechSynthesis) global.speechSynthesis.cancel();
  }

  function closeOverlay() {
    if (overlay) { overlay.remove(); overlay = null; }
  }

  function button(label, onclick, big) {
    var b = document.createElement("button"); b.textContent = label;
    b.style.cssText = "margin:8px;border:0;border-radius:12px;padding:" + (big ? "16px 40px;font-size:1.6rem" : "10px 28px;font-size:1.1rem");
    b.onclick = onclick; return b;
  }

  function showOverlay(text, buttons, showTimer) {
    closeOverlay();
    overlay = document.createElement("div");
    overlay.style.cssText = "position:fixed;inset:0;z-index:99999;background:#b00020;color:#fff;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:24px;text-align:center;font-family:sans-serif;white-space:pre-line";
    var p = document.createElement("p"); p.style.fontSize = "1.3rem"; p.textContent = text; overlay.appendChild(p);
    if (showTimer) { var t = document.createElement("p"); t.id = "bl-timer"; t.style.fontSize = "2rem"; overlay.appendChild(t); }
    buttons.forEach(function (b) { overlay.appendChild(b); });
    document.body.appendChild(overlay);
  }

  function ring(a) {
    current = a; deadline = Date.now() + a.seconds_left * 1000;
    showOverlay(alertText(a), [
      button(lang() === "hi" ? "✅ स्वीकार करें" : "✅ Accept", function () { respond("accept"); }, true),
      button(lang() === "hi" ? "❌ नहीं आ सकता" : "❌ Can't come", function () { respond("decline"); }, false)], true);
    startSiren(); startVibration(); speak();
    timers.push(setInterval(speak, 12000));
    timers.push(setInterval(function () {
      var t = document.getElementById("bl-timer");
      if (t) t.textContent = Math.max(0, Math.round((deadline - Date.now()) / 1000)) + " s";
    }, 500));
  }

  function showResult(view) {
    var text = view.message || "";
    if (view.receiver_phone) text += "\n" + (view.receiver_name || "") + ": " + view.receiver_phone;
    showOverlay(text, [button("OK", function () { closeOverlay(); }, false)], false);
    if (cfg.onResult) cfg.onResult(view);
  }

  function respond(action) {
    var a = current; stopAlarm();
    api("/alerts/" + a.alert_id + "/" + action, "POST").then(function (res) {
      if (!res.ok) { showOverlay(res.body.detail || "Could not respond.", [button("OK", closeOverlay, false)], false); current = null; return; }
      if (FINAL.indexOf(res.body.response) >= 0) { current = null; showResult(res.body); return; }
      // accepted, but a nearer donor may still be deciding: wait for the result
      showOverlay(res.body.message || "...", [], false);
      waitTimer = setInterval(function () {
        api("/alerts/" + a.alert_id).then(function (r) {
          if (r.ok && FINAL.indexOf(r.body.response) >= 0) { clearInterval(waitTimer); current = null; showResult(r.body); }
        });
      }, 2000);
    }).catch(function () { showOverlay("Could not reach the server.", [button("OK", closeOverlay, false)], false); });
  }

  function pollOnce() {
    api("/donors/me/alerts").then(function (res) {
      if (!res.ok || !Array.isArray(res.body)) return;
      var a = res.body[0];
      if (a && (!current || current.alert_id !== a.alert_id) && !overlayBusy()) ring(a);
      if (!a && current) { stopAlarm(); closeOverlay(); current = null; }
    }).catch(function () {});
  }

  function overlayBusy() { return overlay !== null && current === null; }

  function start(c) { cfg = c; pollTimer = setInterval(pollOnce, 2000); pollOnce(); }

  global.BloodLinkSiren = { enable: enable, start: start, stop: function () { stopAlarm(); closeOverlay(); clearInterval(pollTimer); clearInterval(waitTimer); } };
})(window);
