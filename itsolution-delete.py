from suds.client import Client
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
def DeleteClient(ServerID):
    ticketInfoLst = GetTicketInfo(ServerID)
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

def UpdateTicketInfo(ticketInfo):
    authInfo = AUTH_INFO
    serverId = SERVER_ID
    ticketId = ticketInfo.TicketId
    wsdl = "http://13.231.65.63:8999/VPNAPIService.svc?wsdl"
    client = Client(wsdl)
    result = client.service.CompleteInstructionTicket(authInfo, ticketId, serverId)
    print('Updated')

def GetTicketInfo(serverId):
    authInfo = AUTH_INFO
    reqInfo = REQ_INFO
    ticketInfoLst = []
    wsdl = "http://13.231.65.63:8999/VPNAPIService.svc?wsdl"
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

#########################################################################################
#                                  Entry Point                                          #
#########################################################################################

SERVER_ID = str(105)
HOME_DIR = '/home/ubuntu/client/'
AUTH_INFO = {'UserID' : 'APIUser', 'Password' : '2017hacker'}
REQ_INFO = {'ServerID' : SERVER_ID, 'CommandCode' : 103}
DeleteClient(SERVER_ID)
