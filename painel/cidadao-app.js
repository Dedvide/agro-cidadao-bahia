/* Agro Cidadão Bahia — chat web automatizado */

const API_BASE = "";  // mesmo domínio em produção

const SUGESTOES = [
  "Como combater a mosca-das-frutas?",
  "Minhas folhas estão amarelando. O que fazer?",
  "Como melhorar meu solo para o plantio?",
  "Qual a época certa para plantar milho na Bahia?",
  "Como economizar água na irrigação?",
  "Como iniciar uma horta em casa?",
  "Como cuidar de abelhas para apicultura?",
  "O que fazer quando a planta fica murcha?",
];

let imagemFile = null;

// ── DOM refs ──
const mensagensEl = document.getElementById("mensagens");
const entrada = document.getElementById("entrada");
const btnEnviar = document.getElementById("btn-enviar");
const inputImagem = document.getElementById("input-imagem");
const nomeArquivo = document.getElementById("nome-arquivo");
const municipioEl = document.getElementById("municipio");
const sugestoesEl = document.getElementById("sugestoes");
const formEl = document.getElementById("form-chat");

// ── Inicialização ──
function init() {
  renderSugestoes();
  addMsg("bot",
    "Olá! Sou o *Agro Cidadão Bahia* 🌱\n\n" +
    "Estou aqui para ajudar agricultores familiares com dúvidas sobre plantio, pragas, " +
    "solo, irrigação e muito mais — de forma totalmente gratuita.\n\n" +
    "Você pode me enviar uma *pergunta* ou *foto* da sua lavoura. Como posso ajudar hoje?"
  );

  formEl.addEventListener("submit", onSubmit);
  inputImagem.addEventListener("change", onImagemSelecionada);
  entrada.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); formEl.dispatchEvent(new Event("submit")); }
  });
}

// ── Sugestões ──
function renderSugestoes() {
  sugestoesEl.innerHTML = SUGESTOES
    .sort(() => Math.random() - .5).slice(0, 4)
    .map(s => `<button class="chip" type="button">${s}</button>`)
    .join("");
  sugestoesEl.querySelectorAll(".chip").forEach(c =>
    c.addEventListener("click", () => { entrada.value = c.textContent; enviar(); })
  );
}

// ── Comprime imagem para max 800px / 200KB antes de enviar ──
function comprimirImagem(file) {
  return new Promise((resolve) => {
    const MAX = 800;
    const reader = new FileReader();
    reader.onload = (e) => {
      const img = new Image();
      img.onload = () => {
        const canvas = document.createElement("canvas");
        let w = img.width, h = img.height;
        if (w > MAX || h > MAX) {
          if (w > h) { h = Math.round(h * MAX / w); w = MAX; }
          else       { w = Math.round(w * MAX / h); h = MAX; }
        }
        canvas.width = w; canvas.height = h;
        canvas.getContext("2d").drawImage(img, 0, 0, w, h);
        canvas.toBlob((blob) => resolve(blob), "image/jpeg", 0.82);
      };
      img.src = e.target.result;
    };
    reader.readAsDataURL(file);
  });
}

// ── Imagem selecionada ──
function onImagemSelecionada() {
  imagemFile = inputImagem.files[0] || null;
  nomeArquivo.textContent = imagemFile ? imagemFile.name : "";
}

// ── Submit ──
async function onSubmit(e) {
  e.preventDefault();
  enviar();
}

async function enviar() {
  const texto = entrada.value.trim();
  if (!texto && !imagemFile) return;

  const municipio = municipioEl.value.trim();

  // exibir mensagem do usuário
  if (imagemFile) {
    const url = URL.createObjectURL(imagemFile);
    addMsgImagem("user", url, texto || "Analisar imagem");
  } else {
    addMsg("user", texto);
  }

  entrada.value = "";
  const arquivoEnviado = imagemFile;
  imagemFile = null;
  nomeArquivo.textContent = "";
  inputImagem.value = "";

  btnEnviar.disabled = true;
  const typing = addMsg("bot", "Analisando... pode levar alguns segundos.", "digitando");

  try {
    const form = new FormData();
    form.append("pergunta", texto || "Analise esta imagem da minha lavoura.");
    form.append("municipio", municipio);

    if (arquivoEnviado) {
      const blob = await comprimirImagem(arquivoEnviado);
      form.append("imagem", blob, "foto.jpg");
    }

    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 55000);

    const res = await fetch(`${API_BASE}/chat`, { method: "POST", body: form, signal: controller.signal });
    clearTimeout(timer);
    const data = await res.json();

    typing.remove();
    addMsg(res.ok ? "bot" : "erro", data.resposta || "Erro desconhecido.");
    sugestoesEl.style.display = "none";

  } catch (err) {
    typing.remove();
    if (err.name === "AbortError") {
      addMsg("erro", "A resposta demorou demais. Tente com uma foto menor ou envie só a pergunta em texto.");
    } else {
      addMsg("erro", "Não consegui me conectar. Verifique sua internet e tente novamente.");
    }
  } finally {
    btnEnviar.disabled = false;
    entrada.focus();
  }
}

// ── Helpers de mensagem ──
function addMsg(quem, texto, extraClass = "") {
  const div = document.createElement("div");
  div.className = `msg ${quem}${extraClass ? " " + extraClass : ""}`;
  div.textContent = texto.replace(/\*/g, "");  // remove asteriscos de markdown simples
  mensagensEl.appendChild(div);
  mensagensEl.scrollTop = mensagensEl.scrollHeight;
  return div;
}

function addMsgImagem(quem, src, legenda) {
  const div = document.createElement("div");
  div.className = `msg ${quem}`;
  const img = document.createElement("img");
  img.src = src;
  img.className = "preview";
  img.alt = "Foto enviada";
  div.appendChild(img);
  if (legenda) {
    const span = document.createElement("span");
    span.textContent = legenda;
    div.appendChild(span);
  }
  mensagensEl.appendChild(div);
  mensagensEl.scrollTop = mensagensEl.scrollHeight;
  return div;
}

init();
