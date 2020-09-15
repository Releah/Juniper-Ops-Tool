####----------------------------------------------------------------####
####---------------------------#Packages#---------------------------####
####----------------------------------------------------------------####
import re
import os
import time
import threading
import sqlite3
from tkinter import *
from PIL import ImageTk,Image
from jnpr.junos import Device
from lxml import etree
from jnpr.junos.utils.config import Config



####----------------------------------------------------------------####
####---------------------------#tkinter#----------------------------####
####----------------------------------------------------------------####
# mainWindow
mainWindow = Tk()
mainWindow.geometry('800x800')
mainWindow.title("JunOS Ops GUI")
mainWindow.resizable(False, False)


####----------------------------------------------------------------####
####---------------------------#RegEx#------------------------------####
####----------------------------------------------------------------####
interfaceRegEx = re.compile("ge-(0|[1-9])\/[0-9]\/(0|[0-9]|1[0-9]|2[0-9]|3[0-2])")
vlanRegEx = re.compile("(?<=\>)(.*?)(?=\<)")


####----------------------------------------------------------------####
####---------------------------#Variables#--------------------------####
####----------------------------------------------------------------####
connection = None
connectionState = False

monitorARPValue = BooleanVar()
monitorARPValue.set(False)

monitorInterfaceValue = BooleanVar()
monitorInterfaceValue.set(False)


####----------------------------------------------------------------####
####---------------------------#Threading#--------------------------####
####----------------------------------------------------------------####
# Thread def
def threadingFuncARP():
    try:
        thread = threading.Thread(target=showArpFunc)
        thread.start()
    except:
        TextBoxData.insert(END, "\nFailed to thread function.\n")
        TextBoxData.see("end")


####----------------------------------------------------------------####
def threadingFuncInterfaceLogs():
    try:
        thread = threading.Thread(target=monitorInterface)
        thread.start()
    except:
        TextBoxData.insert(END, "\nFailed to thread function.\n")
        TextBoxData.see("end")


####----------------------------------------------------------------####
def threadingFuncConnected():
    try:
        thread = threading.Thread(target=connectionStateFunc)
        thread.start()
    except:
        TextBoxData.insert(END, "\nFailed to thread function.\n")
        TextBoxData.see("end")

####----------------------------------------------------------------####
####---------------------------#Functions#--------------------------####
####----------------------------------------------------------------####
# Set apps CWD to app location
def commiting():
    TextBoxData.insert(END, "\nCommiting changes to switch, please wait. This can take a while.\n")
    TextBoxData.see("end")


####----------------------------------------------------------------####
# Set apps CWD to app location
def changeCWD():
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)


####----------------------------------------------------------------####
# Logon or Log off Function
def logonoroffFunc():
    if connection is None:
        LogOnFunc()
    else:
        LogOffFunc()

####----------------------------------------------------------------####
# Logon Function
def LogOnFunc():
    Username = usernameEntry.get()
    Password = passwordEntry.get()
    HostIP = hostipEntry.get()
    connectionDetials = [Username, Password, HostIP]
    for Line in connectionDetials:
        if Line == "":
            TextBoxData.insert(END, "\nPlease enter username, password and Host IP.\n")
            TextBoxData.see("end")
            return
    try:
        global connection
        global connectionState
        connection = Device(host=HostIP, user=Username, password=Password)    # Specifies connection detials
        connection.open()                                                                           # Opens the connection with switch
        connection.timeout = 300                                                                    # Set session timeout to 5 mins 
        TextBoxData.insert(END, "\nConnected to "+HostIP+".\n")
        TextBoxData.see("end")
        connectionState = True
        threadingFuncConnected()
        return connection
    except:
        TextBoxData.insert(END, "\nFailed to connect to switch. Please check connection details.\n")
        TextBoxData.see("end")
        return


####----------------------------------------------------------------####
# Log off Function
def LogOffFunc():
    global connectionState
    global connection
    if connection is None:
        TextBoxData.insert(END, "\nPlease log on before trying to log off.\n")
        TextBoxData.see("end")
    else:
        try:
            connection.close()
            connectionState = False
            TextBoxData.insert(END, "\nConnection closed.\n")
            TextBoxData.see("end")
            connection = None
            SwitchPortEntry.delete(0, END)
            UINEntry.delete(0, END)
            buildingNameEntry.delete(0, END)
            hostipEntry.delete(0, END)
            adminEntry.delete(0, END)
            operEntry.delete(0, END)
            vlanEntry.delete(0, END)
            MACEntry.delete(0, END)
            IPEntry.delete(0, END)
            Dot1xEntry.delete(0, END)
            return connectionState
        except:
            TextBoxData.insert(END, "\nFailed to end connection.\n")
            TextBoxData.see("end")
            return


