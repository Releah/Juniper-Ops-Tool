from tkinter import * 
import sqlite3
from jnpr.junos import Device
from lxml import etree
from jnpr.junos.utils.config import Config
import re

#------------------------------------------------------------------------------------

#Create Main Window
mainWindow = Tk()
mainWindow.geometry('800x800')
mainWindow.title("Ryan's Epic Python Quest")
mainWindow.resizable(False, False)

#------------------------------------------------------------------------------------ 
#------------------------------------------------------------------------------------ 
# Main Function

def switchSearch():
    # Create/ Connect to DB
    dbConnection = sqlite3.connect('App_DB')
    # Cursor
    cursor = dbConnection.cursor()
    # Query DB
    cursor.execute("SELECT * FROM Switch_Table WHERE Switch_Name LIKE " + "'%" + SwitchNameEntry.get() + "%'")
    records = cursor.fetchall()
    #print(records)
    printSwName = ""
    printSwIP = ""
    for record in records:
        printSwName += str(record[0])
    for record in records:
        printSwIP += str(record[1])
 
    SwitchNameEntry.delete(0, END)
    SwitchNameEntry.insert(INSERT, printSwName)
    SwitchIPEntry.delete(0, END)
    SwitchIPEntry.insert(INSERT, printSwIP)
               
    # DB Commit
    dbConnection.commit()
    # db Close connection
    dbConnection.close()

#------------------------------------------------------------------------------------ 

def toggleAdmin():
    username = usernameEntry.get()      # Get username from entrybox in mainWindow
    password1 = passwordEntry.get()     # Get password from entrybox in mainWindow
    hostIP = SwitchIPEntry.get()        # Get switch IP from entrybox in mainWindow
    switchPort = SwitchPortEntry.get()  # Get switchport from entrybox in mainWindow

    #-- Grab if port is up or down
    dev = Device(host=hostIP, user=username, password=password1, use_filter=True) # Specifies connection detials
    dev.open() # Opens the connection with switch  
    filter = '<interface-information><physical-interface><name/><admin-status/><oper-status/></physical-interface></interface-information>'  # limits the ammount of information gathered
    result = dev.rpc.get_interface_information(interface_name=switchPort, filter_xml=filter) # 
    interfaceInfo = etree.tostring(result, encoding='unicode')
    splitString = interfaceInfo.splitlines()
    interfaceUpDown = ('{3}'.format(*splitString))
    TextBoxData.insert(INSERT, "\nInterface " + switchPort + " is " + interfaceUpDown)
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
        TextBoxData.insert(INSERT, ", Disabling interface... \n")

        cu = Config(dev)
        cu.lock()
        cu.load(config_disable)
        diff = cu.diff()
        TextBoxData.insert(INSERT, "\nNow commiting, please wait. \n")
        cu.commit()
        TextBoxData.insert(INSERT, "Commit complete.\n")
        cu.unlock()
        TextBoxData.insert(INSERT, '%s' % (diff))
        TextBoxData.see("end")
        dev.close()
        
    elif interfaceUpDown == "down":
        TextBoxData.insert(INSERT, ", Enabling interface... \n")

        cu = Config(dev)
        cu.lock()
        cu.load(config_enable)
        diff = cu.diff()
        TextBoxData.insert(INSERT, "\nNow commiting, please wait. \n")
        cu.commit()
        TextBoxData.insert(INSERT, "Commit complete. \n")
        cu.unlock()
        TextBoxData.insert(INSERT, '%s' % (diff))
        TextBoxData.see("end")
        dev.close()

    else:
        TextBoxData.insert(INSERT, "\nERROR\n")
        TextBoxData.see("end")
        dev.close()
        
#------------------------------------------------------------------------------------
# Turn dot1x on or off and move interface to correct vlan

