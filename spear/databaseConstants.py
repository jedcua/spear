"""
Database Constants.
    This is a special module for representing all constant
    strings and integers such as Database name, TableNames,
    Column Names and index numbers for interfacing with the
    MySQL through SPEAR's Database module.
"""
#Database Connection
SQL_USERNAME = "root"  #Username when connecting to the MySQL Server.
SQL_HOSTSERVER = "127.0.0.1" #IP Address or Hostname of the MySQL Server.
SQL_DATABASE = "spear" #Database to use upon connecting to MySQL Server.

SPEAR_SRV_BIND_ADDR = "0.0.0.0" #IP address / Network interface to bind the SPEAR server to.
SPEAR_SRV_BIND_PORT = 1475 # Port number to bind the SPEAR server to.

#For MySQL Queries and Parsing
DATABSE_NAME = "spear"
TABLE_NAME = "licensePlates"

COL_ALPHACODE_NAME = "AlphaNumCode"
COL_ALPHACODE_INDEX = 0

COL_CATEGORY_NAME = "Category"
COL_CATEGORY_INDEX = 1

COL_EXPDATE_NAME = "ExpirationDate"
COL_EXPDATE_INDEX = 2

COL_ISSTOLEN_NAME = "IsStolen"
COL_ISSTOLEN_INDEX = 3

COL_ISHOTCAR_NAME = "IsHotCar"
COL_ISHOTCAR_INDEX = 4

"""
STATUS CODE BYTE - Represents status of License Plate upon query to SPEAR Server

Bit Representation: ABCD
    A:
        0 - Registered
        1 - Unregistered
    B:
        0 - Updated
        1 - Expired
    C:
        0 - Not Stolen
        1 - Stolen
    D:
        0 - Not Hot Car
        1 - Hot Car
"""

STAT_OK = 0x00    #0000
STAT_H = 0x01     #0001
STAT_S = 0x02     #0010
STAT_HS = 0x03    #0011
STAT_E = 0x04     #0100
STAT_HE = 0x05    #0101
STAT_SE = 0x06    #0110
STAT_HSE = 0x07   #0111
STAT_UR  = 0x08   #1000

STAT_ERROR = 0x0F #1111 - An error occured in Server, Client MUST resend

def interpretCode(code):

    if code == 0:
        return ["Clear"]
    elif code == 1:
        return ["Wanted"]
    elif code == 2:
        return ["Stolen"]
    elif code == 3:
        return ["Stolen", "Wanted"]
    elif code == 4:
        return ["Expired"]
    elif code == 5:
        return ["Wanted", "Expired"]
    elif code == 6:
        return ["Stolen", "Expired"]
    elif code == 7:
        return ["Wanted", "Stolen", "Expired"]
    elif code == 8:
        return ["Unregistered"]
    elif code == 15:
        return ["Server Error"]
    else:
        return ["Unknown Error"]
