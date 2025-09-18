from numpy import array, where, exp, log, unique, sort
from copy import copy
from pandas import read_excel
from pathlib import Path
from Library.timer import timer

def calcD14C(df):
    newdf = {}
    #for i,time in enumerate(df['bp']):
    #    df['bp'][i] = round(time,0)
    for key in df.keys():
        newdf[key] = array(df[key])
    newdf['fm'] = array(newdf['fm'],dtype=float)
    newdf['bp'] = array(newdf['bp'], dtype=float)
    newdf['year'] = 1950-newdf['bp']
    newdf['fm_sig'] = array(newdf['fm_sig'], dtype=float)
    newdf['d14C'] = (newdf['fm']*exp(newdf['bp']/8267)-1)*1000
    newdf['d14C_sig'] = newdf['fm_sig']*exp(newdf['bp']/8267)*1000
    newdf['c14_age'] = -8033*log(newdf['fm'])
    newdf['c14_age_sig'] = 8033/newdf['fm']*newdf['fm_sig']
    return newdf

def convertCalendarToBCE(t,bp=False):
    if bp == False:
        try:
            res = array(copy(t))
            neginds = where(res <= 0)
            res[neginds] = res[neginds] - 1
        except:
            res = copy(t)
            if res < 0:
                res -= 1
    else:
        return 1950-t
    return res

@timer
def groupdf(df, sortkey):
    data = {}
    for key in df.keys():
        data[key] = array(df[key])
    _, idx = unique(data[sortkey], return_index=True)
    keys = data[sortkey][sort(idx)]
    result = {}
    for key in keys:
        idx = where(data[sortkey]==key)
        result[key] = {}
        for key2 in data.keys():
            result[key][key2] = data[key2][idx]
    return result

def CE_BCE_format(x,pos):
    if x==0:
        return '1 CE/BCE'
    elif x<0:
        return f'{int(-x)} BCE'
    else: return f'{int(x)} CE'

def getIntcalData():
    df = read_excel(Path('Library/Data/Intcal20.xlsx'))
    data = {'Time': array(df['bp']), 'delta': array(df['Delta14C']), 'delta_sig': array(df['Sigm2']),
            'fm': array(df['fm']), 'fm_sig': array(df['fm_sig']), 'bp': array(df['bp']),'years':1950-array(df['bp'])}
    return data
