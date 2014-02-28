""" pyomotools: common helper functions for pyomo model creation """
from datetime import datetime
import pandas as pd
import xlrd

__all__ = ["now", "read_xls"]

def now(mydateformat='%Y%m%dT%H%M%S'):
    """ Return current datetime as string.
    
    Just a shorthand to abbreviate the common task to obtain the current 
    datetime as a string, e.g. for result versioning.
    
    Args:
        mydateformat: optional format string (default: '%Y%m%dT%H%M%S')
    
    Returns:
        datetime.now(), formated to string with argument mydateformat, e.g.
        YYYYMMDDThhmmss ==> 20131007H123456
    """
    return datetime.now().strftime(mydateformat)


def read_xls(filename, sheets=[]):
    """ Convert Excel file to dict of pandas DataFrames.
    
    Parses all spreadsheets within an Excel file using pandas.ExcelFile.parse,
    if its top left cell is not empty. The first row is expected to contain
    column titles. Titles starting with uppercase lettres are used as index
    columns in the resulting DataFrame. Here is a short example summarizing
    these specifications:
    
      Process CoIn   CoOut  | cap   eff ... avail
      -------------------------------------------
      PP      Coal   Elec   | 100  0.90 ...    24
      WT      Wind   Elec   | 300  0.95 ...    10
      PV      Solar  Elec   | 200  0.92 ...     8
      
    A spreadsheet is skipped if a) it is completely empty or b) has an empty 
    first row.
    
    Args:
        filename: an Excel spreadsheet filename
        
    Returns:
        dict of pandas DataFrames with sheet names as keys
    """
    
    dfs = {}
    xls = pd.ExcelFile(filename)
    for sheet in xls.book.sheets():
        # skip sheet if list of sheets was specified
        if sheets and sheet.name not in sheets:
            continue
        
        # extract the sheet's first row to check for emptiness
        first_row = sheet.row_slice(0)
        
        # skip a spreadsheet if completely empty or its first cell is blank
        if not first_row \
           or first_row[0].ctype in (xlrd.XL_CELL_BLANK, xlrd.XL_CELL_EMPTY):
            continue
            
        # otherwise determine column numbers of titles starting with an
        # uppercase lettre...
        uppercase_columns = [k for k, column_title in enumerate(first_row) 
                             if column_title.value[0].isupper()]
                             
        # ... and parse those to a pandas DataFrame
        dfs[sheet.name] = xls.parse(sheet.name, index_col=uppercase_columns)
            
    return dfs