""" pyomotools: common helper functions for pyomo model creation """
from datetime import datetime
import pandas as pd
import xlrd

def now(mydateformat='%Y%m%dT%H%M%S'):
    """Return current datetime as string with custom format
    
    Args:
        mydateformat: optional format string (default: '%Y%m%dT%H%M%S')
    
    Returns:
        datetime.now(), formated to string with argument mydateformat
    """
    return datetime.now().strftime(mydateformat)


def read_xls(filename):
    """Return list of pandas DataFrames from Excel spreadsheet"""
    
    dfs = {}
    xls = pd.ExcelFile(filename)
    for sheet in xls.book.sheets():
        first_row = sheet.row_slice(0)
        
        # skip sheet if completely empty or first cell is blank
        if not first_row or first_row[0].ctype in (xlrd.XL_CELL_BLANK,
                                                   xlrd.XL_CELL_EMPTY):
            continue
            
        # otherwise determine column numbers of titles starting with an
        # uppercase lettre...
        
        uppercase_columns = [k for k, ct in enumerate(first_row) 
                             if ct.value[0].isupper()]
                             
        # ... and parse those to a pandas DataFrame
        dfs[sheet.name] = xls.parse(sheet.name, index_col=uppercase_columns)
            
    return dfs