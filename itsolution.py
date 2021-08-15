import pyodbc
import os

#########################################################################################
#                                  KeyInfo Class                                        #
#########################################################################################

class KeyInfo:
    def __init__(self, TicketId, KeyName, Password, Email):
        self.TicketId = TicketId
        self.KeyName = KeyName
        self.Email = Email
        self.Password = Password

#########################################################################################
#                                  Methods                                              #
#########################################################################################

def GetTicketInfo(serverId):
    ticketInfoLst = []
    server = 'tcp:13.231.65.63' 
    database = 'It-Solution-OpenVPN' 
    username = 'sa' 
    password = 'Superm@n' 
    cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password)
    cursor = cnxn.cursor()

    query = """select Inst.TicketID,Inst.CommandCode,KeyInfo.Name as [KeyName],Cust.EmailAddress as [Emai] from Instructions as Inst
        inner join KeyInformations as KeyInfo on Inst.KeyInfoId = KeyInfo.Id inner join Customers as Cust on KeyInfo.CustomerID = Cust.CustomerId 
        where Inst.InstructionStatusID = 1 and Inst.ServerID = """+serverId+""";"""


    cursor.execute(query)
    resultLst = cursor.fetchall()

    for result in resultLst:
        ticketId = result[0]
        keyName = result[2]
        email = result[3]
        kInfo = KeyInfo(ticketId, keyName, '', email)
        ticketInfoLst.append(kInfo)

    return ticketInfoLst

def UpdateTicketInfo(ticketInfo):
    server = 'tcp:13.231.65.63' 
    database = 'It-Solution-OpenVPN' 
    username = 'sa' 
    password = 'Superm@n' 
    cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password)
    cursor = cnxn.cursor()

    query = "update Instructions Set InstructionStatusID = 2 where TicketID = "+ tickerInfo.TicketId +";"
    curosr.execute(query)
    print('Updated')

def GenerateKey(keyInfo):
    #cmdStr = 'tail -n +2 /etc/openvpn/easy-rsa/pki/index.txt | grep -c -E "/CN='+self.KeyName+'"'
    #existKey = os.system(cmdStr)
    #Check Key is already exist
    existKey = CheckExist(keyInfo.KeyName)
    if existKey == True:
        print('Already exist')
        return
    
    if keyInfo.Password == '':
        cmdStr = './easyrsa build-client-full {} nopass'.format(keyInfo.KeyName)
        result = os.system(cmdStr)
        print('Key Register Process Result : '+str(result))

    #Determine Encryption Method
    TLS_SIG = GetEncryptionType()

    # Generates the custom client.ovpn
    homeDir = '/home/ubuntu/'
    cert_str = str(GetTemplate())
    
    cert_str += '<ca>\n'
    cert_str += str(GetCaInfo())
    cert_str += '</ca>\n'
    cert_str += '<cert>\n'
    cert_str += str(GetCertInfo(keyInfo.KeyName))
    cert_str += '</cert>\n'
    cert_str += '<key>\n'
    cert_str += str(GetKeyInfo(keyInfo.KeyName))
    cert_str += '</key>\n'

    if TLS_SIG == 1:
        cert_str += '<tls-crypt>\n'
        cert_str += str(GetTlsCrypt())
        cert_str += '</tls-crypt>\n'
    else :
        cert_str += '<tls-auth>\n'
        cert_str += str(GetTlsAuth())
        cert_str += '</tls-auth>\n'

    #create file
    fileName = homeDir + keyInfo.KeyName + '.ovpn'
    with open(fileName, 'w') as f:
        f.write(cert_str)


def CheckExist(keyName):
    with open('pki/index.txt','r') as f:
        logstr = f.read()
        if keyName in logstr:
            return True
        else:
            return False

def GetEncryptionType():
    with open('/etc/openvpn/server.conf', 'r') as f:
        logstr = f.read()
        if 'tls-crypt' in logstr:
            return 1
        else:
            return 2

def GetTemplate():
    with open('/etc/openvpn/client-template.txt','r') as f:
        return f.read()

def GetCaInfo():
    with open('/etc/openvpn/easy-rsa/pki/ca.crt','r') as f:
        return f.read()

def GetCertInfo(keyName):
    fileName = '/etc/openvpn/easy-rsa/pki/issued/'+keyName+'.crt'
    with open(fileName,'r') as f:
        lines = f.readlines()
        cert = ''
        startRead = False
        for line in lines:
            if 'BEGIN' in line:
                startRead = True
            if startRead == True:
                cert += line
            if 'END' in line:
                startRead = False
        return cert

def GetKeyInfo(keyName):
    filename = '/etc/openvpn/easy-rsa/pki/private/'+keyName+'.key'
    with open(filename,'r') as f:
        return f.read()

def GetTlsCrypt():
    with open('/etc/openvpn/tls-crypt.key','r') as f:
        return f.read()

def GetTlsAuth():
    with open('/etc/openvpn/tls-auth.key','r') as f:
        retunr f.read()

def SendMail(ticketInfo):
    print('...Sending...')

#########################################################################################
#                                  Entry Point                                          #
#########################################################################################
SERVER_ID = str(102)
print(len(GetTicketInfo(SERVER_ID)))
ticketInfoLst = GetTicketInfo(SERVER_ID)
for ticketInfo in ticketInfoLst:
    GenerateKey(ticketInfo)
    UpdateTicketInfo(ticketInfo)
    SendMail(ticketInfo)

