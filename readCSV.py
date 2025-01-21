import pandas as pd
def saveFileAsArr(fileName):
    arr = []
    file = pd.read_csv(fileName)
    for i in range(len(file)):
        arr.append((int(file.loc[i][0]), int(file.loc[i][1]), int(file.loc[i][2])))
    return arr