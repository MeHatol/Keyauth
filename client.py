import os
import sys
import psutil
import time
import ssl
import hashlib
import uuid
from colorama import init, Fore
import requests
## This keyauth is shitty ass it was just for learning 

init(autoreset=True)


SERVER_IP = "your server ip"
SERVER_PORT = 5000
VALIDATION_URL = f"http://{SERVER_IP}:{SERVER_PORT}/validate"  

# List of known debugger processes(uh should be all tbh)
DEBUGGER_PROCESSES = [
    "http toolkit.exe",
    "httpdebuggerui.exe",
    "wireshark.exe",
    "fiddler.exe",
    "x64dbg.exe",
    "ida.exe",
    "charles.exe",
    "regedit.exe",
    "taskmgr.exe",
    "vboxservice.exe",
    "df5serv.exe",
    "processhacker.exe",
    "vboxtray.exe",
    "vmtoolsd.exe",
    "vmwaretray.exe",
    "ida64.exe",
    "ollydbg.exe",
    "pestudio.exe",
    "vmwareuser",
    "vgauthservice.exe",
    "vmacthlp.exe",
    "x96dbg.exe",
    "vmsrvc.exe",
    "x32dbg.exe",
    "vmusrvc.exe",
    "prl_cc.exe",
    "prl_tools.exe",
    "qemu-ga.exe",
    "joeboxcontrol.exe",
    "ksdumperclient.exe",
    "ksdumper.exe",
    "joeboxserver.exe",
    "xenservice.exe",
    "dbgview.exe",              # DebugView
    "windbg.exe",               # WinDbg
    "immunitydebugger.exe",     # Immunity Debugger
    "procexp.exe",              # Process Explorer
    "procmon.exe",              # Process Monitor
    "binaryninja.exe",          # Binary Ninja
    "r2.exe",                   # Radare2
    "cffexplorer.exe",          # CFF Explorer
    "redbg.exe",                # ReDbg
    "idag.exe",                 # IDA Pro (Interactive Disassembler)
    "ghidra.exe",               # Ghidra
    "vncserver.exe",            # VNC Server
    "cuckoo.exe",               # Cuckoo Sandbox
    "dumpsys.exe",              # Dumpsys
    "boofuzz.exe",              # Boofuzz (Fuzzing tool)
    "americanfuzzylop.exe",     # American Fuzzy Lop (Fuzzing tool)
    "sandboxie.exe",            # Sandboxie
    "apatedns.exe",             # ApateDNS
    "frida-server.exe",         # Frida Server
    "frida.exe",                # Frida
    "x32dbg.exe",               # x32dbg
    "x64dbg.exe",               # x64dbg
    "vboxservice.exe",          # VirtualBox Service
    "vboxtray.exe",             # VirtualBox Tray
    "qemu.exe",                 # QEMU
    "parallels.exe",            # Parallels Tools
    "pslist.exe",               # Sysinternals pslist
    "pskill.exe",               # Sysinternals pskill
    "winice.exe",               # WinICE
    "redmote.exe",              # RedMote (Remote Debugger)
    "timelimit.exe",            # TimeLimit (Debugging)
    "fuzz.exe",                 # Fuzzing Tool
    "pydbg.exe",                # PyDbg
    "bochs.exe",                # Bochs Emulator
    "cheatengine.exe",          # Cheat Engine
    "dbgclr.exe",               # CLR Debugger
    "olympicdebugger.exe",      # Olympic Debugger
    "gdb.exe",                  # GDB
    "pythondbg.exe",            # Python Debugger
    "csdbg.exe",                # C# Debugger
    "jdb.exe",                  # Java Debugger
    "dbx.exe",                  # DBX Debugger
    "nexpose.exe",              # Nexpose Debugger
    "win32dbg.exe",             # Win32Dbg
    "spybot.exe",               # Spybot
    "ida64.exe",                # IDA 64-bit
    "spdb.exe",                 # SPDB Debugger
    "sandboxy.exe",             # Sandboxy
    "xenserver.exe",            # Xen Server
    "virtualbox.exe",           # VirtualBox GUI
    "qemu-ga.exe",              # QEMU Guest Agent
    "sysinternals.exe",         # Sysinternals
    "cldbg.exe",                # CL Debugger
    "strace.exe",               # Strace Debugger
]


# Function to generate HWID
def get_hwid():
    if platform.system() == "Windows":
        # Use Machine GUID for Windows
        hwid = str(uuid.UUID(int=uuid.getnode()))
    else:
        # Use hostname for other OS (simplified example)
        hwid = platform.node()
    return hashlib.sha256(hwid.encode()).hexdigest()


# Function to check for running debuggers
def check_for_debuggers():
    # Check for any processes that match known debugger names
    for process in psutil.process_iter(['name']):
        try:
            if process.info['name'].lower() in [debugger.lower() for debugger in DEBUGGER_PROCESSES]:
                print(Fore.RED + f"[WARNING]: Debugger detected - {process.info['name']}")
                print(Fore.RED + "Debugger detected! Closing the program...\n")
                sys.exit(Fore.RED + "Closing program due to debugger detection...\n")  # Exit program immediately
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue


# Custom SSLAdapter for attaching SSL context
class SSLAdapter(requests.adapters.HTTPAdapter):
    def __init__(self, ssl_context=None, **kwargs):
        self.ssl_context = ssl_context
        super().__init__(**kwargs)

    def init_poolmanager(self, *args, **kwargs):
        # Create the pool manager with the custom SSL context
        kwargs['ssl_context'] = self.ssl_context
        return super().init_poolmanager(*args, **kwargs)


# Function to validate the key
def validate_key():
    hwid = get_hwid()
    key = input(Fore.CYAN + "Enter your license key: ")

    # Check for debuggers before proceeding
    check_for_debuggers()

    # Simulate a delay before validating the key (make it feel more natural)
    print(Fore.YELLOW + "Checking Key!...")

    time.sleep(1)  # Introduces a 1-second delay before making the request

    # Data to send to the server
    data = {
        "key": key,
        "hwid": hwid
    }

    try:
   
        context = ssl.create_default_context()
        context.check_hostname = True  
        context.verify_mode = ssl.CERT_REQUIRED  

   
        session = requests.Session()
        adapter = SSLAdapter(ssl_context=context)
        session.mount("https://", adapter)

        response = session.post(VALIDATION_URL, json=data)

        if response.status_code == 200:
            result = response.json()
            if result["status"] == "success":
                print(Fore.GREEN + f"[SUCCESS]: {result['message']}")
                return True
            else:
                print(Fore.RED + f"[ERROR]: {result['message']}")
                return False
        else:
            print(Fore.RED + f"[ERROR]: Server returned status code {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(Fore.RED + f"[ERROR]: Could not connect to the server: {e}")
        return False


# Main program execution
def main():
    os.system("cls" if os.name == "nt" else "clear")
    print(Fore.BLUE + "=== KeyAuth ===\n")

    # Check for debuggers before proceeding
    check_for_debuggers()

    # Immediately close the program if a debugger is detected
    sys.exit(Fore.RED + "Closing program due to debugger detection...\n")


if __name__ == "__main__":
    main()
