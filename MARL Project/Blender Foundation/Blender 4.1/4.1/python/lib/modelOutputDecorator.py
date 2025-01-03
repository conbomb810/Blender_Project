import pandas as pd
import numpy as np
from functools import wraps
import os
"""The purpose of this function is to wrap the fileReader function and add functionality
by parsing the data in a way that is tailored to the force plate data. It cleans up the data
so that it can be in a usable and organized format.



Parameters:
-----------
'filepath'  :   a single variable (x)
                the filepath that is formatted correctly. It can be a pathlib object, string with
                correct formatting (uses \\ or /), any appropriate format for a filepath. 

Returns:
-----------
'result'    :   a pandas DataFrame
                the original dataframe that was imported into the function using fileReader
'dataset'   :   a pandas DataFrame
                the dataframe that is properly sectioned to the relevant dataset
'outputTable'    :  a pandas DataFrame
                        the final dataframe that has been thouroughly cleaned and contains only the
                        force plate data. It should be multi-indexed by device and axis to allow for
                        more intentional accessing.
"""
def importModelOutputs(func):

    @wraps(func)

    def wrapper(filepath,*args,**kwargs):
        # This would be where I do some kind of preprocessing
        print(f'File Name: {filepath}')

        try:
            result = func(filepath, *args,**kwargs)
            print('Function Complete')
        except Exception as e:
            print(f"Error: {e}")
            return pd.DataFrame()
        
        # The dataframe is now uploaded appropriately, time to clean it up.

        # Starting with creating a copy of the dataframe to manipulate it
        dataset = result.copy()

        # Finding where in the dataframe contains 'AMTI' in the 3rd column (aka the label column)
        labelLocation = result[2][result[2].str.contains('CentreOfMass') == True].index[0]

        
        # Grabbing the column labels
        columnLabels = result.iloc[labelLocation].dropna().to_list()

        # # Cleaning up the column labels so that it removes the participant code
        # for count, marker in enumerate(columnLabels):
        #     splitName = marker.split(':')
        #     columnLabels[count] = splitName[1]

        # Finding the device frequency, is always 1 row before the column labels and in the first column
        deviceFrequency = int(result[0].iloc[labelLocation - 1])

        # Chopping off the unneccessary data
        dataset = dataset.iloc[labelLocation:].reset_index(drop=True)

        # Isolating the first column to find where the dataset ends. Should be where we go from non-NAN value to suddenly a NAN
        # value. Chose the first column because it is formatted uniformly even if there are missing values.
        # ! Note here that because I am keeping the label columns because of the odd outputs (uneven distribution of X, Y, Z)
        # ! so I need to add 3 to where it starts counting NAN's otherwise it'll find a location that is too early
        emptyValues = dataset[0].iloc[3:].isna()
        emptyValueLocs = []

        for num in emptyValues.index:
            try:
                if emptyValues[num] == False and emptyValues[num+1] == True:
                    emptyValueLocs.append(num)
                    
            except KeyError:
                print('Finished finding breakpoints of dataset')
        
        
        # The end of the dataset should be the first instance
        try:
            endLocation = emptyValueLocs[0] + 1
            
            # Cutting off data that is not apart of the dataset
            dataset = dataset.iloc[:endLocation]
        except IndexError:
            print('This is the last section until the end so no need for endLocation')


        # Dropping the first two columns that contains the frames and subframes (going to base the time off of index
        # and device frequency)
        dataset = dataset.drop([0,1], axis=1)



        # Replacing the empty values (NAN) in the label row by propagating the last valid observation
        dataset.iloc[0] = dataset.iloc[0].ffill()

        # Cleaning up the column labels so that the participant code isnt there
        dataset.iloc[0] = dataset.iloc[0].apply(lambda x: x.split(':')[1])


        # Now creating a multi-index to properly access the data
        tuplesForIndexing = list(zip(dataset.iloc[0],dataset.iloc[1]))
        multiIndex = pd.MultiIndex.from_tuples(tuplesForIndexing)

        # Changing the name of the columns to properly apply the multi-index
        dataset.columns = multiIndex

        # Dropping the measurement unit row and the 2 rows used for multi-indexing the columns
        dataset = dataset.drop([0,1,2])

        # Resetting the index now that unneccessary rows are dropped
        dataset = dataset.reset_index(drop=True)

        # Now the unneccessary rows are out of the way, now we can create a time index
        timeIndex = pd.MultiIndex.from_product([(dataset.index + 1)/deviceFrequency], names = ['Time (s)'])
        dataset.index = timeIndex

        # The Vicon model output has roughly 42 columns that are straight up duplicates. Removing 
        # those duplicates
        dataset = dataset.loc[:,~dataset.columns.duplicated()]

        # Casting the data to be a float64
        outputTable = dataset.astype(dtype = np.dtype('float64'))

        # Printing Device Frequency
        print(f'Device Frequency: {deviceFrequency}')
        print('-'*10)

        # Junk used to check certain values properly updating
        # print(columnLabels)
        # print(deviceFrequency)
        # print(numEmptyVals)
        # print(emptyValueLocs)
        # print(result.shape)
        # print(dataset.shape)
        # print(labelLocation)
        # print(len(columnLabels))
        
        return result, dataset, outputTable
    
    return wrapper