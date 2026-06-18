/* Assistente CETAB — chat offline. Lê demo-chat.json (respostas reais sobre o Data Lake).
   Casa a pergunta do usuário por palavras-chave; senão, sugere as perguntas conhecidas. */
let QA;

async function carregar() {
  QA = await fetch("demo-chat.json").then((r) => r.json());
  sugestoes();
  bot("Olá! Sou o assistente do CETAB. Pergunte sobre as análises, municípios e riscos — " +
      "ou clique numa sugestão acima.");
  document.getElementById("form-chat").addEventListener("submit", (e) => {
    e.preventDefault();
    const txt = document.getElementById("entrada").value.trim();
    if (txt) responder(txt);
    document.getElementById("entrada").value = "";
  });
}

function sugestoes() {
  document.getElementById("sugestoes").innerHTML = QA.map((q, i) =>
    `<button class="chip" data-i="${i}">${q.pergunta}</button>`).join("");
  document.querySelectorAll(".chip").forEach((c) =>
    c.addEventListener("click", () => responder(QA[+c.dataset.i].pergunta)));
}

function responder(pergunta) {
  usuario(pergunta);
  const p = pergunta.toLowerCase();
  // pontua cada QA pela quantidade de tags presentes na pergunta
  let melhor = null, score = 0;
  for (const qa of QA) {
    const s = qa.tags.filter((t) => p.includes(t)).length;
    if (s > score) { score = s; melhor = qa; }
  }
  setTimeout(() => {
    if (melhor && score > 0) bot(melhor.resposta);
    else bot("Ainda não tenho essa resposta no modo demonstração. Tente, por exemplo: " +
             QA.slice(0, 3).map((q) => `"${q.pergunta}"`).join(", ") + ".");
  }, 350);
}

function usuario(t) { msg(t, "user"); }
function bot(t) { msg(t, "bot"); }
function msg(texto, quem) {
  const div = document.createElement("div");
  div.className = "msg " + quem;
  div.textContent = texto;
  const cont = document.getElementById("mensagens");
  cont.appendChild(div);
  cont.scrollTop = cont.scrollHeight;
}

carregar().catch((e) => {
  document.getElementById("mensagens").innerHTML =
    `<div class="card" style="border-color:#c0392b">Erro: ${e.message}.<br>` +
    `<small>Rode <code>python gerar_demo_secretario.py</code> e sirva via <code>python -m http.server</code>.</small></div>`;
});
