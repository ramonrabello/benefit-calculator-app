from typing import Dict, Any, Optional, TypedDict
from langgraph.graph import StateGraph, END
import pandas as pd

from .data_processor_agent import DataProcessorAgent
from .eligibility_calculator_agent import EligibilityCalculatorAgent
from .analysis_agent import AnalysisAgent

class GraphState(TypedDict):
    """Estado do grafo que persiste informações entre os nós."""
    zip_file_bytes: bytes
    raw_dataframes: list
    unified_df: pd.DataFrame
    processed_df: pd.DataFrame
    summary: Dict[str, Any]
    ineligibility_breakdown: Dict[str, int]
    gemini_analysis: Dict[str, str]
    error: Optional[str]
    use_gemini: bool
    gemini_api_key: Optional[str]

class CoordinatorAgent:
    """
    Agente Coordenador que orquestra o fluxo de trabalho entre os outros agentes
    usando LangGraph para gerenciar o estado e as transições.
    """
    
    def __init__(self):
        self.name = "CoordinatorAgent"
        self.data_processor = DataProcessorAgent()
        self.eligibility_calculator = EligibilityCalculatorAgent()
        self.analysis_agent = None  # Será inicializado quando necessário
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """
        Constrói o grafo de execução usando LangGraph.
        
        Returns:
            StateGraph configurado com nós e arestas
        """
        # Cria o grafo
        workflow = StateGraph(GraphState)
        
        # Adiciona os nós
        workflow.add_node("process_data", self._process_data_node)
        workflow.add_node("calculate_benefits", self._calculate_benefits_node)
        workflow.add_node("analyze_with_gemini", self._analyze_with_gemini_node)
        
        # Define o ponto de entrada
        workflow.set_entry_point("process_data")
        
        # Define as arestas (transições)
        workflow.add_edge("process_data", "calculate_benefits")
        workflow.add_conditional_edges(
            "calculate_benefits",
            self._should_use_gemini,
            {
                "use_gemini": "analyze_with_gemini",
                "skip_gemini": END
            }
        )
        workflow.add_edge("analyze_with_gemini", END)
        
        return workflow.compile()
    
    def _process_data_node(self, state: GraphState) -> Dict[str, Any]:
        """
        Nó responsável pelo processamento de dados.
        
        Args:
            state: Estado atual do grafo
            
        Returns:
            Atualizações para o estado
        """
        try:
            result = self.data_processor.process(state["zip_file_bytes"])
            
            if result["success"]:
                return {
                    "unified_df": result["unified_df"],
                    "error": None
                }
            else:
                return {
                    "unified_df": pd.DataFrame(),
                    "error": result["error"]
                }
                
        except Exception as e:
            return {
                "unified_df": pd.DataFrame(),
                "error": f"Erro no processamento de dados: {str(e)}"
            }
    
    def _calculate_benefits_node(self, state: GraphState) -> Dict[str, Any]:
        """
        Nó responsável pelo cálculo de elegibilidade e benefícios.
        
        Args:
            state: Estado atual do grafo
            
        Returns:
            Atualizações para o estado
        """
        try:
            # Verifica se há erro anterior
            if state.get("error"):
                return {"error": state["error"]}
            
            result = self.eligibility_calculator.process(state["unified_df"])
            
            if result["success"]:
                return {
                    "processed_df": result["processed_df"],
                    "summary": result["summary"],
                    "ineligibility_breakdown": result["ineligibility_breakdown"],
                    "error": None
                }
            else:
                return {
                    "processed_df": pd.DataFrame(),
                    "summary": {},
                    "ineligibility_breakdown": {},
                    "error": result["error"]
                }
                
        except Exception as e:
            return {
                "processed_df": pd.DataFrame(),
                "summary": {},
                "ineligibility_breakdown": {},
                "error": f"Erro no cálculo de benefícios: {str(e)}"
            }
    
    def _analyze_with_gemini_node(self, state: GraphState) -> Dict[str, Any]:
        """
        Nó responsável pela análise com Gemini.
        
        Args:
            state: Estado atual do grafo
            
        Returns:
            Atualizações para o estado
        """
        try:
            # Verifica se há erro anterior
            if state.get("error"):
                return {"error": state["error"]}
            
            # Inicializa o agente de análise se necessário
            if not self.analysis_agent:
                self.analysis_agent = AnalysisAgent(state.get("gemini_api_key"))
            
            result = self.analysis_agent.process(
                state["processed_df"], 
                state["summary"]
            )
            
            return {
                "gemini_analysis": result["gemini_analysis"],
                "error": result.get("error")
            }
                
        except Exception as e:
            return {
                "gemini_analysis": {
                    "detailed_analysis": f"Erro na análise: {str(e)}",
                    "executive_summary": f"Erro no resumo executivo: {str(e)}",
                    "eligibility_explanation": f"Erro na explicação: {str(e)}"
                },
                "error": f"Erro na análise com Gemini: {str(e)}"
            }
    
    def _should_use_gemini(self, state: GraphState) -> str:
        """
        Função condicional que decide se deve usar o Gemini.
        
        Args:
            state: Estado atual do grafo
            
        Returns:
            String indicando o próximo nó
        """
        # Verifica se há erro anterior
        if state.get("error"):
            return "skip_gemini"
        
        # Verifica se o usuário quer usar Gemini
        if state.get("use_gemini", False):
            return "use_gemini"
        else:
            return "skip_gemini"
    
    def process(self, zip_file_bytes: bytes, use_gemini: bool = False, 
                gemini_api_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Processa completamente um arquivo ZIP através do grafo de agentes.
        
        Args:
            zip_file_bytes: Bytes do arquivo ZIP
            use_gemini: Se deve usar análise com Gemini
            gemini_api_key: Chave da API do Gemini (opcional)
            
        Returns:
            Dicionário com todos os resultados processados
        """
        try:
            # Estado inicial
            initial_state = GraphState(
                zip_file_bytes=zip_file_bytes,
                raw_dataframes=[],
                unified_df=pd.DataFrame(),
                processed_df=pd.DataFrame(),
                summary={},
                ineligibility_breakdown={},
                gemini_analysis={},
                error=None,
                use_gemini=use_gemini,
                gemini_api_key=gemini_api_key
            )
            
            # Executa o grafo
            final_state = self.graph.invoke(initial_state)
            
            # Retorna o resultado final
            return {
                'success': final_state.get("error") is None,
                'processed_df': final_state.get("processed_df", pd.DataFrame()),
                'summary': final_state.get("summary", {}),
                'ineligibility_breakdown': final_state.get("ineligibility_breakdown", {}),
                'gemini_analysis': final_state.get("gemini_analysis", {}),
                'error': final_state.get("error")
            }
            
        except Exception as e:
            return {
                'success': False,
                'processed_df': pd.DataFrame(),
                'summary': {},
                'ineligibility_breakdown': {},
                'gemini_analysis': {},
                'error': f"Erro no coordenador: {str(e)}"
            }
    
    def get_workflow_status(self) -> Dict[str, Any]:
        """
        Retorna informações sobre o workflow configurado.
        
        Returns:
            Dicionário com informações do workflow
        """
        return {
            'name': self.name,
            'agents': [
                self.data_processor.name,
                self.eligibility_calculator.name,
                'AnalysisAgent (opcional)'
            ],
            'workflow_nodes': ['process_data', 'calculate_benefits', 'analyze_with_gemini'],
            'description': 'Coordena o fluxo de processamento de benefícios através de múltiplos agentes especializados'
        }

