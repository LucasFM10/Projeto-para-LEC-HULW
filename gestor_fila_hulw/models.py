from django.db import models
import datetime
from django.db import models

class Paciente(models.Model):

    SEXO_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Feminino'),
    ]

    nome = models.CharField(max_length=255)  # Nome completo do paciente
    data_nascimento = models.DateField(blank=True, null=True, verbose_name="Data de nascimento")  # Data de nascimento do paciente
    sexo = models.CharField(blank=True, null=True, max_length=1, choices=SEXO_CHOICES)  # Sexo do paciente
    telefone_contato_principal = models.CharField(blank=True, null=True, verbose_name="Telefone para contato principal", max_length=15)  # Telefone principal
    telefone_contato_secundario = models.CharField(blank=True, null=True, verbose_name="Telefone para contato secundário", max_length=15)  # Telefone secundário
    nome_responsavel = models.CharField(blank=True, null=True, verbose_name="Nome do responsável", max_length=255)  # Nome do responsável
    numero_prontuario = models.CharField(blank=True, null=True, verbose_name= "Número do prontuário", max_length=20)

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
    atributo_complementar = models.JSONField(default=list, blank=True, null=True)  # Usando JSONField para armazenar lista de atributos
    sexo = models.CharField(max_length=50, blank=True, null=True)
    idade_minima = models.IntegerField(blank=True, null=True)
    idade_maxima = models.IntegerField(blank=True, null=True)
    quantidade_maxima = models.IntegerField(blank=True, null=True)
    media_permanencia = models.IntegerField(blank=True, null=True)
    pontos = models.IntegerField(blank=True, null=True)
    cbo = models.JSONField(default=list, blank=True, null=True)  # Usando JSONField para armazenar lista de CBOs


    def __str__(self):
        return f"{self.codigo} - {self.nome}"

    class Meta:
        verbose_name = "Procedimento Sigtap"
        verbose_name_plural = "Procedimentos Sigtap"
        ordering = ["codigo"]

class Especialidade(models.Model):
    cod_especialidade = models.CharField(max_length=10, unique=True)
    nome_especialidade = models.CharField(max_length=255)

    def __str__(self):
        return self.nome_especialidade
    
class EspecialidadeProcedimento(models.Model):
    especialidade = models.ForeignKey(Especialidade, on_delete=models.CASCADE)
    procedimento = models.ForeignKey(ProcedimentoAghu, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('especialidade', 'procedimento')  # Garante que não haja duplicatas
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

class Situacao(models.Model):
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

    tipo = models.CharField(max_length=5, choices=SITUACAO_CHOICES, unique=True, verbose_name="Situação")
    observacao = models.TextField(blank=True, null=True, verbose_name="Observação")

    def __str__(self):
        return dict(self.SITUACAO_CHOICES).get(self.tipo, "Desconhecido")

class ListaEsperaCirurgica(models.Model):

    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE)
    procedimento = models.ForeignKey(ProcedimentoAghu, on_delete=models.CASCADE, blank=True, null=True)
    medico = models.ForeignKey(Medico, on_delete=models.CASCADE, blank=True, null=True)
    
    data_entrada = models.DateTimeField(auto_now_add=True)

    # PRIORIDADE_CLINICA_CHOICES = [
    #     ('P0', 'ONCOLOGIA'),
    #     ('P1', 'PACIENTES COM ALTA PRIORIDADE'),
    #     ('SP', 'SEM PRIORIDADE'),
    # ]

    # prioridade = models.CharField(choices=PRIORIDADE_CLINICA_CHOICES)

    # demanda_judicial = models.BooleanField(verbose_name="Demanda Judicial", null=True)

    observacoes = models.CharField(max_length=255, verbose_name="observações", blank=True, null=True)

    data_novo_contato = models.DateField(verbose_name="Data para novo contato")

    class Meta:
        verbose_name = "Lista de Espera Cirúrgica"
        verbose_name_plural = "Lista de Espera Cirúrgica"
        ordering = ['data_entrada']


    def __str__(self):
        return f"{self.paciente}"# esperando para {self.especialidadeprocedimento.procedimento}"
    
    def get_posicao(self):
        # Obtém a posição do paciente na fila ordenada
        return list(ListaEsperaCirurgica.objects.order_by('data_entrada').values_list('id', flat=True)).index(self.id) + 1

    get_posicao.short_description = "Posição na Fila"  # Nome da coluna no Django Admin
    
    # pontos = models.IntegerField(default=0, editable=False)

    # def save(self, *args, **kwargs):
            
    #         data_entrada = self.data_entrada.replace(tzinfo=None)
    #         data_entrada = data_entrada

    #         datetime_str = '11/30/24 00:00:00'
    #         datetime_object = datetime.datetime.strptime(datetime_str, '%m/%d/%y %H:%M:%S')

    #         data_entrada = data_entrada - datetime_object
            
    #         print(f'{data_entrada} - {data_entrada.total_seconds()}')

    #         segundos_totais = data_entrada.total_seconds()
            
    #         pontos = segundos_totais
    #         if self.prioridade == 'P0':  # Oncologia
    #             pontos /= 3
    #         if self.demanda_judicial:  # Demanda Judicial
    #             pontos /= 100

    #         self.pontos = pontos
    #         super().save(*args, **kwargs)
        