def toggleDot1x():
    username = usernameEntry.get()      # Get username from entrybox in mainWindow
    password1 = passwordEntry.get()     # Get password from entrybox in mainWindow
    hostIP = SwitchIPEntry.get()        # Get switch IP from entrybox in mainWindow
    switchPort = SwitchPortEntry.get()  # Get switchport from entrybox in mainWindow

    #TextBoxData.insert(INSERT, "Working with port: " + switchPort)
 
    if "ge-0" in switchPort:
        portVlan = "User_Data_11"
    elif "ge-1" in switchPort:
        portVlan = "User_Data_21"
    elif "ge-2" in switchPort:
        portVlan = "User_Data_31"
    elif "ge-3" in switchPort:
        portVlan = "User_Data_41"
    elif "ge-4" in switchPort:
        portVlan = "User_Data_51"
    elif "ge-5" in switchPort:
        portVlan = "User_Data_61"
    elif "ge-6" in switchPort:
        portVlan = "User_Data_71"
    elif "ge-7" in switchPort:
        portVlan = "User_Data_81"
    elif "ge-8" in switchPort:
        portVlan = "User_Data_91"
    else:
        TextBoxData.insert(INSERT, "\n" + "Error in Vlan selection \n")

    config_interface_userdata = '''
    interfaces {
        '''+switchPort+''' {
            description "User Access Port";
            unit 0 {
                family ethernet-switching {
                    vlan {
                        delete: members Dot1x_Holding;
                        members '''+portVlan+''';
                    }
                    storm-control sc1;
                }
            }
        }
    }
    protocols {
        dot1x {
            authenticator {
                interface {
                    inactive: '''+switchPort+''' {
                        supplicant single-secure;
                    }
                }
            }
        }
    }
    '''
    config_interface_dot1x = '''
    interfaces {
        ge-0/0/1 {
            description "User Access Port";
            unit 0 {
                family ethernet-switching {
                    vlan {
                        delete: members User_Data_11;
                        members Dot1x_Holding;
                    }
                    storm-control sc1;
                }
            }
        }
    }
    protocols {
        dot1x {
            authenticator {
                interface {
                     active: ge-0/0/1 {
                        supplicant single-secure;
                    }
                }
            }
        }
    }
    '''
        
    TextBoxData.insert(INSERT, "\nThis port will end up in Vlan: " + portVlan + "\n")

    dev = Device(host=hostIP, user=username, password=password1, use_filter=True) # Specifies connection detials
    dev.open() # Opens the connection with switch
    filter = '<interfaces><interface><name>'+switchPort+'</name><unit><name>0</name><family><ethernet-switching><vlan><members/></vlan></ethernet-switching></family></unit></interface></interfaces>'  # limits the ammount of information gathered
    data = dev.rpc.get_config(filter_xml=filter)
    result = (etree.tostring(data, encoding='unicode', pretty_print=True))

    splitString = result.splitlines()
    currentVlan = ('{9}'.format(*splitString))

    TextBoxData.insert(INSERT, "\nThis interface is currently in: " + currentVlan + "\n")
    TextBoxData.see("end")

    if "Dot1x_Holding" in currentVlan:
        TextBoxData.insert(INSERT, "\nThis port is in Dot1x_Holding it will be placed in " + portVlan + "\n")
        TextBoxData.insert(INSERT, "\nThis interface is currently in: Dot1x_Holding \n")
        cu = Config(dev)
        cu.lock()
        #print(config_interface_userdata)
        cu.load(config_interface_userdata)
        diff = cu.diff()
        TextBoxData.insert(INSERT, "Now commiting, please wait. \n")
        cu.commit()
        TextBoxData.insert(INSERT, "Commit complete.\n")
        cu.unlock()
        TextBoxData.insert(INSERT, '%s' % (diff))
        TextBoxData.see("end")
        dev.close()
        
    elif "User_Data" in currentVlan:
        TextBoxData.insert(INSERT, "\nThis port is in " + portVlan + " it will be placed in Dot1x_Holding\n")
        cu = Config(dev)
        cu.lock()
        cu.load(config_interface_dot1x)
        diff = cu.diff()
        TextBoxData.insert(INSERT, "Now commiting, please wait. \n")
        cu.commit()
        TextBoxData.insert(INSERT, "Commit complete.\n")
        cu.unlock()
        TextBoxData.insert(INSERT, '%s' % (diff))
        TextBoxData.see("end")
        dev.close()
    else:  

        dev.close()   

#------------------------------------------------------------------------------------
#def monitorInterface():        
    username = usernameEntry.get()      # Get username from entrybox in mainWindow
    password1 = passwordEntry.get()     # Get password from entrybox in mainWindow
    hostIP = SwitchIPEntry.get()        # Get switch IP from entrybox in mainWindow
    switchPort = SwitchPortEntry.get()  # Get switchport from entrybox in mainWindow
    count = 0

    with Device(host=hostIP, user=username, password=password1) as dev:
        dev.open()

        while count < 10:
            logReturn = dev.rpc.get_log(filename='interface-logs')
            logReturn1 = interfaceInfo = etree.tostring(logReturn, encoding='unicode', pretty_print=True)
            logReturn2 = logReturn1.split('\n')
            logReturn3 = logReturn2[-10:]
                       
           # for x in logReturn3:
            #    if "ge-" in x:
            #        x = 


            


            

            count = count+1
        dev.close()

        
#------------------------------------------------------------------------------------

