from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Sum
from .models import Transacao, Grupo
import random
from django.core.files.storage import default_storage
from ofxparse import OfxParser
import decimal
from decimal import Decimal  # já importado corretamente
from django.contrib.auth.forms import UserCreationForm  # Importa o formulário de criação de usuário padrão do Django
from django.contrib.auth import login
from django.contrib import messages



# Paleta de cores para a foto do usuário com iniciais
PALETA_CORES = ["#E8DAEF", "#D6EAF8", "#D5F5E3", "#FCF3CF", "#FADBD8"]

# View para exibir o painel financeiro do usuário logado
@login_required
def painel(request):
    usuario = request.user

    # Pegue todos os grupos que o usuário faz parte
    grupos = Grupo.objects.filter(membros=usuario)   # Supondo que `grupos` é o relacionamento para os grupos que o usuário pertence

    # Exibe as iniciais do usuário e uma cor de fundo aleatória
    iniciais = "".join([parte[0] for parte in usuario.username.split()][:2]).upper()
    cor_aleatoria = random.choice(PALETA_CORES)

    # Calculando os totais de receitas e despesas
    total_receitas = Transacao.objects.filter(user=usuario, tipo='receita').aggregate(Sum('valor'))['valor__sum'] or Decimal('0.00')
    total_despesas = Transacao.objects.filter(user=usuario, tipo='despesa').aggregate(Sum('valor'))['valor__sum'] or Decimal('0.00')
    total_provisao_receitas = Transacao.objects.filter(user=usuario, tipo='provisao_receita').aggregate(Sum('valor'))['valor__sum'] or Decimal('0.00')
    total_provisao_despesas = Transacao.objects.filter(user=usuario, tipo='provisao_despesa').aggregate(Sum('valor'))['valor__sum'] or Decimal('0.00')

    saldo_total = total_receitas - total_despesas

    # Pegando as próximas 5 receitas e despesas para o usuário logado
    proximas_receitas = Transacao.objects.filter(user=usuario, tipo='receita').order_by('data')[:5]
    proximas_despesas = Transacao.objects.filter(user=usuario, tipo='despesa').order_by('data')[:5]
    proximas_provisoes_receitas = Transacao.objects.filter(user=usuario, tipo='provisao_receita').order_by('data')[:5]
    proximas_provisoes_despesas = Transacao.objects.filter(user=usuario, tipo='provisao_despesa').order_by('data')[:5]

    contexto = {
        'user': usuario,
        'total_receitas': total_receitas,
        'total_despesas': total_despesas,
        'provisao_receita': total_provisao_receitas,
        'provisao_despesa': total_provisao_despesas,
        'saldo_total': saldo_total,
        'proximas_receitas': proximas_receitas,
        'proximas_despesas': proximas_despesas,
        'proximas_prov_receitas': proximas_provisoes_receitas,
        'proximas_prov_despesas': proximas_provisoes_despesas,
        'current_datetime': timezone.now(),
        'grupos': grupos,

        'iniciais': iniciais,
        'cor_aleatoria': cor_aleatoria,
    }

    return render(request, 'gestao_financeiro/painel.html', contexto)

# View para exibir o painel do grupo
@login_required
def painel_grupo(request, grupo_id):

    grupo = get_object_or_404(Grupo, id=grupo_id, membros=request.user)


    # Verifica se o usuário é membro do grupo
    if request.user not in grupo.membros.all():
        return redirect('painel')  # Redireciona para o painel pessoal se não for membro

    # Calcula as somas das transações para todos os membros do grupo
    total_receitas_grupo = grupo.transacoes.filter(tipo='receita').aggregate(Sum('valor'))['valor__sum'] or Decimal('0.00')
    total_despesas_grupo = grupo.transacoes.filter(tipo='despesa').aggregate(Sum('valor'))['valor__sum'] or Decimal('0.00')

    saldo_grupo = total_receitas_grupo -- total_despesas_grupo


    # Transações recentes do grupo
    transacoes_grupo = grupo.transacoes.order_by('-data')[:5]

    contexto = {
        'grupo': grupo,
        'total_receitas_grupo': total_receitas_grupo,
        'total_despesas_grupo': total_despesas_grupo,
        'saldo_grupo': saldo_grupo,
        'transacoes_grupo': transacoes_grupo,
    }
    return render(request, 'gestao_financeiro/painel_grupo.html', contexto)

# View para adicionar uma nova transação associada ao usuário logado
@login_required
def adicionar_transacao(request):
    if request.method == 'POST':
        tipo = request.POST.get('categoria')
        valor = Decimal(request.POST.get('valor'))  # Converte o valor para Decimal
        data = request.POST.get('data')
        descricao = request.POST.get('historico')

        # Verifica se o usuário pertence a um grupo
        grupo = request.user.grupos.first()  # Supondo que o usuário só pode pertencer a um grupo por vez

        # Cria a transação e associa ao grupo (se houver)
        transacao = Transacao(
            user=request.user,
            grupo=grupo,  # Será None se o usuário não estiver em nenhum grupo
            tipo=tipo,
            valor=valor,  # Valor já convertido para Decimal
            data=data,
            descricao=descricao,
        )
        transacao.save()


        return redirect('painel')

    return render(request, 'gestao_financeiro/painel.html')

