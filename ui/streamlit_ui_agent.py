import streamlit as st
import pandas as pd
import io
import os
from datetime import datetime
from typing import Dict, Any, Optional

from agents.coordinator_agent import CoordinatorAgent

class StreamlitUIAgent:
    """
    Agente de Interface do Usuário usando Streamlit.
    Gerencia a interação com o usuário e se comunica com o Agente Coordenador.
    """
    
    def __init__(self):
        self.name = "StreamlitUIAgent"
        self.coordinator = CoordinatorAgent()
    
    def setup_page_config(self):
        """Configura a página do Streamlit."""
        st.set_page_config(
            page_title="Sistema de Cálculo de Benefícios (A2A)",
            page_icon="🤖",
            layout="wide",
            initial_sidebar_state="expanded"
        )
    
    def setup_custom_css(self):
        """Aplica CSS customizado."""
        st.markdown("""
        <style>
            .main-header {
                font-size: 2.5rem;
                font-weight: bold;
                color: #1f77b4;
                text-align: center;
                margin-bottom: 2rem;
            }
            .agent-badge {
                background-color: #e8f4fd;
                color: #1f77b4;
                padding: 0.25rem 0.5rem;
                border-radius: 0.25rem;
                font-size: 0.8rem;
                font-weight: bold;
                margin: 0.25rem;
                display: inline-block;
            }
            .metric-card {
                background-color: #f0f2f6;
                padding: 1rem;
                border-radius: 0.5rem;
                border-left: 4px solid #1f77b4;
            }
            .success-message {
                background-color: #d4edda;
                color: #155724;
                padding: 1rem;
                border-radius: 0.5rem;
                border: 1px solid #c3e6cb;
            }
            .error-message {
                background-color: #f8d7da;
                color: #721c24;
                padding: 1rem;
                border-radius: 0.5rem;
                border: 1px solid #f5c6cb;
            }
        </style>
        """, unsafe_allow_html=True)
    
    def render_sidebar(self) -> Dict[str, Any]:
        """
        Renderiza a barra lateral e retorna as configurações do usuário.
        
        Returns:
            Dicionário com as configurações selecionadas pelo usuário
        """
        with st.sidebar:
            st.header("🤖 Sistema Agent-to-Agent")
            st.markdown("---")
            
            # Informações sobre a arquitetura
            st.subheader("🏗️ Arquitetura A2A")
            st.markdown("""
            <div class="agent-badge">DataProcessorAgent</div>
            <div class="agent-badge">EligibilityCalculatorAgent</div>
            <div class="agent-badge">AnalysisAgent</div>
            <div class="agent-badge">CoordinatorAgent</div>
            <div class="agent-badge">StreamlitUIAgent</div>
            """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Informações sobre o sistema
            st.subheader("ℹ️ Sobre o Sistema")
            st.write("""
            Sistema multi-agente para calcular benefícios de vale alimentação/refeição.
            
            **Agentes Especializados:**
            - **Processamento:** Extrai e unifica dados
            - **Elegibilidade:** Aplica regras e calcula benefícios
            - **Análise:** Gera insights com IA (Gemini)
            - **Coordenador:** Orquestra o fluxo (LangGraph)
            - **UI:** Interface do usuário (Streamlit)
            """)
            
            st.markdown("---")
            
            # Configurações
            st.subheader("⚙️ Configurações")
            use_gemini = st.checkbox("Usar análise com IA (Gemini)", value=True)
            
            gemini_api_key = None
            if use_gemini:
                gemini_api_key = st.text_input(
                    "Chave API do Gemini (opcional)",
                    type="password",
                    help="Se não fornecida, usará a variável de ambiente GOOGLE_API_KEY"
                )
            
            return {
                'use_gemini': use_gemini,
                'gemini_api_key': gemini_api_key if gemini_api_key else None
            }
    
    def render_main_content(self, config: Dict[str, Any]):
        """
        Renderiza o conteúdo principal da aplicação.
        
        Args:
            config: Configurações do usuário da barra lateral
        """
        # Título principal
        st.markdown('<h1 class="main-header">🤖 Sistema de Cálculo de Benefícios (Agent-to-Agent)</h1>', 
                   unsafe_allow_html=True)
        
        # Área de upload e processamento
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("📁 Upload de Arquivo")
            st.write("Faça o upload de um arquivo ZIP contendo as planilhas de dados dos funcionários.")
            
            uploaded_file = st.file_uploader(
                "Selecione o arquivo ZIP",
                type=['zip'],
                help="O arquivo deve conter planilhas Excel (.xlsx, .xls) ou CSV com dados dos funcionários"
            )
            
            # Botão de processamento
            process_button = st.button(
                "🚀 Processar com Agentes",
                disabled=uploaded_file is None,
                use_container_width=True
            )
        
        with col2:
            st.subheader("📊 Status do Workflow")
            status_placeholder = st.empty()
            
            # Status inicial
            with status_placeholder.container():
                st.info("Aguardando upload do arquivo...")
        
        # Processamento dos dados
        if process_button and uploaded_file is not None:
            self.process_file(uploaded_file, config, status_placeholder)
    
    def process_file(self, uploaded_file, config: Dict[str, Any], status_placeholder):
        """
        Processa o arquivo através do Agente Coordenador.
        
        Args:
            uploaded_file: Arquivo enviado pelo usuário
            config: Configurações do usuário
            status_placeholder: Placeholder para atualizar o status
        """
        try:
            # Atualiza status
            with status_placeholder.container():
                st.warning("🔄 Iniciando processamento com agentes...")
            
            # Lê o arquivo ZIP
            zip_bytes = uploaded_file.read()
            
            # Processa através do Agente Coordenador
            with st.spinner("🤖 Agentes processando dados..."):
                result = self.coordinator.process(
                    zip_file_bytes=zip_bytes,
                    use_gemini=config['use_gemini'],
                    gemini_api_key=config['gemini_api_key']
                )
            
            if not result['success']:
                st.error(f"❌ Erro no processamento: {result['error']}")
                with status_placeholder.container():
                    st.error("Processamento falhou!")
                return
            
            # Atualiza status para sucesso
            with status_placeholder.container():
                st.success("✅ Processamento concluído pelos agentes!")
            
            # Armazena os resultados na sessão
            st.session_state['result'] = result
            st.session_state['upload_time'] = datetime.now()
            
        except Exception as e:
            st.error(f"❌ Erro durante o processamento: {str(e)}")
            with status_placeholder.container():
                st.error("Erro no processamento!")
            return
    
    def display_results(self, result: Dict[str, Any]):
        """
        Exibe os resultados do processamento.
        
        Args:
            result: Resultado do processamento pelos agentes
        """
        st.markdown("---")
        st.header("📈 Resultados do Processamento Agent-to-Agent")
        
        df = result['processed_df']
        summary = result['summary']
        gemini_analysis = result.get('gemini_analysis', {})
        
        # Métricas principais
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total de Funcionários",
                summary.get('total_funcionarios', 0),
                help="Número total de funcionários processados pelo DataProcessorAgent"
            )
        
        with col2:
            st.metric(
                "Funcionários Elegíveis",
                summary.get('funcionarios_elegiveis', 0),
                help="Funcionários elegíveis calculados pelo EligibilityCalculatorAgent"
            )
        
        with col3:
            st.metric(
                "Funcionários Inelegíveis",
                summary.get('funcionarios_inelegiveis', 0),
                help="Funcionários inelegíveis identificados pelas regras"
            )
        
        with col4:
            st.metric(
                "Custo Total",
                f"R$ {summary.get('total_beneficio_geral', 0):,.2f}",
                help="Valor total dos benefícios calculado pelos agentes"
            )
        
        # Resumo por sindicato
        st.subheader("📊 Resumo por Sindicato")
        
        sindicato_data = []
        for sindicato, data in summary.get('resumo_por_sindicato', {}).items():
            sindicato_data.append({
                'Sindicato': sindicato,
                'Funcionários': data['funcionarios'],
                'Total Benefício': f"R$ {data['total_beneficio']:,.2f}"
            })
        
        if sindicato_data:
            sindicato_df = pd.DataFrame(sindicato_data)
            st.dataframe(sindicato_df, use_container_width=True)
        
        # Tabela de funcionários elegíveis
        st.subheader("👥 Funcionários Elegíveis")
        
        eligible_df = df[df['Elegivel'] == 'Sim'].copy()
        if not eligible_df.empty:
            # Seleciona colunas relevantes para exibição
            display_columns = ['MATRICULA', 'EMPRESA', 'TITULO DO CARGO', 'DESC. SITUACAO', 'Sindicato']
            display_df = eligible_df[display_columns].copy()
            
            # Formata valores monetários
            for col in ['Valor_Beneficio_Base', 'Ajuste_Sindicato', 'Valor_Beneficio_Final']:
                if col in display_df.columns:
                    display_df[col] = display_df[col].apply(lambda x: f"R$ {x:,.2f}")
            
            st.dataframe(display_df, use_container_width=True)
        else:
            st.warning("Nenhum funcionário elegível encontrado.")
        
        # Funcionários inelegíveis
        ineligible_df = df[df['Elegivel'] == 'Não'].copy()
        if not ineligible_df.empty:
            with st.expander("❌ Funcionários Inelegíveis"):
                ineligible_display = ineligible_df[['Nome', 'Cargo', 'Status', 'Sindicato', 'Motivo_Inelegibilidade']].copy()
                st.dataframe(ineligible_display, use_container_width=True)
        
        # Análise com Gemini (se disponível)
        if gemini_analysis:
            self.display_gemini_analysis(gemini_analysis)
        
        # Seção de downloads
        self.display_download_section(df, summary)
    
    def display_gemini_analysis(self, gemini_analysis: Dict[str, str]):
        """
        Exibe a análise gerada pelo Gemini.
        
        Args:
            gemini_analysis: Análises geradas pelo AnalysisAgent
        """
        st.subheader("🤖 Análise com IA (AnalysisAgent + Gemini)")
        
        # Tabs para diferentes tipos de análise
        tab1, tab2, tab3 = st.tabs(["📊 Análise Detalhada", "📋 Resumo Executivo", "📖 Critérios de Elegibilidade"])
        
        with tab1:
            st.markdown(gemini_analysis.get('detailed_analysis', 'Análise não disponível'))
        
        with tab2:
            st.markdown(gemini_analysis.get('executive_summary', 'Resumo não disponível'))
        
        with tab3:
            st.markdown(gemini_analysis.get('eligibility_explanation', 'Explicação não disponível'))
    
    def display_download_section(self, df: pd.DataFrame, summary: Dict[str, Any]):
        """
        Exibe a seção de downloads.
        
        Args:
            df: DataFrame processado
            summary: Resumo dos cálculos
        """
        st.subheader("💾 Downloads")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Download Excel
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Dados Processados', index=False)
                
                # Adiciona uma planilha de resumo
                summary_df = pd.DataFrame([
                    ['Total de Funcionários', summary.get('total_funcionarios', 0)],
                    ['Funcionários Elegíveis', summary.get('funcionarios_elegiveis', 0)],
                    ['Funcionários Inelegíveis', summary.get('funcionarios_inelegiveis', 0)],
                    ['Custo Total dos Benefícios', f"R$ {summary.get('total_beneficio_geral', 0):,.2f}"]
                ], columns=['Métrica', 'Valor'])
                summary_df.to_excel(writer, sheet_name='Resumo', index=False)
            
            excel_buffer.seek(0)
            
            st.download_button(
                label="📊 Baixar Planilha Excel",
                data=excel_buffer.getvalue(),
                file_name=f"beneficios_a2a_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        
        with col2:
            # Download CSV
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            csv_data = csv_buffer.getvalue()
            
            st.download_button(
                label="📄 Baixar CSV",
                data=csv_data,
                file_name=f"beneficios_a2a_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    def run(self):
        """Executa a aplicação Streamlit."""
        # Configuração inicial
        self.setup_page_config()
        self.setup_custom_css()
        
        # Renderiza a interface
        config = self.render_sidebar()
        self.render_main_content(config)
        
        # Exibe resultados se disponíveis
        if 'result' in st.session_state:
            self.display_results(st.session_state['result'])

