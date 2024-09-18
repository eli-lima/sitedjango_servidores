# seappb/context_processors.py

def user_group(request):
    if request.user.is_authenticated:
        user = request.user

        # Verificando o grupo do usuário
        if user.groups.filter(name='Administrador').exists():
            return {'user_role': 'Administrador'}
        elif user.groups.filter(name='GerGesipe').exists():
            return {'user_role': 'Gerente'}
        elif user.groups.filter(name='SupGesipe').exists():
            return {'user_role': 'Supervisor'}
        elif user.groups.filter(name='CoordGesipe').exists():
            return {'user_role': 'Coordenador'}
        elif user.groups.filter(name='Padrao').exists():
            return {'user_role': 'Servidor'}
        # Adicione mais grupos conforme necessário
    return {'user_role': 'Usuário Padrão'}  # Caso o usuário não esteja logado ou não tenha um grupo específico