def interfaceStatus():
    #TextBoxData.delete('1.0', END)
    
    username = usernameEntry.get()      # Get username from entrybox in mainWindow
    password1 = passwordEntry.get()     # Get password from entrybox in mainWindow
    hostIP = SwitchIPEntry.get()        # Get switch IP from entrybox in mainWindow
    switchPort = SwitchPortEntry.get()  # Get switchport from entrybox in mainWindow
    switchName = SwitchNameEntry.get()  # Get switchName from entrybox in mainWindow
    
    with Device(host=hostIP, user=username, password=password1, use_filter=True) as dev:
        dev.open()
        
        filter = '<interface-information><physical-interface><name/><admin-status/><oper-status/></physical-interface></interface-information>'
        result = dev.rpc.get_interface_information(interface_name=switchPort, filter_xml=filter)
        interfaceInfo = etree.tostring(result, encoding='unicode')
        splitString = interfaceInfo.split("\n")
        
        interfaceInfo1 = ("Building: " +switchName+ '\nInterface: {1}\nAdmin Status:\t{3}\nOper Status:\t{5}\n'.format(*splitString))
        interfaceInfo2 = ('{5}'.format(*splitString))
        TextBoxData.see("end")

        filter = '<interfaces><interface><name>'+switchPort+'</name><unit><name>0</name><family><ethernet-switching><vlan><members/></vlan></ethernet-switching></family></unit></interface></interfaces>'
        result2 = dev.rpc.get_config(filter_xml=filter)
        interfaceVlan = etree.tostring(result2, encoding='unicode', pretty_print=True)
        interfaceVlanList = interfaceVlan.split("\n")
        currentVlanUgly = interfaceVlanList[9]
        
        dev.close()
        
        if "User_Data" in currentVlanUgly:
            currentVlan = currentVlanUgly[23:35]
        elif "Dot1x_Holding" in currentVlanUgly:
            currentVlan = "Dot1x Holding"
        else:
            currentVlan = "Unknown Vlan"

    TextBoxData.insert(INSERT, "\n" + interfaceInfo1 + "\nCurrnet Vlan: " +currentVlan+ "\n" )
    TextBoxData.see("end")
    
    #TextBoxData.insert(INSERT, interfaceInfo2)
    if "down" in interfaceInfo2:
        TextBoxData.insert(INSERT, "\nThis interface is physically DOWN,\nPlease check fibres and then send to:\n'DXC Desk Side Support'\n")
        TextBoxData.see("end")
    else:
        #TextBoxData.insert(INSERT, "\nThis interface is physically UP\n")
        return
        
#------------------------------------------------------------------------------------   
# Show Dot1x Status
def interfaceDot1xStatus():
    
    username = usernameEntry.get()      # Get username from entrybox in mainWindow
    password1 = passwordEntry.get()     # Get password from entrybox in mainWindow
    hostIP = SwitchIPEntry.get()        # Get switch IP from entrybox in mainWindow
    switchPort = SwitchPortEntry.get()  # Get switchport from entrybox in mainWindow
    switchName = SwitchNameEntry.get()  # Get switchName from entrybox in mainWindow

       
    with Device(host=hostIP, user=username, password=password1) as dev: #, use_filter=True) as dev:
        dev.open()
        result = dev.rpc.get_dot1x_interface_information(interface_name=switchPort)
        dev.close()

    interfaceDot1xInfo = etree.tostring(result, encoding='unicode', pretty_print=True)

    if "Initialize" in interfaceDot1xInfo:
        TextBoxData.insert(INSERT, "\nInterface: " +switchPort+ "\nState: Initialize\nMAC: --:--:--:--:--:--\nHostname: None\n")
        TextBoxData.see("end")
    elif "Connecting" in interfaceDot1xInfo:
        TextBoxData.insert(INSERT, "\nInterface: " +switchPort+ "\nState: Connecting\nMAC: --:--:--:--:--:--\nHostname: None\n")
        TextBoxData.see("end")
    elif "Authenticated" in interfaceDot1xInfo:
        a = interfaceDot1xInfo.split("\n")
        interfaceNameUgly = a[2]
        interfaceName = interfaceNameUgly[20:28]
        macAddressUgly = a[4]
        macAddress = macAddressUgly[22:39]
        hostNameUgly = a[5]
        hostName = hostNameUgly[15:49]
        dot1xStateUgly = a[6]
        dot1xState = dot1xStateUgly[11:24]
        TextBoxData.insert(INSERT, "\nInterface: " +interfaceName + "\nState: " +dot1xState+ "\nMAC: " +macAddress+ "\nHostname: " +hostName + "\n")
        TextBoxData.see("end")
    else:
        TextBoxData.insert(INSERT, "\nInterface: " +switchPort+ "\nState: Not in Dot1x\nMAC: --:--:--:--:--:--\nHostname: None\n")
        TextBoxData.see("end")



    
        
        