####----------------------------------------------------------------####
# Connection state function
def connectionStateFunc():
    connectionCross = ImageTk.PhotoImage(Image.open("Images/GreenTick40.png"))
    while connectionState is True:      
        imgLabel = Label(mainWindow, image=connectionCross)
        imgLabel.place(x=640, y=40)
        time.sleep(1)
    

####----------------------------------------------------------------####   
# Show arp function
def showArpFunc():
    switchPort = SwitchPortEntry.get() # Get port to look at 
    monitorARPTF = monitorARPValue.get()
    if connection is None:
        monitorARPCheckbox.deselect()
        TextBoxData.insert(END, "\nPlease logon.\n")
        TextBoxData.see("end")
    else:
        while monitorARPTF is True:
            if switchPort == (''):
                TextBoxData.insert(END, "\nPlease enter a interface.\n")
                TextBoxData.see("end")
                monitorARPCheckbox.deselect()
            else:
                portReg = interfaceRegEx.search(switchPort)           
                if portReg is None:
                    TextBoxData.insert(END, "\nInvalid interface. Please enter valid interface.\n")
                    TextBoxData.see("end")
                    monitorARPCheckbox.deselect()
                else:
                    switchPort = (switchPort+".0")
                    informationFromSwitch = connection.rpc.get_arp_table_information()
                    arpTableEncoded = etree.tostring(informationFromSwitch, encoding='unicode')
                    aprTableDecoded = arpTableEncoded.splitlines()
                    for line in aprTableDecoded:
                        if switchPort in line:
                            index = aprTableDecoded.index(line)
                            TextBoxData.insert(END, "\nMAC: "+aprTableDecoded[index -6] + "\t\t |   IP Address: " + aprTableDecoded[index -2] + "\t\t|   Interface: " + aprTableDecoded[index]+"\n")
                            TextBoxData.see("end")
            time.sleep(1)
            switchPort = SwitchPortEntry.get()
            monitorARPTF = monitorARPValue.get()
            

####----------------------------------------------------------------####   
# Get IP - Working
def getIP():
    switchPort = SwitchPortEntry.get()
    IPEntry.delete(0, END)
    if connection is None:
        monitorARPCheckbox.deselect()
        TextBoxData.insert(END, "\nPlease logon.\n")
        TextBoxData.see("end")
    else:
        if switchPort == (''):
            TextBoxData.insert(END, "\nPlease enter a interface.\n")
            TextBoxData.see("end")
            return
        else:
            portReg = interfaceRegEx.search(switchPort)
            if portReg is None:
                TextBoxData.insert(END, "\nInvalid interface. Please enter valid interface.\n")
                TextBoxData.see("end")
                return
            else:
                switchPort = (switchPort+".0")
                informationFromSwitch = connection.rpc.get_arp_table_information()
                arpTableEncoded = etree.tostring(informationFromSwitch, encoding='unicode')
                aprTableDecoded = arpTableEncoded.splitlines()
                for line in aprTableDecoded:
                    if switchPort in line:
                        index = aprTableDecoded.index(line)
                        IPAddress = aprTableDecoded[index -2]
                        return IPAddress


####----------------------------------------------------------------####   
# Get MAC - Not working
# def getMAC():
#     switchPort = SwitchPortEntry.get()
#     IPEntry.delete(0, END)
#     if connection is None:
#         monitorARPCheckbox.deselect()
#         TextBoxData.insert(END, "\nPlease logon.\n")
#         TextBoxData.see("end")
#     else:
#         if switchPort == (''):
#             TextBoxData.insert(END, "\nPlease enter a interface.\n")
#             TextBoxData.see("end")
#             return
#         else:
#             portReg = interfaceRegEx.search(switchPort)
#             if portReg is None:
#                 TextBoxData.insert(END, "\nInvalid interface. Please enter valid interface.\n")
#                 TextBoxData.see("end")
#                 return
#             else:
#                 switchPort = (switchPort+".0")
#                 informationFromSwitch = connection.rpc.get_ethernet_switching_table_information(interface_name=switchPort)
#                 ethernetTableEncoded = etree.tostring(informationFromSwitch, encoding='unicode', pretty_print=True)
#                 ethernetTableDecoded = ethernetTableEncoded.splitlines()
#                 print(ethernetTableDecoded)
#                 # for line in ethernetTableDecoded:
#                 #     if switchPort in line:
#                 #         index = ethernetTableDecoded.index(line)
#                 #         IPAddress = aprTableDecoded[index -3]
#                 #         print(IPAddress)
                        


