"""
Sistema de Cálculo de Benefícios - Arquitetura Agent-to-Agent (A2A)

Este sistema utiliza uma arquitetura multi-agente para processar dados de funcionários
e calcular benefícios de vale alimentação/refeição.

Agentes:
- DataProcessorAgent: Processa e unifica dados de planilhas
- EligibilityCalculatorAgent: Aplica regras de elegibilidade e calcula benefícios
- AnalysisAgent: Gera análises usando Google Gemini
- CoordinatorAgent: Orquestra o fluxo usando LangGraph
- StreamlitUIAgent: Interface do usuário

Tecnologias:
- Python
- Streamlit
- LangChain/LangGraph
- Google Gemini
- Pandas
"""

import sys
import os

# Adiciona o diretório raiz ao path para importações
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ui.streamlit_ui_agent import StreamlitUIAgent

def main():
    """Função principal da aplicação."""
    # Inicializa e executa o agente de UI
    ui_agent = StreamlitUIAgent()
    ui_agent.run()

if __name__ == "__main__":
    main()

