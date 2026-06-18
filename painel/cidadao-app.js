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
let municipioSessao = "";        // município capturado na conversa
let aguardandoMunicipio = true;  // primeira mensagem é o município

// ── DOM refs ──
const mensagensEl = document.getElementById("mensagens");
const entrada = document.getElementById("entrada");
const btnEnviar = document.getElementById("btn-enviar");
const inputImagem = document.getElementById("input-imagem");
const nomeArquivo = document.getElementById("nome-arquivo");
const municipioEl = document.getElementById("municipio");
const sugestoesEl = document.getElementById("sugestoes");
const formEl = document.getElementById("form-chat");

// ── Palavras que indicam pergunta agrícola, não município ──
const PALAVRAS_AGRICOLAS = [
  "lavoura","plantio","planta","cacau","café","mandioca","milho","feijão","tomate",
  "banana","cana","soja","algodão","sisal","coco","laranja","manga","mamão","uva",
  "praga","doença","fungo","vassoura","bruxa","broca","lagarta","formiga","cupim","mosca",
  "amarelando","murchando","caindo","podre","mancha","folha","raiz","fruto","caule",
  "solo","terra","adubo","calcário","irrigação","seca","chuva","colheita","pesca",
  "peixe","camarão","boi","vaca","galinha","porco","cabra","abelha","mel","leite",
  "problema","ajuda","socorro","como","qual","quando","quanto","onde","por que","estou com"
];

function parecePerguntoAgricola(texto) {
  const t = texto.toLowerCase();
  return PALAVRAS_AGRICOLAS.some(p => t.includes(p));
}

// ── Extrai município de texto livre ──
function extrairMunicipio(texto) {
  const t = texto.toLowerCase();
  // só prefixos explícitos de localização — nunca o genérico "de " que captura "lavoura de cacau"
  const prefixos = ["sou de ", "moro em ", "aqui em ", "estou em ", "municipio ", "município ", "cidade de "];
  for (const p of prefixos) {
    const i = t.indexOf(p);
    if (i !== -1) {
      const resto = texto.slice(i + p.length).trim().split(/[\s,\.]/)[0];
      if (resto.length > 2) return resto.charAt(0).toUpperCase() + resto.slice(1);
    }
  }
  // texto curto sem palavras agrícolas = provavelmente só o nome do município
  const palavras = texto.trim().split(/\s+/);
  if (palavras.length <= 3 && !parecePerguntoAgricola(texto)) return texto.trim();
  return "";
}

// ── Microfone (Web Speech API) ──
let recognition = null;
let gravando = false;

function iniciarMic() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  const btnMic = document.getElementById("btn-mic");
  const micStatus = document.getElementById("mic-status");

  if (!SpeechRecognition) {
    micStatus.style.display = "block";
    micStatus.textContent = "Seu navegador não suporta áudio. Use o Chrome no celular.";
    return;
  }

  if (gravando) {
    recognition.stop();
    return;
  }

  recognition = new SpeechRecognition();
  recognition.lang = "pt-BR";
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;

  recognition.onstart = () => {
    gravando = true;
    btnMic.classList.add("gravando");
    btnMic.textContent = "⏹";
    micStatus.style.display = "block";
    micStatus.textContent = "Ouvindo... fale sua dúvida";
  };

  recognition.onresult = (e) => {
    const transcrito = e.results[0][0].transcript;
    entrada.value = transcrito;
    micStatus.textContent = `Entendido: "${transcrito}"`;
    entrada.focus();
  };

  recognition.onerror = (e) => {
    micStatus.textContent = e.error === "not-allowed"
      ? "Permita o acesso ao microfone nas configurações do navegador."
      : "Não entendi. Tente falar mais devagar ou use o texto.";
  };

  recognition.onend = () => {
    gravando = false;
    btnMic.classList.remove("gravando");
    btnMic.textContent = "🎤";
    setTimeout(() => { micStatus.style.display = "none"; }, 3000);
  };

  recognition.start();
}

