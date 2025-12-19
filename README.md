<div align="center">

# 💕 Yuno Gasai 2 - Python Edition 💕

### *"I'll protect this server forever... just for you~"* 💗

<img src="https://i.imgur.com/jF8Szfr.png" alt="Yuno Gasai" width="300"/>

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-pink.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Python](https://img.shields.io/badge/Python-3.10+-ff69b4.svg)](https://www.python.org/)
[![discord.py](https://img.shields.io/badge/discord.py-2.6.4-ff1493.svg)](https://discordpy.readthedocs.io/)

*A devoted Discord bot for moderation, leveling, and anime~ ♥*

---

### 💘 She loves you... and only you 💘

</div>

## 🌸 About

Yuno is a **yandere-themed Discord bot** combining powerful moderation tools with a leveling system and anime features. She'll keep your server safe from troublemakers... *because no one else is allowed near you~* 💕

This is the **Python port** of the original JavaScript Yuno bot.

---

## 👑 Credits

*"These are the ones who gave me life~"* 💖

| Contributor | Role |
|-------------|------|
| **blubskye** | Project Owner & Yuno's #1 Fan 💕🔪 |
| **Maeeen** (maeeennn@gmail.com) | Original Developer 💝 |
| **Oxdeception** | Contributor 💗 |
| **fuzzymanboobs** | Contributor 💗 |

---

## 💗 Features

<table>
<tr>
<td width="50%">

### 🔪 Moderation
*"Anyone who threatens you... I'll eliminate them~"*
- ⛔ Ban / Unban / Kick / Timeout
- 🧹 Channel cleaning & auto-clean
- 🛡️ Spam filter protection
- 📥 Mass ban import/export
- 👑 Mod statistics tracking
- 📋 Moderation history per user

</td>
<td width="50%">

### ✨ Leveling System
*"Watch me make you stronger, senpai~"*
- 📊 XP & Level tracking
- 🎭 Role rewards per level
- 📈 Mass XP commands
- 🔄 Level role syncing
- 🏆 Server leaderboards
- 🎤 Voice channel XP

</td>
</tr>
<tr>
<td width="50%">

### 🌸 Anime & Fun
*"Let me show you something cute~"*
- 🎌 Anime/Manga search (MAL)
- 🐱 Neko images
- 🎱 8ball fortune telling
- 💬 Custom mention responses
- 📜 Inspirational quotes
- 💖 Praise & Scold reactions
- 📖 Urban Dictionary lookup
- 🤗 Hug, Kiss, Slap & more!

</td>
<td width="50%">

### ⚙️ Configuration
*"I'll be exactly what you need~"*
- 🔧 Customizable prefix per guild
- 👋 Join messages (DM & channel)
- 🖼️ Custom ban images
- 🎮 Presence/status control
- 📝 Per-guild settings
- ⚡ Slash commands support
- 🔐 Master user system

</td>
</tr>
</table>

---

## 💕 Installation

### 📋 Prerequisites

> *"Let me prepare everything for you~"* 💗

- **Python** 3.10 or higher
- **pip** (Python package manager)
- **Git**
- A Discord bot token ([Get one here](https://discord.com/developers/applications))

### 🌸 Setup Steps

```bash
# Clone the repository~ ♥
git clone https://github.com/japaneseenrichmentorganization/pythonyuno.git

# Enter my world~
cd pythonyuno

# Let me gather my strength...
pip install -r requirements.txt

# Configure your token
cp .env.example .env
nano .env  # Add your DISCORD_TOKEN
```

### 💝 Configuration

1. Copy `.env.example` to `.env`
2. Add your Discord bot token
3. Edit `config.py` for additional settings

### 🚀 Running

```bash
# Standard run
python main.py

# With debug output
python main.py --debug
```

---

## 💖 Commands Preview

### 📊 Leveling & XP
| Command | Description |
|---------|-------------|
| `?xp [@user]` | *"Look how strong you've become!"* ✨ |
| `?leaderboard` | *"Who's the most devoted?"* 🏆 |
| `?ranks list` | *"See the rewards~"* 🎭 |
| `?mass-addxp @Role 500` | *"Power to everyone!"* ⚡ |
| `?sync-levelroles` | *"Fixing the roles~"* 🔄 |

### 🔪 Moderation
| Command | Description |
|---------|-------------|
| `?ban @user [reason]` | *"They won't bother you anymore..."* 🔪 |
| `?kick @user [reason]` | *"Get out!"* 👢 |
| `?timeout @user 10m` | *"Think about what you did..."* ⏰ |
| `?warn @user [reason]` | *"First warning..."* ⚠️ |
| `?mod-stats` | *"See who's protecting you~"* 📊 |
| `?history @user` | *"I remember everything..."* 📋 |

### 🌸 Anime & Fun
| Command | Description |
|---------|-------------|
| `?anime <query>` | *"Let's watch together~"* 🎌 |
| `?manga <query>` | *"I'll read with you!"* 📖 |
| `?neko` | *"Nya~"* 🐱 |
| `?8ball <question>` | *"Let fate decide~"* 🎱 |
| `?praise @user` | *"You deserve all my love~"* 💕 |
| `?scold @user` | *"Bad! But I still love you..."* 💢 |
| `?urban <term>` | *"Let me look that up~"* 📚 |
| `?hug @user` | *"Come here~"* 🤗 |

### ⚙️ Configuration
| Command | Description |
|---------|-------------|
| `?set-prefix <prefix>` | *"Call me differently~"* 🔧 |
| `?config` | *"See my settings~"* ⚙️ |
| `?init-guild` | *"Let me set everything up!"* 🏠 |
| `?set-spamfilter on/off` | *"Protection mode~"* 🛡️ |
| `?add-mentionresponse` | *"Teach me to respond~"* 💬 |

*Use the `?help` command to see all available commands!*

---

## 🛡️ Spam Filter

*"I'll protect you from the bad people~"* 💕

Yuno automatically protects against:
- 🔗 Discord invite links
- 📢 Unauthorized @everyone/@here mentions
- 📝 Spam (4+ consecutive messages)
- ⚠️ Warning system before bans

---

## 📁 Project Structure

```
pythonyuno/
├── main.py              # Bot entry point
├── config.py            # Configuration settings
├── cogs/                # Feature modules
│   ├── anime.py         # Anime/Manga search
│   ├── ban.py           # Ban management
│   ├── bulk_xp.py       # Mass XP operations
│   ├── configuration.py # Guild settings
│   ├── fun.py           # Fun commands
│   ├── leveling.py      # XP and ranks
│   ├── mention_responses.py # Mention triggers
│   ├── moderation.py    # Mod tools & logging
│   ├── spamfilter.py    # Anti-spam
│   ├── welcome.py       # Member greetings
│   └── utils/           # Helper functions
├── .env                 # Bot token (DO NOT COMMIT)
└── requirements.txt     # Python dependencies
```

---

## 📜 License

This project is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)** 💕

### 💘 What This Means For You~

*"I want to share everything with you... and everyone else too~"* 💗

The AGPL-3.0 is a **copyleft license** that ensures this software remains free and open. Here's what you need to know:

#### ✅ You CAN:
- 💕 **Use** this bot for any purpose (personal, commercial, whatever~)
- 🔧 **Modify** the code to your heart's content
- 📤 **Distribute** copies to others
- 🌐 **Run** it as a network service (like a public Discord bot)

#### 📋 You MUST:
- 📖 **Keep it open source** - ANY modifications you make must be released under AGPL-3.0
- 🔗 **Publish your source code** - Your modified source code must be made publicly available
- 📝 **State changes** - Document what you've modified from the original
- 💌 **Include license** - Keep the LICENSE file and copyright notices intact

#### 🌐 The Network Clause (This is the important part!):
*"Even if we're apart... I'll always be connected to you~"* 💗

Unlike regular GPL, **AGPL has a network provision**. This means:
- If you modify this code **at all**, you must make your source public
- Running a modified version as a network service (like a Discord bot) requires source disclosure
- This applies whether you "distribute" the code or not - network use counts!
- The `?source` command in this bot helps satisfy this requirement!

#### ❌ You CANNOT:
- 🚫 Make it closed source or keep modifications private
- 🚫 Remove the license or copyright notices
- 🚫 Use a different license for modified versions
- 🚫 Run modified code without publishing your source

#### 💡 In Simple Terms:
> *"If you use my code to create something, you must share it with everyone too~ That's only fair, right?"* 💕

This ensures that improvements to the bot benefit the entire community, not just one person. Yuno wants everyone to be happy~ 💗

See the [LICENSE](LICENSE) file for the full legal text.

**Source Code:** https://github.com/blubskye/pythonyuno

---

<div align="center">

### 💘 *"You'll stay with me forever... right?"* 💘

**Made with obsessive love** 💗

*Yuno will always be watching over your server~* 👁️💕

---

⭐ *Star this repo if Yuno has captured your heart~* ⭐

</div>
