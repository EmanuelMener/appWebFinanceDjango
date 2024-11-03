from django.db import models
from django.contrib.auth.models import User
import uuid



class Grupo(models.Model):
    nome = models.CharField(max_length=100)
    criador = models.ForeignKey(User, on_delete=models.CASCADE, related_name='grupos_criados')
    membros = models.ManyToManyField(User, related_name='grupos')
    chave_convite = models.UUIDField(default=uuid.uuid4, unique=True)  # Gera uma chave única

    def __str__(self):
        return self.nome

class Transacao(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    grupo = models.ForeignKey(Grupo, on_delete=models.CASCADE, null=True, blank=True, related_name="transacoes")

    TIPO_CHOICES = [
        ('receita', 'Receita'),
        ('despesa', 'Despesa'),
        ('provisao_receita', 'Provisão Receita'),
        ('provisao_despesa', 'Provisão Despesa'),
    ]
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    descricao = models.CharField(max_length=255)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    data = models.DateField()


    # Novo campo para armazenar o saldo acumulado
    saldo = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    importado_ofx = models.BooleanField(default=False)  # Novo campo para indicar importação OFX

    def save(self, *args, **kwargs):
        # Pega a última transação para calcular o saldo
        ultima_transacao = Transacao.objects.filter(user=self.user, grupo=self.grupo).exclude(id=self.id).order_by(
            '-data', '-id').first()

        # Se é uma receita, soma ao saldo anterior; se é despesa, subtrai
        if ultima_transacao:
            if self.tipo == 'receita':
                self.saldo = ultima_transacao.saldo + self.valor
            elif self.tipo == 'despesa':
                self.saldo = ultima_transacao.saldo - self.valor
            else:
                self.saldo = ultima_transacao.saldo
        else:
            # Se não há transação anterior, define o saldo inicial como o valor da transação
            self.saldo = self.valor if self.tipo == 'receita' else -self.valor

        # Salva a transação com o saldo atualizado
        super(Transacao, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.descricao} - {self.valor} ({self.tipo})"
