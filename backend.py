import discord
from discord import app_commands
import json
import os
import uuid
import datetime
import hashlib
import hmac
from flask import Flask, request, jsonify
import threading

# Initialize Discord client
intents = discord.Intents.default()
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

# JSON database for keys
DB_FILE = "keys.json"

if not os.path.exists(DB_FILE):
    with open(DB_FILE, 'w') as f:
        json.dump({"keys": []}, f)

# Load and save keys from the database
def load_keys():
    with open(DB_FILE, 'r') as f:
        return json.load(f)

def save_keys(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def generate_signature(data: str) -> str:
    return hmac.new(SECRET_KEY.encode(), data.encode(), hashlib.sha256).hexdigest()

# List of allowed user IDs for command access
ALLOWED_USER_IDS = ["1325045539192049767", "1008733385272856597"]

# List of blacklisted GPUs
BLACKLISTED_GPUS = [
    "NVIDIA GeForce 9500 GT (Microsoft Corporation - WDDM v1.1)",
    "Системный VGA графический адаптер",
    "Microsoft Remote Display Adapter",
    "Microsoft Basic Display Adapter",
    "Standard VGA Graphics Adapter",
    "ASPEED Graphics Family(WDDM)",
    "Intel(R) HD Graphics 4600",
    "Microsoft Hyper-V Video",
    "VirtualBox Graphics Adapter",
    "NVIDIA GeForce 9400M",
    "NVIDIA GeForce 840M",
    "AMD Radeon HD 8650G",
    "VMware SVGA 3D",
    "UKBEHH_S",
]

# Function to check if the user is authorized to run commands
async def is_authorized(interaction: discord.Interaction):
    if str(interaction.user.id) not in ALLOWED_USER_IDS:
        await interaction.response.send_message("You are not authorized to use this command.", ephemeral=True)
        return False
    return True

# Slash command to create a key
@tree.command(name="createkey", description="Generate a new key")
@app_commands.describe(duration="Duration of the key in days")
async def create_key(interaction: discord.Interaction, duration: int):
    if not await is_authorized(interaction):
        return
    
    keys = load_keys()
    new_key = str(uuid.uuid4())
    expiry_date = (datetime.datetime.now() + datetime.timedelta(days=duration)).strftime("%Y-%m-%d")
    
    # Generate the hash/signature for the key
    key_data = new_key + expiry_date  # Combine key and expiry date
    signature = generate_signature(key_data)  # Generate signature

    keys["keys"].append({
        "key": new_key,
        "expiry": expiry_date,
        "signature": signature,
        "hwid": None,
        "ip": None
    })
    save_keys(keys)
    await interaction.response.send_message(f"Key generated: `{new_key}`, Expiry: {expiry_date}", ephemeral=True)

# Slash command to remove a key
@tree.command(name="removekey", description="Remove an existing key")
async def remove_key(interaction: discord.Interaction, key: str):
    if not await is_authorized(interaction):
        return
    
    keys = load_keys()
    key_to_remove = None
    for k in keys["keys"]:
        if k["key"] == key:
            key_to_remove = k
            break
    
    if key_to_remove:
        keys["keys"].remove(key_to_remove)
        save_keys(keys)
        await interaction.response.send_message(f"Key `{key}` has been removed.", ephemeral=True)
    else:
        await interaction.response.send_message(f"Key `{key}` not found.", ephemeral=True)

# Slash command to list all keys
@tree.command(name="keylist", description="List all keys")
async def key_list(interaction: discord.Interaction):
    if not await is_authorized(interaction):
        return
    
    keys = load_keys()
    key_list = [k["key"] for k in keys["keys"]]
    if key_list:
        await interaction.response.send_message(f"Keys: {', '.join(key_list)}", ephemeral=True)
    else:
        await interaction.response.send_message("No keys found.", ephemeral=True)

# Slash command to get key info
@tree.command(name="keyinfo", description="Get information about a specific key")
async def key_info(interaction: discord.Interaction, key: str):
    if not await is_authorized(interaction):
        return
    
    keys = load_keys()
    for k in keys["keys"]:
        if k["key"] == key:
            await interaction.response.send_message(
                f"Key: {k['key']}\nHWID: {k['hwid']}\nIP: {k['ip']}\nExpiry: {k['expiry']}",
                ephemeral=True
            )
            return
    await interaction.response.send_message(f"Key `{key}` not found.", ephemeral=True)

# Flask API for key validation with hash check
app = Flask(__name__)

@app.route('/validate', methods=['POST'])
def validate_key():
    """Validate a key with HWID, IP, and GPU information."""
    data = request.json
    key = data.get("key")
    hwid = data.get("hwid")
    ip = request.remote_addr
    gpu_info = data.get("gpu")  # Assuming GPU info is provided in the request

    # Check if the GPU is blacklisted
    if gpu_info and any(blacklisted_gpu in gpu_info for blacklisted_gpu in BLACKLISTED_GPUS):
        return jsonify({"status": "error", "message": "Your GPU is blacklisted, access denied."})

    # Load keys and validate
    keys = load_keys()
    for k in keys["keys"]:
        if k["key"] == key:
            # Check the hash (signature) for tampering
            key_data = key + k['expiry']  # Combine key and expiry date
            signature = generate_signature(key_data)  # Generate signature for comparison

            if signature != k['signature']:
                return jsonify({"status": "error", "message": "Key data has been tampered with."})

            # If HWID is not set, link it to the incoming HWID and IP
            if k['hwid'] is None:
                k['hwid'] = hwid
                k['ip'] = ip
                save_keys(keys)
                return jsonify({"status": "success", "message": "Key linked and validated"})
            elif k['hwid'] == hwid:
                # If HWID matches, return success
                return jsonify({"status": "success", "message": "Key validated"})
            else:
                # If HWID doesn't match, return error
                return jsonify({"status": "error", "message": "HWID mismatch. This key is linked to a different HWID"})

    return jsonify({"status": "error", "message": "Invalid key"})

# Run Flask API in a separate thread
def run_api():
    app.run(host='0.0.0.0', port=5000)

@bot.event
async def on_ready():
    await tree.sync()
    print(f"Logged in as {bot.user}!")

if __name__ == "__main__":
    # Start Flask API and Discord bot
    threading.Thread(target=run_api).start()

bot.run("your bot token")
