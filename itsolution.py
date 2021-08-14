import pyodbc
import os

#########################################################################################
#                                  KeyInfo Class                                        #
#########################################################################################

class KeyInfo:
    def __init__(self, TicketId, KeyName, Email):
        self.TicketId = TicketId
        self.KeyName = KeyName
        self.Email = Email
    
    def GenerateKey(self):
        cmdStr = 'sudo ./home/ubuntu/OpenVPN-Worker-POC-Python/itsolution-openvpn.sh {}'.format(self.KeyName)
        os.system(cmdStr)

    def SendMail(self):
        print('...Sending...')

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
        kInfo = KeyInfo(ticketId, keyName, email)
        ticketInfoLst.append(kInfo)

    return ticketInfoLst

def UpdateTicketInfo():
    print('Updated')

#########################################################################################
#                                  Entry Point                                          #
#########################################################################################
SERVER_ID = str(102)
print(len(GetTicketInfo(SERVER_ID)))
ticketInfoLst = GetTicketInfo(SERVER_ID)
for ticketInfo in ticketInfoLst:
    ticketInfo.GenerateKey()
    UpdateTicketInfo()
    ticketInfo.SendMail()
