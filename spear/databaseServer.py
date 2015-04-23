import pymysql
import socket
import thread
import datetime

import databaseConstants as const

def startServer(NUM_SPEAR_CLIENTS=5, RECV_SIZE=2048):

    """
    Method:
        Initializes the SPEAR Server to perform MySQL queries from SPEAR clients, and
        send those queries on their behalf, then reply to SPEAR clients the result
        of their queries.

    Parameters:
        numSpearClients   - Number of concurrent SPEAR clients to accept.
        recvSize          - Maximum length of Data to receive from SPEAR Clients.

    Returns:
        None.
    """


    spear_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    spear_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    spear_server_socket.bind((const.SPEAR_SRV_BIND_ADDR, const.SPEAR_SRV_BIND_PORT))
    spear_server_socket.listen(NUM_SPEAR_CLIENTS)

    _acceptSpearClients(NUM_SPEAR_CLIENTS, spear_server_socket, RECV_SIZE)

    try:
        while True:
            pass
    except KeyboardInterrupt:
        pass

    print "Closing MySQL Client and SPEAR Server..."

    spear_server_socket.close()


class SpearClient:

    def __init__(self, (client_socket, (ip, port))):
        self.socket = client_socket
        self.ip = ip
        self.port = port


class LicensePlateData:

    def __init__(self, inp_data_list):

        self.alphaNumCode = inp_data_list[const.COL_ALPHACODE_INDEX]
        self.category = inp_data_list[const.COL_CATEGORY_INDEX]
        self.expDate = inp_data_list[const.COL_EXPDATE_INDEX]
        self.isStolen = inp_data_list[const.COL_ISSTOLEN_INDEX]
        self.isHotCar = inp_data_list[const.COL_ISHOTCAR_INDEX]


def _acceptSpearClients(NUM_CLIENTS, server_socket, RECV_SIZE):

    for i in range(NUM_CLIENTS):
        thread.start_new_thread(_processClient, (server_socket, RECV_SIZE))


def _processClient(server_socket, RECV_SIZE):

    this_spear_client = SpearClient(server_socket.accept())

    #Every thread will have its own MySQL connection string and cursor
    sql_conn = pymysql.connect(user=const.SQL_USERNAME, host=const.SQL_HOSTSERVER, database=const.SQL_DATABASE)
    sql_cur = sql_conn.cursor()

    while True:

        #Receives in the form of ABC123 or ABC1234
        client_msg = this_spear_client.socket.recv(RECV_SIZE).strip("\n")

        if not(client_msg) or client_msg == '':
            break

        stat_code  = _queryToSQLServer(client_msg, sql_cur)

        this_spear_client.socket.send(str(stat_code) + "\n")

    #Close MySQL Connections
    sql_cur.close()
    sql_conn.close()

    #Recurse method after SPEAR client disconnects
    this_spear_client.socket.close()

    return _processClient(server_socket, RECV_SIZE)


def _queryToSQLServer(client_msg, sql_cursor):

    query = "SELECT * FROM %s WHERE %s = '%s' LIMIT 1;" %(const.TABLE_NAME,
                                                          const.COL_ALPHACODE_NAME,
                                                          client_msg)

    #If querying is too fast, it may result in AssertionError,
    #if so, then query again
    while  True:
        try:
            has_result = sql_cursor.execute(query)
            break

        except AssertionError:
            pass


    if has_result:

        fetched_data = sql_cursor.fetchall()

        if fetched_data:
            plate_data = LicensePlateData(fetched_data[0])
            status_code = _getStatusCode(plate_data)

        else:
            status_code = const.STAT_ERROR

    else:
        #Unregistered
        status_code = const.STAT_UR

    return status_code


def _getStatusCode(plate_data):

    #Expiration Date
    date_today = datetime.date.today()
    exp_date = plate_data.expDate

    if (exp_date - date_today).days > 0:
        is_expired = 0
    else:
        is_expired = 1

    is_stolen = plate_data.isStolen
    is_hotCar = plate_data.isHotCar

    flag_stat = (is_expired, is_stolen, is_hotCar)

    if flag_stat == (0, 0, 0):
        return const.STAT_OK

    elif flag_stat == (0, 0, 1):
        return const.STAT_H

    elif flag_stat == (0, 1, 0):
        return const.STAT_S

    elif flag_stat == (0, 1, 1):
        return const.STAT_HS

    elif flag_stat == (1, 0 ,0):
        return const.STAT_E

    elif flag_stat == (1, 0, 1):
        return const.STAT_HE

    elif flag_stat == (1, 1, 0):
        return const.STAT_SE

    elif flag_stat == (1, 1, 1):
        return const.STAT_HSE