####----------------------------------------------------------------####   
# Show interface-logs function
def monitorInterface():
    MonitorTF = monitorInterfaceValue.get()
    interfaceLogsDecodedOLD = "No Log Found"
    if connection is None:
        monitorInterfaceCheckbox.deselect()
        TextBoxData.insert(END, "\nPlease logon.\n")
    else:
        while MonitorTF is True:
            informationFromSwitch = connection.rpc.get_log(filename='interface-log')
            interfaceLogsEncoded = etree.tostring(informationFromSwitch, encoding='unicode')
            interfaceLogsDecoded = interfaceLogsEncoded.splitlines()
            interfaceLogsDecoded = interfaceLogsDecoded[1:-1]
            interfaceLogsDecoded = interfaceLogsDecoded[-2:]
            if interfaceLogsDecoded == interfaceLogsDecodedOLD:
                pass
            else:
                for line in interfaceLogsDecoded:
                    lineSplit = line.split(' ')
                    interfaceLog = ("\n" + lineSplit[0] + " " + lineSplit[1] + " " + lineSplit[2] + "  |  " + lineSplit[8] + "\t\t|  Admin status UP/DOWN\n")
                    TextBoxData.insert(END, interfaceLog)
                    TextBoxData.see("end")
                    interfaceLogsDecodedOLD = interfaceLogsDecoded

        MonitorTF = monitorInterfaceValue.get()
        time.sleep(1)


####----------------------------------------------------------------####
# Show Interface Status
def interfaceStatus():
    adminEntry.delete(0, END)
    operEntry.delete(0, END)
    vlanEntry.delete(0, END)
    MACEntry.delete(0, END)
    IPEntry.delete(0, END)
    Dot1xEntry.delete(0, END)
    switchPort = SwitchPortEntry.get()  # Get switchport from entrybox in mainWindow
    #switchName = SwitchNameEntry.get()  # Get switchName from entrybox in mainWindow
    if connection is None:
        monitorInterfaceCheckbox.deselect()
        TextBoxData.insert(END, "\nPlease logon.\n")
    else:
        if switchPort == (''):
                    TextBoxData.insert(END, "\nPlease enter a interface.\n")
                    monitorARPCheckbox.deselect()
        else:
            try:
                filter = '<terse/><interface-name></interface-name>'
                informationFromSwitch = connection.rpc.get_interface_information(interface_name=switchPort, filter_xml=filter)
                interfaceInfo = etree.tostring(informationFromSwitch, encoding='unicode')
                splitString = interfaceInfo.split("\n")
                adminStatus = splitString[3]
                operStatus = splitString[5]

                filter = '<interfaces><interface><name>'+switchPort+'</name><unit><name>0</name><family><ethernet-switching><vlan><members/></vlan></ethernet-switching></family></unit></interface></interfaces>'
                result2 = connection.rpc.get_config(filter_xml=filter)
                interfaceVlan = etree.tostring(result2, encoding='unicode', pretty_print=True)
                interfaceVlanList = interfaceVlan.split("\n")
                vlanLine = interfaceVlanList[9]
                currentVlan = vlanRegEx.search(vlanLine)
                currentVlan = currentVlan.group(0)

#-------------------NEED TO CALL A FUNCTION HERE----------------------------------
                switchPort = (switchPort+".0")
                informationFromSwitch = connection.rpc.get_arp_table_information()
                arpTableEncoded = etree.tostring(informationFromSwitch, encoding='unicode')
                aprTableDecoded = arpTableEncoded.splitlines()
                print(aprTableDecoded)
                for line in aprTableDecoded:
                    if switchPort in line:
                        index = aprTableDecoded.index(line)
                        MAC = aprTableDecoded[index -6]
                        IP = aprTableDecoded[index -2]
                adminEntry.insert(END, adminStatus)
                operEntry.insert(END, operStatus)
                vlanEntry.insert(END, currentVlan)
                MACEntry.insert(END, MAC)
                IPEntry.insert(END, IP)
