(function () {
  const script  = document.currentScript;
  const ownerId = script.getAttribute("data-owner-id");
  const API     = script.getAttribute("data-api") || "http://localhost:8000";
  const id      = ownerId.replace(/[^a-z0-9]/gi, "");

  // ── Inject Styles ─────────────────────────────────
  const style = document.createElement("style");
  style.innerHTML = `
    #vst-btn-${id} {
      position:fixed; bottom:30px; right:30px; width:60px; height:60px;
      background:#405189; border-radius:50%; cursor:pointer;
      box-shadow:0 4px 15px rgba(0,0,0,0.3); font-size:26px;
      z-index:9999; border:none; color:white;
    }
    #vst-box-${id} {
      position:fixed; bottom:100px; right:30px; width:370px; height:500px;
      background:#ffffff; border-radius:16px; display:none;
      flex-direction:column; z-index:9999; overflow:hidden;
      box-shadow:0 8px 32px rgba(0,0,0,0.4);
    }
    #vst-box-${id}.open { display:flex; }
    .vh-${id} {
      background:#405189; padding:14px 18px; color:white;
      font-family:Arial; font-weight:bold; font-size:14px;
      display:flex; justify-content:space-between; align-items:center;
    }
    .vm-${id} {
      flex:1; overflow-y:auto; padding:14px;
      display:flex; flex-direction:column; gap:8px; font-family:Arial;
    }
    .vu-${id} {
      align-self:flex-end; background:#e94560; color:white;
      padding:9px 13px; border-radius:12px; max-width:80%; font-size:13px;
    }
    .vb-${id} {
      align-self:flex-start; background:#0f3460; color:white;
      padding:9px 13px; border-radius:12px; max-width:80%; font-size:13px;
    }
    .vi-${id} {
      display:flex; padding:10px; gap:8px; background:#405189;
    }
    .vi-${id} select {
      padding:8px; border-radius:8px; border:none;
      background:#405189; color:white; font-size:12px;
    }
    .vi-${id} input {
      flex:1; padding:8px 12px; border-radius:8px; border:none;
      background:#ffffff; color:#403d3d; font-size:13px; outline:none;
    }
    .vi-${id} button {
      padding:8px 14px; background:#ffffff; color:#88888;
      border:none; border-radius:8px; cursor:pointer; font-size:13px;
    }
    .vt-${id} { color:#888; font-size:12px; padding:0 14px 8px; font-family:Arial; display:none; }
  `;
  document.head.appendChild(style);

  // ── Inject HTML ───────────────────────────────────
  const wrap = document.createElement("div");
  wrap.innerHTML = `
    <button id="vst-btn-${id}">💬</button>
    <div id="vst-box-${id}">
      <div class="vh-${id}">
        🤖 Support AI
        <button onclick="document.getElementById('vst-box-${id}').classList.remove('open')"
          style="background:none;border:none;color:white;font-size:18px;cursor:pointer">✕</button>
      </div>
      <div class="vm-${id}" id="vst-msgs-${id}">
        <div class="vb-${id}">Hello! How can I help you? 👋</div>
      </div>
      <div class="vt-${id}" id="vst-typ-${id}">Typing...</div>
      <div class="vi-${id}">
        <select id="vst-lang-${id}">
          <option value="en">EN</option>
          <option value="ur">UR</option>
          <option value="ar">AR</option>
          <option value="fr">FR</option>
          <option value="hi">HI</option>
        </select>
        <input id="vst-inp-${id}" type="text" placeholder="Ask a question..."
          onkeypress="if(event.key==='Enter') vstSend_${id}()" autocomplete="off">
        <button onclick="vstSend_${id}()">Send</button>
      </div>
    </div>
  `;
  document.body.appendChild(wrap);

  document.getElementById(`vst-btn-${id}`)
    .addEventListener("click", () => {
      document.getElementById(`vst-box-${id}`).classList.toggle("open");
    });

  window[`vstSend_${id}`] = async function () {
    const input = document.getElementById(`vst-inp-${id}`);
    const lang  = document.getElementById(`vst-lang-${id}`).value;
    const q     = input.value.trim();
    if (!q) return;

    const msgs = document.getElementById(`vst-msgs-${id}`);
    msgs.innerHTML += `<div class="vu-${id}">${q}</div>`;
    input.value = "";
    msgs.scrollTop = msgs.scrollHeight;

    const typing = document.getElementById(`vst-typ-${id}`);
    typing.style.display = "block";

    try {
      const res  = await fetch(`${API}/widget/query`, {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({ owner_id: ownerId, question: q, language: lang })
      });
      const data = await res.json();
      typing.style.display = "none";
      msgs.innerHTML += `<div class="vb-${id}">${data.data.answer}</div>`;
    } catch (e) {
      typing.style.display = "none";
      msgs.innerHTML += `<div class="vb-${id}">Sorry, unable to connect.</div>`;
    }
    msgs.scrollTop = msgs.scrollHeight;
  };
})();