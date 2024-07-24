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