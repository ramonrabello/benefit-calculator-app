import os
from typing import Dict, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage
import pandas as pd

class AnalysisAgent:
    """
    Agente responsável por integrar com o Google Gemini via LangChain
    para análises e sumarizações dos dados de benefícios.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Inicializa o agente de análise.
        
        Args:
            api_key: Chave da API do Google Gemini (opcional, pode usar variável de ambiente)
        """
        self.name = "AnalysisAgent"
        self.api_key = api_key or os.getenv('GOOGLE_API_KEY')
        self.llm = None
        
        if self.api_key:
            try:
                # Inicializa o modelo Gemini via LangChain
                self.llm = ChatGoogleGenerativeAI(
                    model="gemini-pro",
                    google_api_key=self.api_key,
                    temperature=0.3
                )
            except Exception as e:
                print(f"Erro ao inicializar Gemini: {e}")
                self.llm = None
    
    def is_available(self) -> bool:
        """
        Verifica se o agente de análise está disponível (API key configurada).
        
        Returns:
            True se o Gemini estiver disponível, False caso contrário
        """
        return self.llm is not None
    
    def analyze_benefit_data(self, summary: Dict[str, Any], df: pd.DataFrame) -> str:
        """
        Analisa os dados de benefícios e gera insights usando Gemini.
        
        Args:
            summary: Resumo dos dados processados
            df: DataFrame com os dados completos
            
        Returns:
            Análise textual gerada pelo Gemini
        """
        if not self.is_available():
            return "Análise com IA não disponível. Configure a chave da API do Google Gemini."
        
        try:
            # Prepara o contexto para o Gemini
            context = self._prepare_context(summary, df)
            
            system_message = SystemMessage(content="""
            Você é um especialista em análise de benefícios corporativos e recursos humanos.
            Analise os dados fornecidos sobre benefícios de vale alimentação/refeição e forneça:
            
            1. Insights principais sobre a distribuição dos benefícios
            2. Análise da elegibilidade dos funcionários
            3. Observações sobre os custos por sindicato
            4. Recomendações para otimização dos benefícios
            
            Seja objetivo e profissional na análise.
            """)
            
            human_message = HumanMessage(content=f"""
            Analise os seguintes dados de benefícios corporativos:
            
            {context}
            
            Forneça uma análise detalhada e insights úteis para a gestão de RH.
            """)
            
            response = self.llm([system_message, human_message])
            return response.content
            
        except Exception as e:
            return f"Erro na análise com Gemini: {str(e)}"
    
    def generate_executive_summary(self, summary: Dict[str, Any]) -> str:
        """
        Gera um resumo executivo dos resultados.
        
        Args:
            summary: Resumo dos dados processados
            
        Returns:
            Resumo executivo gerado pelo Gemini
        """
        if not self.is_available():
            return "Resumo executivo não disponível. Configure a chave da API do Google Gemini."
        
        try:
            system_message = SystemMessage(content="""
            Você é um assistente executivo especializado em relatórios de RH.
            Crie um resumo executivo conciso e profissional baseado nos dados fornecidos.
            O resumo deve ser adequado para apresentação à diretoria.
            """)
            
            human_message = HumanMessage(content=f"""
            Crie um resumo executivo baseado nos seguintes dados de benefícios:
            
            Total de funcionários: {summary.get('total_funcionarios', 0)}
            Funcionários elegíveis: {summary.get('funcionarios_elegiveis', 0)}
            Funcionários inelegíveis: {summary.get('funcionarios_inelegiveis', 0)}
            Custo total dos benefícios: R$ {summary.get('total_beneficio_geral', 0):,.2f}
            
            Distribuição por sindicato:
            {self._format_sindicato_summary(summary.get('resumo_por_sindicato', {}))}
            """)
            
            response = self.llm([system_message, human_message])
            return response.content
            
        except Exception as e:
            return f"Erro na geração do resumo executivo: {str(e)}"
    
    def explain_eligibility_criteria(self) -> str:
        """
        Gera uma explicação clara dos critérios de elegibilidade.
        
        Returns:
            Explicação dos critérios gerada pelo Gemini
        """
        if not self.is_available():
            return "Explicação de critérios não disponível. Configure a chave da API do Google Gemini."
        
        try:
            system_message = SystemMessage(content="""
            Você é um especialista em políticas de RH.
            Explique de forma clara e didática os critérios de elegibilidade para benefícios corporativos.
            """)
            
            human_message = HumanMessage(content="""
            Explique os seguintes critérios de elegibilidade para benefícios de vale alimentação/refeição:
            
            Funcionários INELEGÍVEIS:
            - Estagiários
            - Aprendizes
            - Diretores
            - Funcionários afastados
            - Funcionários demitidos
            - Funcionários no exterior
            
            Forneça uma explicação clara do porquê cada categoria é considerada inelegível.
            """)
            
            response = self.llm([system_message, human_message])
            return response.content
            
        except Exception as e:
            return f"Erro na explicação dos critérios: {str(e)}"
    
    def _prepare_context(self, summary: Dict[str, Any], df: pd.DataFrame) -> str:
        """
        Prepara o contexto dos dados para análise pelo Gemini.
        
        Args:
            summary: Resumo dos dados
            df: DataFrame com os dados
            
        Returns:
            Contexto formatado como string
        """
        context = f"""
        RESUMO GERAL:
        - Total de funcionários: {summary.get('total_funcionarios', 0)}
        - Funcionários elegíveis: {summary.get('funcionarios_elegiveis', 0)}
        - Funcionários inelegíveis: {summary.get('funcionarios_inelegiveis', 0)}
        - Custo total dos benefícios: R$ {summary.get('total_beneficio_geral', 0):,.2f}
        
        DISTRIBUIÇÃO POR SINDICATO:
        {self._format_sindicato_summary(summary.get('resumo_por_sindicato', {}))}
        
        MOTIVOS DE INELEGIBILIDADE:
        {self._analyze_ineligibility_reasons(df)}
        """
        
        return context
    
    def _format_sindicato_summary(self, sindicato_data: Dict[str, Any]) -> str:
        """
        Formata o resumo por sindicato.
        
        Args:
            sindicato_data: Dados por sindicato
            
        Returns:
            Resumo formatado
        """
        formatted = []
        for sindicato, data in sindicato_data.items():
            funcionarios = data.get('funcionarios', 0)
            total = data.get('total_beneficio', 0)
            formatted.append(f"- {sindicato}: {funcionarios} funcionários, R$ {total:,.2f}")
        
        return "\n".join(formatted)
    
    def _analyze_ineligibility_reasons(self, df: pd.DataFrame) -> str:
        """
        Analisa os motivos de inelegibilidade.
        
        Args:
            df: DataFrame com os dados
            
        Returns:
            Análise dos motivos de inelegibilidade
        """
        if 'Motivo_Inelegibilidade' not in df.columns:
            return "Dados de inelegibilidade não disponíveis"
        
        ineligible_df = df[df['Elegivel'] == 'Não']
        
        if ineligible_df.empty:
            return "Todos os funcionários são elegíveis"
        
        # Conta os motivos de inelegibilidade
        motivos = {}
        for motivo in ineligible_df['Motivo_Inelegibilidade']:
            if pd.notna(motivo) and motivo:
                for m in motivo.split(';'):
                    m = m.strip()
                    motivos[m] = motivos.get(m, 0) + 1
        
        formatted_motivos = []
        for motivo, count in motivos.items():
            formatted_motivos.append(f"- {motivo}: {count} funcionários")
        
        return "\n".join(formatted_motivos)
    
    def process(self, processed_df: pd.DataFrame, summary: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa completamente a análise dos dados com Gemini.
        
        Args:
            processed_df: DataFrame com os dados processados
            summary: Resumo dos cálculos
            
        Returns:
            Dicionário contendo as análises geradas
        """
        try:
            if not self.is_available():
                return {
                    'success': False,
                    'gemini_analysis': {
                        'detailed_analysis': 'Análise com IA não disponível. Configure a chave da API do Google Gemini.',
                        'executive_summary': 'Resumo executivo não disponível. Configure a chave da API do Google Gemini.',
                        'eligibility_explanation': 'Explicação de critérios não disponível. Configure a chave da API do Google Gemini.'
                    },
                    'error': 'API key do Google Gemini não configurada'
                }
            
            # Gera as análises
            detailed_analysis = self.analyze_benefit_data(summary, processed_df)
            executive_summary = self.generate_executive_summary(summary)
            eligibility_explanation = self.explain_eligibility_criteria()
            
            return {
                'success': True,
                'gemini_analysis': {
                    'detailed_analysis': detailed_analysis,
                    'executive_summary': executive_summary,
                    'eligibility_explanation': eligibility_explanation
                },
                'error': None
            }
            
        except Exception as e:
            return {
                'success': False,
                'gemini_analysis': {
                    'detailed_analysis': f'Erro na análise: {str(e)}',
                    'executive_summary': f'Erro no resumo executivo: {str(e)}',
                    'eligibility_explanation': f'Erro na explicação: {str(e)}'
                },
                'error': str(e)
            }

