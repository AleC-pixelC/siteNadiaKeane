function paginaPrincipal() {
    const mar = document.getElementById("transicaoMar");
    const som = document.getElementById("somMar");

    mar.classList.add("entrando");

    som.volume = 0.5;
    som.play();

    setTimeout(function () {

        const diminuirSom = setInterval(function () {

            if (som.volume > 0.05) {
                som.volume -= 0.05;
            } else {
                som.volume = 0;
                som.pause();
                clearInterval(diminuirSom);
            }
        }, 100);
    }, 7000);

    setTimeout(function () {
        window.location.href = "/inicio";
    }, 8000);
}

document.addEventListener("DOMContentLoaded", function () {
    const botoesSpoiler = document.querySelectorAll(".botaoSpoiler");

    botoesSpoiler.forEach(function (botao) {
        botao.addEventListener("click", function () {
            const texto = botao.nextElementSibling;
            botao.classList.toggle("aberto");
            texto.classList.toggle("aberto");
        });
    });

    inicializarEventosPublicacoes(document);
    inicializarFormNovoPost();
});
 
function anexarEventoCurtir(form) {
    form.addEventListener("submit", function (evento) {
        evento.preventDefault();
        fetch(form.action, {
            method: "POST",
            headers: { "X-Requested-With": "XMLHttpRequest" }
        })
            .then(function (r) { if (!r.ok) throw new Error(); return r.json(); })
            .then(function (dados) {
                form.querySelector(".iconeCurtir").textContent = dados.curtido ? "❤️" : "🤍";
                form.querySelector(".contadorCurtidas").textContent = dados.total;
            })
            .catch(function () {
                alert("Não foi possível curtir agora. Tente novamente.");
            });
    });
}
 
// ---------- Comentar ----------
function anexarEventoComentario(form) {
    form.addEventListener("submit", function (evento) {
        evento.preventDefault();
        const postId = form.dataset.postId;
        const campoTexto = form.querySelector('textarea[name="texto_comentario"]');
        const texto = campoTexto.value;
 
        fetch(form.action, {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded",
                "X-Requested-With": "XMLHttpRequest"
            },
            body: "texto_comentario=" + encodeURIComponent(texto)
        })
            .then(function (r) { if (!r.ok) throw new Error(); return r.json(); })
            .then(function (dados) {
                const listaComentarios = document.getElementById("comentarios-" + postId);
 
                const item = document.createElement("div");
                item.className = "itemComentario";
                if (dados.idComentarios) item.id = "comentario-" + dados.idComentarios;
 
                const paragrafo = document.createElement("p");
                const nomeForte = document.createElement("strong");
                nomeForte.textContent = dados.nomeCadastroUsuario + ": ";
                paragrafo.appendChild(nomeForte);
                paragrafo.appendChild(document.createTextNode(dados.textComentarios));
                item.appendChild(paragrafo);
 
                if (dados.idComentarios) {
                    const formExcluir = document.createElement("form");
                    formExcluir.method = "POST";
                    formExcluir.action = "/excluir_comentario/" + dados.idComentarios;
                    formExcluir.className = "formExcluirComentario";
                    formExcluir.dataset.commentId = dados.idComentarios;
 
                    const botao = document.createElement("button");
                    botao.type = "submit";
                    botao.className = "botaoExcluirComentario";
                    botao.textContent = "Excluir";
                    formExcluir.appendChild(botao);
 
                    anexarEventoExcluirComentario(formExcluir);
                    item.appendChild(formExcluir);
                }
 
                listaComentarios.appendChild(item);
 
                const contador = document.querySelector('.contadorComentarios[data-post-id="' + postId + '"]');
                if (contador) contador.textContent = dados.total;
 
                campoTexto.value = "";
            })
            .catch(function () {
                alert("Não foi possível comentar agora. Tente novamente.");
            });
    });
}
 
// ---------- Excluir post ----------
function anexarEventoExcluirPost(form) {
    form.addEventListener("submit", function (evento) {
        evento.preventDefault();
        const confirmado = confirm("Tem certeza que quer excluir essa publicação?");
        if (!confirmado) return;
 
        const postId = form.dataset.postId;
        fetch(form.action, {
            method: "POST",
            headers: { "X-Requested-With": "XMLHttpRequest" }
        })
            .then(function (r) { if (!r.ok) throw new Error(); return r.json(); })
            .then(function () {
                const cartao = document.getElementById("post-" + postId);
                if (cartao) cartao.remove();
            })
            .catch(function () {
                alert("Não foi possível excluir agora. Tente novamente.");
            });
    });
}
 
function anexarEventoExcluirComentario(form) {
    form.addEventListener("submit", function (evento) {
        evento.preventDefault();
        const confirmado = confirm("Tem certeza que quer excluir esse comentário?");
        if (!confirmado) return;
 
        const commentId = form.dataset.commentId;
        const item = document.getElementById("comentario-" + commentId);
        const listaComentarios = item ? item.closest(".listaComentarios") : null;
        const postId = listaComentarios ? listaComentarios.id.replace("comentarios-", "") : null;
 
        fetch(form.action, {
            method: "POST",
            headers: { "X-Requested-With": "XMLHttpRequest" }
        })
            .then(function (r) { if (!r.ok) throw new Error(); return r.json(); })
            .then(function () {
                if (item) item.remove();
                if (postId) {
                    const contador = document.querySelector('.contadorComentarios[data-post-id="' + postId + '"]');
                    if (contador) contador.textContent = Math.max(0, parseInt(contador.textContent, 10) - 1);
                }
            })
            .catch(function () {
                alert("Não foi possível excluir agora. Tente novamente.");
            });
    });
}
 
function inicializarFormNovoPost() {
    const form = document.getElementById("formNovoPost");
    if (!form) return;
 
    form.addEventListener("submit", function (evento) {
        evento.preventDefault();
        const dadosFormulario = new FormData(form);
 
        fetch(form.action, {
            method: "POST",
            headers: { "X-Requested-With": "XMLHttpRequest" },
            body: dadosFormulario
        })
            .then(function (r) { if (!r.ok) throw new Error(); return r.json(); })
            .then(function () {
                form.reset();
                atualizarMural();
            })
            .catch(function () {
                alert("Não foi possível publicar agora. Tente novamente.");
            });
    });
}
 
function atualizarMural() {
    fetch(window.location.href, { headers: { "X-Requested-With": "XMLHttpRequest" } })
        .then(function (r) { return r.text(); })
        .then(function (html) {
            const parser = new DOMParser();
            const novoDoc = parser.parseFromString(html, "text/html");
            const novaLista = novoDoc.getElementById("listaPublicacoes");
            const listaAtual = document.getElementById("listaPublicacoes");
            if (novaLista && listaAtual) {
                listaAtual.innerHTML = novaLista.innerHTML;
                inicializarEventosPublicacoes(listaAtual);
            }
        });
}
 
function inicializarEventosPublicacoes(raiz) {
    raiz.querySelectorAll(".formCurtir").forEach(anexarEventoCurtir);
    raiz.querySelectorAll(".formComentario").forEach(anexarEventoComentario);
    raiz.querySelectorAll(".formExcluirPost").forEach(anexarEventoExcluirPost);
    raiz.querySelectorAll(".formExcluirComentario").forEach(anexarEventoExcluirComentario);
}