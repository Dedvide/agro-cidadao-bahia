/* Painel de Metas ABC+ — consome /abc/metas (mesma origem, servido por /app). */

async function carregar() {
  let d;
  try { d = await fetch("/abc/metas").then((r) => r.json()); }
  catch (e) { document.getElementById("aviso-api").style.display = "block"; return; }

  document.getElementById("proj").textContent = d.projeto;
  metas(d.metas);
  bioma(d.propriedades_por_bioma, d.uds_por_bioma);
}

function corPct(p) {
  if (p >= 100) return "#1b7a3d";
  if (p >= 50) return "#2e86c1";
  if (p >= 20) return "#e67e22";
  return "#c0392b";
}

function metas(linhas) {
  document.getElementById("metas").innerHTML = linhas.map((m) => {
    const aoVivo = m.fonte.includes("vivo");
    const w = Math.min(100, m.pct);
    return `<div class="meta-card">
      <div class="meta-top"><b>${m.meta}</b>
        <span class="pill" style="background:${aoVivo ? "#1b7a3d" : "#7f8c8d"}">${m.fonte}</span></div>
      <div class="meta-num"><span class="meta-atual">${m.atual}</span>
        <span class="meta-alvo">/ ${m.alvo} ${m.unidade}</span></div>
      <div class="meta-bar"><div class="meta-fill" style="width:${w}%;background:${corPct(m.pct)}"></div></div>
      <div class="meta-pct">${m.pct}% da meta</div>
    </div>`;
  }).join("");
}

function bioma(porBioma, uds) {
  document.getElementById("bioma").innerHTML = Object.entries(porBioma).map(([b, n]) =>
    `<div class="linha-campo"><b>${b}</b> <span class="meta">${n} propriedade(s)</span></div>`).join("");
  document.getElementById("uds").innerHTML = Object.entries(uds).map(([b, n]) => {
    const ok = n >= 1;
    return `<div class="linha-campo"><b>${b}</b>
      <span style="color:${ok ? "#1b7a3d" : "#c0392b"};font-weight:600">${n}/1 UD</span></div>`;
  }).join("") || "<p class='hint'>—</p>";
}

carregar();
