(function () {
  "use strict";

  // ── CONFIG ───────────────────────────────────────────────
  var script = document.currentScript ||
    document.querySelector('script[data-owner-id]');

  var OWNER_ID = script && script.getAttribute("data-owner-id");
  var API_BASE = (script && script.getAttribute("data-api-url")) || "http://localhost:8000";
  var STYLE_MODE = (script && script.getAttribute("data-style")) || "simple";
  var BOT_NAME = (script && script.getAttribute("data-bot-name")) || "Support Bot";
  var THEME = (script && script.getAttribute("data-theme")) || "light";

  if (!OWNER_ID) {
    console.error("[Chatbot] data-owner-id is required on the <script> tag.");
    return;
  }

  // ── STYLES ───────────────────────────────────────────────
  var css = `
    #llm-chat-btn {
      position: fixed; bottom: 28px; right: 28px; z-index: 9999;
      width: 56px; height: 56px; border-radius: 50%;
      background: #4F46E5; color: #fff; border: none;
      box-shadow: 0 4px 14px rgba(79,70,229,.45);
      cursor: pointer; display: flex; align-items: center; justify-content: center;
      transition: transform .2s, box-shadow .2s;
    }
    #llm-chat-btn:hover { transform: scale(1.08); box-shadow: 0 6px 20px rgba(79,70,229,.55); }
    #llm-chat-btn svg   { width: 26px; height: 26px; }

    #llm-chat-box {
      position: fixed; bottom: 96px; right: 28px; z-index: 9999;
      width: 360px; max-height: 540px;
      background: #fff; border-radius: 16px;
      box-shadow: 0 8px 32px rgba(0,0,0,.18);
      display: none; flex-direction: column; overflow: hidden;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      font-size: 14px; color: #1a1a1a;
    }
    #llm-chat-box.open   { display: flex; }
    #llm-chat-box.dark   { background: #1e1e2e; color: #e0e0e0; }

    #llm-chat-header {
      background: #4F46E5; color: #fff;
      padding: 14px 16px; font-weight: 600; font-size: 15px;
      display: flex; align-items: center; justify-content: space-between;
      flex-shrink: 0;
    }
    #llm-chat-header .llm-close {
      background: none; border: none; color: #fff;
      font-size: 20px; cursor: pointer; line-height: 1; padding: 0;
    }
    #llm-chat-header .llm-dot {
      width: 8px; height: 8px; border-radius: 50%;
      background: #4ade80; display: inline-block; margin-right: 8px;
    }

    #llm-chat-messages {
      flex: 1; overflow-y: auto; padding: 14px 14px 6px;
      display: flex; flex-direction: column; gap: 10px;
    }
    #llm-chat-messages::-webkit-scrollbar { width: 4px; }
    #llm-chat-messages::-webkit-scrollbar-thumb { background: #ccc; border-radius: 4px; }

    .llm-msg {
      max-width: 82%; padding: 9px 13px; border-radius: 14px;
      line-height: 1.5; word-wrap: break-word;
    }
    .llm-msg.bot  {
      background: #f0f0f5; color: #1a1a1a;
      border-bottom-left-radius: 4px; align-self: flex-start;
    }
    .llm-msg.user {
      background: #4F46E5; color: #fff;
      border-bottom-right-radius: 4px; align-self: flex-end;
    }
    #llm-chat-box.dark .llm-msg.bot { background: #2a2a3e; color: #e0e0e0; }

    .llm-typing {
      display: flex; gap: 5px; padding: 10px 14px;
      align-self: flex-start;
    }
    .llm-typing span {
      width: 7px; height: 7px; border-radius: 50%; background: #999;
      animation: llm-bounce .9s infinite;
    }
        #llm-chat-lang {
    border: none;
    border-radius: 999px;
    padding: 6px 10px;
    font-size: 12px;
    background: #eef2ff;
    color: #3730a3;
    cursor: pointer;
    outline: none;
  }
    .llm-typing span:nth-child(2) { animation-delay: .15s; }
    .llm-typing span:nth-child(3) { animation-delay: .30s; }
    @keyframes llm-bounce {
      0%,80%,100% { transform: translateY(0); }
      40%          { transform: translateY(-6px); }
    }

    #llm-chat-input-row {
      display: flex; gap: 8px; padding: 10px 12px;
      border-top: 1px solid #e5e7eb; flex-shrink: 0;
      background: inherit;
    }
    #llm-chat-box.dark #llm-chat-input-row { border-color: #333; }
    #llm-chat-input {
      flex: 1; border: 1px solid #d1d5db; border-radius: 22px;
      padding: 8px 14px; font-size: 13px; outline: none;
      background: #fafafa; color: inherit;
      transition: border-color .2s;
    }
    #llm-chat-input:focus { border-color: #4F46E5; background: #fff; }
    #llm-chat-box.dark #llm-chat-input { background: #2a2a3e; border-color: #444; color: #e0e0e0; }
    #llm-chat-send {
      width: 36px; height: 36px; border-radius: 50%;
      background: #4F46E5; color: #fff; border: none;
      cursor: pointer; display: flex; align-items: center; justify-content: center;
      flex-shrink: 0; transition: background .2s;
    }
    #llm-chat-send:hover   { background: #4338CA; }
    #llm-chat-send:disabled{ background: #a5b4fc; cursor: not-allowed; }
    #llm-chat-send svg { width: 16px; height: 16px; }

    #llm-chat-footer {
      text-align: center; font-size: 11px; color: #9ca3af;
      padding: 4px 0 8px;
    }

    @media (max-width: 400px) {
      #llm-chat-box { width: calc(100vw - 24px); right: 12px; bottom: 80px; }
    }
  `;

  document.head.appendChild(Object.assign(document.createElement("style"), { textContent: css }));

  // ── UI ───────────────────────────────────────────────
  var btn = document.createElement("button");
  btn.id = "llm-chat-btn";
  btn.innerHTML = "💬";

  var box = document.createElement("div");
  box.id = "llm-chat-box";
  if (THEME === "dark") box.classList.add("dark");

  box.innerHTML = `
    <div id="llm-chat-header">
      <span>${BOT_NAME}</span>
      <button class="llm-close">&times;</button>
    </div>

    <div id="llm-chat-messages"></div>

    <div id="llm-chat-input-row">
      <select id="llm-chat-lang">
        <option value="auto">🌐 Auto</option>
        <option value="en">🇺🇸 EN</option>
        <option value="ur">🇵🇰 UR</option>
        <option value="ar">🇸🇦 AR</option>
        <option value="fr">🇫🇷 FR</option>
        <option value="hi">🇮🇳 HI</option>
      </select>

      <input id="llm-chat-input" type="text" placeholder="Type your message…" />

      <button id="llm-chat-send">➤</button>
    </div>
  `;

  document.body.appendChild(btn);
  document.body.appendChild(box);

  // ── REFS ───────────────────────────────────────────────
  var messages = box.querySelector("#llm-chat-messages");
  var input = box.querySelector("#llm-chat-input");
  var sendBtn = box.querySelector("#llm-chat-send");
  var lang = box.querySelector("#llm-chat-lang");
  var closeBtn = box.querySelector(".llm-close");

  // Load saved language
  lang.value = localStorage.getItem("chat_lang") || "auto";

  lang.addEventListener("change", function () {
    localStorage.setItem("chat_lang", lang.value);
  });

  function addMsg(text, role) {
    var el = document.createElement("div");
    el.className = "llm-msg " + role;
    el.textContent = text;
    messages.appendChild(el);
    messages.scrollTop = messages.scrollHeight;
  }

  function typing() {
    var el = document.createElement("div");
    el.className = "llm-typing";
    el.innerHTML = "<span></span><span></span><span></span>";
    messages.appendChild(el);
    return el;
  }

  function openChat() {
    box.classList.add("open");
    if (!messages.children.length) {
      addMsg("Hi! How can I help you today?", "bot");
    }
  }

  function closeChat() {
    box.classList.remove("open");
  }

  btn.onclick = () => box.classList.contains("open") ? closeChat() : openChat();
  closeBtn.onclick = closeChat;

  async function sendMessage() {
    var text = input.value.trim();
    if (!text) return;

    addMsg(text, "user");
    input.value = "";
    sendBtn.disabled = true;
    input.disabled = true;
    lang.disabled = true;

    var loader = typing();

    messages.scrollTo({
      top: messages.scrollHeight,
      behavior: "smooth"
    });

    try {
      var res = await fetch(API_BASE + "/widget/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          owner_id: OWNER_ID,
          question: text,
          language: lang.value || "auto",
          style: STYLE_MODE
        })
      });

      var data = await res.json();
      loader.remove();

      addMsg(
        (data.data && data.data.answer) ? data.data.answer : "No response",
        "bot"
      );

    } catch (e) {
      loader.remove();
      addMsg("Connection error. Try again.", "bot");
    }

    sendBtn.disabled = false;
    input.disabled = false;
    lang.disabled = false;
    input.focus();
  }

  sendBtn.onclick = sendMessage;

  input.addEventListener("keydown", function (e) {
    if (e.key === "Enter") sendMessage();
  });

})();
