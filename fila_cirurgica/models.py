# models.py
from django.db import models
from django.db.models import Case, When, IntegerField, Exists, OuterRef
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from simple_history.models import HistoricalRecords


class Paciente(models.Model):
    SEXO_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Feminino'),
    ]

    nome = models.CharField(max_length=255)
    data_nascimento = models.DateField(blank=True, null=True, verbose_name="Data de nascimento")
    sexo = models.CharField(max_length=1, choices=SEXO_CHOICES, blank=True, null=True)
    telefone_contato_principal = models.CharField(
        max_length=15, verbose_name="Telefone para contato principal", blank=True, null=True
    )
    telefone_contato_secundario = models.CharField(
        max_length=15, verbose_name="Telefone secundário", blank=True, null=True
    )
    nome_responsavel = models.CharField(
        max_length=255, verbose_name="Nome do responsável", blank=True, null=True
    )
    numero_prontuario = models.CharField(
        max_length=20, verbose_name="Número do prontuário", blank=True, null=True
    )

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "paciente"
        verbose_name_plural = "pacientes"


class ProcedimentoAghu(models.Model):
    codigo = models.CharField(max_length=20, unique=True, verbose_name="Código do Procedimento")
    nome = models.CharField(max_length=255, verbose_name="Nome do Procedimento")

    def __str__(self):
        return f"{self.codigo} - {self.nome}"

    class Meta:
        verbose_name = "Procedimento"
        verbose_name_plural = "Procedimentos"


class ProcedimentoSigtap(models.Model):
    codigo = models.CharField(max_length=50, blank=True, null=True)
    nome = models.CharField(max_length=255, blank=True, null=True)
    origem = models.TextField(blank=True, null=True)
    complexidade = models.CharField(max_length=100, blank=True, null=True)
    modalidades = models.TextField(blank=True, null=True)
    instrumento_registro = models.CharField(max_length=255, blank=True, null=True)
    tipo_financiamento = models.CharField(max_length=255, blank=True, null=True)
    valor_ambulatorial_sa = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    valor_ambulatorial_total = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    valor_hospitalar_sp = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    valor_hospitalar_sh = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    valor_hospitalar_total = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    atributo_complementar = models.JSONField(default=list, blank=True, null=True)
    sexo = models.CharField(max_length=50, blank=True, null=True)
    idade_minima = models.IntegerField(blank=True, null=True)
    idade_maxima = models.IntegerField(blank=True, null=True)
    quantidade_maxima = models.IntegerField(blank=True, null=True)
    media_permanencia = models.IntegerField(blank=True, null=True)
    pontos = models.IntegerField(blank=True, null=True)
    cbo = models.JSONField(default=list, blank=True, null=True)

    def __str__(self):
        return f"{self.codigo} - {self.nome}"

    class Meta:
        verbose_name = "Procedimento Sigtap"
        verbose_name_plural = "Procedimentos Sigtap"
        ordering = ["codigo"]


class Especialidade(models.Model):
    cod_especialidade = models.CharField(max_length=10, unique=True)
    nome_especialidade = models.CharField(max_length=255)
    demanda_pedagogica = models.BooleanField(
        verbose_name="Demanda Pedagógica", default=False, null=True
    )

    def __str__(self):
        return self.nome_especialidade


class EspecialidadeProcedimento(models.Model):
    especialidade = models.ForeignKey(Especialidade, on_delete=models.CASCADE)
    procedimento = models.ForeignKey(ProcedimentoAghu, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('especialidade', 'procedimento')
        verbose_name = "Especialidade e Procedimento"
        verbose_name_plural = "Especialidades e Procedimentos"

    def __str__(self):
        return f"{self.especialidade.nome_especialidade} - {self.procedimento.nome}"


class Medico(models.Model):
    matricula = models.CharField(max_length=10, unique=True)
    nome = models.CharField(max_length=255)
    especialidades = models.ManyToManyField(Especialidade, blank=True)

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Médico"
        verbose_name_plural = "Médicos"


class ListaEsperaCirurgicaQuerySet(models.QuerySet):
    def with_prioridade_index(self):
        # subquery que testa se há vínculo com uma especialidade de demanda pedagógica
        demanda_ped_qs = EspecialidadeProcedimento.objects.filter(
            procedimento=OuterRef('procedimento'),
            especialidade__demanda_pedagogica=True
        )

        return self.annotate(
            prioridade_num=Case(
                When(medida_judicial=True, then=0),
                When(prioridade='ONC', then=1),
                When(prioridade='BRE', then=2),
                default=3,
                output_field=IntegerField()
            ),
            demanda_pedagogica_bool=Exists(demanda_ped_qs),
            demanda_pedagogica_num=Case(
                When(demanda_pedagogica_bool=True, then=0),
                default=1,
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
                    'demanda_pedagogica_num',   # depois: demanda pedagógica
                    'data_entrada'              # por fim: ordem de chegada
                )
        )

class ListaEsperaCirurgica(models.Model):
    history = HistoricalRecords(inherit=True)

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

    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE)
    procedimento = models.ForeignKey(ProcedimentoAghu, on_delete=models.CASCADE)
    especialidade = models.ForeignKey(Especialidade, on_delete=models.CASCADE)
    medico = models.ForeignKey(Medico, on_delete=models.CASCADE, blank=True, null=True, verbose_name="Médico")
    data_entrada = models.DateTimeField(auto_now_add=True)
    prioridade = models.CharField(max_length=3, choices=PRIORIDADE_CHOICES, default='SEM')
    medida_judicial = models.BooleanField(default=False, null=True, verbose_name="Medida Judicial")
    situacao = models.CharField(choices=SITUACAO_CHOICES, verbose_name="Situação")
    observacoes = models.CharField(max_length=255, blank=True, null=True, verbose_name="Observações")
    data_novo_contato = models.DateField(blank=True, null=True, verbose_name="Data para novo contato")

    objects = ListaEsperaCirurgicaManager()

    class Meta:
        verbose_name = "Lista de Espera Cirúrgica"
        verbose_name_plural = "Lista de Espera Cirúrgica"

    def __str__(self):
        return f"{self.paciente} esperando {self.procedimento} em {self.especialidade}"

    def clean(self):
        super().clean()
        from .models import EspecialidadeProcedimento
        if not EspecialidadeProcedimento.objects.filter(
            procedimento=self.procedimento,
            especialidade=self.especialidade
        ).exists():
            raise ValidationError({
                'especialidade': _(
                    'Especialidade não associada ao procedimento selecionado.'
                )
            })

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