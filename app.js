
const $ = (s) => document.querySelector(s);
const lessonEl = $("#lesson");
const statusEl = $("#status");
const template = $("#itemTemplate");

let currentVideoId = "";

function normalise(s){
  return (s || "").toLowerCase().replace(/[^a-z0-9']+/g," ").trim();
}

function speak(text){
  if(!("speechSynthesis" in window)) return;
  speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text);
  u.lang = "en-GB";
  u.rate = 0.92;
  speechSynthesis.speak(u);
}

function seek(seconds){
  if(!currentVideoId) return;
  $("#player").src = `https://www.youtube.com/embed/${currentVideoId}?start=${Math.floor(seconds)}&autoplay=1`;
  $("#playerWrap").hidden = false;
  $("#playerWrap").scrollIntoView({behavior:"smooth",block:"center"});
}

function render(data){
  lessonEl.innerHTML = "";
  currentVideoId = data.video_id || "";

  if(currentVideoId){
    $("#player").src = `https://www.youtube.com/embed/${currentVideoId}`;
    $("#playerWrap").hidden = false;
  } else {
    $("#playerWrap").hidden = true;
  }

  data.items.forEach(item => {
    const node = template.content.cloneNode(true);
    const card = node.querySelector(".lesson-card");
    node.querySelector(".badge").textContent = `#${item.number}`;
    node.querySelector(".phrase").textContent = item.text;

    const time = node.querySelector(".time");
    time.textContent = `▶ ${Math.floor(item.start/60)}:${String(Math.floor(item.start%60)).padStart(2,"0")}`;
    time.onclick = () => seek(item.start);
    if(!currentVideoId) time.hidden = true;

    const notes = node.querySelector(".notes");
    item.notes.forEach(n => {
      const p = document.createElement("div");
      p.className = "note";
      p.textContent = `${n.phrase} — ${n.note}`;
      notes.appendChild(p);
    });

    node.querySelector(".speak").onclick = () => speak(item.text);

    const practiceBtn = node.querySelector(".practice");
    const practiceBox = node.querySelector(".practice-box");
    practiceBtn.onclick = () => {
      practiceBox.hidden = !practiceBox.hidden;
      if(!practiceBox.hidden) node.querySelector(".answer").focus();
    };

    const answer = node.querySelector(".answer");
    const feedback = node.querySelector(".feedback");
    node.querySelector(".check").onclick = () => {
      const a = normalise(answer.value);
      const b = normalise(item.text);
      if(!a) return;
      if(a === b){
        feedback.textContent = "Perfect.";
        feedback.className = "feedback good";
      } else {
        const aw = new Set(a.split(" "));
        const bw = b.split(" ");
        const hit = bw.filter(w => aw.has(w)).length;
        const score = Math.round((hit / Math.max(bw.length,1))*100);
        feedback.textContent = score >= 80
          ? `Very close — about ${score}% of the words matched.`
          : `About ${score}% matched. Listen once more and try again.`;
        feedback.className = score >= 80 ? "feedback good" : "feedback try";
      }
    };

    lessonEl.appendChild(node);
  });
}

$("#makeLesson").onclick = async () => {
  const url = $("#url").value.trim();
  const transcript = $("#transcript").value.trim();
  statusEl.textContent = "Creating your lesson…";
  $("#makeLesson").disabled = true;
  lessonEl.innerHTML = "";

  try{
    const r = await fetch("/api/lesson",{
      method:"POST",
      headers:{"Content-Type":"application/json"},
      body:JSON.stringify({url, transcript})
    });
    const data = await r.json();
    if(!r.ok || !data.ok) throw new Error(data.error || "Something went wrong.");
    render(data);
    statusEl.textContent = `Ready — ${data.items.length} useful sentences from ${data.source}.`;
  }catch(e){
    statusEl.textContent = e.message;
  }finally{
    $("#makeLesson").disabled = false;
  }
};

// PWA install
let deferredPrompt = null;
const installBtn = $("#installBtn");
window.addEventListener("beforeinstallprompt",(e)=>{
  e.preventDefault();
  deferredPrompt = e;
  installBtn.hidden = false;
});
installBtn.onclick = async ()=>{
  if(!deferredPrompt) return;
  deferredPrompt.prompt();
  await deferredPrompt.userChoice;
  deferredPrompt = null;
  installBtn.hidden = true;
};

if("serviceWorker" in navigator){
  navigator.serviceWorker.register("/static/sw.js");
}
