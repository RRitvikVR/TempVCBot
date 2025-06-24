# TempVCBot

A modern and flexible Discord bot that empowers users to create and manage their own **temporary voice channels** on demand.

---

## About The Project

Tired of a cluttered voice channel list?

**TempVCBot** solves this by allowing server members to instantly create private, temporary voice channels whenever they need them. Once everyone leaves, the channel is **automatically deleted**, keeping your server clean and organized.

This bot offers two convenient ways for users to get a channel:

* A simple `/createvc` slash command
* Joining a dedicated `➕ Create VC` voice channel

The channel creator gets full control via **DM-based menus** and **slash commands** to manage privacy, user limits, invites, and more.

---

## Key Features

* **🎙 On-Demand Channel Creation**
  Users can create a VC instantly using either a slash command or by joining a special "Create VC" channel.

* **🔧 Full User Control**
  The channel creator can:

  * 🔒 Set the channel to Public or Private
  * ➕ Invite specific members to a private channel
  * 👢 Kick members from the channel
  * 🔢 Set a custom user limit

* **Automatic Cleanup**
  Channels are deleted automatically when the last user leaves.

* ** Admin Setup**
  A one-time `/setup` command handles everything: it creates the needed category and permissions for you.

* **Interface**
  Built with `discord.py` using slash commands and ephemeral messages for a clean, user-friendly experience.

---

## Setup & Installation

### 1. Prerequisites

* Python 3.8+
* `discord.py`
  Install with:

  ```sh
  pip install discord.py
  ```

### 2. Create a Discord Bot Application

* Go to the [Discord Developer Portal](https://discord.com/developers/applications) and click **New Application**
* Navigate to the **Bot** tab → **Add Bot**
* Click **Reset Token** to get your bot’s token. **Keep it secret!**
* Under **Privileged Gateway Intents**, enable:

  * ✅ Server Members Intent
  * ✅ Voice States Intent
(If that doesn't work then give it admin power)

### 3. Run the Bot

* Download or clone the bot's code
* Open the `.py` file and replace:

  ```python
  TOKEN = "YOUR_BOT_TOKEN"
  ```
* Run the bot:

  ```sh
  python your_bot_file_name.py
  ```

### 4. Invite the Bot to Your Server

* In the Developer Portal, go to **OAuth2 → URL Generator**
* Select the following scopes:

  * `bot`
  * `applications.commands`
* Under **Bot Permissions**, select:

  * `Manage Channels`
  * `Manage Roles`
  * `Move Members`
* Copy the generated URL, paste it into your browser, and add the bot to your server

---

## Usage Guide

### For Server Admins

* Run the setup command:

  ```
  /setup
  ```
* This creates:

  * A category: **Temporary Channels**
  * A voice channel: **➕ Create VC**
* Permissions are auto-configured. This only needs to be done **once**.

### For All Users

#### ➕ Method 1: Join-to-Create

* Join the **➕ Create VC** voice channel
* A private voice channel will be created, and you’ll be moved into it

#### Method 2: Slash Command

* Type:

  ```
  /createvc
  ```
* The bot will create a channel and send you a DM with controls

#### Manage Your Channel

* In DMs, you'll receive buttons to:

  * Make the channel **Public** or **Private**
  * Set a **User Limit**

* Use these slash commands:

  ```
  /invite [user]   # Grants access to your private channel
  /kick [user]     # Removes a user from your channel
  ```

---

## License

This project is open-source and free to use under the [MIT License](LICENSE).
