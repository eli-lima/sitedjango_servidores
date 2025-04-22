// Código da navbar ao rolar a página
const nav = document.querySelector('nav');

document.addEventListener("scroll", e => {
    // Verifica se é mobile (telas menores que 768px)
    if (window.innerWidth < 768) {
        if (scrollY > 100) {
            if (scrollY > window.innerHeight) {
                nav.classList.add('invisible');
            } else {
                nav.classList.remove('invisible');
            }
        }
    }
    // Em desktop não faz nada - navbar sempre visível
});





//script editar pelas tabela do site



document.querySelectorAll('.clickable-row').forEach(row => {
    row.addEventListener('click', () => {
        // Verifica se o atributo data-href existe e se tem um valor
        const href = row.getAttribute('data-href');
        if (href) {
            window.location.href = href;
        }
    });
});


//script rolar a pagina ao mudar os pages

window.onload = function() {
        // Verifica se a URL contém o parâmetro 'page'
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.has('page')) {
            // Rola até a div com id 'paginacao'
            document.getElementById('paginacao').scrollIntoView({ behavior: 'smooth' });
        }
    };