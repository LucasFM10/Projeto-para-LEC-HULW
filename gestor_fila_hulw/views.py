import pdfplumber
from django.shortcuts import render
from fila_cirurgica.models import Procedimento
import re
from bs4 import BeautifulSoup

def home(request):
    if request.method == 'POST' and request.FILES.get('file'):
        # Obter o arquivo HTML enviado
        html_file = request.FILES['file']

        procedimentos_criados = processar_html_para_procedimentos(html_file)
        return render(request, 'upload.html')

    return render(request, 'upload.html')

def processar_html_para_procedimentos(html_file):

    # Inicializando as variáveis com valores padrão
    codigo = ''
    nome = ''
    origem = ''
    complexidade = ''
    modalidades = ''
    instrumento_registro = ''
    tipo_financiamento = ''
    valor_ambulatorial_sa = 0.0
    valor_ambulatorial_total = 0.0
    valor_hospitalar_sp = 0.0
    valor_hospitalar_sh = 0.0
    valor_hospitalar_total = 0.0
    atributo_complementar = ''
    sexo = ''
    idade_minima = 0
    idade_maxima = 130
    quantidade_maxima = 0
    media_permanencia = 0
    pontos = 0
    cbo = []

    # Lê o conteúdo do arquivo HTML
    html_content = html_file.read().decode('utf-8')
    
    # Inicializa o BeautifulSoup para processar o HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    
    tabelas = soup.find_all('table', class_='jrPage')

    for tabela in tabelas:
        # Iterar sobre os <tr>
        linhas = tabela.find_all('tr')

        last = ''

        for row in linhas:

            row_text = extrair_texto_de_tr(row)

            if "Procedimento:" in row_text:
                print("\n\n - - - - - - - \n\n")
                partes = row_text.split(":")[1].split("-")
                codigo = partes[0]
                nome = partes[1]

            # Verifica se a linha contém "Origem:"
            match = re.search(r"Origem:(.*?)Origem:", row_text)
            if match:
                print("Origem: " + match.group(1).strip())
                origem = match.group(1).strip()

            if "Complexidade:" in row_text:
                print(row_text)
                complexidade = row_text.split(":")[1]

            match = re.search(r"Modalidade:(.*?)Modalidade:", row_text)
            if match:
                modalidade = match.group(1).strip()
                print("Modalidade: " + match.group(1).strip())

            match = re.search(r"Instrumento de Registro:(.*?)Instrumento de Registro:", row_text)
            if match:
                instrumento_registro = match.group(1).strip()
                print("Instrumentro de Registro: " + match.group(1).strip())

            if "Tipo de Financiamento:" in row_text:
                tipo_financiamento = row_text.split("Tipo de Financiamento:")[1].strip()
                print(row_text)

            if "Valor Ambulatorial S.A.:" in last:
                valor_ambulatorial_sa = extrair_valor(row_text, 'Valor Ambulatorial S.A.:')
                print("Valor Ambulatorial S.A.:" + row_text)

            if "Valor Ambulatorial Total:" in last:
                valor_ambulatorial_total = extrair_valor(row_text, 'Valor Ambulatorial Total:')
                print("Valor  Ambulatorial Total:" + row_text)

            if "Valor Hospitalar S.P.:" in last:
                valor_hospitalar_sp = extrair_valor(row_text, 'Valor Hospitalar S.P.:')
                print("Valor Hospitalar S.P.:" + row_text)

            if "Valor Hospitalar S.H.:" in row_text:
                valor_hospitalar_sh = extrair_valor(row_text, 'Valor Hospitalar S.H.:')
                print(row_text)

            if "Valor Hospitalar Total:" in row_text:
                valor_hospitalar_total = extrair_valor(row_text, 'Valor Hospitalar Total:')
                print(row_text)

            match = re.search(r"Atributo Complementar:(.*?)Atributo Complementar:", row_text)
            if match:
                atributo_complementar = match.group(1).strip()
                print("Atributo Complementar:" + match.group(1).strip())

            if "Sexo:" in row_text:
                sexo = row_text.split("Sexo:")[1].strip()
                print(row_text)

            if "Idade Mínima:" in row_text:
                idade_minima = extrair_idade(row_text, "Mínima")
                print(row_text)

            if "Idade Máxima:" in row_text:
                idade_minima = extrair_idade(row_text, "Mínima")
                print(row_text)

            if "Quantidade Máxima:" in row_text:
                quantidade_maxima = extrair_quantidade_maxima(row_text)
                print(row_text)

            if "Média Permanência:" in row_text:
                media_permanencia = extrair_media_permanencia(row_text)
                print(row_text)

            if "Pontos:" in row_text:
                pontos = extrair_pontos(row_text)
                print(row_text)

            match = re.search(r"CBO:(.*?)CBO:", row_text)
            if match:
                cbo = [x.strip() for x in match.group(1).split(',')]
                print("CBO: " + match.group(1).strip())

            last = row_text

        # Criar o Procedimento no banco de dados
        procedimento = Procedimento.objects.create(
            codigo=codigo,
            nome=nome,
            origem=origem,
            complexidade=complexidade,
            modalidades=modalidades,
            instrumento_registro=instrumento_registro,
            tipo_financiamento=tipo_financiamento,
            valor_ambulatorial_sa=valor_ambulatorial_sa,
            valor_ambulatorial_total=valor_ambulatorial_total,
            valor_hospitalar_sp=valor_hospitalar_sp,
            valor_hospitalar_sh=valor_hospitalar_sh,
            valor_hospitalar_total=valor_hospitalar_total,
            atributo_complementar=atributo_complementar,
            sexo=sexo,
            idade_minima=idade_minima,
            idade_maxima=idade_maxima,
            quantidade_maxima=quantidade_maxima,
            media_permanencia=media_permanencia,
            pontos=pontos,
            cbo=cbo,
        )

        procedimento.save()

def extrair_texto_de_tr(row):     
    cells = row.find_all('td')
    text = ''
    for cell in cells:
        text+= cell.get_text().strip().replace('\n', ' ')
    palavras = text.split()
    text = ' '.join(palavras)
    return text


def extrair_valor(texto, campo):
    match = re.search(rf"{campo}R\$(\d+,\d+)", texto)
    return float(match.group(1).replace(',', '.')) if match else 0.0

def extrair_idade(texto, tipo):
    match = re.search(rf"Idade {tipo}:(\d+)", texto)
    return int(match.group(1)) if match else 0

def extrair_quantidade_maxima(texto):
    match = re.search(r"Quantidade Máxima:(\d+)", texto)
    return int(match.group(1)) if match else 0

def extrair_media_permanencia(texto):
    match = re.search(r"Média Permanência:(\d+)", texto)
    return int(match.group(1)) if match else 0

def extrair_pontos(texto):
    match = re.search(r"Pontos:(\d+)", texto)
    return int(match.group(1)) if match else 0
