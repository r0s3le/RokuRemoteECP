import pycurl
import re
import readchar
import socket
import xml.etree.ElementTree as ET
from io import BytesIO

# This is a simple script to control a Roku TV with External Control Protocol over a local network.
# It validates that an IP address is a ECP enabled Roku device, and sends http requests to control the TV

# Todo: make UDP multicast discovery function



                                ###### Variable Decs ######

# number of connection/reconnection attempts before quitting
conAttempts = 5

# if you know your Roku's IP, place it here to avoid scanning
# helpful if you have multiple Roku devices
ROKU_IP = None

# number of attempts to listen for Roku devices on network
# a larger number means more time scanning



                                ###### Function Defs ######

def Roku_SSDP():
# this function sends a udp 1900 request to the multicast address to find a roku device
# if you have more than one roku device please input the IP of the one you want to control
# in the variable def 
    
    def ParseResponse(response: str) -> dict:
    # this nested function parses the SSDP response into a dictionary
        headers = {}
        lines = response.split("\r\n")

        # first line is the status line (not a key:value pair)
        if lines:
            headers["_status"] = lines[0]

        for line in lines[1:]:
            if not line.strip():
                continue    # skip empty lines

            if ":" in line:
                key, value = line.split(":", 1)     # split only on first colon
                headers[key.strip().lower()] = value.strip()

        return headers
    
    # Roku_SSDP() begins here
    message = (
        "M-SEARCH * HTTP/1.1\r\n"
        "HOST: 239.255.255.250:1900\r\n"
        "MAN: \"ssdp:discover\"\r\n"
        "ST: roku:ecp\r\n"
        "\r\n"
    )

    print("[+] Starting scan for Roku Devices")

    try:
        # create UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.settimeout(5)

        # send SSDP discovery request
        sock.sendto(message.encode("utf-8"), ("239.255.255.250", 1900))

        # listen for response
        while True:
            try:
                data, addr = sock.recvfrom(1024)
                print(f"[+] Found device at {addr}")
                print(f"[+] SSDP response received\n\n{data.decode("utf-8")}")

            except socket.timeout:
                break

    except Exception as e:
        print(f"[-] Error: {e}")
        return None
    
    # check parsed list for service type and ip variables
    try:
        SSDP_Dict = ParseResponse(data.decode("utf-8"))
        if SSDP_Dict["st"] == "roku:ecp":
            # This only works digit wise, further validation will occur shortly
            match = re.search(r'(\d{1,3}(?:\.\d{1,3}){3})', SSDP_Dict["location"])

            if match: 
                if match.group(1) != addr[0]:
                    raise Exception("IP address of sender and SSDP message dont match")

                return match.group(1)

            else:
                raise Exception("Invalid Roku SSDP response")

    except Exception as e:
        print(f"[-] {e}")
        return None

def validate_RokuECP(IPV4_addr):
# this function takes an IP address as a string arguement and returns a true boolean value if it determines
# a device is a valid Roku External Control Protocol. If the device cannot be reached, or it 

    # set pattern to regex identifying IPV4
    pattern = r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
    pattern = re.compile(pattern)
    
    # match regex pattern against the entered IP
    if IPV4_addr is not None and re.fullmatch(pattern,IPV4_addr):
        print(f"[+] {IPV4_addr} Accepted") 

        # build a curl request to port 8060 for ECP
        buffer = BytesIO()              # response buffer
        rokucurl = pycurl.Curl()        # create the curl object
        rokucurl.setopt(rokucurl.URL, "http://" + IPV4_addr + ":8060/query/device-info")    # curl URL will return XML response if Roku
        rokucurl.setopt(rokucurl.TIMEOUT, 10)
        rokucurl.setopt(rokucurl.WRITEDATA, buffer)      # curl will write to variable

        # handle the actual request
        try:
            rokucurl.perform()

        except Exception as e:
            print(f"[-] Failed to reach Roku device: {e}")
            return False        # retry loop

        finally:
            rokucurl.close()

        # load response into string 
        response = buffer.getvalue()
        #print(response.decode('utf-8'))    # print out response for development
        
        # parse XML response
        try:
            root = ET.fromstring(response)

        except Exception as e:
            print(f"[-] Invalid XML response: {e}")
            return False
        
        # get <ecp-setting-mode> to detect ECP status
        if root.find('ecp-setting-mode').text != "enabled":
            print("[-] External Control Protocol isn't enabled on this device...")
            return False        # retry loop

        else:
            print("[+] ECP enabled. Connected to Roku Device!")
            return True         # exit loop

    else:
        if IPV4_addr is not None:
            print("[-] "+IPV4_addr+" is not a valid IPV4 address")

        return False        # retry loop



                                ###### Class Defs ######
   
