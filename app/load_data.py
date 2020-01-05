import pandas as pd
import numpy as np

class load_data:

    def __init__(self, file_path):
        self.file_path = file_path
    
    def get_df(self):
        df = pd.read_csv(self.file_path)
        return df
