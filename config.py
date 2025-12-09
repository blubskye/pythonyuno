"""
Configuration file for Yuno Discord Bot
Customize these values to adjust bot behavior
"""

# ===== BOT SETTINGS =====
BOT_PREFIX = "?"
BOT_DESCRIPTION = "Yuno - A yandere-themed Discord bot"
BOT_CASE_INSENSITIVE = True

# ===== LEVELING SYSTEM =====
# XP rewards for activities
TEXT_XP_MIN = 15
TEXT_XP_MAX = 25
VOICE_XP_MIN = 18
VOICE_XP_MAX = 30

# Voice XP award interval (seconds)
VOICE_XP_INTERVAL = 60

# Level calculation formula parameters
# Formula: level = int((sqrt(1 + 8 * exp / LEVEL_DIVISOR) - 1) / 2)
LEVEL_DIVISOR = 50

# ===== SPAM FILTER =====
# Consecutive message limit in main chat before warning
SPAM_MESSAGE_LIMIT = 4

# Warning timeout (seconds) - how long warning messages stay visible
WARNING_TIMEOUT = 15

# Auto-ban message deletion period (seconds) - 86400 = 24 hours
BAN_DELETE_MESSAGES_SECONDS = 86400

# ===== DATABASE =====
DB_PATH = "Leveling/main.db"

# ===== LOGGING =====
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE = "yuno.log"
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# ===== EMBED COLORS (Decimal) =====
COLOR_PRIMARY = 0xff003d      # Yuno's signature red/pink
COLOR_SUCCESS = 0x00ff00      # Green for success
COLOR_ERROR = 0xff0000        # Red for errors
COLOR_INFO = 0x3498db         # Blue for info
COLOR_WARNING = 0xffaa00      # Orange for warnings

# ===== TIMEOUTS (seconds) =====
INTERACTIVE_COMMAND_TIMEOUT = 60     # For commands that wait for user input
TERMINAL_SESSION_TIMEOUT = 300       # For interactive Python shell (5 min)

# ===== DISCORD REGEX PATTERNS =====
# These are compiled in the spamfilter cog, don't modify unless you know regex
INVITE_PATTERN = r"(discord\.(gg|io|me|li)|discordapp\.com/invite)/[a-zA-Z0-9]+"
LINK_PATTERN = r"(https?://|www\.)[a-zA-Z0-9\-]+\.[a-zA-Z0-9\-\._~:\/\?#\[\]@!\$&'\(\)\*\+,;=%]+"

# ===== FEATURE FLAGS =====
# Enable/disable features
ENABLE_SPAM_FILTER = True
ENABLE_LEVELING = True
ENABLE_WELCOME = True
ENABLE_TERMINAL = True  # Set to False to disable terminal access in production