// ── Inicialização ──
function init() {
  renderSugestoes();
  addMsg("bot",
    "Olá! Sou o Agro Cidadão Bahia 🌱\n\n" +
    "Estou aqui para ajudar agricultores familiares com dúvidas sobre plantio, pragas, " +
    "solo, irrigação e muito mais — de forma totalmente gratuita.\n\n" +
    "Para começar: de qual município você é?"
  );

  formEl.addEventListener("submit", onSubmit);
  inputImagem.addEventListener("change", onImagemSelecionada);
  document.getElementById("btn-mic").addEventListener("click", iniciarMic);
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

  // primeira mensagem: tentar capturar município, mas só se não parecer pergunta agrícola
  if (aguardandoMunicipio && texto && !imagemFile) {
    const municipioDetectado = extrairMunicipio(texto);
    if (municipioDetectado && !parecePerguntoAgricola(texto)) {
      municipioSessao = municipioDetectado;
      municipioEl.value = municipioSessao;
      aguardandoMunicipio = false;
      addMsg("user", texto);
      entrada.value = "";
      addMsg("bot",
        `Obrigado! Registrei que você é de ${municipioSessao}. ` +
        "Agora pode me fazer sua pergunta ou enviar uma foto da lavoura."
      );
      sugestoesEl.style.display = "flex";
      renderSugestoes();
      entrada.focus();
      return;
    }
    // usuário ignorou a pergunta do município e foi direto à dúvida — tudo bem, continuar normalmente
    aguardandoMunicipio = false;
  }

  const municipio = municipioSessao || municipioEl.value.trim();

  // tenta extrair município do texto mesmo após boas-vindas
  if (!municipioSessao) {
    const extraido = extrairMunicipio(texto);
    if (extraido) { municipioSessao = extraido; municipioEl.value = extraido; }
  }

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

// ── Renderiza markdown simples como HTML seguro ──
function renderMarkdown(texto) {
  // 1. escapa HTML para prevenir XSS
  let h = texto
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
  // 2. links markdown [texto](url) — aceita https:// e caminhos relativos /...
  h = h.replace(
    /\[([^\]]{1,80})\]\(((?:https?:\/\/|\/)[^)]{1,200})\)/g,
    '<a href="$2" target="_blank" rel="noopener noreferrer">$1 ↗</a>'
  );
  // 3. negrito **texto**
  h = h.replace(/\*\*([^*\n]{1,100})\*\*/g, "<strong>$1</strong>");
  // 4. quebras de linha
  h = h.replace(/\n/g, "<br>");
  return h;
}

// ── Texto limpo para leitura em voz (sem markdown nem links) ──
function textoParaVoz(texto) {
  return texto
    .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")  // [texto](url) → texto
    .replace(/[#*_`]/g, "")
    .replace(/\n+/g, ". ")
    .trim();
}

// ── Voz de saída (Text-to-Speech) ──
function lerEmVoz(texto) {
  if (!window.speechSynthesis) return;
  speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(textoParaVoz(texto));
  u.lang  = "pt-BR";
  u.rate  = 0.88;
  u.pitch = 1;
  speechSynthesis.speak(u);
}

// ── Helpers de mensagem ──
function addMsg(quem, texto, extraClass = "") {
  const div = document.createElement("div");
  div.className = `msg ${quem}${extraClass ? " " + extraClass : ""}`;

  if (quem === "bot" && !extraClass) {
    div.innerHTML = renderMarkdown(texto);
    const btnOuvir = document.createElement("button");
    btnOuvir.className = "btn-ouvir";
    btnOuvir.title = "Ouvir resposta";
    btnOuvir.textContent = "🔊";
    btnOuvir.addEventListener("click", () => lerEmVoz(texto));
    div.appendChild(btnOuvir);
    lerEmVoz(texto);
  } else {
    div.textContent = texto;
  }

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
