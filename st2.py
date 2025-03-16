import os
import sys
import subprocess
import webbrowser
import time
import requests
import socket
import psutil
import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import numpy as np
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

# Caminho para o arquivo config.toml
def resource_path(relative_path):
    """Get the absolute path to the resource, works for dev and for PyInstaller."""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# Carregar o arquivo config.toml
config_path = resource_path("config.toml")
os.environ["STREAMLIT_CONFIG_FILE"] = config_path  # Forçar o Streamlit a usar este arquivo de configuração

# Função para encontrar uma porta livre
def find_free_port():
    """Find a free port automatically."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))  # Encontra uma porta disponível automaticamente
        return s.getsockname()[1]

STREAMLIT_PORT = find_free_port()
STREAMLIT_URL = f"http://localhost:{STREAMLIT_PORT}"

# Verificar se a porta está em uso
def is_port_in_use(port):
    """Check if a specific port is already in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

# Verificar se o Streamlit já está em execução
def is_streamlit_running():
    """Check if Streamlit is already running using psutil."""
    for proc in psutil.process_iter(attrs=['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info.get('cmdline')
            if cmdline and 'streamlit' in cmdline:
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return False

# Função para abrir o navegador quando o Streamlit estiver pronto
def open_browser_once():
    """Opens the browser only once after the server is ready."""
    try:
        # Esperar o servidor iniciar (máximo de 15 segundos)
        for _ in range(15):
            try:
                response = requests.get(STREAMLIT_URL)
                if response.status_code == 200:
                    webbrowser.open(STREAMLIT_URL, new=2)  # Abrir em uma nova aba
                    logging.info("Navegador aberto com sucesso.")
                    return
            except requests.ConnectionError:
                time.sleep(1)  # Tentar novamente após 1 segundo
        logging.warning(f"Servidor não está pronto a tempo. Acesse manualmente: {STREAMLIT_URL}")
    except Exception as e:
        logging.error(f"Erro ao abrir o navegador: {e}")

# Lógica principal para evitar múltiplas janelas
if __name__ == "__main__":
    if not is_streamlit_running():
        # Iniciar o aplicativo Streamlit
        subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", os.path.abspath(__file__), "--server.port", str(STREAMLIT_PORT)]
        )
        open_browser_once()
    else:
        logging.info("O Streamlit já está em execução. Não é necessário iniciar outra instância.")
        
#Código separado em definitions para facilitar o processo e entrecruzamento na seleção de páginas
#Primeiro definição de constantes e de informações relevantes
RELEVANT_MICROORGANISMS = [
    "Acinetobacter baumannii", "Citrobacter species", "Enterobacter species",
    "Escherichia coli", "Klebsiella oxytoca", "Klebsiella pneumoniae",
    "Morganella morganii", "Pseudomonas aeruginosa", "Proteus mirabilis",
    "Serratia marcescens", "Salmonella species", "Providencia species",
    "Haemophilus influenzae", "Enterococcus faecalis", "Enterococcus faecium",
    "Streptococcus agalactiae", "Staphylococcus aureus", "Staphylococcus epidermidis",
    "Streptococcus pneumoniae", "Staphylococcus saprophyticus"
]

GRAM_POSITIVE = [
    "Enterococcus faecalis", "Enterococcus faecium", "Streptococcus agalactiae",
    "Staphylococcus aureus", "Staphylococcus epidermidis", "Streptococcus pneumoniae",
    "Staphylococcus saprophyticus"
]

GRAM_NEGATIVE = [
    "Acinetobacter baumannii", "Citrobacter species", "Enterobacter species",
    "Escherichia coli", "Klebsiella oxytoca", "Klebsiella pneumoniae",
    "Morganella morganii", "Pseudomonas aeruginosa", "Proteus mirabilis",
    "Serratia marcescens", "Salmonella species", "Providencia species",
    "Haemophilus influenzae"
]

ANTIBIOTICS = [
    "Amicacina", "Amoxicillina/Ac. Clavulânico", "Ampicillina", "Ampicillina/sulbactam",
    "Aztreonam", "Cefepima", "Cefotaxima", "Ceftazidima", "Ceftriaxone", "Cefuroxima",
    "Cefuroxima - Axetil", "Cefuroxima - Sódica", "Cloranfenicol", "Ciprofloxacina",
    "Clindamicina", "Doxycycline", "Eritromicina", "Fosfomicina", "Ácido Fusídico",
    "Gentamicina", "Gentamicina (alta concentr.)", "Imipenem", "Meropenem",
    "Nitrofurantoína", "Oxacillin MIC", "Penicillina", "Piperacillina/tazobactam",
    "Rifampicina", "Estreptomicina (alta concentr.)", "Teicoplanina", "Tetraciclina",
    "Tobramicina", "Cotrimoxazol", "Vancomicina", "Levofloxacina",
    "Quinupristina/Dalfopristina", "Oxacillina", "Mupirocina", "Linezolid",
    "Tigeciclina", "Ertapenem", "Fluconazol", "Anfotericina B", "Amoxicilina",
    "Moxifloxacina", "ESBL", "Beta Lactamase", "Colistina", "Caspofungina",
    "Voricanazol", "Micafungina", "Benzylpenicilina", "Ceftolozane/Tazobactam",
    "Etambutol", "Isoniazida", "Estreptomicina", "Pirazinamida", "Daptomicina",
    "ESBL (Neg)", "Amphotericin B", "Ceftazidime/Avibactam",
    "Amoxicillina/Ac. Clavulânico (oral)", "Amoxicillina/Ac. Clavulânico (intravenoso)",
    "Gentamicina (tópico)", "Imipenem/Relebactam"
]
eskape_microorganisms = ["Enterococcus faecium", "Staphylococcus aureus", "Klebsiella pneumoniae", 
                             "Acinetobacter baumannii", "Pseudomonas aeruginosa", "Enterobacter spp."]

CARBAPENEMES = [
    'Imipenem',
    'Meropenem',
    'Ertapenem',
    'Doripenem'
]

ANTI_MRSA = [
    'Vancomicina',
    'Linezolid',
    'Daptomicina',
    'Ceftarolina',
    'Tigeciclina'
]

POLIMIXINAS = [
    'Polimixina B',
    'Colistina']

CEFALOSPORINAS_3A_4A = [
    'Cefotaxima',
    'Ceftriaxona',
    'Ceftazidima',
    'Cefepima'
]

AMOXICILINA_ACIDO_CLAVULANICO = [
    'Amoxicilina + Ácido clavulânico',
    'Amoxicilina'
]

FLUOROQUINOLONAS = [
    'Ciprofloxacina',
    'Levofloxacina',
    'Moxifloxacina']

FLUOROQUINOLONAS = [
    'Ciprofloxacina',
    'Levofloxacina',
    'Moxifloxacina'
]

AMINOGLICOSIDEOS = [
    'Amicacina',
    'Gentamicina',
    'Gentamicina (alta concentr.)',
    'Tobramicina'
]

BETA_LACTAMICOS_INIBIDORES = [
    'Amoxicillina/Ac. Clavulânico',
    'Ampicillina/sulbactam',
    'Piperacillina/tazobactam',
    'Ceftolozane/Tazobactam',
    'Ceftazidime/Avibactam',
    'Imipenem/Relebactam'
]




ANTIBIOTIC_CLASSES = {
    "Aminoglicosídeos": ["Amicacina", "Gentamicina", "Gentamicina (alta concentr.)", "Tobramicina"],
    "Beta-lactâmicos": ["Amoxicillina/Ac. Clavulânico", "Ampicillina", "Ampicillina/sulbactam", "Aztreonam",
                        "Cefepima", "Cefotaxima", "Ceftazidima", "Ceftriaxona", "Cefuroxima", "Cefuroxima - Axetil",
                        "Cefuroxima - Sódica", "Oxacillin MIC", "Oxacillina", "Penicillina", "Piperacillina/tazobactam",
                        "Imipenem", "Meropenem", "Ertapenem", "Ceftolozane/Tazobactam", "Ceftazidime/Avibactam",
                        "Imipenem/Relebactam"],
    "Glicopeptídeos": ["Teicoplanina", "Vancomicina"],
    "Lincosamidas": ["Clindamicina"],
    "Macrolídeos": ["Eritromicina"],
    "Quinolonas": ["Ciprofloxacina", "Levofloxacina", "Moxifloxacina"],
    "Sulfamidas": ["Cotrimoxazol"],
    "Tetraciclinas": ["Tetraciclina", "Doxycycline"],
    "Outros": ["Cloranfenicol", "Fosfomicina", "Ácido Fusídico", "Rifampicina", "Estreptomicina (alta concentr.)",
               "Linezolid", "Tigeciclina", "Fluconazol", "Anfotericina B", "Mupirocina", "Colistina", "Caspofungina",
               "Voricanazol", "Micafungina", "Etambutol", "Isoniazida", "Estreptomicina", "Pirazinamida", "Daptomicina"],
    **{antibiotic: 'Carbapenemes' for antibiotic in CARBAPENEMES},
    **{antibiotic: 'Anti-MRSA' for antibiotic in ANTI_MRSA},
    **{antibiotic: 'Polimixina' for antibiotic in POLIMIXINAS},
    **{antibiotic: 'Cefalosporina (3ª/4ª Geração)' for antibiotic in CEFALOSPORINAS_3A_4A},
    **{antibiotic: 'Amoxicilina/Ácido Clavulânico' for antibiotic in AMOXICILINA_ACIDO_CLAVULANICO},
    **{antibiotic: 'Fluoroquinolona' for antibiotic in FLUOROQUINOLONAS}
}


def read_data(uploaded_file):
    """Ler e processar dados do Excel."""
    try:
        df = pd.read_excel(uploaded_file)
        sensitive_columns = ['Nº Benef.', 'Nº SNS', 'Data Nasc.', 'Nome']
        df.drop(columns=sensitive_columns, errors='ignore', inplace=True)
        return df, None
    except Exception as e:
        return None, str(e)


def df_clean(df):
    """Limpar e dispor os dados removendo as colunas com informação privada, modificar as datas, disposição e expor filtros."""
    try:
        # Convertendo a coluna 'Data Colheita' para datetime
        df['Data Colheita'] = pd.to_datetime(df['Data Colheita'], format='%d/%m/%Y', errors='coerce')
        df.sort_values(by=['Nº Processo', 'Microorganismo', 'Data Colheita'], inplace=True)
        
        # Combinando colunas de antibióticos em uma única string
        df['Antibiotics'] = df.iloc[:, 23:].apply(lambda row: '_'.join(row.astype(str)), axis=1)
        
        # Calculando a diferença de dias entre as colheitas
        df['Difference'] = df.groupby(['Nº Processo', 'Microorganismo'])['Data Colheita'].diff().abs().dt.days
        
        # Máscara para identificar duplicados
        mask = (df['Difference'] <= 15) & df.duplicated(['Nº Processo', 'Microorganismo', 'Antibiotics'], keep=False)
        
        # DataFrame de duplicados
        df_duplicates = df.loc[mask]
        
        # Mantendo apenas uma ocorrência de cada duplicado
        df_no_duplicates = df.drop_duplicates(subset=['Nº Processo', 'Microorganismo', 'Antibiotics', 'Data Colheita'], keep='first')
        
        # Contagem antes e depois da remoção de duplicados
        before_count = df.shape[0]
        after_count = df_no_duplicates.shape[0]
        unique_microorganisms_before = df['Microorganismo'].nunique()
        unique_microorganisms_after = df_no_duplicates['Microorganismo'].nunique()
        
        st.write(f"Número de casos antes da remoção de duplicados: {before_count}")
        st.write(f"Número de casos após a remoção de duplicados com o mesmo número de processo, num intervalo de 15 dias: {after_count}")
        st.write(f"Número de duplicados removidos: {before_count - after_count}")
        st.write(f"Quantidade de microorganismos antes da remoção de duplicados: {unique_microorganisms_before}")
        st.write(f"Quantidade de microorganismos depois da remoção de duplicados: {unique_microorganisms_after}")

        # Criar e exibir a legenda
        legend_html = """
        <div style="display: inline-block; margin-top: 10px;">
            <div style="background-color: lightblue; width: 15px; height: 15px; display: inline-block; margin-right: 5px;"></div>
            <span>Menos de 40% de estirpes resistentes</span>
        </div><br>
        <div style="display: inline-block; margin-top: 10px;">
            <div style="background-color: lightgoldenrodyellow; width: 15px; height: 15px; display: inline-block; margin-right: 5px;"></div>
            <span>40% a 80% de estirpes resistentes</span>
        </div><br>
        <div style="display: inline-block; margin-top: 10px;">
            <div style="background-color: lightcoral; width: 15px; height: 15px; display: inline-block; margin-right: 5px;"></div>
            <span>Mais de 80% de estirpes resistentes</span>
        </div>
        """

        st.write(" Legenda de Resistência :")
        st.markdown(legend_html, unsafe_allow_html=True)

        return df_no_duplicates, df_duplicates
    except Exception as e:
        st.error(f"Erro durante a limpeza dos dados: {e}")
        return df, pd.DataFrame()
    

def check_duplicates(df):
    """Permitir o utilizador rever os duplicados aquando da sua existência."""
    if not df.empty:
        if st.checkbox("Revisão dos duplicados"):
            st.write(df[df.duplicated(['Nº Processo', 'Microorganismo', 'Antibiotics'], keep=False)])

def classify_gram_stain(microorganismo):
    """Classificar microorganismos como Gram-positivo ou Gram-negativo."""
    if microorganismo in GRAM_POSITIVE:
        return 'Gram-Positivo'
    elif microorganismo in GRAM_NEGATIVE:
        return 'Gram-Negativo'
    else:
        return 'Unknown'

def detect_antibiotic_columns(df):
    """Dynamically identify columns that are likely to contain antibiotic data based on a predefined list."""
    return [col for col in df.columns if col in ANTIBIOTICS]




def create_antibiotic_legend():
    """Legenda para os antibióticos e as suas classes."""
    legend_data = []
    for category, antibiotics in ANTIBIOTIC_CLASSES.items():
        for antibiotic in antibiotics:
            legend_data.append({"Class": category, "Antibiotic": antibiotic})
    legend_df = pd.DataFrame(legend_data)
    st.write("### Legenda de Antibióticos")
    st.dataframe(legend_df)


def show_resistance_profile(df_cleaned):
    """Exibir o perfil de resistências com base na seleção do Gram e do microorganimo."""
    gram_stains = df_cleaned.index.get_level_values('Gram_Stain').unique()
    selected_gram = st.selectbox('Selecionar Coloração Gram :', gram_stains)
    microorganisms = df_cleaned.loc[selected_gram].index.get_level_values('Microorganismo').unique()
    selected_microorganism = st.selectbox('Selecionar Microorganismo:', microorganisms)
    filtered_df = df_cleaned.loc[(selected_gram, selected_microorganism)]

    st.write(f"Perfil de Resistência para {selected_microorganism} ({selected_gram}):")
    if not filtered_df.empty:
        st.dataframe(filtered_df.style.applymap(highlight_resistance))
    else:
        st.write("No data available for the selected microorganism.")

def classify_resistance(value):
    """Classifica a percentagem da resistência em categorias."""
    if value < 40:
        return 'Menos de 40% de estirpes resistentes'
    elif value > 80:
        return 'Mais de 80% de estirpes resistentes'
    elif 40 <= value <= 80:
        return '40% a 80% de estirpes resistentes'
    else:
        return 'Resistências naturais'


def classify_antibiotic(antibiotic):
    """ Classificar o antibiótico nas classes."""
    for category, antibiotics in ANTIBIOTIC_CLASSES.items():
        if antibiotic in antibiotics:
            return category

def intrinsic_resistance(microorganismo, antibiotic):
    """Verificar se um antibiótico é intrinsicamente resistente para um microorganismo."""
    intrinsic_resistance_dict = {
        "Acinetobacter baumannii": ["Ampicillina", "Amoxicilina", "Cefuroxima", "Cefuroxima - Axetil", "Cefuroxima - Sódica"],
        "Citrobacter species": ["Ampicillina", "Cefuroxima"],
        "Enterobacter species": ["Ampicillina", "Cefuroxima", "Cefuroxima - Axetil", "Cefuroxima - Sódica"],
        "Escherichia coli": ["Penicillina", "Vancomicina"],
        "Klebsiella oxytoca": ["Ampicillina", "Amoxicilina"],
        "Klebsiella pneumoniae": ["Ampicillina", "Amoxicilina"],
        "Morganella morganii": ["Ampicillina", "Amoxicilina", "Cefuroxima"],
        "Pseudomonas aeruginosa": ["A maioria dos Beta-lactâmicos", "Cotrimoxazol", "Tetraciclina", "Cloranfenicol", "Colistina"],
        "Proteus mirabilis": ["Tetraciclina", "Nitrofurantoína", "Polimixinas", "Tigeciclina"],
        "Serratia marcescens": ["Ampicillina", "Amoxicilina", "Cefuroxima"],
        "Providencia species": ["Ampicillina", "Amoxicilina", "Cefuroxima", "Nitrofurantoína"],
        "Haemophilus influenzae": ["Vancomicina", "Clindamicina", "Cefuroxima", "Cefuroxima - Axetil", "Cefuroxima - Sódica"],
        "Enterococcus faecalis": ["Cefalosporinas", "Clindamicina", "Aminoglicosídeos"],
        "Enterococcus faecium": ["Cefalosporinas", "Clindamicina", "Aminoglicosídeos"],
        "Streptococcus agalactiae": ["Aminoglicosídeos", "Cotrimoxazol"],
        "Staphylococcus aureus": [],  # MRSA specifics can be handled separately
        "Staphylococcus epidermidis": [],  # MRSE specifics can be handled separately
        "Streptococcus pneumoniae": ["Aminoglicosídeos", "Clindamicina"],
        "Staphylococcus saprophyticus": ["Novobiocina"]
    }

    return 'x' if antibiotic in intrinsic_resistance_dict.get(microorganismo, []) else ''





def calculate_resistance(df_cleaned):
    df_cleaned.loc[:, 'Gram_Stain'] = df_cleaned['Microorganismo'].apply(classify_gram_stain)
    antibiotic_columns = detect_antibiotic_columns(df_cleaned)
    results = []
    microorganism_counts = df_cleaned['Microorganismo'].value_counts().to_dict()

    for microorganismo in RELEVANT_MICROORGANISMS:
        micro_df = df_cleaned[df_cleaned['Microorganismo'] == microorganismo]
        for col in antibiotic_columns:
            count = micro_df[col].count()
            if count > 0:  # só antibióticos com resultados
                resistant = micro_df[micro_df[col] == 'Resistente'].shape[0]
                resistance = (resistant / count) * 100 if count else 0
                resistance = round(resistance, 1)  
                results.append({
                    'Microorganismo': f"{microorganismo} (n={microorganism_counts.get(microorganismo, 0)})",
                    'Antibiotic': col,
                    'Resistance': resistance,
                    'Gram_Stain': classify_gram_stain(microorganismo),
                    'Category': classify_resistance(resistance),
                    'Class': classify_antibiotic(col),
                    'Intrinsic_Resistance': intrinsic_resistance(microorganismo, col)
                })

    result_df = pd.DataFrame(results)
    
    if not result_df.empty:
        result_df = result_df.pivot(index=['Gram_Stain', 'Microorganismo'], columns='Antibiotic', values='Resistance')
        
        result_df = result_df.applymap(lambda x: '{:.1f}'.format(x).rstrip('0').rstrip('.') if pd.notnull(x) else x)

    return result_df

def highlight_resistance(val):
    """Identificar os valores e associar com as cores específicas."""
    if isinstance(val, str) and val != '':
        val = float(val)
        if val < 40:
            return 'background-color: lightblue; color: black'
        elif val > 80:
            return 'background-color: lightcoral; color: black'
        elif 40 <= val <= 80:
            return 'background-color: lightgoldenrodyellow; color: black'
    return ''

def detect_antibiotic_columns(df):
    """Identificar as colunas de antibióticos."""
    return [col for col in df.columns if col in ANTIBIOTICS]

# Definição da função classify_antibiotic
def classify_antibiotic(antibiotic):
    if antibiotic in CARBAPENEMES:
        return 'Carbapenemes'
    elif antibiotic in ANTI_MRSA:
        return 'Anti-MRSA'
    elif antibiotic in POLIMIXINAS:
        return 'Polimixina'
    elif antibiotic in CEFALOSPORINAS_3A_4A:
        return 'Cefalosporina (3ª/4ª Geração)'
    elif antibiotic in AMOXICILINA_ACIDO_CLAVULANICO:
        return 'Amoxicilina/Ácido Clavulânico'
    elif antibiotic in FLUOROQUINOLONAS:
        return 'Fluoroquinolona'
    elif antibiotic in AMINOGLICOSIDEOS:
        return 'Aminoglicosídeo'
    elif antibiotic in BETA_LACTAMICOS_INIBIDORES:
        return 'Beta-lactâmico com Inibidor de Beta-lactamase'
    else:
        return 'Outros'
        
def show_product_service_chart(df_cleaned):
    df_cleaned['Serviço'] = df_cleaned['Serviço'].astype(str).fillna('Sem Identificação')
    df_cleaned['Produto'] = df_cleaned['Produto'].astype(str).fillna('Sem Identificação')
    services_list = ['Total'] + sorted(df_cleaned['Serviço'].unique())
    products_list = ['Total'] + sorted(df_cleaned['Produto'].unique())
    
    selected_service = st.selectbox("Selecionar Serviço:", services_list)
    if selected_service == 'Total':
        selected_product = st.selectbox("Selecionar Produto:", products_list)
        filtered_data = df_cleaned if selected_product == 'Total' else df_cleaned[df_cleaned['Produto'] == selected_product]
    else:
        filtered_data = df_cleaned[df_cleaned['Serviço'] == selected_service]
        selected_product = st.selectbox("Selecionar Produto:", ['Total'] + sorted(filtered_data['Produto'].unique()))
        filtered_data = filtered_data if selected_product == 'Total' else filtered_data[filtered_data['Produto'] == selected_product]
    
    microorganism_counts = filtered_data['Microorganismo'].value_counts().reset_index()
    microorganism_counts.columns = ['Microorganismo', 'Counts']
    top_microorganisms = microorganism_counts.head(10)
    fig = px.bar(top_microorganisms, x='Microorganismo', y='Counts',
                 title=f'Top 10 Microorganisms in {selected_product} for {selected_service}',
                 color='Microorganismo', color_continuous_scale=px.colors.qualitative.Pastel)
    st.plotly_chart(fig)
    
    # Exibir perfil de resistências
    st.write("### Perfil de Resistências")
    if not filtered_data.empty:
        resistance_df = calculate_resistance(filtered_data)
        antibiotic_columns = detect_antibiotic_columns(filtered_data)
        resistance_summary_df = resistance_df.reset_index().melt(id_vars=['Microorganismo', 'Gram_Stain'], var_name='Antibiotic', value_name='Resistance')
        resistance_summary_df = resistance_summary_df[resistance_summary_df['Resistance'].notna()]
        
        # Adicionar a coluna de classe de antibióticos
        resistance_summary_df['Class'] = resistance_summary_df['Antibiotic'].apply(classify_antibiotic)
        
        # Filtrar os microorganismos do gráfico anterior
        top_microorganisms_list = top_microorganisms['Microorganismo'].tolist()
        filtered_resistance_summary_df = resistance_summary_df[resistance_summary_df['Microorganismo'].str.contains('|'.join(top_microorganisms_list))]
        
        # Exibir DataFrame com o perfil de resistências
        st.write(filtered_resistance_summary_df[['Microorganismo', 'Antibiotic', 'Class', 'Resistance', 'Gram_Stain']])
        
        # Gráficos de barras para as classes específicas de antibióticos
        st.write("### Perfil de Resistência para Classes Específicas de Antibióticos")
        specific_classes = ['Carbapenemes', 'Anti-MRSA', 'Polimixina', 'Cefalosporina (3ª/4ª Geração)', 
                            'Amoxicilina/Ácido Clavulânico', 'Fluoroquinolona', 'Aminoglicosídeo', 
                            'Beta-lactâmico com Inibidor de Beta-lactamase']
        for antibiotic_class in specific_classes:
            class_df = filtered_resistance_summary_df[filtered_resistance_summary_df['Class'] == antibiotic_class]
            if not class_df.empty:
                st.write(f"#### {antibiotic_class}")
                fig = px.bar(class_df, x='Resistance', y='Antibiotic', color='Antibiotic', orientation='h',
                             title=f'Perfil de Resistência para {antibiotic_class}',
                             labels={'Resistance': 'Resistência (%)', 'Antibiotic': 'Antibiótico'})
                st.plotly_chart(fig)
    else:
        st.write("No resistance data available for the selected criteria.")


def process_and_plot_data(df_clean, gram_positive, gram_negative, eskape_microorganisms):
    st.header("Análise exploratória dos dados")

    # Selecionar a opção para filtrar os dados, ignorando as primeiras nove colunas
    options = ['Microorganismo', 'Gram-positive', 'Gram-negative', 'ESKAPE', 'Sexo', 'Idade'] + list(df_clean.columns[10:])
    groupby_column = st.selectbox('Que deseja verificar?', options)
    st.write(f"Seleção atual: {groupby_column}")

    # Filtrar o DataFrame com base na opção selecionada
    if groupby_column == 'Microorganismo':
        df_filtered = df_clean
    elif groupby_column in ['Gram-positive', 'Gram-negative', 'ESKAPE']:
        if groupby_column == 'Gram-positive':
            relevant_microorganisms = gram_positive
        elif groupby_column == 'Gram-negative':
            relevant_microorganisms = gram_negative
        else:
            relevant_microorganisms = eskape_microorganisms
        df_filtered = df_clean[df_clean['Microorganismo'].isin(relevant_microorganisms)]
    else:
        df_filtered = df_clean[df_clean[groupby_column].notnull()]

    # Número de ocorrências para cada grupo
    if groupby_column in ['Microorganismo', 'Gram-positive', 'Gram-negative', 'ESKAPE']:
        data_counts = df_filtered['Microorganismo'].value_counts().reset_index()
        data_counts.columns = ['Microorganismo', 'Contagem']
    else:
        data_counts = df_filtered[groupby_column].value_counts().reset_index()
        data_counts.columns = [groupby_column, 'Contagem']

    # Plot da distribuição de microorganismos com cores 
    fig = px.bar(data_counts, x=data_counts.columns[0], y='Contagem', title='Distribuição de Microorganismos',
                 color=data_counts.columns[0], color_continuous_scale=px.colors.sequential.Viridis)
    st.plotly_chart(fig)

    # Listar as colunas de antibióticos
    colunas_antibioticos = detect_antibiotic_columns(df_clean)

    # Escolher a opção de visualizar 'Resistente' ou 'Sensível'
    opcao_visualizacao = st.radio("Escolha o que deseja visualizar:", ('Resistente', 'Sensível'))
    contagens = {coluna: df_filtered[coluna].value_counts().get(opcao_visualizacao, 0) for coluna in colunas_antibioticos}
    contagens_df = pd.DataFrame(list(contagens.items()), columns=['Antibiótico', 'Contagem'])
    contagens_df.sort_values(by='Contagem', ascending=False, inplace=True)

    # Plot das contagens de antibióticos com cores 
    fig = px.bar(contagens_df, x='Antibiótico', y='Contagem', color='Contagem',
                 color_continuous_scale=px.colors.sequential.Plasma,
                 labels={'Contagem': f'Quantidade de {opcao_visualizacao}'},
                 title=f'Quantidade de Antibióticos {opcao_visualizacao}')
    st.plotly_chart(fig)

    # New section for percentage of isolates by patient sex and age group, by bacterial species
    st.subheader("Percentagem de isolados por sexo e grupo etário")
    microorganismo_filter = st.selectbox('Escolha o Microorganismo para detalhar (ou Todos):', ['Todos'] + df_clean['Microorganismo'].unique().tolist())
    
    if microorganismo_filter == 'Todos':
        df_sex_age = df_clean
    else:
        df_sex_age = df_clean[df_clean['Microorganismo'] == microorganismo_filter]

    groupby_sex_age = st.selectbox('Selecione um grupo para analisar:', ['Sexo', 'Idade'])
    if groupby_sex_age:
        grouped_sex_age = df_sex_age.groupby(groupby_sex_age).size().reset_index()
        grouped_sex_age.columns = [groupby_sex_age, 'count']
        total_sex_age = df_sex_age.shape[0]
        grouped_sex_age['percentage'] = (grouped_sex_age['count'] / total_sex_age) * 100

        fig_sex_age = px.bar(grouped_sex_age, x=groupby_sex_age, y='percentage', color=groupby_sex_age,
                             title=f'Percentagem de isolados por {groupby_sex_age} ({microorganismo_filter})',
                             labels={'percentage': 'Percentagem'})
        st.plotly_chart(fig_sex_age)

    # Nova seção para o número total de isolados invasivos testados e percentagem de isolados com fenótipo de resistência
    st.subheader("Número total de isolados invasivos testados e percentagem de isolados com fenótipo de resistência")

    # Transformar os dados para calcular a resistência
    grouped_resistance = df_filtered.melt(id_vars=['Microorganismo'], value_vars=colunas_antibioticos, 
                                        var_name='Antimicrobial Class', value_name='Resistance Phenotype')

    # Filtrar apenas os fenotipos de resistência
    grouped_resistance = grouped_resistance[grouped_resistance['Resistance Phenotype'] == 'Resistente']

    # Contagem dos isolados resistentes por classe antimicrobiana e microorganismo
    grouped_resistance = grouped_resistance.groupby(['Microorganismo', 'Antimicrobial Class']).size().reset_index(name='count')

    # Contagem total de isolados testados por classe antimicrobiana e microorganismo
    total_resistance = grouped_resistance.groupby(['Microorganismo', 'Antimicrobial Class'])['count'].sum().reset_index()
    total_resistance.columns = ['Microorganismo', 'Antimicrobial Class', 'total']

    # Calcular a percentagem de isolados resistentes
    percent_resistance = pd.merge(grouped_resistance, total_resistance, on=['Microorganismo', 'Antimicrobial Class'])
    percent_resistance['percentage'] = (percent_resistance['count'] / percent_resistance['total']) * 100

    # Criar o gráfico de barras
    fig_resistance = px.bar(percent_resistance, x='Antimicrobial Class', y='percentage', color='Microorganismo',
                            title='Percentagem de isolados com fenótipo de resistência',
                            labels={'percentage': 'Percentagem', 'Antimicrobial Class': 'Classe Antimicrobiana', 'Microorganismo': 'Microorganismo'})

    # Exibir o gráfico
    st.plotly_chart(fig_resistance)

    df_clean['Faixa Etária'] = pd.cut(df_clean['Idade'], 
                                      bins=[0, 12, 18, 60, 120], 
                                      labels=['Pediátrico', 'Adolescente', 'Adulto', 'Idoso'], 
                                      right=False)

    st.subheader("Filtrar detalhes específicos")

    # Microorganismo
    microorganismos = ['Todos'] + list(df_clean['Microorganismo'].unique())
    microorganismo = st.selectbox('Escolha o Microorganismo:', microorganismos)

    # Idade
    faixas_etarias = ['Todas'] + ['Pediátrico', 'Adolescente', 'Adulto', 'Idoso']
    faixa_etaria = st.selectbox('Escolha a Faixa Etária:', faixas_etarias)

    # Sexo
    sexos = ['Todos'] + list(df_clean['Sexo'].unique())
    sexo = st.selectbox('Escolha o Sexo:', sexos)

    # Serviço
    servicos = ['Todos'] + list(df_clean['Serviço'].unique())
    servico = st.selectbox('Escolha o Serviço:', servicos)

    # Produto
    produtos = ['Todos'] + list(df_clean['Produto'].unique())
    produto = st.selectbox('Escolha o Produto:', produtos)

    # Filtrando o DataFrame
    df_specific = df_clean[
        ((df_clean['Microorganismo'] == microorganismo) | (microorganismo == 'Todos')) &
        ((df_clean['Faixa Etária'] == faixa_etaria) | (faixa_etaria == 'Todas')) &
        ((df_clean['Sexo'] == sexo) | (sexo == 'Todos')) &
        ((df_clean['Serviço'] == servico) | (servico == 'Todos')) &
        ((df_clean['Produto'] == produto) | (produto == 'Todos'))
    ]

    if not df_specific.empty:
        st.write(f"Detalhes para {microorganismo}, {faixa_etaria}, {sexo}, {servico}, {produto}:")
        st.dataframe(df_specific)
    else:
        st.write(f"Nenhum dado encontrado para {microorganismo}, {faixa_etaria}, {sexo}, {servico}, {produto}.")

def process_and_plot_data(df_clean, gram_positive, gram_negative, eskape_microorganisms):
    st.header("Análise exploratória dos dados")

    # Selecionar a opção para filtrar os dados, ignorando as primeiras nove colunas
    options = ['Microorganismo', 'Gram-positive', 'Gram-negative', 'ESKAPE', 'Sexo', 'Idade'] + list(df_clean.columns[10:])
    groupby_column = st.selectbox('Que deseja verificar?', options)
    st.write(f"Seleção atual: {groupby_column}")

    # Filtrar o DataFrame com base na opção selecionada
    if groupby_column == 'Microorganismo':
        df_filtered = df_clean
    elif groupby_column in ['Gram-positive', 'Gram-negative', 'ESKAPE']:
        if groupby_column == 'Gram-positive':
            relevant_microorganisms = gram_positive
        elif groupby_column == 'Gram-negative':
            relevant_microorganisms = gram_negative
        else:
            relevant_microorganisms = eskape_microorganisms
        df_filtered = df_clean[df_clean['Microorganismo'].isin(relevant_microorganisms)]
    else:
        df_filtered = df_clean[df_clean[groupby_column].notnull()]

    # Número de ocorrências para cada grupo
    if groupby_column in ['Microorganismo', 'Gram-positive', 'Gram-negative', 'ESKAPE']:
        data_counts = df_filtered['Microorganismo'].value_counts().reset_index()
        data_counts.columns = ['Microorganismo', 'Contagem']
    else:
        data_counts = df_filtered[groupby_column].value_counts().reset_index()
        data_counts.columns = [groupby_column, 'Contagem']

    # Plot da distribuição de microorganismos com cores suaves
    fig = px.bar(data_counts, x=data_counts.columns[0], y='Contagem', title='Distribuição de Microorganismos',
                 color=data_counts.columns[0], color_discrete_sequence=px.colors.qualitative.Pastel)
    st.plotly_chart(fig)

    # Listar as colunas de antibióticos
    colunas_antibioticos = detect_antibiotic_columns(df_clean)

    # Escolher a opção de visualizar 'Resistente' ou 'Sensível'
    opcao_visualizacao = st.radio("Escolha o que deseja visualizar:", ('Resistente', 'Sensível'))
    contagens = {coluna: df_filtered[coluna].value_counts().get(opcao_visualizacao, 0) for coluna in colunas_antibioticos}
    contagens_df = pd.DataFrame(list(contagens.items()), columns=['Antibiótico', 'Contagem'])
    contagens_df.sort_values(by='Contagem', ascending=False, inplace=True)

    # Plot das contagens de antibióticos com cores suaves
    fig = px.bar(contagens_df, x='Antibiótico', y='Contagem', color='Antibiótico',
                 color_discrete_sequence=px.colors.qualitative.Pastel,
                 labels={'Contagem': f'Quantidade de {opcao_visualizacao}'},
                 title=f'Quantidade de Antibióticos {opcao_visualizacao}')
    st.plotly_chart(fig)

    # New section for percentage of isolates by patient sex and age group, by bacterial species
    st.subheader("Percentagem e total de isolados por sexo e grupo etário")
    microorganismo_filter = st.selectbox('Escolha o Microorganismo para detalhar (ou Todos):', ['Todos'] + df_clean['Microorganismo'].unique().tolist())
    
    if microorganismo_filter == 'Todos':
        df_sex_age = df_clean
    else:
        df_sex_age = df_clean[df_clean['Microorganismo'] == microorganismo_filter]

    groupby_sex_age = st.selectbox('Selecione um grupo para analisar:', ['Sexo', 'Idade'])
    if groupby_sex_age:
        grouped_sex_age = df_sex_age.groupby(groupby_sex_age).size().reset_index()
        grouped_sex_age.columns = [groupby_sex_age, 'count']
        total_sex_age = df_sex_age.shape[0]
        grouped_sex_age['percentage'] = (grouped_sex_age['count'] / total_sex_age) * 100

        fig_sex_age = px.bar(grouped_sex_age, x=groupby_sex_age, y='percentage', color=groupby_sex_age,
                             title=f'Percentagem de isolados por {groupby_sex_age} ({microorganismo_filter})',
                             labels={'percentage': 'Percentagem'}, color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_sex_age.update_layout(yaxis_title='Percentagem', xaxis_title=groupby_sex_age)
        fig_sex_age.update_traces(texttemplate='%{text:.2s}%', textposition='outside')
        
        # Adiciona as contagens totais ao gráfico
        fig_sex_age.update_traces(text=grouped_sex_age['count'])

        st.plotly_chart(fig_sex_age)
        st.write(grouped_sex_age)

    # Nova seção para o número total de isolados invasivos testados e percentagem de isolados com fenótipo de resistência
    st.subheader("Número total de isolados invasivos testados e percentagem de isolados com fenótipo de resistência")

    # Transformar os dados para calcular a resistência
    grouped_resistance = df_filtered.melt(id_vars=['Microorganismo'], value_vars=colunas_antibioticos, 
                                        var_name='Antibiotic', value_name='Resistance Phenotype')

    # Filtrar apenas os fenotipos de resistência
    grouped_resistance = grouped_resistance[grouped_resistance['Resistance Phenotype'] == 'Resistente']

    # Contagem dos isolados resistentes por antibiótico e microorganismo
    grouped_resistance = grouped_resistance.groupby(['Microorganismo', 'Antibiotic']).size().reset_index(name='count')

    # Contagem total de isolados testados por antibiótico e microorganismo
    total_resistance = grouped_resistance.groupby(['Microorganismo', 'Antibiotic'])['count'].sum().reset_index()
    total_resistance.columns = ['Microorganismo', 'Antibiotic', 'total']

    # Calcular a percentagem de isolados resistentes
    percent_resistance = pd.merge(grouped_resistance, total_resistance, on=['Microorganismo', 'Antibiotic'])
    percent_resistance['percentage'] = (percent_resistance['count'] / percent_resistance['total']) * 100

    # Gráfico para fenotipos de resistência com 100% de resistência
    percent_resistance_100 = percent_resistance[percent_resistance['percentage'] == 100]
    if not percent_resistance_100.empty:
        fig_resistance_100 = px.bar(percent_resistance_100, x='Antibiotic', y='percentage', color='Microorganismo',
                                    title='Percentagem de isolados com fenótipo de resistência (100%)',
                                    labels={'percentage': 'Percentagem', 'Antibiotic': 'Antibiótico', 'Microorganismo': 'Microorganismo'},
                                    color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_resistance_100.update_layout(yaxis_title='Percentagem', xaxis_title='Antibiótico')
        fig_resistance_100.update_traces(texttemplate='%{text:.2s}%', textposition='outside')
        fig_resistance_100.update_traces(text=percent_resistance_100['count'])
        st.plotly_chart(fig_resistance_100)

    # Gráfico para fenotipos de resistência entre 80% e 100%
    percent_resistance_80_100 = percent_resistance[(percent_resistance['percentage'] >= 80) & (percent_resistance['percentage'] < 100)]
    if not percent_resistance_80_100.empty:
        fig_resistance_80_100 = px.bar(percent_resistance_80_100, x='Antibiotic', y='percentage', color='Microorganismo',
                                       title='Percentagem de isolados com fenótipo de resistência (80% a 100%)',
                                       labels={'percentage': 'Percentagem', 'Antibiotic': 'Antibiótico', 'Microorganismo': 'Microorganismo'},
                                       color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_resistance_80_100.update_layout(yaxis_title='Percentagem', xaxis_title='Antibiótico')
        fig_resistance_80_100.update_traces(texttemplate='%{text:.2s}%', textposition='outside')
        fig_resistance_80_100.update_traces(text=percent_resistance_80_100['count'])
        st.plotly_chart(fig_resistance_80_100)

    # Certificar-se de que a coluna 'Idade' contém apenas valores numéricos
    df_clean['Idade'] = pd.to_numeric(df_clean['Idade'], errors='coerce')

    # Adicionar colunas para categorizar as idades em intervalos de 10 anos
    df_clean['Faixa Etária'] = pd.cut(df_clean['Idade'], 
                                      bins=range(0, 121, 10), 
                                      labels=[f'{i}-{i+9}' for i in range(0, 120, 10)], 
                                      right=False)

    st.subheader("Filtrar detalhes específicos")

    # Microorganismo
    microorganismos = ['Todos'] + list(df_clean['Microorganismo'].unique())
    microorganismo = st.selectbox('Escolha o Microorganismo:', microorganismos)

    # Idade (intervalos de 10 anos)
    faixas_etarias = ['Todas'] + [f'{i}-{i+9}' for i in range(0, 120, 10)]
    faixa_etaria = st.multiselect('Escolha os intervalos de idade:', faixas_etarias, default=['Todas'])

    # Sexo
    sexos = ['Todos'] + list(df_clean['Sexo'].unique())
    sexo = st.selectbox('Escolha o Sexo:', sexos)

    # Serviço
    servicos = ['Todos'] + list(df_clean['Serviço'].unique())
    servico = st.selectbox('Escolha o Serviço:', servicos)

    # Produto
    produtos = ['Todos'] + list(df_clean['Produto'].unique())
    produto = st.selectbox('Escolha o Produto:', produtos)

    # Filtrando o DataFrame
    df_specific = df_clean[
        ((df_clean['Microorganismo'] == microorganismo) | (microorganismo == 'Todos')) &
        ((df_clean['Faixa Etária'].isin(faixa_etaria)) | ('Todas' in faixa_etaria)) &
        ((df_clean['Sexo'] == sexo) | (sexo == 'Todos')) &
        ((df_clean['Serviço'] == servico) | (servico == 'Todos')) &
        ((df_clean['Produto'] == produto) | (produto == 'Todos'))
    ]

    if not df_specific.empty:
        st.write(f"Detalhes para {microorganismo}, {faixa_etaria}, {sexo}, {servico}, {produto}:")
        st.dataframe(df_specific)
    else:
        st.write(f"Nenhum dado encontrado para {microorganismo}, {faixa_etaria}, {sexo}, {servico}, {produto}.")



def summarize_microorganism(df, microorganismo_selecionado):
    """Sumário da sensibilidade e resistência para um dado microorganismo."""
    filtered_df = df[df['Microorganismo'] == microorganismo_selecionado]
    
    if filtered_df.empty:
        return f"Sem dados disponíveis para o microorganismo: {microorganismo_selecionado}"

    antibiotic_columns = detect_antibiotic_columns(filtered_df)

    sensitive_antibiotics = []
    resistant_antibiotics = []
    sensitive_exposure_antibiotics = []

    for antibiotic in antibiotic_columns:
        if (filtered_df[antibiotic] == 'sensível').all():
            sensitive_antibiotics.append(antibiotic)
        elif (filtered_df[antibiotic] == 'resistente').all():
            resistant_antibiotics.append(antibiotic)
        elif (filtered_df[antibiotic] == 'sensível com maior exposição').all():
            sensitive_exposure_antibiotics.append(antibiotic)

    summary_counts = {
        'sensível': len(sensitive_antibiotics),
        'resistente': len(resistant_antibiotics),
        'sensível com maior exposição': len(sensitive_exposure_antibiotics)
    }

    sensitive_list = ", ".join(sensitive_antibiotics)
    resistant_list = ", ".join(resistant_antibiotics)
    sensitive_exposure_list = ", ".join(sensitive_exposure_antibiotics)

    summary = (f"Resumo para {microorganismo_selecionado}:\n\n"
               f"Antibióticos sensíveis: {summary_counts['sensível']} ({sensitive_list})\n"
               f"Antibióticos resistentes: {summary_counts['resistente']} ({resistant_list})\n"
               f"Antibióticos sensíveis com maior exposição: {summary_counts['sensível com maior exposição']} ({sensitive_exposure_list})")

    return summary



def show_microorganism_chart(df_cleaned):
    # Usar uma chave única para o selectbox para evitar erro DuplicateWidgetID
    microorganismos = df_cleaned['Microorganismo'].unique()
    microorganismo_selecionado = st.selectbox('Selecione um microorganismo:', sorted(microorganismos), key='microorganismo_selectbox_chart_final')

    if microorganismo_selecionado:
        filtered_df = df_cleaned[df_cleaned['Microorganismo'] == microorganismo_selecionado]

        if not filtered_df.empty:
            antibiotic_columns = detect_antibiotic_columns(filtered_df)
            
            # Calcular perfil de resistência para o treemap
            resistance_df = calculate_resistance(filtered_df)
            
            if not resistance_df.empty:
                # Garantir que o DataFrame tenha a estrutura correta para o treemap
                resistance_df = resistance_df.reset_index().melt(id_vars=['Microorganismo'], var_name='Antibiotic', value_name='Resistance')
                resistance_df = resistance_df.dropna(subset=['Resistance'])
                resistance_df['Resistance'] = pd.to_numeric(resistance_df['Resistance'], errors='coerce')
                
                # Adicionar a coluna 'Class' com as classes dos antibióticos
                resistance_df['Class'] = resistance_df['Antibiotic'].apply(classify_antibiotic)
                
                # Adicionar um valor mínimo não-zero para evitar divisão por zero
                resistance_df['Resistance'] = resistance_df['Resistance'].apply(lambda x: x if x > 0 else 0.0001)
                
                # Gráfico de treemap para todos os antibióticos
                st.write(f"Perfil de resistência para {microorganismo_selecionado}")
                fig = px.treemap(resistance_df, path=['Microorganismo', 'Antibiotic'], values='Resistance',
                                 color='Resistance', hover_data={'Resistance': ':.2f'},
                                 color_continuous_scale=px.colors.sequential.BuGn,  # Paleta de cores agradável
                                 title=f"Resistência aos antibióticos para {microorganismo_selecionado}")
                st.plotly_chart(fig)

                # Criar um DataFrame com microorganismo no eixo x e classes de antibióticos no eixo y
                resistance_summary_df = resistance_df.pivot_table(index='Microorganismo', columns='Class', values='Resistance', aggfunc='mean').fillna(0)
                resistance_summary_df.columns = [f"{col} (%)" for col in resistance_summary_df.columns]
                st.write("### Perfis de Resistência por Classe de Antibióticos")
                st.write(resistance_summary_df)
                    
            else:
                st.write("No resistance data available for the selected microorganismo.")
            
            # Informações adicionais sobre o microorganismo
            st.write("### Informações Adicionais")
            num_cases = filtered_df.shape[0]
            if 'Serviço' in filtered_df.columns:
                common_service = filtered_df['Serviço'].mode()[0]
                service_count = filtered_df[filtered_df['Serviço'] == common_service].shape[0]
                st.write(f"Este microorganismo apresentou {num_cases} casos, dos quais {service_count} casos no serviço de {common_service}.")
            else:
                st.write(f"Este microorganismo apresentou {num_cases} casos.")
            
            if 'Produto' in filtered_df.columns:
                common_product = filtered_df['Produto'].mode()[0]
                product_count = filtered_df[filtered_df['Produto'] == common_product].shape[0]
                st.write(f"O produto {common_product} é o que apresenta maior número de identificações , {product_count} identificações.")
            
            if not resistance_df.empty:
                most_resistant_antibiotic = resistance_df.loc[resistance_df['Resistance'].astype(float).idxmax()]
                st.write(f"Apresenta uma resistência mais alta ao antibiótico {most_resistant_antibiotic['Antibiotic']} com {most_resistant_antibiotic['Resistance']}% de resistência.")
            
            # Exibir os antibióticos relevantes
            relevant_antibiotics_df = filtered_df[['Microorganismo'] + antibiotic_columns]
            relevant_antibiotics_df = relevant_antibiotics_df.dropna(how='all', subset=antibiotic_columns)
            relevant_antibiotics_df = relevant_antibiotics_df.loc[:, relevant_antibiotics_df.isin(['Resistente', 'Sensível', 'Sensível, com maior exposição.']).any()]
            st.write(f"Antibióticos para {microorganismo_selecionado} com resultados de resistência")
            st.write(relevant_antibiotics_df)
        else:
            st.write("Sem dados disponíveis para o microorganismo selecionado.")


def multi_selection_filter(df):
    st.subheader("Filtro Multisseleção para Microorganismos e Antibióticos")

    # Seleção de Microorganismos
    selected_microorganisms = st.multiselect('Selecione os Microorganismos', df['Microorganismo'].unique())

    # Seleção de Antibióticos
    antibiotic_columns = [col for col in df.columns if col not in ['Microorganismo', 'Gram_Stain']]
    selected_antibiotics = st.multiselect('Selecione os Antibióticos', antibiotic_columns)

    # Mostrar contagem das seleções
    if selected_microorganisms:
        st.write(f"Microorganismos selecionados: {len(selected_microorganisms)}")
    else:
        st.write("Nenhum microorganismo selecionado.")

    if selected_antibiotics:
        st.write(f"Antibióticos selecionados: {len(selected_antibiotics)}")
    else:
        st.write("Nenhum antibiótico selecionado.")

    # Filtrar DataFrame
    if selected_microorganisms and selected_antibiotics:
        filtered_df = df[df['Microorganismo'].isin(selected_microorganisms)][['Microorganismo'] + selected_antibiotics]
        st.write(filtered_df)
        
        # Plotar Gráficos de Pizza
        for antibiotic in selected_antibiotics:
            counts = filtered_df[antibiotic].value_counts().reset_index()
            counts.columns = ['Resposta', 'Contagem']
            fig = px.pie(counts, values='Contagem', names='Resposta', title=f'Distribuição de Respostas para {antibiotic}')
            st.plotly_chart(fig)
    else:
        st.write("Selecione pelo menos um Microorganismo e um Antibiótico.")



# Main Streamlit app
st.set_page_config(layout='wide', initial_sidebar_state='expanded')
st.title('🧫Ferramenta de apoio à Microbiologia do ULSRA')
st.header("💊 Uso exclusivo do Serviço ")

uploaded_file = st.sidebar.file_uploader("Upload your Excel file here", type=['xlsx', 'xls'])

df = pd.DataFrame()
df_cleaned = pd.DataFrame()

if uploaded_file is not None:
    df, error = read_data(uploaded_file)
    if error:
        st.error(f"Failed to read data: {error}")
    else:
        df_cleaned, df_duplicates = df_clean(df)

if not df_cleaned.empty:
    resistance_data = calculate_resistance(df_cleaned)
    st.write("")
    st.write("Perfil de resistência por microorganismo e antibótico:")
    
    if not resistance_data.empty:
        styled_data = resistance_data.style.applymap(highlight_resistance)
        st.dataframe(styled_data)

   

    page = st.sidebar.selectbox("Select Page", ["Microorganismos", "Análise exploratória com Classes","Verificação de Duplicados","Distribuição e Frequência","Filtros"])

    if page == "Microorganismos":
        show_microorganism_chart(df_cleaned)
    elif page == "Análise exploratória com Classes":
        show_product_service_chart(df_cleaned)
    elif page == "Verificação de Duplicados":
        check_duplicates(df_duplicates)
    elif page == "Distribuição e Frequência":
        process_and_plot_data(df_cleaned, GRAM_POSITIVE, GRAM_NEGATIVE, RELEVANT_MICROORGANISMS)
    elif page == "Filtros":
        multi_selection_filter(df)


