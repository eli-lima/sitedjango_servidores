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





//script editar pelas tabela do site


<script>
    document.querySelectorAll('.clickable-row').forEach(row => {
        row.addEventListener('click', () => {
            window.location.href = row.getAttribute('data-href');
        });
    });
</script>