#-------------------NEED TO CALL A FUNCTION HERE----------------------------------


                TextBoxData.insert(END, "\nAdministratively: " +adminStatus+ "\t\t  |  Physically: " + operStatus+ "\t\t  |  Current Vlan : " +currentVlan+ "\n")
                TextBoxData.see("end")
            except:
                TextBoxData.insert(END, "\nInterface not found on switch, this interface has no SFP.\n")
                TextBoxData.see("end")
 

 ####----------------------------------------------------------------####
# Disable/ Enable Port
def toggleAdmin():
    switchPort = SwitchPortEntry.get()  # Get switchport from entrybox in mainWindow
    if connection is None:
        monitorInterfaceCheckbox.deselect()
        TextBoxData.insert(END, "\nPlease logon.\n")
    else:
        if switchPort == (''):
                    TextBoxData.insert(END, "\nPlease enter a interface.\n")
                    monitorARPCheckbox.deselect()
        else:
            filter = '<interface-information><physical-interface><name/><admin-status/><oper-status/></physical-interface></interface-information>'  # limits the ammount of information gathered
            result = connection.rpc.get_interface_information(interface_name=switchPort, filter_xml=filter) # 
            interfaceInfo = etree.tostring(result, encoding='unicode')
            splitString = interfaceInfo.splitlines()
            interfaceUpDown = ('{3}'.format(*splitString))
            TextBoxData.insert(END, "\nInterface " + switchPort + " is " + interfaceUpDown)
            ## Configlets
            config_disable = '''
            interfaces {
                '''+switchPort+''' {
                    disable;
                }
            }
                '''
            config_enable = '''
            interfaces {
                '''+switchPort+''' {
                    delete: disable;
                }
            }
                '''
            ## coniglet used based on port status
            if interfaceUpDown == "up":
                TextBoxData.insert(END, ", Disabling interface... \n")
                commiting()
                cu = Config(connection)
                cu.lock()
                cu.load(config_disable)
                diff = cu.diff()
                cu.commit()
                TextBoxData.insert(END, "Commit complete.\n")
                cu.unlock()
                TextBoxData.insert(END, '%s' % (diff))
                TextBoxData.see("end")
            elif interfaceUpDown == "down":
                TextBoxData.insert(END, ", Enabling interface... \n")
                commiting()
                cu = Config(connection)
                cu.lock()
                cu.load(config_enable)
                diff = cu.diff()
                cu.commit()
                TextBoxData.insert(END, "Commit complete. \n")
                cu.unlock()
                TextBoxData.insert(END, '%s' % (diff))
                TextBoxData.see("end")
            else:
                TextBoxData.insert(END, "\nERROR\n")
                TextBoxData.see("end")


####----------------------------------------------------------------####
####---------------------------#Code#-------------------------------####
####----------------------------------------------------------------####
changeCWD()

####----------------------------------------------------------------####
####---------------------------#Database#---------------------------####
####----------------------------------------------------------------####
def databaseManagment(): 
    # Add to DB Window Function
    def addDB():
        adddbWindow = Tk()
        adddbWindow.geometry('300x100')
        adddbWindow.title("Add to DB")
        
        def addSubmit(): #Save to DB Functio    
            dbConnection = sqlite3.connect('App_DB') # Create/ Connect to DB
            cursor = dbConnection.cursor() # Cursor
            cursor.execute("INSERT INTO Switch_Table VALUES (:Switch_Name, :Switch_IP)", # Inset data in to table
                           {
                               'Switch_Name':swNameEntry.get(),
                               'Switch_IP':swIPEntry.get()
                               })
            dbConnection.commit()  # DB Commit
            dbConnection.close() # db Close connection
            swNameEntry.delete(0, END) # Clear Entry Boxes
            swIPEntry.delete(0, END) # Clear Entry Boxes
        # Labels
        swNameLabel = Label(adddbWindow, text="Switch Name: ")
        swNameLabel.grid(row=0, column=0, padx=5, pady=5)
        swIPLabel = Label(adddbWindow, text="Switch IP: ")
        swIPLabel.grid(row=1, column=0, padx=5, pady=5)
        # Buttons
        addSubmitButton = Button(adddbWindow, text="Add Switch", command=addSubmit)
        addSubmitButton.grid(row=2, column=0, padx=5, pady=5)
        # Text Entry
        swNameEntry = Entry(adddbWindow)
        swNameEntry.grid(row=0, column=1, padx=5, pady=5)
        swIPEntry = Entry(adddbWindow)
        swIPEntry.grid(row=1, column=1, padx=5, pady=5)
        

