//codigo da navbar ao rolar a pagina

const nav = document.querySelector('nav')

        document.addEventListener("scroll",e=>{
            if(scrollY>100){
                if(scrollY>window.innerHeight){
                nav.classList.add('invisible')
            }else{

                nav.classList.remove('invisible')
            }
            }
        })


//        codigo navbar responsiva

    //menu do navbar


document.addEventListener('DOMContentLoaded', () => {
    const mobileMenuButton = document.getElementById('mobile-menu-button');
    const mobileMenu = document.getElementById('mobile-menu');
    const iconOpen = document.getElementById('icon-open');
    const iconClose = document.getElementById('icon-close');
    const userMenuButton = document.getElementById('user-menu-button');
    const userMenu = document.getElementById('user-menu');

    // Menu mobile
    mobileMenuButton.addEventListener('click', () => {
      const isExpanded = mobileMenuButton.getAttribute('aria-expanded') === 'true';
      mobileMenuButton.setAttribute('aria-expanded', !isExpanded);
      mobileMenu.classList.toggle('hidden');
      iconOpen.classList.toggle('hidden');
      iconClose.classList.toggle('hidden');
    });

    // Menu do perfil
    userMenuButton.addEventListener('click', () => {
      userMenu.classList.toggle('hidden');
    });

    // Fechar o menu do perfil ao clicar fora
    document.addEventListener('click', (event) => {
      if (!userMenuButton.contains(event.target) && !userMenu.contains(event.target)) {
        userMenu.classList.add('hidden');
      }
    });
});