@login_required
def editar_transacao(request, transacao_id):
    transacao = get_object_or_404(Transacao, id=transacao_id, user=request.user)
    if request.method == 'POST':
        transacao.descricao = request.POST.get('descricao')
        transacao.valor = Decimal(request.POST.get('valor'))
        transacao.data = request.POST.get('data')
        transacao.save()
        return redirect('painel')  # Redireciona para o painel após a edição
    return render(request, 'gestao_financeiro/editar_transacao.html', {'transacao': transacao})

@login_required
def apagar_transacao(request, transacao_id):
    transacao = get_object_or_404(Transacao, id=transacao_id, user=request.user)
    if request.method == 'POST':
        transacao.delete()
        return redirect('painel')  # Redireciona para o painel após exclusão
    return render(request, 'gestao_financeiro/confirmar_exclusao.html', {'transacao': transacao})

# View para criar um novo grupo
@login_required
def criar_grupo(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        grupo = Grupo.objects.create(nome=nome, criador=request.user)
        grupo.membros.add(request.user)  # O criador se torna o primeiro membro do grupo
        return redirect('detalhes_grupo', grupo_id=grupo.id)  # Redireciona para ver o grupo
    return render(request, 'gestao_financeiro/criar_grupo.html')

def detalhes_grupo(request, grupo_id):
    grupo = get_object_or_404(Grupo, id=grupo_id)
    contexto = {'grupo': grupo}
    return render(request, 'gestao_financeiro/detalhes_grupo.html', contexto)


# View para entrar em um grupo com código de acesso
@login_required
def entrar_grupo(request):
    if request.method == 'POST':
        codigo_acesso = request.POST.get('codigo_acesso')
        try:
            grupo = Grupo.objects.get(chave_convite=codigo_acesso)
            grupo.membros.add(request.user)  # Adiciona o usuário como membro do grupo
            return redirect('painel_grupo', grupo_id=grupo.id)
        except Grupo.DoesNotExist:
            return render(request, 'gestao_financeiro/entrar_grupo.html', {'erro': 'Código de acesso inválido'})

    return render(request, 'gestao_financeiro/entrar_grupo.html')

# View para exibir o extrato completo com paginação e agrupamento por data

@login_required
def extrato_completo(request):
    user = request.user
    transacoes = Transacao.objects.filter(user=user).order_by('-data', '-id')

    paginator = Paginator(transacoes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    transacoes_por_dia = {}
    for transacao in page_obj:
        dia = transacao.data
        if dia not in transacoes_por_dia:
            transacoes_por_dia[dia] = []
        transacoes_por_dia[dia].append(transacao)

    context = {
        'transacoes_por_dia': transacoes_por_dia,
        'page_obj': page_obj
    }
    return render(request, 'gestao_financeiro/extrato_completo.html', context)


@login_required
def importar_ofx(request):
    if request.method == 'POST' and request.FILES.get('ofx_file'):
        ofx_file = request.FILES['ofx_file']
        ofx = OfxParser.parse(ofx_file)

        # Identifica o grupo ao qual o usuário pertence, se houver
        grupo = request.user.grupos.first()  # Supondo que o usuário pertence a um único grupo

        for account in ofx.accounts:
            for transaction in account.statement.transactions:
                # Verifica se a transação já existe para evitar duplicação
                if not Transacao.objects.filter(
                    user=request.user,
                    descricao=transaction.memo,
                    valor=Decimal(transaction.amount),
                    data=transaction.date,
                    grupo=grupo
                ).exists():
                    # Cria uma nova transação, associada ao grupo se houver
                    transacao = Transacao(
                        user=request.user,
                        grupo=grupo,  # Associa ao grupo diretamente
                        descricao=transaction.memo,
                        valor=Decimal(transaction.amount),
                        data=transaction.date,
                        tipo='receita' if transaction.amount >= 0 else 'despesa',
                    )
                    transacao.save()

        # Redireciona para o painel do grupo, se o usuário estiver em um
        if grupo:
            return redirect('painel_grupo', grupo_id=grupo.id)
        else:
            return redirect('painel')

    return render(request, 'gestao_financeiro/importar_ofx.html')


def criar_conta(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Login automático após cadastro
            messages.success(request, "Conta criada com sucesso!")
            return redirect('painel')  # Redireciona para o painel após cadastro
    else:
        form = UserCreationForm()

    return render(request, 'gestao_financeiro/criar_conta.html', {'form': form})