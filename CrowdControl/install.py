import subprocess
import sys
import webbrowser
from os import path

if sys.version_info.major < 3 or (sys.version_info.major >= 3 and sys.version_info.minor < 7):
    print("Must be using at least Python 3.7!")
    sys.exit(1)


print("Installing requirements.\n")

try:
    code = subprocess.call(
        ["python", "-m", "pip", "install", "-r", "requirements.txt"],
        cwd=path.dirname(__file__)
    )
    if code != 0:
        raise FileNotFoundError
except FileNotFoundError:
    print("ERROR: Unable to start python, are you sure you added it to your PATH?")
    sys.exit(1)

input((
    "\nWhen you continue, a website will open. Login with Twitch, which will redirect you, then"
    " copy the displayed token into this command prompt.\n"
    "Press enter to continue.\n"
))

webbrowser.open("https://apple1417.dev/bl2/crowdcontrol/")

token = input("Paste the token here:\n")
open(path.join(path.dirname(__file__), "token.txt"), "w").write(token)  # noqa: SIM115

print((
    "\nRunning test program."
    " You should see a big dump of data whenever someone redeems a custom channel points reward in"
    " your channel."
    " Twitch default rewards will not do this."
    "\nIf this happens then you can safely close this window."
    " If not, restart this and make sure you pasted the token correctly.\n"
))

subprocess.call(
    ["python", "-m", "Listener", token],
    cwd=path.dirname(__file__)
)