#------------------------------------------------------------------------------------     
#------------------------------------------------------------------------------------ 
def databaseManagment():
    # Nested Functions
#------------------------------------------------------------------------------------
    
    # Add to DB Window Function
    def addDB():
        adddbWindow = Tk()
        adddbWindow.geometry('300x100')
        adddbWindow.title("Add to DB")
        #Save to DB Functio
        def addSubmit():
            # Create/ Connect to DB
            dbConnection = sqlite3.connect('App_DB')
            # Cursor
            cursor = dbConnection.cursor()
            # Inset data in to table
            cursor.execute("INSERT INTO Switch_Table VALUES (:Switch_Name, :Switch_IP)",
                           {
                               'Switch_Name':swNameEntry.get(),
                               'Switch_IP':swIPEntry.get()
                               })
            # DB Commit
            dbConnection.commit()
            # db Close connection
            dbConnection.close()
            # Clear Entry Boxes
            swNameEntry.delete(0, END)
            swIPEntry.delete(0, END)
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
        
#------------------------------------------------------------------------------------        
    #Show DB in Text Window
        
    def displayDB():
        # Clear screen
        textBox.delete('1.0', END)
        # Create/ Connect to DB
        dbConnection = sqlite3.connect('App_DB')
        # Cursor
        cursor = dbConnection.cursor()
        # Query DB
        cursor.execute("SELECT *, oid FROM Switch_Table")
        records = cursor.fetchall()
        #print(records)
        print_db = ""
        for record in records:
            print_db += str(record[2]) + " " + "\t" + str(record[0]) + " " + str(record[1]) + "\n"

        textBox.insert(INSERT, print_db)
               
        # DB Commit
        dbConnection.commit()
        # db Close connection
        dbConnection.close()
        
#------------------------------------------------------------------------------------

    # Delete Entry from DB
    def deleteDBEntry():
        # Create/ Connect to DB
        dbConnection = sqlite3.connect('App_DB')
        # Cursor
        cursor = dbConnection.cursor()
        # Delete record
        cursor.execute("DELETE from Switch_Table WHERE oid = " + deleteRecordEntry.get())         
        # DB Commit
        dbConnection.commit()
        # db Close connection
        dbConnection.close()
        #Clear Box
        deleteRecordEntry.delete(0, END)
 
#------------------------------------------------------------------------------------
    # Create Window 'databaseManagment'
    
    dbManagment = Tk()
    dbManagment.geometry('645x500')
    dbManagment.title("DB Managment")
    dbManagment.resizable(False, False)
    # Labels
    manageDBLabel = Label(dbManagment, text="Database Management")
    manageDBLabel.config(font=("Verdana", 25, "bold"))
    manageDBLabel.place(x=10, y=5)
    oidLabel = Label(dbManagment, text="OID to Delete:")
    oidLabel.config(font=("Verdana", 8, "bold"))
    oidLabel.place(x=400, y=60, height=40, width=100)
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
    
    # Entry Box
    deleteRecordEntry = Entry(dbManagment, justify='center')
    deleteRecordEntry.config(font=("Verdana", 8, "bold"))
    deleteRecordEntry.place(x=500, y=60, height=40, width=50)
    # Textbox
    textBox = Text(dbManagment)
    textBox.config(font=("Verdana", 8))
    textBox.place(x=2, y=110, height=340, width=640)
 
#------------------------------------------------------------------------------------
#DATABASE SECTION
    
# Create/ Connect to DB
dbConnection = sqlite3.connect('App_DB')
# Cursor
cursor = dbConnection.cursor()
# Create table
#cursor.execute("""CREATE TABLE Switch_Table (
#                Switch_Name text,
#                Switch_IP integer)""")
# DB Commit
dbConnection.commit()
# db Close connection
dbConnection.close()

#------------------------------------------------------------------------------------

