# seappb/context_processors.py

def user_group(request):
    if request.user.is_authenticated:
        user = request.user
        # Obter todos os grupos do usuário
        user_groups = user.groups.values_list('name', flat=True)

        # Definir o papel principal (role) com base nos grupos
        if 'Administrador' in user_groups:
            user_role = 'Administrador'
        elif 'GerGesipe' in user_groups:
            user_role = 'Gerência Gesipe'
        elif 'GerRh' in user_groups:
            user_role = 'Gerência Recursos Humanos'
        elif 'CoordGesipe' in user_groups:
            user_role = 'Coordenador'
        elif 'Padrao' in user_groups:
            user_role = 'Servidor'
        else:
            user_role = 'Usuário Padrão'

        return {
            'user_groups': list(user_groups),  # Retorna todos os grupos do usuário
            'user_role': user_role  # Retorna o papel principal
        }

    return {
        'user_groups': [],  # Caso o usuário não esteja logado ou não tenha grupos
        'user_role': 'Usuário Padrão'  # Papel padrão para usuários não autenticados
    }
