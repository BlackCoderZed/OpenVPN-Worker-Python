from xml.dom import minidom
from suds.client import Client
import os
import email, smtplib, ssl
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from email.utils import formataddr

#########################################################################################
#                                  Configuartion Class                                        #
#########################################################################################

class Configuration:
    def __init__(self, ServerId, ServerIP, SecretKey, EmailAddress, Password, SmtpServer, IpPrefix, SaveDir, ApiUrl):
        self.ServerId = ServerId
        self.ServerIP = ServerIP
        self.SecretKey = SecretKey
        self.EmailAddress = EmailAddress
        self.Password = Password
        self.SmtpServer = SmtpServer
        self.IpPrefix = IpPrefix
        self.SaveDir = SaveDir
        self.ApiUrl = ApiUrl

    def LoadConfiguration():
        filedir = os.path.dirname(os.path.realpath(__file__))
        doc = minidom.parse(filedir+"/config.xml")
        config = doc.getElementsByTagName("config")[0]
        serverId = config.getElementsByTagName("ServerId")[0].firstChild.data
        serverIP = config.getElementsByTagName("ServerIP")[0].firstChild.data
        secretKey = config.getElementsByTagName("SecretKey")[0].firstChild.data
        emailAddress = config.getElementsByTagName("EmailAddress")[0].firstChild.data
        password = config.getElementsByTagName("Password")[0].firstChild.data
        smtpAddress = config.getElementsByTagName("SmtpAddress")[0].firstChild.data
        ipPrefix = config.getElementsByTagName("IpPrefix")[0].firstChild.data
        saveDir = config.getElementsByTagName("SaveDir")[0].firstChild.data
        apiUrl = config.getElementsByTagName("APIUrl")[0].firstChild.data
        config = Configuration(serverId, serverIP, secretKey, emailAddress, password, smtpAddress, ipPrefix, saveDir, apiUrl)
        return config

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
#      Operation       #
########################

def StartRegistrationProcess():
    ticketInfoLst = GetTicketInfo(REGISTER_REQ_INFO)
    for ticketInfo in ticketInfoLst:
          GenerateKey(ticketInfo)
          UpdateTicketInfo(ticketInfo)
          SendMail(ticketInfo)

def StartDeleteProcess():
    ticketInfoLst = GetTicketInfo(DELETE_REQ_INFO)
    for ticketInfo in ticketInfoLst:
        cmd = './easyrsa --batch revoke ' + ticketInfo.KeyName
        os.system(cmd)
        cmd2 = 'EASYRSA_CRL_DAYS=3650 ./easyrsa gen-crl'
        os.system(cmd2)
        cmd3 = 'rm -f /etc/openvpn/crl.pem'
        os.system(cmd3)
        cmd4 = 'cp /etc/openvpn/easy-rsa/pki/crl.pem /etc/openvpn/crl.pem'
        os.system(cmd4)
        cmd5 = 'chmod 644 /etc/openvpn/crl.pem'
        os.system(cmd5)
        UpdateTicketInfo(ticketInfo)
        print('Deleted')

def GetTicketInfo(requestInfo):
    authInfo = AUTH_INFO
    reqInfo = requestInfo
    ticketInfoLst = []
    wsdl = API_URL
    client = Client(wsdl)
    result = client.service.GetInstructionInfoList(authInfo, reqInfo)

    if(result.InstructionList is None or len(result.InstructionList) <= 0):
        return ticketInfoLst

    for instList in result.InstructionList:
        for inst in instList[1]:
            ticketId = inst[0]
            keyName = inst[2]
            email = inst[3]
            kInfo = KeyInfo(ticketId, keyName, '', email)
            ticketInfoLst.append(kInfo)
    
    return ticketInfoLst

def UpdateTicketInfo(ticketInfo):
    authInfo = AUTH_INFO
    serverId = SERVER_ID
    ticketId = ticketInfo.TicketId
    wsdl = API_URL
    client = Client(wsdl)
    result = client.service.CompleteInstructionTicket(authInfo, ticketId, serverId)
    print('Updated')

def GenerateKey(keyInfo):
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
    subject = "OpenVPN by IT-Solution"
    body = "Thanks for choosing IT-Solution.\n***Automated email***"
    sender_email = EMAIL_ADDRESS
    receiver_email = ticketInfo.Email
    filename = HOME_DIR + ticketInfo.KeyName + '.ovpn'
    password = EMAIL_PASSWORD
    attachName = ticketInfo.KeyName + '.ovpn'

    # Create a multipart message and set headers
    message = MIMEMultipart()
    message["From"] = formataddr((SENDER_NAME, sender_email))
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
                f"attachment; filename= {attachName}",
    )

    # Add attachment to message and convert message to string
    message.attach(part)
    text = message.as_string()

    # Log in to server using secure context and send email
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(SMTP_ADDRESS, 465, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, text)
    print('Send...')
    

#########################################################################################
#                                  Entry Point                                          #
#########################################################################################
config = Configuration.LoadConfiguration()
SERVER_ID = config.ServerId
SERVER_IP = config.ServerIP
SECRET_KEY = config.SecretKey
SENDER_NAME = "IT-Solution"
EMAIL_ADDRESS = config.EmailAddress
EMAIL_PASSWORD = config.Password
SMTP_ADDRESS = config.SmtpServer
IP_Prefix = config.IpPrefix
HOME_DIR = config.SaveDir
API_URL = config.ApiUrl
AUTH_INFO = {'UserID' : 'APIUser', 'Password' : '2017hacker'}
REGISTER_REQ_INFO = {'ServerID' : SERVER_ID, 'CommandCode' : 101}
DELETE_REQ_INFO = {'ServerID' : SERVER_ID, 'CommandCode' : 103}
StartRegistrationProcess()
StartDeleteProcess()

