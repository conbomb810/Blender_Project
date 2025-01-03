import pandas as pd
import numpy as np
import os
def fileReader(filepath):
    fileExtension = os.path.splitext(filepath)[1].lower()

    try:
        if fileExtension == '.csv':
            dataset = pd.read_csv(filepath, encoding = 'unicode_escape', engine= 'python', header= None)
        elif fileExtension in ['.xls','xlsx']:
            dataset = pd.read_excel(filepath, engine='openpyxl')
        else:
            dataset = pd.DataFrame()
            raise ValueError(f"The file extension does not work for this file: {fileExtension}")
    except UnicodeDecodeError as e:
        print(f"Unicode error reading file: {e}")
        dataset= pd.DataFrame()
    except FileNotFoundError as e:
        print(f"File not found: {e}")
        dataset= pd.DataFrame()
    except Exception as e:
        print(f"Error reading file: {e}")
        dataset= pd.DataFrame()

    return dataset