####----------------------------------------------------------------####       
    #Show DB in Text Window       
    def displayDB():
        textBox.delete('1.0', END) # Clear screen
        dbConnection = sqlite3.connect('App_DB') # Create/ Connect to DB
        cursor = dbConnection.cursor() # Cursor
        cursor.execute("SELECT *, oid FROM Switch_Table") # Query DB
        records = cursor.fetchall()
        print_db = ""
        for record in records: #print(records)
            print_db += str(record[2]) + " " + "\t" + str(record[0]) + " " + str(record[1]) + "\n"
        textBox.insert(END, print_db)              
        dbConnection.commit() # DB Commit
        dbConnection.close() # db Close connection
        

    ####----------------------------------------------------------------####
    # Delete Entry from DB
    def deleteDBEntry():
        dbConnection = sqlite3.connect('App_DB') # Create/ Connect to DB
        cursor = dbConnection.cursor() # Cursor
        cursor.execute("DELETE from Switch_Table WHERE oid = " + deleteRecordEntry.get()) # Delete record      
        dbConnection.commit() # DB Commit
        dbConnection.close() # db Close connection
        deleteRecordEntry.delete(0, END) #Clear Box
 
    ####----------------------------------------------------------------####
    # Create Window 'databaseManagment'
    dbManagment = Tk()
    dbManagment.geometry('645x500')
    dbManagment.title("DB Managment")
    dbManagment.resizable(False, False)


    ####----------------------------------------------------------------####
    # Labels
    manageDBLabel = Label(dbManagment, text="Database Management")
    manageDBLabel.config(font=("Verdana", 25, "bold"))
    manageDBLabel.place(x=10, y=5)
    oidLabel = Label(dbManagment, text="OID to Delete:")
    oidLabel.config(font=("Verdana", 8, "bold"))
    oidLabel.place(x=400, y=60, height=40, width=100)


    ####----------------------------------------------------------------####
    # Buttons
    displayDBButton = Button(dbManagment, text="Display\nDatabase", command=displayDB)
    displayDBButton.config(font=("Verdana", 8, "bold"))
    displayDBButton.place(x=25, y=60, height=40, width=80)
    
    newDBButton = Button(dbManagment, text="New\nDB Entry", command=addDB)
    newDBButton.config(font=("Verdana", 8, "bold"))
    newDBButton.place(x=120, y=60, height=40, width=80)
    
    deleteDBButton = Button(dbManagment, text="Delete\nDB Entry", command=deleteDBEntry)
    deleteDBButton.config(font=("Verdana", 8, "bold"))
    deleteDBButton.place(x=560, y=60, height=40, width=80)
    
    exitButton = Button(dbManagment, text="Exit", command=dbManagment.destroy)
    exitButton.config(font=("Verdana", 10, "bold"))
    exitButton.place(x=560, y=455, height=40, width=80)
    

    ####----------------------------------------------------------------####
    # Entry Box
    deleteRecordEntry = Entry(dbManagment, justify='center')
    deleteRecordEntry.config(font=("Verdana", 8, "bold"))
    deleteRecordEntry.place(x=500, y=60, height=40, width=50)


    ####----------------------------------------------------------------####
    # Textbox
    textBox = Text(dbManagment)
    textBox.config(font=("Verdana", 8))
    textBox.place(x=2, y=110, height=340, width=640)
 

#------------------------------------------------------------------------------------
# Create/ Connect to DB
dbConnection = sqlite3.connect('App_DB') # Create/ Connect to DB
cursor = dbConnection.cursor()# Cursor
# Create table
#cursor.execute("""CREATE TABLE Switch_Table ( 
#                Switch_Name text,
#                Switch_IP integer)""")
dbConnection.commit()# DB Commit
dbConnection.close()# db Close connection


