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

    // abre a página depois da animação
    setTimeout(function () {
        window.location.href = "paginaPrincipal.html";
    }, 8000);
}