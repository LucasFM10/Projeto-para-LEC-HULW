# models.py
from django.db import models
from django.db.models import Case, When, IntegerField, Exists, OuterRef
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from simple_history.models import HistoricalRecords


class PacienteAghu(models.Model):
    prontuario = models.CharField(
        max_length=20, unique=True, verbose_name="Prontuário do Paciente")
    nome = models.CharField(max_length=255, verbose_name="Nome do Paciente")

    def __str__(self):
        return f"{self.nome} ({self.prontuario})"

    class Meta:
        verbose_name = "Paciente"
        verbose_name_plural = "Pacientes"


class ProcedimentoAghu(models.Model):
    codigo = models.CharField(
        max_length=20, unique=True, verbose_name="Código do Procedimento")
    nome = models.CharField(
        max_length=255, verbose_name="Nome do Procedimento")

    def __str__(self):
        return f"{self.codigo} - {self.nome}"

    class Meta:
        verbose_name = "Procedimento"
        verbose_name_plural = "Procedimentos"


class EspecialidadeAghu(models.Model):
    cod_especialidade = models.CharField(max_length=10, unique=True)
    nome_especialidade = models.CharField(max_length=255)

    def __str__(self):
        return self.nome_especialidade

    class Meta:
        verbose_name = "Especialidade"
        verbose_name_plural = "Especialidades"


class ProfissionalAghu(models.Model):
    matricula = models.CharField(max_length=10, unique=True)
    nome = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.nome} (Matrícula: {self.matricula})"

    class Meta:
        verbose_name = "médico"
        verbose_name_plural = "médicos"


class ListaEsperaCirurgicaQuerySet(models.QuerySet):
    def with_prioridade_index(self):

        return self.annotate(
            prioridade_num=Case(
                When(medida_judicial=True, then=0),
                When(prioridade='ONC', then=1),
                When(prioridade='BRE', then=2),
                default=3,
                output_field=IntegerField()
            ),
        )


class ListaEsperaCirurgicaManager(models.Manager):
    def get_queryset(self):
        return ListaEsperaCirurgicaQuerySet(self.model, using=self._db)

    def ordered(self):
        return (
            self.get_queryset()
                .with_prioridade_index()
                .order_by(
                    'prioridade_num',           # primeiro: medida/clinica
                    'data_entrada'              # por fim: ordem de chegada
            )
        )


class ListaEsperaCirurgica(models.Model):
    history = HistoricalRecords()

    PRIORIDADE_CHOICES = [
        ('ONC', 'Paciente Oncológico'),
        ('BRE', 'Com Brevidade'),
        ('SEM', 'Sem Brevidade'),
    ]

    SITUACAO_CHOICES = [
        ('CA', 'CONSULTA AGENDADA'),
        ('AE', 'EXAMES PENDENTES'),
        ('DP', 'DOCUMENTAÇÃO PENDENTE'),
        ('PP', 'PACIENTE PRONTO PARA CIRURGIA'),
        ('CNR', 'CONTATO NÃO REALIZADO'),
        ('T1F', 'TENTATIVA 1 FALHOU'),
        ('T2F', 'TENTATIVA 2 FALHOU'),
        ('T3F', 'TENTATIVA 3 FALHOU, NÃO SERÃO REALIZADOS NOVOS CONTATOS'),
        ('CRS', 'CONTATO REALIZADO COM SUCESSO'),
    ]

    paciente = models.ForeignKey(PacienteAghu, on_delete=models.CASCADE)
    procedimento = models.ForeignKey(
        ProcedimentoAghu, on_delete=models.CASCADE)
    especialidade = models.ForeignKey(EspecialidadeAghu, on_delete=models.CASCADE)
    medico = models.ForeignKey(
        ProfissionalAghu, on_delete=models.CASCADE, blank=True, null=True, verbose_name="médico")
    data_entrada = models.DateTimeField(auto_now_add=True)
    prioridade = models.CharField(
        max_length=3, choices=PRIORIDADE_CHOICES, default='SEM')
    medida_judicial = models.BooleanField(
        default=False, null=True, verbose_name="Medida Judicial")
    situacao = models.CharField(
        choices=SITUACAO_CHOICES, verbose_name="Situação")
    observacoes = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="Observações")
    data_novo_contato = models.DateField(
        blank=True, null=True, verbose_name="Data para novo contato")

    MOTIVO_SAIDA_CHOICES = [
        ('MORTE', 'Paciente faleceu'),
        ('OUTRO_LOCAL', 'Cirurgia realizada em outro local'),
        ('AUTOEXCLUSAO', 'Paciente solicitou autoexclusão da fila'),
    ]

    ativo = models.BooleanField(
        default=True, verbose_name="Está ativo na fila?")
    motivo_saida = models.CharField(
        max_length=20,
        choices=MOTIVO_SAIDA_CHOICES,
        blank=True,
        null=True,
        verbose_name="Motivo da saída da fila"
    )

    objects = ListaEsperaCirurgicaManager()

    class Meta:
        verbose_name = "Lista de Espera Cirúrgica"
        verbose_name_plural = "Lista de Espera Cirúrgica"

    def __str__(self):
        return f"{self.paciente} esperando {self.procedimento} em {self.especialidade}"

    def get_posicao(self):
        """
        Retorna a posição do objeto na fila, considerando medida judicial e tipo de prioridade.
        """
        qs = type(self).objects.ordered().values_list('id', flat=True)
        return list(qs).index(self.id) + 1


class IndicadorEspecialidade(ListaEsperaCirurgica):
    """
    Proxy model para exibir indicadores de especialidade no admin.
    """
    class Meta:
        proxy = True
        verbose_name = _("Indicadores de Especialidades")
        verbose_name_plural = _("Indicadores de Especialidades")
