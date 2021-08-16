import pyodbc
import os
import email, smtplib, ssl
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

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

########################
#      New Ticket      #
########################

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
    cursor.close()
    cnxn.close()

    return ticketInfoLst

def NewTicket(ServerID):
    ticketInfoLst = GetTicketInfo(ServerID)
    for ticketInfo in ticketInfoLst:
          GenerateKey(ticketInfo)
          UpdateTicketInfo(ticketInfo)
          SendMail(ticketInfo)

def UpdateTicketInfo(ticketInfo):
    server = 'tcp:13.231.65.63' 
    database = 'It-Solution-OpenVPN' 
    username = 'sa' 
    password = 'Superm@n' 
    cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password)
    cursor = cnxn.cursor()

    query = "update Instructions Set InstructionStatusID = 2 where TicketID = "+ str(ticketInfo.TicketId) +";"
    cursor.execute(query)
    cursor.commit()
    cursor.close()
    cnxn.close()
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
    homeDir = HOME_DIR
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
        return f.read()

def SendMail(ticketInfo):
    print('...Sending...')
    subject = "OpenVPN"
    body = "Automated email"
    sender_email = "blackcoder.zed@gmail.com"
    receiver_email = ticketInfo.Email
    filename = HOME_DIR + ticketInfo.KeyName + '.ovpn'
    password = 'Password'

    # Create a multipart message and set headers
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject
    message["Bcc"] = receiver_email

    # Add body to email
    message.attach(MIMEText(body, "plain"))

    with open(filename, "rb") as attachment:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())

    encoders.encode_base64(part)

    # Add header as key/value pair to attachment part
    part.add_header(
                "Content-Disposition",
                f"attachment; filename= {filename}",
    )

    # Add attachment to message and convert message to string
    message.attach(part)
    text = message.as_string()

    # Log in to server using secure context and send email
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, text)
    print('Send...')
    

#########################################################################################
#                                  Entry Point                                          #
#########################################################################################
SERVER_ID = str(102)
HOME_DIR = '/home/ubuntu/client/'
NewTicket(SERVER_ID)
