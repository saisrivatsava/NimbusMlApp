import pandas as pd
import numpy as np

class LoadData:

    def get_df(self, file_path):
        df = pd.read_csv(file_path)
        return df
