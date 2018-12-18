# Get DB credentials from standard places

import dbcredentials
import pymysql

def opendb(name):
    """Open the database with the name given"""
    
    dbc = dbcredentials.DBcred()
    h,d,u,p = dbc.get(name)
    return  pymysql.connect(host=h, user=u, passwd=p, db=d)
     