class RokuECP_Remote:
# this is a class for handling keyboard input, and sending ECP commands to Roku devices.
    
    def __init__(self, IPV4_addr):
        self.IPV4_addr = IPV4_addr
        self.keybinds = {'q' : "keypress/poweroff",
                        'w' : "keypress/poweron",
                        'h' : "keypress/left",
                        'j' : "keypress/down",
                        'k' : "keypress/up",
                        'l' : "keypress/right",
                        ' ' : "keypress/select",
                        'b' : "keypress/back",
                        'u' : "keypress/volumedown",
                        'i' : "keypress/volumeup",
                        'm' : "keypress/volumemute",
                        'e' : "keypress/home",
                        't' : "typetext"}       # special case for typing to Roku

    def sendCommand(self,ECP_Command):
    # This function sends an http post request to the IPV4 address given in arg1 and submits the URL
    # encoded command from arg2
        if ECP_Command is None:
            return True
        # create buffer and curl object
        buffer = BytesIO()
        rokuRemote = pycurl.Curl()

        # set roku remote object to post and use IPV4_addr and ECP_Command to create URL
        rokuRemote.setopt(rokuRemote.URL, "http://"+self.IPV4_addr+":8060/"+ECP_Command)
        rokuRemote.setopt(rokuRemote.CONNECTTIMEOUT, 2)
        rokuRemote.setopt(rokuRemote.TIMEOUT, 1)
        rokuRemote.setopt(rokuRemote.WRITEDATA, buffer)
        rokuRemote.setopt(rokuRemote.POST, 1)
        rokuRemote.setopt(rokuRemote.POSTFIELDS, "")
        
        # handle send request and handle 
        try:
            rokuRemote.perform()

        except Exception as e:
            print(f"[-] Could not deliver request: {e}")
            return False

        finally:
            rokuRemote.close()

        return True
     

    def listen(self):
    # listener function for reading console input
        command = None
        while command is None:

            # readchar.readkey() reads input from the console
            keyboardInput = readchar.readkey()

            # use get with None type to continue loop if no key is pressed
            command = self.keybinds.get(keyboardInput, None) 

        # typetext is a special client side command that calls the class function typetext
        if command == "typetext":
            return self.typeText()
        else:
            return command

    def typeText(self):
        print("\nWARNING: Sending passwords over HTTP is insecure!\n\nEnter Text:")
        
        # capture user input and break it down into individual keypress events
        sendString = input()
        for letter in sendString:
            if letter != ' ':
                self.sendCommand("keypress/Lit_"+letter)

            else:
                self.sendCommand("keypress/Lit_%20") # Roku uses select as spaces

        # return enter to the RokuECP_Remote() class call in main       
        return "keypress/enter"


                                 ###### Main Control Structure ######

# validate ip address as a Roku device with ECP enabled
is_RokuECP = False
while (is_RokuECP is False) and (conAttempts > 0): 
    if ROKU_IP is None:
        ROKU_IP = Roku_SSDP()
    if ROKU_IP is None:
        print("Please enter Roku IP: ")
        ROKU_IP=input()

    is_RokuECP = validate_RokuECP(ROKU_IP)
    
    # device has 5 connection attempts
    if is_RokuECP is True:
        conAttempts = 5

    else:
        conAttempts -= 1

    while (is_RokuECP is True):
        # Check if remote object exists
        try:
            loopRemote

        # if the object doesnt exist make one    
        except NameError:
            loopRemote = RokuECP_Remote(ROKU_IP)

        is_RokuECP = loopRemote.sendCommand(loopRemote.listen())

    print("[-] Disconnected from Roku device. Reconnecting...")

print("[-] Connection failed. aborting..")