####----------------------------------------------------------------####
####---------------------------#tkinter#----------------------------####
####----------------------------------------------------------------####
# Labels
headingLabel = Label(mainWindow, text="JunOS Ops GUI")
headingLabel.config(font=("Verdana", 25, "bold"))
headingLabel.place(x=15, y=15)

connectionheadingLabel = Label(mainWindow, text="Connection Credentials:")
connectionheadingLabel.config(font=("Verdana", 11, "bold"))
connectionheadingLabel.place(x=15, y=70)

usernameLabel = Label(mainWindow, text="Username: ")
usernameLabel.config(font=("Verdana", 10, "bold"))
usernameLabel.place(x=30, y=100)

passwordLabel = Label(mainWindow, text="Password: ")
passwordLabel.config(font=("Verdana", 10, "bold"))
passwordLabel.place(x=30, y=130)

UINheadingLabel = Label(mainWindow, text="UIN Search:")
UINheadingLabel.config(font=("Verdana", 11, "bold"))
UINheadingLabel.place(x=15, y=170)

searchUINLable = Label(mainWindow, text="Enter UIN:")
searchUINLable.config(font=("Verdana", 10, "bold"))
searchUINLable.place(x=30, y=200)

connectionheadingLabel = Label(mainWindow, text="Connection Detials:")
connectionheadingLabel.config(font=("Verdana", 11, "bold"))
connectionheadingLabel.place(x=15, y=240)

buildingLable = Label(mainWindow, text="Building:")
buildingLable.config(font=("Verdana", 10, "bold"))
buildingLable.place(x=30, y=270)

hostipLabel = Label(mainWindow, text="Switch IP: ")
hostipLabel.config(font=("Verdana", 10, "bold"))
hostipLabel.place(x=30, y=300)

switchPortLable = Label(mainWindow, text="Interface:")
switchPortLable.config(font=("Verdana", 10, "bold"))
switchPortLable.place(x=30, y=330)

conectionStateLabel = Label(mainWindow, text="Connected to switch: ")
conectionStateLabel.config(font=("Verdana", 10, "bold"))
conectionStateLabel.place(x=480, y=60)

adminLabel = Label(mainWindow, text="Admin Status:")
adminLabel.config(font=("Verdana", 10, "bold"))
adminLabel.place(x=480, y=90)

operLabel = Label(mainWindow, text="Oper Status:")
operLabel.config(font=("Verdana", 10, "bold"))
operLabel.place(x=480, y=120)

vlanLabel = Label(mainWindow, text="Current Vlan:")
vlanLabel.config(font=("Verdana", 10, "bold"))
vlanLabel.place(x=480, y=150)

MACLabel = Label(mainWindow, text="MAC Address:")
MACLabel.config(font=("Verdana", 10, "bold"))
MACLabel.place(x=480, y=180)

IPLabel = Label(mainWindow, text="IP Address:")
IPLabel.config(font=("Verdana", 10, "bold"))
IPLabel.place(x=480, y=210)

Dot1xLabel = Label(mainWindow, text="Do1x State: ")
Dot1xLabel.config(font=("Verdana", 10, "bold"))
Dot1xLabel.place(x=480, y=240)


####----------------------------------------------------------------####
# Buttons
logonButton = Button(mainWindow, text="Log\nOn/Off", command=logonoroffFunc)
logonButton.config(font=("Verdana", 10, "bold"))
logonButton.place(x=330, y=100, height=54, width=80)

searchUINButton = Button(mainWindow, text="Search")
searchUINButton.config(font=("Verdana", 10, "bold"))
searchUINButton.place(x=330, y=198, height=28, width=80)

searchSwitchButton = Button(mainWindow, text="Search")#, command=switchSearch)
searchSwitchButton.config(font=("Verdana", 10, "bold"))
searchSwitchButton.place(x=330, y=268, height=28, width=80)

exitButton = Button(mainWindow, text="Exit", command=mainWindow.destroy)
exitButton.config(font=("Verdana", 10, "bold"))
exitButton.place(x=710, y=755, height=40, width=80)

manageDBButton = Button(mainWindow, text="Manage Database", command=databaseManagment)
manageDBButton.config(font=("Verdana", 10, "bold"))
manageDBButton.place(x=550, y=755, height=40, width=150)

