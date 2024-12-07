from django.db import models

class Paciente(models.Model):
    SEXO_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Feminino'),
        ('O', 'Outro'),
    ]

    nome = models.CharField(max_length=255)  # Nome completo do paciente
    data_nascimento = models.DateField()  # Data de nascimento do paciente
    sexo = models.CharField(max_length=1, choices=SEXO_CHOICES)  # Sexo do paciente
    prontuario = models.CharField(max_length=20, unique=True)  # Número único do prontuário
    telefone_contato = models.CharField(max_length=15, blank=True, null=True)  # Telefone principal
    telefone_contato2 = models.CharField(max_length=15, blank=True, null=True)  # Telefone secundário
    nome_responsavel = models.CharField(max_length=255, blank=True, null=True)  # Nome do responsável

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