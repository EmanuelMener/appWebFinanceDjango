from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Sum
from decimal import Decimal
from .models import Transacao, Grupo
import random

# Paleta de cores para a foto do usuário com iniciais
PALETA_CORES = ["#E8DAEF", "#D6EAF8", "#D5F5E3", "#FCF3CF", "#FADBD8"]

# View para exibir o painel financeiro do usuário logado
@login_required
def painel(request):
    usuario = request.user

    # Calculando os totais de receitas e despesas apenas para o usuário logado
    total_receitas = Transacao.objects.filter(user=usuario, tipo='receita').aggregate(Sum('valor'))['valor__sum'] or Decimal('0.00')
    total_despesas = Transacao.objects.filter(user=usuario, tipo='despesa').aggregate(Sum('valor'))['valor__sum'] or Decimal('0.00')
    total_provisao_receitas = Transacao.objects.filter(user=usuario, tipo='provisao_receita').aggregate(Sum('valor'))['valor__sum'] or Decimal('0.00')
    total_provisao_despesas = Transacao.objects.filter(user=usuario, tipo='provisao_despesa').aggregate(Sum('valor'))['valor__sum'] or Decimal('0.00')

    # Pegando as próximas 5 receitas e despesas para o usuário logado
    proximas_receitas = Transacao.objects.filter(user=usuario, tipo='receita').order_by('data')[:5]
    proximas_despesas = Transacao.objects.filter(user=usuario, tipo='despesa').order_by('data')[:5]

    # Exibir as iniciais do usuário e uma cor de fundo aleatória
    iniciais = "".join([parte[0] for parte in usuario.username.split()][:2]).upper()
    cor_aleatoria = random.choice(PALETA_CORES)

    contexto = {
        'user': usuario,
        'current_datetime': timezone.now(),
        'total_receitas': total_receitas,
        'total_despesas': total_despesas,
        'total_provisao_receitas': total_provisao_receitas,
        'total_provisao_despesas': total_provisao_despesas,
        'proximas_receitas': proximas_receitas,
        'proximas_despesas': proximas_despesas,
        'iniciais': iniciais,
        'cor_aleatoria': cor_aleatoria,
    }

    return render(request, 'gestao_financeiro/painel.html', contexto)

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

        # Redireciona com grupo_id se o usuário pertence a um grupo
        if grupo:
            return redirect('painel_grupo', grupo_id=grupo.id)
        else:
            return redirect('painel')

    return render(request, 'gestao_financeiro/painel.html')

# View para criar um novo grupo
@login_required
def criar_grupo(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        grupo = Grupo.objects.create(nome=nome, criador=request.user)
        grupo.membros.add(request.user)  # O criador se torna o primeiro membro do grupo
        return redirect('painel_grupo', grupo_id=grupo.id)

    return render(request, 'gestao_financeiro/criar_grupo.html')

# View para exibir o painel do grupo
@login_required
def painel_grupo(request, grupo_id):
    grupo = get_object_or_404(Grupo, id=grupo_id)

    # Verifica se o usuário é membro do grupo
    if request.user not in grupo.membros.all():
        return redirect('painel')  # Redireciona para o painel pessoal se não for membro

    # Calcula as somas das transações para todos os membros do grupo
    total_receitas_grupo = grupo.transacoes.filter(tipo='receita').aggregate(Sum('valor'))['valor__sum'] or Decimal('0.00')
    total_despesas_grupo = grupo.transacoes.filter(tipo='despesa').aggregate(Sum('valor'))['valor__sum'] or Decimal('0.00')
    saldo_grupo = total_receitas_grupo - total_despesas_grupo

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

# View para entrar em um grupo com código de acesso
@login_required
def entrar_grupo(request):
    if request.method == 'POST':
        codigo_acesso = request.POST.get('codigo_acesso')
        try:
            grupo = Grupo.objects.get(codigo_acesso=codigo_acesso)
            grupo.membros.add(request.user)  # Adiciona o usuário como membro do grupo
            return redirect('painel_grupo', grupo_id=grupo.id)
        except Grupo.DoesNotExist:
            return render(request, 'gestao_financeiro/entrar_grupo.html', {'erro': 'Código de acesso inválido'})

    return render(request, 'gestao_financeiro/entrar_grupo.html')

# View para exibir o extrato completo com paginação e agrupamento por data
@login_required
def extrato_completo(request):
    user = request.user
    transacoes = Transacao.objects.filter(user=user).order_by('data', 'id')

    # Paginação - definindo 10 transações por página
    paginator = Paginator(transacoes, 10)  # Altere o número para ajustar o limite de lançamentos
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    transacoes_por_dia = {}
    saldo_acumulado = Decimal('0.00')

    for transacao in page_obj:
        # Atualiza o saldo acumulado com base no tipo da transação
        if transacao.tipo.lower() == 'receita':
            saldo_acumulado += transacao.valor
        elif transacao.tipo.lower() == 'despesa':
            saldo_acumulado -= transacao.valor

        # Atribui o saldo acumulado para exibição
        transacao.saldo = saldo_acumulado

        # Agrupa transações por dia
        dia = transacao.data if transacao.data else None
        if dia not in transacoes_por_dia:
            transacoes_por_dia[dia] = []
        transacoes_por_dia[dia].append(transacao)

    # Remove entradas com chave None
    transacoes_por_dia = {k: v for k, v in transacoes_por_dia.items() if k is not None}

    # Ordena o dicionário de transações_por_dia em ordem decrescente
    transacoes_por_dia = dict(sorted(transacoes_por_dia.items(), reverse=True))

    context = {
        'transacoes_por_dia': transacoes_por_dia,
        'page_obj': page_obj
    }
    return render(request, 'gestao_financeiro/extrato_completo.html', context)