interfaceStatusButton = Button(mainWindow, text="Get Interface Information", command=interfaceStatus)
interfaceStatusButton.config(font=("Verdana", 10, "bold"))
interfaceStatusButton.place(x=480, y=275, height=30, width=272)

toggleAdminButton = Button(mainWindow, text="Admin Toggle", command=toggleAdmin)
toggleAdminButton.config(font=("Verdana", 10, "bold"))
toggleAdminButton.place(x=480, y=310, height=30, width=135)

toggledot1xButton = Button(mainWindow, text="Toggle dot1x", command=getMAC)
toggledot1xButton.config(font=("Verdana", 10, "bold"))
toggledot1xButton.place(x=617, y=310, height=30, width=135)


####----------------------------------------------------------------####
# EntryBoxs
usernameEntry = Entry(mainWindow, justify='center')
usernameEntry.config(font=("Verdana", 10, "bold"))
usernameEntry.place(x=120, y=100, height=25, width=200)

passwordEntry = Entry(mainWindow, show="*", justify='center')
passwordEntry.config(font=("Verdana", 10, "bold"))
passwordEntry.place(x=120, y=130, height=25, width=200)

UINEntry = Entry(mainWindow, justify='center')
UINEntry.config(font=("Verdana", 10))
UINEntry.place(x=120, y=200, height=25, width=200)

buildingNameEntry = Entry(mainWindow, justify='center')
buildingNameEntry.config(font=("Verdana", 10, "bold"))
buildingNameEntry.place(x=120, y=270, height=25, width=200)

hostipEntry = Entry(mainWindow, justify='center')
hostipEntry.config(font=("Verdana", 10, "bold"))
hostipEntry.place(x=120, y=300, height=25, width=200)

SwitchPortEntry = Entry(mainWindow, justify='center')
SwitchPortEntry.config(font=("Verdana", 10))
SwitchPortEntry.place(x=120, y=330, height=25, width=200)

adminEntry = Entry(mainWindow, text="Admin Status:", justify='center')
adminEntry.config(font=("Verdana", 10, "bold"))
adminEntry.place(x=600, y=90, height=25, width=150)

operEntry = Entry(mainWindow, text="Oper Status:", justify='center')
operEntry.config(font=("Verdana", 10, "bold"))
operEntry.place(x=600, y=120, height=25, width=150)

vlanEntry = Entry(mainWindow, text="Current Vlan:", justify='center')
vlanEntry.config(font=("Verdana", 10, "bold"))
vlanEntry.place(x=600, y=150, height=25, width=150)

MACEntry = Entry(mainWindow, text="MAC Address:", justify='center')
MACEntry.config(font=("Verdana", 10, "bold"))
MACEntry.place(x=600, y=180, height=25, width=150)

IPEntry = Entry(mainWindow, text="IP Address:", justify='center')
IPEntry.config(font=("Verdana", 10, "bold"))
IPEntry.place(x=600, y=210, height=25, width=150)

Dot1xEntry = Entry(mainWindow, text="Do1x State:", justify='center')
Dot1xEntry.config(font=("Verdana", 10, "bold"))
Dot1xEntry.place(x=600, y=240, height=25, width=150)


####----------------------------------------------------------------####
# Text Box
TextBoxData = Text(mainWindow)
TextBoxData.config(font=("Verdana", 8))
TextBoxData.place(x=10, y=420, height=330, width=780)


####----------------------------------------------------------------####
# Check Box
monitorARPCheckbox = Checkbutton(mainWindow, text="Monitor\nInterface ARP", justify='left', var=monitorARPValue, command=threadingFuncARP)
monitorARPCheckbox.config(font=("Verdana", 10, "bold"))
monitorARPCheckbox.place(x=617, y=350, height=50, width=120)

monitorInterfaceCheckbox = Checkbutton(mainWindow, text="Monitor\nInterfaces", justify='left', var=monitorInterfaceValue, command=threadingFuncInterfaceLogs)
monitorInterfaceCheckbox.config(font=("Verdana", 10, "bold"))
monitorInterfaceCheckbox.place(x=480, y=350, height=50, width=120)


####----------------------------------------------------------------####
# Frame
#detailFrame = Frame(mainWindow, width=360, height=380, bd=2, relief=SUNKEN)
#detailFrame.place(x=430, y=20)


####----------------------------------------------------------------####
# End mainWindow
mainWindow.mainloop()