# Buttons
searchUINButton = Button(mainWindow, text="Search UIN")
searchUINButton.config(font=("Verdana", 10, "bold"))
searchUINButton.place(x=215, y=185, height=30, width=100)
searchSwitchButton = Button(mainWindow, text="Search", command=switchSearch)
searchSwitchButton.config(font=("Verdana", 10, "bold"))
searchSwitchButton.place(x=330, y=260, height=25, width=80)
exitButton = Button(mainWindow, text="Exit", command=mainWindow.destroy)
exitButton.config(font=("Verdana", 10, "bold"))
exitButton.place(x=710, y=755, height=40, width=80)
manageDBButton = Button(mainWindow, text="Manage Database", command=databaseManagment)
manageDBButton.config(font=("Verdana", 10, "bold"))
manageDBButton.place(x=550, y=755, height=40, width=150)
interfaceStatusButton = Button(mainWindow, text="Interface\nStatus", command=interfaceStatus)
interfaceStatusButton.config(font=("Verdana", 10, "bold"))
interfaceStatusButton.place(x=15, y=360, height=50, width=90)
monitorInterfaceButton = Button(mainWindow, text="Monitor\nInterface")#, command=monitorInterface)
monitorInterfaceButton.config(font=("Verdana", 10, "bold"))
monitorInterfaceButton.place(x=120, y=360, height=50, width=90)
toggleAdminButton = Button(mainWindow, text="Toogle\nAdmin", command=toggleAdmin)
toggleAdminButton.config(font=("Verdana", 10, "bold"))
toggleAdminButton.place(x=225, y=360, height=50, width=90)
toggledot1xButton = Button(mainWindow, text="Toogle\ndot1x", command=toggleDot1x)
toggledot1xButton.config(font=("Verdana", 10, "bold"))
toggledot1xButton.place(x=330, y=360, height=50, width=90)
showDo1xStatusButton = Button(mainWindow, text="Show\nDot1x", command=interfaceDot1xStatus)
showDo1xStatusButton.config(font=("Verdana", 10, "bold"))
showDo1xStatusButton.place(x=435, y=360, height=50, width=90)

# Lables
mainLabel = Label(mainWindow, text="Quest for Py")
mainLabel.config(font=("Verdana", 25, "bold"))
mainLabel.place(x=15, y=15)
usernameLabel = Label(mainWindow, text="Username: ")
usernameLabel.config(font=("Verdana", 10))
usernameLabel.place(x=30, y=90)
passwordLabel = Label(mainWindow, text="Password: ")
passwordLabel.config(font=("Verdana", 10))
passwordLabel.place(x=30, y=120)
switchSearchLabel = Label(mainWindow, text="Switch: ")
switchSearchLabel.config(font=("Verdana", 10))
switchSearchLabel.place(x=30, y=265)
switchIPLabel = Label(mainWindow, text="Switch IP: ")
switchIPLabel.config(font=("Verdana", 10))
switchIPLabel.place(x=30, y=295)
switchPortLable = Label(mainWindow, text="Switch Port: ")
switchPortLable.config(font=("Verdana", 10))
switchPortLable.place(x=30, y=325)
subTitleLoginLabel = Label(mainWindow, text="Login Credentials: ")
subTitleLoginLabel.config(font=("Verdana", 10, "bold"))
subTitleLoginLabel.place(x=15, y=65)
subTitleLoginUIN = Label(mainWindow, text="UIN Search: ")
subTitleLoginUIN.config(font=("Verdana", 10, "bold"))
subTitleLoginUIN.place(x=15, y=160)
searchUINLable = Label(mainWindow, text="UIN: ")
searchUINLable.config(font=("Verdana", 10))
searchUINLable.place(x=30, y=190)
subTitleSwitchInfo = Label(mainWindow, text="Switch Information: ")
subTitleSwitchInfo.config(font=("Verdana", 10, "bold"))
subTitleSwitchInfo.place(x=15, y=240)

# Entry
usernameEntry = Entry(mainWindow, justify='center')
usernameEntry.config(font=("Verdana", 10))
usernameEntry.place(x=110, y=90, height=25, width=200)
passwordEntry = Entry(mainWindow, show="*", justify='center')
passwordEntry.config(font=("Verdana", 10))
passwordEntry.place(x=110, y=120, height=25, width=200)
UINEntry = Entry(mainWindow, justify='center')
UINEntry.config(font=("Verdana", 10))
UINEntry.place(x=75, y=185, height=30, width=130)
SwitchNameEntry = Entry(mainWindow, justify='center')
SwitchNameEntry.config(font=("Verdana", 10))
SwitchNameEntry.place(x=120, y=260, height=25, width=200)
SwitchIPEntry = Entry(mainWindow, justify='center')
SwitchIPEntry.config(font=("Verdana", 10))
SwitchIPEntry.place(x=120, y=290, height=25, width=200)
SwitchPortEntry = Entry(mainWindow, justify='center')
SwitchPortEntry.config(font=("Verdana", 10))
SwitchPortEntry.place(x=120, y=320, height=25, width=200)


# Text Box
TextBoxData = Text(mainWindow)
TextBoxData.place(x=10, y=420, height=330, width=780)


mainWindow.mainloop()
