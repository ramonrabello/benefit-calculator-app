import zipfile
import pandas as pd
import os
import tempfile
from typing import List, Dict, Any, Optional
import io

class DataProcessorAgent:
    """
    Agente responsável por processar os dados brutos dos funcionários.
    Extrai arquivos ZIP e unifica múltiplas planilhas em um único DataFrame.
    """
    
    def __init__(self):
        self.name = "DataProcessorAgent"
    
    def extract_zip_file(self, zip_file_bytes: bytes) -> List[pd.DataFrame]:
        """
        Extrai e lê todas as planilhas de um arquivo ZIP.
        
        Args:
            zip_file_bytes: Bytes do arquivo ZIP
            
        Returns:
            Lista de DataFrames contendo os dados das planilhas
            
        Raises:
            Exception: Se houver erro na extração ou leitura dos arquivos
        """
        dataframes = []
        
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                # Salva o arquivo ZIP temporariamente
                zip_path = os.path.join(temp_dir, 'uploaded.zip')
                with open(zip_path, 'wb') as f:
                    f.write(zip_file_bytes)
                
                # Extrai o ZIP
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                
                # Lê todos os arquivos Excel/CSV extraídos
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        if file.endswith(('.xlsx', '.xls', '.csv')):
                            file_path = os.path.join(root, file)
                            try:
                                if file.endswith('.csv'):
                                    df = pd.read_csv(file_path)
                                else:
                                    df = pd.read_excel(file_path)
                                
                                if not df.empty:
                                    dataframes.append(df)
                            except Exception as e:
                                print(f"Erro ao ler arquivo {file}: {e}")
                                continue
        
        except Exception as e:
            raise Exception(f"Erro na extração do ZIP: {str(e)}")
        
        return dataframes
    
    def unify_dataframes(self, dataframes: List[pd.DataFrame]) -> pd.DataFrame:
        """
        Unifica múltiplos DataFrames em um único DataFrame.
        
        Args:
            dataframes: Lista de DataFrames para unificar
            
        Returns:
            DataFrame unificado
            
        Raises:
            Exception: Se não houver DataFrames válidos para unificar
        """
        if not dataframes:
            raise Exception("Nenhum DataFrame válido encontrado para unificar")
        
        # Padroniza os nomes das colunas
        standardized_dfs = []
        for df in dataframes:
            df_copy = df.copy()
            
            # Mapeia possíveis variações de nomes de colunas
            column_mapping = {
                'matricula': 'MATRICULA',
                'empresa': 'EMPRESA',
                'titulo_cargo': 'TITULO DO CARGO',
                'desc_situacao': 'DESC. SITUACAO',
                'sindicato': 'Sindicato'
            }
            
            # Renomeia as colunas (case-insensitive)
            df_copy.columns = [column_mapping.get(str(col).lower(), col) for col in df_copy.columns]
            
            standardized_dfs.append(df_copy)
        
        # Concatena todos os DataFrames
        unified_df = pd.concat(standardized_dfs, ignore_index=True)
        
        # Remove duplicatas baseadas na MATRICULA, se existir
        if 'MATRICULA' in unified_df.columns:
            unified_df = unified_df.drop_duplicates(subset=['MATRICULA'], keep='first')
        
        return unified_df
    
    def process(self, zip_file_bytes: bytes) -> Dict[str, Any]:
        """
        Processa completamente um arquivo ZIP com dados de funcionários.
        
        Args:
            zip_file_bytes: Bytes do arquivo ZIP
            
        Returns:
            Dicionário contendo o DataFrame unificado e metadados
        """
        try:
            # Extrai e unifica os dados
            dataframes = self.extract_zip_file(zip_file_bytes)
            unified_df = self.unify_dataframes(dataframes)
            
            return {
                'success': True,
                'unified_df': unified_df,
                'total_files': len(dataframes),
                'total_records': len(unified_df),
                'columns': list(unified_df.columns),
                'error': None
            }
            
        except Exception as e:
            return {
                'success': False,
                'unified_df': pd.DataFrame(),
                'total_files': 0,
                'total_records': 0,
                'columns': [],
                'error': str(e)
            }

