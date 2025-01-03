import pandas as pd
import numpy as np
from functools import wraps
import os

def importMocap(func):

    @wraps(func)

    def wrapper(filepath,*args,**kwargs):
        # This would be where I do some kind of preprocessing
        print(f'File Name: {filepath}')

        try:
            result = func(filepath, *args,**kwargs)
            print('Import Complete')
        except Exception as e:
            print(f"Error: {e}")
            return pd.DataFrame()
        
        # The dataframe is now uploaded appropriately, time to clean it up.

        # Starting with creating a copy of the dataframe to manipulate it
        dataset = result.copy()

        # Finding where in the dataframe contains 'AMTI' in the 3rd column (aka the label column)
        labelLocation = result[2][result[2].str.contains('LFHD') == True].index[0]
        
        # Grabbing the column labels
        columnLabels = result.iloc[labelLocation].dropna().to_list()

        # Cleaning up the column labels so that it removes the participant code
        for count, marker in enumerate(columnLabels):
            splitName = marker.split(':')
            columnLabels[count] = splitName[1]

        # Finding the device frequency, is always 1 row before the column labels and in the first column
        deviceFrequency = int(result[0].iloc[labelLocation - 1])

        # Adding 3 to the starting position because that is where the data officially starts
        startLocation = labelLocation + 3

        # Chopping off the unneccessary data
        dataset = dataset.iloc[startLocation:].reset_index(drop=True)

        # Isolating the first column to find where the dataset ends. Should be where we go from non-NAN value to suddenly a NAN
        # value. Chose the first column because it is formatted uniformly even if there are missing values
        emptyValues = dataset[0].isna()
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
            print('Assumed last section of datasheet')


        # Now the dataset is vertically taken care of. Now need to cut off the columns that don't apply
        numEmptyVals = dataset.isnull().sum()
        colsToDrop = numEmptyVals[numEmptyVals == dataset.shape[0]].index.to_list()

        # # Dropping the columns that are all empty values
        dataset = dataset.drop(colsToDrop, axis=1)

        # Dropping the first two columns that contains the frames and subframes (going to base the time off of index
        # and device frequency)
        dataset = dataset.drop([0,1], axis=1)

        # # Creating a multi-level index in the columns section since each force plate will have its own X, Y and Z outputs. The multiindex
        # # # is an OBJECT that has its own properties and can be used alongside the dataframe. Takes in a series/array-like object.
        newIndex = pd.MultiIndex.from_product([(dataset.index + 1)/deviceFrequency], names = ['Time (s)']) 
        newColumns = pd.MultiIndex.from_product([columnLabels, ['X', 'Y', 'Z']], names = ['Markers', 'Axis'])

        # # Creating the dataframe that is properly indexed
        mocapTable= pd.DataFrame(dataset.values, index = newIndex, columns = newColumns)

        # Casing the data to be a float64
        mocapTable = mocapTable.astype(dtype = np.dtype('float64'))

        # Checking to see if the cleaned dataset shape is 36 columns long (should be for forceplate data every time)
        if dataset.shape[1] != 117:
            print('Dataset may not have been properly cropped, please double check the dataset')

        # Junk used to check certain values properly updating
        print(f'Device Frequency: {deviceFrequency}')
        print('-'*10)

        # Junk stuff for testing
        # print(numEmptyVals)
        # print(emptyValueLocs)
        # print(result.shape)
        # print(dataset.shape)
        # print(len(columnLabels))
        
        return result, dataset, mocapTable
    
    return wrapper