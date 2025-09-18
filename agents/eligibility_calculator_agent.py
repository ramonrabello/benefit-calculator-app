import pandas as pd
from typing import Dict, Any, List

class EligibilityCalculatorAgent:
    """
    Agente responsável por aplicar as regras de elegibilidade e calcular os benefícios finais.
    """
    
    def __init__(self):
        self.name = "EligibilityCalculatorAgent"
        
        # Configurações padrão para sindicatos
        self.sindicato_ajustes = {
            'SP': 50,
            'RJ': 70,
            'PR': 60,
            'RS': 80
        }
        
        # Critérios de inelegibilidade
        self.cargos_inelegiveis = ['Estagiário', 'Aprendiz', 'Diretor']
        self.status_inelegiveis = ['Afastado', 'Demitido']
        self.locais_inelegiveis = ['Exterior']
    
    def apply_eligibility_rules(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Aplica as regras de elegibilidade aos funcionários.
        
        Args:
            df: DataFrame com os dados dos funcionários
            
        Returns:
            DataFrame com colunas adicionais de elegibilidade
        """
        df_copy = df.copy()
        
        # Inicializa colunas de elegibilidade
        df_copy['Elegivel'] = 'Sim'
        df_copy['Motivo_Inelegibilidade'] = ''
        
        # Aplica regras de inelegibilidade
        for index, row in df_copy.iterrows():
            motivos = []
            
            # Verifica cargo
            if 'Cargo' in row and pd.notna(row['Cargo']) and row['Cargo'] in self.cargos_inelegiveis:
                motivos.append(f"Cargo: {row['Cargo']}")
            
            # Verifica status
            if 'Status' in row and pd.notna(row['Status']) and row['Status'] in self.status_inelegiveis:
                motivos.append(f"Status: {row['Status']}")
            
            # Verifica localização (sindicato)
            if 'Sindicato' in row and pd.notna(row['Sindicato']) and row['Sindicato'] in self.locais_inelegiveis:
                motivos.append(f"Localização: {row['Sindicato']}")
            
            if motivos:
                df_copy.at[index, 'Elegivel'] = 'Não'
                df_copy.at[index, 'Motivo_Inelegibilidade'] = '; '.join(motivos)
        
        return df_copy
    
    def calculate_benefits(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcula os benefícios finais aplicando os ajustes por sindicato.
        
        Args:
            df: DataFrame com os dados dos funcionários elegíveis
            
        Returns:
            DataFrame com os valores de benefício calculados
        """
        df_copy = df.copy()
        
        # Inicializa colunas de cálculo
        df_copy['Ajuste_Sindicato'] = 0
        df_copy['Valor_Beneficio_Final'] = 0
        
        # Calcula apenas para funcionários elegíveis
        eligible_mask = df_copy['Elegivel'] == 'Sim'
        
        for index, row in df_copy[eligible_mask].iterrows():
            sindicato = row.get('Sindicato', '')
            valor_base = row.get('Valor_Beneficio_Base', 0)
            
            # Converte valor_base para float se necessário
            try:
                valor_base = float(valor_base) if pd.notna(valor_base) else 0
            except (ValueError, TypeError):
                valor_base = 0
            
            # Aplica ajuste por sindicato
            ajuste = self.sindicato_ajustes.get(sindicato, 0)
            valor_final = valor_base + ajuste
            
            df_copy.at[index, 'Ajuste_Sindicato'] = ajuste
            df_copy.at[index, 'Valor_Beneficio_Final'] = valor_final
        
        return df_copy
    
    def generate_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Gera um resumo dos benefícios calculados.
        
        Args:
            df: DataFrame com os benefícios calculados
            
        Returns:
            Dicionário com o resumo dos resultados
        """
        eligible_df = df[df['Elegivel'] == 'Sim']
        
        summary = {
            'total_funcionarios': len(df),
            'funcionarios_elegiveis': len(eligible_df),
            'funcionarios_inelegiveis': len(df) - len(eligible_df),
            'total_beneficio_geral': float(eligible_df['Valor_Beneficio_Final'].sum()),
            'resumo_por_sindicato': {}
        }
        
        # Resumo por sindicato
        for sindicato in self.sindicato_ajustes.keys():
            sindicato_df = eligible_df[eligible_df['Sindicato'] == sindicato]
            summary['resumo_por_sindicato'][sindicato] = {
                'funcionarios': len(sindicato_df),
                'total_beneficio': float(sindicato_df['Valor_Beneficio_Final'].sum())
            }
        
        return summary
    
    def get_ineligibility_breakdown(self, df: pd.DataFrame) -> Dict[str, int]:
        """
        Analisa os motivos de inelegibilidade e retorna um breakdown.
        
        Args:
            df: DataFrame com os dados processados
            
        Returns:
            Dicionário com contagem de motivos de inelegibilidade
        """
        ineligible_df = df[df['Elegivel'] == 'Não']
        
        if ineligible_df.empty:
            return {}
        
        # Conta os motivos de inelegibilidade
        motivos = {}
        for motivo in ineligible_df['Motivo_Inelegibilidade']:
            if pd.notna(motivo) and motivo:
                for m in motivo.split(';'):
                    m = m.strip()
                    motivos[m] = motivos.get(m, 0) + 1
        
        return motivos
    
    def process(self, unified_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Processa completamente a elegibilidade e cálculo de benefícios.
        
        Args:
            unified_df: DataFrame unificado com dados dos funcionários
            
        Returns:
            Dicionário contendo o DataFrame processado e resumo
        """
        try:
            if unified_df.empty:
                return {
                    'success': False,
                    'processed_df': pd.DataFrame(),
                    'summary': {},
                    'ineligibility_breakdown': {},
                    'error': 'DataFrame vazio fornecido'
                }
            
            # Aplica regras de elegibilidade
            eligible_df = self.apply_eligibility_rules(unified_df)
            
            # Calcula benefícios
            final_df = self.calculate_benefits(eligible_df)
            
            # Gera resumo
            summary = self.generate_summary(final_df)
            
            # Gera breakdown de inelegibilidade
            ineligibility_breakdown = self.get_ineligibility_breakdown(final_df)
            
            return {
                'success': True,
                'processed_df': final_df,
                'summary': summary,
                'ineligibility_breakdown': ineligibility_breakdown,
                'error': None
            }
            
        except Exception as e:
            return {
                'success': False,
                'processed_df': pd.DataFrame(),
                'summary': {},
                'ineligibility_breakdown': {},
                'error': str(e)
            }

