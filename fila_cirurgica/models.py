from django.db import models
import datetime

class Paciente(models.Model):

    SEXO_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Feminino'),
    ]

    nome = models.CharField(max_length=255)  # Nome completo do paciente
    data_nascimento = models.DateField(verbose_name="Data de nascimento")  # Data de nascimento do paciente
    sexo = models.CharField(max_length=1, choices=SEXO_CHOICES)  # Sexo do paciente
    telefone_contato = models.CharField(verbose_name="Telefone para contato principal", max_length=15, blank=True, null=True)  # Telefone principal
    telefone_contato2 = models.CharField(verbose_name="Telefone para contato secundário", max_length=15, blank=True, null=True)  # Telefone secundário
    nome_responsavel = models.CharField(verbose_name="Nome do responsável", max_length=255, blank=True, null=True)  # Nome do responsável
    numero_prontuario = models.CharField(verbose_name= "Número do prontuário", max_length=20)

    def __str__(self):
        return self.nome
    
    class Meta:
        verbose_name = "paciente"
        verbose_name_plural = "pacientes"
    
class Procedimento(models.Model):
    
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
        verbose_name = "Procedimento"
        verbose_name_plural = "Procedimentos"
        ordering = ["codigo"]

class ListaEsperaCirurgica(models.Model):

    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE)
    procedimentos = models.ForeignKey(Procedimento, on_delete=models.CASCADE)
    data_entrada = models.DateTimeField(auto_now_add=True)

    PRIORIDADE_CLINICA_CHOICES = [
        ('P0', 'ONCOLOGIA'),
        ('P1', 'PACIENTES COM ALTA PRIORIDADE'),
        ('SP', 'SEM PRIORIDADE'),
    ]

    prioridade = models.CharField(choices=PRIORIDADE_CLINICA_CHOICES)

    demanda_judicial = models.BooleanField(verbose_name="Demanda Judicial", null=True)

    SITUACAO_CHOICES = [
        ('CA', 'CONSULTA AGENDADA'),
        ('AE', 'AGUARDANDO EXAMES'),
        ('DP', 'DOCUMENTAÇÃO PENDENTE'),
        ('EA', 'EXAMES EM ATRASO'),
        ('PP', 'PACIENTE PRONTO PARA CIRURGIA'),
        ('CA', 'CIRURGIA AGENDADA'),
    ]

    situacao = models.CharField(choices=SITUACAO_CHOICES)

    observacoes = models.CharField(max_length=255, verbose_name="observações", blank=True, null=True)

    data_novo_contato = models.DateField(verbose_name="Data para novo contato")

    class Meta:
        verbose_name = "Lista de Espera Cirúrgica"
        verbose_name_plural = "Listas de Espera Cirúrgica"

    
    pontos = models.IntegerField(default=0, editable=False)

    def save(self, *args, **kwargs):
            
            data_entrada = self.data_entrada.replace(tzinfo=None)
            segundos_totais = data_entrada.timestamp() / 1000
            
            pontos = segundos_totais
            if self.prioridade == 'P0':  # Oncologia
                pontos /= 3
            if self.demanda_judicial:  # Demanda Judicial
                pontos /= 100

            self.pontos = pontos
            super().save(*args, **kwargs)
        