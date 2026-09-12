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
});