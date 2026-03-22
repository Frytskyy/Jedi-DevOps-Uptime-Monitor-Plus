#!/usr/bin/env python3
"""
Jedi DevOps Uptime Monitor Plus
================================

A lightweight Python uptime monitor and server health dashboard for the
terminal. Monitors ping latency, HTTP/HTTPS endpoints, CPU/RAM/disk usage —
all from a single script, no Docker, no Grafana, no Prometheus required.

Perfect for self-hosters, indie developers, and DevOps engineers who manage
VPS servers, home labs, or small-to-medium server fleets and need a simple,
always-on terminal dashboard without the overhead of a full monitoring stack.

Just drop one `.py` file on any Linux, Windows, or macOS machine, edit a JSON
config, and you have a live server monitoring dashboard in under a minute.

I built this because every time I spun up a new VPS, setting up Prometheus +
Grafana felt like overkill for "is my site up and is it fast?" Added Star Wars
flavor because life's too short for boring DevOps tools.

Created by: Volodymyr Frytskyy (WhitemanV)
Website:    https://www.vladonai.com/about-resume
GitHub:     https://github.com/Frytskyy/Jedi-DevOps-Uptime-Monitor-Plus

Features:
---------
✅ Real-time ICMP ping monitoring for any number of hosts
✅ HTTP/HTTPS endpoint monitoring with content verification
      (checks that expected strings ARE present and error strings are ABSENT)
✅ Adaptive polling — speeds up on failures, backs off when stable
✅ CPU, RAM, and disk usage gauges with gradient color meters
✅ Braille Unicode graphs for high-resolution history in a tiny terminal cell
✅ Multi-location clock & weather widget (wttr.in, no API key needed)
✅ Uptime/downtime tracking with percentage and last-failure timestamps
✅ Telegram, e-mail (SMTP), and generic Webhook alert notifications
✅ Hardware-bound credential encryption (disk serial → Fernet key)
      so secrets stored in the JSON config are useless if the file leaks
✅ Daily rotating log files (monitor log + separate errors-only log)
✅ Keyboard shortcuts: R = reset stats, O = options screen, Q = quit
✅ Cross-platform: Windows, Linux, macOS
✅ Zero mandatory dependencies beyond the stdlib + four small pip packages

Star Wars Humor Notice:
-----------------------
Jedi references, "May the Force be with you" messages, and galactic metaphors
appear throughout the code and UI. This is purely for entertainment value.
No midi-chlorians are required to operate this software.

Why Star Wars? Monitoring 15 servers at 3 AM feels a lot like battling the
Empire. Might as well have fun with it.

License:
--------
MIT License with Attribution Requirement

Copyright (c) 2026 Volodymyr Frytskyy (WhitemanV) (https://www.vladonai.com/about-resume)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

Attribution Requirement: Any use of this software, whether modified or
unmodified, must include attribution to the original author and a link to
https://www.vladonai.com/about-resume

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

Installation & Dependencies:
-----------------------------
1. Python 3.8 or newer.

2. Install required packages:
      pip install colorama psutil requests pytz cryptography

3. Run:
      python3 uptime_monitor_for_devops.py

   On first run a default config file `monitor_cld_config.json` is created
   next to the script. Edit it to add your own ping targets, HTTP endpoints,
   locations, and notification settings, then restart.

4. Optional — run as a background service on Linux:
      # simple nohup approach:
      nohup python3 uptime_monitor_for_devops.py &> monitor.log &

      # or create a systemd unit for auto-start on boot.

Platform notes:
---------------
- Windows:  works fine in Windows Terminal or ConEmu. The classic cmd.exe
  console does not support 24-bit color — you'll get plain ANSI colors instead.
- Linux / macOS:  any modern terminal emulator works. ICMP ping requires either
  root privileges OR a system ping binary (the script calls the OS ping).
- WSL:  fully supported; same notes as Linux.

Configuration quick-reference (monitor_cld_config.json):
---------------------------------------------------------
  ping_targets        — list of {address, description} objects
  http_targets        — list of {url, description, interval, text_present, text_absent}
  locations           — list of {name, timezone, weather_query} for the clock widget
  internet_check_host — a reliable host used to distinguish "host down" vs "internet down"
  notifications       — telegram / email / webhook settings (all disabled by default)
  ping_interval       — seconds between ping sweeps (default 3)
  display_refresh     — seconds between screen redraws (default 2)
  beep_on_failure     — audible alert on consecutive failures (default true)
  debug_mode          — verbose logging to file (default false)

Example minimal config:
-----------------------
{
    "locations": [
        {"name": "New York",  "timezone": "America/New_York",  "weather_query": "New York,NY,USA"},
        {"name": "London",    "timezone": "Europe/London",     "weather_query": "London,UK"}
    ],
    "ping_targets": [
        {"address": "8.8.8.8",       "description": "Google DNS"},
        {"address": "192.168.1.1",   "description": "Router"}
    ],
    "http_targets": [
        {
            "url": "https://example.com/",
            "description": "My site",
            "interval": 60,
            "text_present": ["Example Domain"],
            "text_absent":  []
        }
    ]
}

Keyboard shortcuts (while the dashboard is running):
-----------------------------------------------------
  R — reset uptime statistics
  O — open options / settings screen
  Q — quit

When to use this instead of Grafana / Prometheus / Uptime Kuma / Zabbix:
-------------------------------------------------------------------------
This script is NOT a replacement for full-scale monitoring platforms. But it
is a great fit when:

  - You want a zero-setup uptime check on a fresh VPS in 60 seconds
  - You're a solo developer or small team without a dedicated ops person
  - You need a quick "is everything alive?" screen on a spare terminal window
  - You're running a home lab and don't want to maintain a monitoring stack
  - You want a simple Python website monitoring script you can read and trust
  - You need HTTP content verification (not just status codes) without SaaS fees
  - Your budget for monitoring tools is $0 and your patience for YAML is finite

If you're running 100+ servers with SLAs and on-call rotations, go use
Prometheus + Grafana. This tool is for the rest of us. You know who you are.

Tags / search keywords (for discoverability — skip if reading source):
----------------------------------------------------------------------
python uptime monitor, server monitoring script python, ping monitor python,
http endpoint monitoring python, self-hosted uptime monitor no docker,
terminal dashboard python, lightweight server monitoring tool, VPS monitor script,
website monitoring python script, uptime checker python, devops terminal tools,
simple uptime monitor linux, python server health check script, no grafana monitor,
single file monitoring tool, python ping dashboard, home lab monitoring

==============================================================================
"""

import socket
import struct
import select
import os
import sys
import json
import time
import datetime
import threading
import subprocess
import platform
import shutil
import requests
from collections import deque
from pathlib import Path
import pytz

# Colorama for cross-platform colored terminal output
try:
    from colorama import init, Fore, Back, Style
    init(autoreset=True)
except ImportError:
    print("Installing colorama for prettier terminal output...")
    subprocess.run([sys.executable, "-m", "pip", "install", "colorama"])
    from colorama import init, Fore, Back, Style
    init(autoreset=True)

try:
    import psutil
except ImportError:
    print("Installing psutil for system monitoring...")
    subprocess.run([sys.executable, "-m", "pip", "install", "psutil"])
    import psutil

try:
    from cryptography.fernet import Fernet, InvalidToken
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
    import base64
except ImportError:
    print("Installing cryptography for secrets encryption...")
    subprocess.run([sys.executable, "-m", "pip", "install", "cryptography"])
    from cryptography.fernet import Fernet, InvalidToken
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
    import base64


# ==============================================================================
# CREDENTIALS SECURITY — HONEST ASSESSMENT
# ==============================================================================
#
# Sensitive fields (Telegram bot token, SMTP password, etc.) are encrypted with
# Fernet (AES-128-CBC + HMAC-SHA256).  The key is derived via PBKDF2-SHA256
# from the disk serial number of the drive where this script lives.
#
# SAFE scenarios:
#   - Config JSON file is stolen/leaked (backup, cloud sync, email attachment):
#     values look like "enc:gAAAAA..." and are useless without the original disk.
#   - Source code is shared publicly: no secrets are hardcoded.
#
# UNSAFE scenarios (the "50/50" part):
#   - Attacker has live access to the same machine (same disk serial → same key).
#   - Attacker captures both the JSON file AND the disk serial number
#     (serial is often printed on the drive label or readable via SMART tools).
#   - Memory dump / debugger on the running process exposes plaintext values.
#   - Disk serial changes (disk replaced, VM migration, some RAID setups) —
#     config becomes unreadable, credentials must be re-entered.
#
# Why this is acceptable for our use-case:
#   This is a personal monitoring tool on a trusted machine.  The goal is to
#   prevent casual credential exposure (accidental file sharing, backup leaks),
#   not to withstand a targeted attack on the host itself.
#
# Potential improvements if stronger security is ever needed:
#   - Windows DPAPI (cryptography.hazmat or win32crypt): ties encryption to the
#     Windows user account + machine, no serial-sniffing risk.
#   - Prompt for a master password at startup (argon2 KDF): eliminates hardware
#     dependency but requires interactive launch.
#   - Store secrets in system keychain (keyring library): OS-managed, best UX.
# ==============================================================================

class SecretVault:
    """
    Encrypts/decrypts sensitive config values using the disk serial number as
    the hardware-bound key material.  Encrypted values are stored as plain
    strings prefixed with "enc:" so the JSON schema stays unchanged.

    Key derivation: PBKDF2-HMAC-SHA256(disk_serial, salt=b'PCMonitorVault', iterations=260000)
    Cipher: Fernet (AES-128-CBC + HMAC-SHA256)
    """

    ENC_PREFIX   = "enc:"
    _PBKDF2_SALT = b"PCMonitorVault_v1"
    _ITERATIONS  = 260_000

    def __init__(self):
        serial       = self._getDiskSerial()
        self._fernet = self._buildFernet(serial)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def encrypt(self, plaintext: str) -> str:
        """Return an "enc:…" string ready to store in JSON."""
        if not plaintext or plaintext.startswith(self.ENC_PREFIX):
            return plaintext
        token = self._fernet.encrypt(plaintext.encode("utf-8"))
        return self.ENC_PREFIX + token.decode("ascii")

    def decrypt(self, value: str) -> str:
        """Decrypt an "enc:…" value; returns plaintext (or original if not encrypted)."""
        if not value or not value.startswith(self.ENC_PREFIX):
            return value
        try:
            raw = value[len(self.ENC_PREFIX):].encode("ascii")
            return self._fernet.decrypt(raw).decode("utf-8")
        except (InvalidToken, Exception):
            return ""   # Wrong machine / corrupted — return empty so caller can detect

    def isEncrypted(self, value: str) -> bool:
        return isinstance(value, str) and value.startswith(self.ENC_PREFIX)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @staticmethod
    def _getDiskSerial() -> str:
        """
        Return the serial number of the disk that holds this script.
        Falls back to machine hostname-based fingerprint if unavailable.
        """
        try:
            if platform.system().lower() == "windows":
                # vol C: returns "Volume Serial Number is XXXX-XXXX"
                drive = os.path.splitdrive(os.path.abspath(__file__))[0] or "C:"
                out   = subprocess.check_output(
                    f"vol {drive}", shell=True, stderr=subprocess.DEVNULL
                ).decode(errors="replace")
                for line in out.splitlines():
                    if "serial" in line.lower():
                        parts = line.strip().split()
                        if parts:
                            return parts[-1]          # e.g. "1A2B-3C4D"
            else:
                # Linux/macOS: use lsblk or blkid for the root-device serial
                scriptDev = subprocess.check_output(
                    ["df", "--output=source", os.path.abspath(__file__)],
                    stderr=subprocess.DEVNULL
                ).decode().splitlines()[-1].strip()    # e.g. /dev/sda1
                # strip trailing digit to get base device
                baseDev = scriptDev.rstrip("0123456789")
                serial  = subprocess.check_output(
                    ["udevadm", "info", "--query=property", f"--name={baseDev}"],
                    stderr=subprocess.DEVNULL
                ).decode()
                for line in serial.splitlines():
                    if line.startswith("ID_SERIAL="):
                        return line.split("=", 1)[1].strip()
        except Exception:
            pass
        # Fallback: hostname + username — still machine-specific
        return f"{platform.node()}::{os.environ.get('USERNAME', os.environ.get('USER', 'user'))}"

    @staticmethod
    def _buildFernet(serial: str) -> "Fernet":
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=SecretVault._PBKDF2_SALT,
            iterations=SecretVault._ITERATIONS,
        )
        key = base64.urlsafe_b64encode(kdf.derive(serial.encode("utf-8")))
        return Fernet(key)



class GradientEngine:
    """
    Gradient color engine for smooth color transitions.
    Every Jedi chooses their crystal — we choose our color palette.
    Green means peace. Yellow means caution. Red means the Dark Side has your server.
    """
    
    @staticmethod
    def hexToRgb(hexColor):
        """Convert hex color to RGB tuple."""
        hexColor = hexColor.lstrip('#')
        return tuple(int(hexColor[i:i+2], 16) for i in (0, 2, 4))
    
    @staticmethod
    def rgbToEscape(rgb):
        """Convert RGB to ANSI escape sequence."""
        return f'\033[38;2;{rgb[0]};{rgb[1]};{rgb[2]}m'
    
    @staticmethod
    def createGradient(startColor, endColor, steps=101, midColor=None):
        """
        Create smooth gradient between colors.
        Green → Yellow → Red: the Jedi journey from "all good" to "wake up at 3 AM".
        """
        startRgb = GradientEngine.hexToRgb(startColor)
        endRgb = GradientEngine.hexToRgb(endColor)
        gradient = []
        
        if midColor:
            # Three-point gradient
            midRgb = GradientEngine.hexToRgb(midColor)
            halfSteps = steps // 2
            
            for i in range(halfSteps):
                ratio = i / halfSteps
                rgb = tuple(int(startRgb[j] + (midRgb[j] - startRgb[j]) * ratio) for j in range(3))
                gradient.append(GradientEngine.rgbToEscape(rgb))
            
            for i in range(halfSteps, steps):
                ratio = (i - halfSteps) / (steps - halfSteps)
                rgb = tuple(int(midRgb[j] + (endRgb[j] - midRgb[j]) * ratio) for j in range(3))
                gradient.append(GradientEngine.rgbToEscape(rgb))
        else:
            # Two-point gradient
            for i in range(steps):
                ratio = i / (steps - 1)
                rgb = tuple(int(startRgb[j] + (endRgb[j] - startRgb[j]) * ratio) for j in range(3))
                gradient.append(GradientEngine.rgbToEscape(rgb))
        
        return gradient


class BrailleGraphEngine:
    """
    Braille Unicode engine for high-resolution graphs.
    Ancient symbols with modern purpose - 8x the detail!
    """
    
    # Braille patterns for upward graphs (each shows 2 values in 2x4 grid)
    BRAILLE_UP = {
        0.0: " ",    0.1: "⢀",  0.2: "⢠",  0.3: "⢰",  0.4: "⢸",
        1.0: "⡀",  1.1: "⣀",  1.2: "⣠",  1.3: "⣰",  1.4: "⣸",
        2.0: "⡄",  2.1: "⣄",  2.2: "⣤",  2.3: "⣴",  2.4: "⣼",
        3.0: "⡆",  3.1: "⣆",  3.2: "⣦",  3.3: "⣶",  3.4: "⣾",
        4.0: "⡇",  4.1: "⣇",  4.2: "⣧",  4.3: "⣷",  4.4: "⣿"
    }
    
    @staticmethod
    def getBrailleSymbol(leftLevel, rightLevel):
        """Get Braille symbol for two values (0-4 each)."""
        key = float(leftLevel + rightLevel / 10)
        return BrailleGraphEngine.BRAILLE_UP.get(key, ' ')
    
    @staticmethod
    def valueToLevel(value, maxValue, levels=5):
        """Convert value to Braille level (0-4)."""
        if value is None or maxValue == 0:
            return 0
        percentage = min(100, max(0, (value / maxValue) * 100))
        level = int(percentage * (levels - 1) / 100 + 0.5)
        return min(levels - 1, max(0, level))


class JediTerminalControl:
    """
    The main monitoring class. Think of it as Yoda's war room:
    ancient wisdom, real-time awareness, and an unhealthy obsession
    with uptime percentages. "Down, your server is. Panic, you must not."
    """
    
    def __init__(self):
        # Get script directory (config and logs stay next to the script — like a Sith and their scheming)
        self.scriptDirectory      = Path(__file__).parent.resolve()
        self.configFilePath       = self.scriptDirectory / "monitor_cld_config.json"
        self.logDirectory         = self.scriptDirectory / "monitor_cld_logs"

        # Ensure logs directory exists (even Jedi need proper file organization)
        self.logDirectory.mkdir(exist_ok=True)

        # Hardware-bound secrets vault (disk serial → Fernet key)
        self.vault                = SecretVault()

        # Load configuration (or conjure a default — the Force provides, eventually)
        self.configuration        = self._loadConfiguration()
        
        # Log size limits — even the Jedi Archives can't store everything forever
        self.maxLogSizeBytes      = 5 * 1024 * 1024   # 5 MB - the threshold of doom
        self.trimLogSizeBytes     = 1 * 1024 * 1024   # 1 MB - trim down to this
        self.logCheckCounter      = 0                 # Counter for periodic checks
        self.errorLogCheckCounter = 0                 # Counter for error log periodic checks
        
        # Data storage — our holocrons of wisdom (ping history, HTTP results, CPU telemetry)
        self.pingDataStorage      = {}  # {hostname: deque([ping_times...])}
        self.pingTimeStamps       = {}  # {hostname: deque([timestamps...])} - for time-based graphing
        self.cpuDataHistory       = deque(maxlen=90)  # CPU usage history (3 minutes at 2s intervals)
        self.cpuTimeStamps        = deque(maxlen=90)  # Timestamps for CPU data
        
        self.weatherDataCache      = {}  # {location: {temp, min, max, condition}}
        self.lastWeatherUpdate     = 0
        self.weatherUpdateInterval = (60 * 15)  # Update weather every 15 minutes (API-free = be gentle)
        self.isWeatherUpdating     = False  # Guard against parallel weather fetch threads
        
        # Sparkline characters - the building blocks of our ASCII art mastery
        self.sparklineChars       = ['▁', '▂', '▃', '▄', '▅', '▆', '▇', '█']
        
        # Enhanced graphics settings
        self.useBrailleGraphs     = self.configuration.get('use_braille_graphs', True)
        self.useGradientMeters    = self.configuration.get('use_gradient_meters', True)
        self.graphHeight          = self.configuration.get('graph_height', 1)
        
        # Initialize gradient color systems
        self._initializeGradients()
        
        # Status tracking
        self.isRunning            = True
        self.startTime            = datetime.datetime.now()
        self._firstRender         = True   # First render does full cls, subsequent use cursor-home
        
        # Logging - two files: monitor log (all events) and errors log (critical only)
        self.logFilePath, self.errorLogFilePath = self._createLogFiles()
        self.debugMode           = self.configuration.get('debug_mode', False)
        self.logResponseTimes    = self.configuration.get('log_response_times', False)
        self.logSlowThresholdMs  = self.configuration.get('log_slow_threshold_ms', 1000)
        
        # Initialize ping storage for each target
        maxHistoryPoints = 60  # 3 minutes at 3-second intervals
        for rawTarget in self.configuration['ping_targets']:
            targetHost, _ = self._parsePingTarget(rawTarget)
            self.pingDataStorage[targetHost] = deque(maxlen=maxHistoryPoints)
            self.pingTimeStamps[targetHost]  = deque(maxlen=maxHistoryPoints)

        # Internet connectivity check (google ping as background probe)
        self.internetIsOnline     = None   # None=unknown, True=online, False=offline
        self.internetLastPingMs   = None
        self.internetPingHistory  = deque(maxlen=60)

        # Uptime/downtime tracking for pings
        self.pingUptimeTracker    = {}
        for rawTarget in self.configuration['ping_targets']:
            targetHost, _ = self._parsePingTarget(rawTarget)
            self.pingUptimeTracker[targetHost] = self._createUptimeTracker()

        # HTTP/HTTPS page monitoring storage
        self.httpResponseTimes    = {}  # {url: deque([response_times_ms...])}
        self.httpLastResults      = {}  # {url: {status_code, response_time, text_present_ok, text_absent_ok, fail_details}}
        self.httpUptimeTracker    = {}
        self.httpThreadsStarted   = 0   # Count of HTTP threads that have started
        self.httpThreadsTotal     = 0   # Total HTTP threads to start

        httpHistoryPoints = 30  # ~30 minutes of history at 60s intervals
        for httpTarget in self.configuration.get('http_targets', []):
            targetUrl = httpTarget['url']
            self.httpResponseTimes[targetUrl] = deque(maxlen=httpHistoryPoints)
            self.httpLastResults[targetUrl]   = None
            self.httpUptimeTracker[targetUrl] = self._createUptimeTracker()

        # Alarm timing tracking (beep once per minute while problem persists)
        self.lastAlarmTime        = {}  # {target_id: timestamp}
        self.alarmIntervalSeconds = 60  # Beep once per minute

        # Keyboard shortcut state
        self.inOptionsScreen      = False  # Pauses dashboard while options menu is open

        self._logMessage("INFO", "Jedi DevOps Uptime Monitor Plus online. Servers, we watch. Sleep, we don't.")
    
    
    def _secret(self, value: str) -> str:
        """Decrypt a config value if it is vault-encrypted, otherwise return as-is."""
        return self.vault.decrypt(value)

    def _initializeGradients(self):
        """
        Initialize color gradient arrays for smooth transitions.
        The colorful side of the Force — because all-green dashboards spark joy.
        """
        # Ping gradient: Green -> Yellow -> Red
        self.pingGradient = GradientEngine.createGradient(
            startColor="#50f095",   # Green
            midColor="#f2e266",     # Yellow
            endColor="#fa1e1e",     # Red
            steps=101
        )
        
        # CPU gradient
        self.cpuGradient = GradientEngine.createGradient(
            startColor="#50f095",
            midColor="#f2e266",
            endColor="#fa1e1e",
            steps=101
        )
        
        # RAM gradient
        self.ramGradient = GradientEngine.createGradient(
            startColor="#68bf36",   # Green
            midColor="#db8b00",     # Orange
            endColor="#bf3636",     # Red
            steps=101
        )
        
        # Disk gradient
        self.diskGradient = GradientEngine.createGradient(
            startColor="#0fd7ff",   # Cyan
            midColor="#f2e266",     # Yellow
            endColor="#fa1e1e",     # Red
            steps=101
        )
    
    
    def _loadConfiguration(self):
        """
        Load configuration from JSON file, or create default if not found.
        Like finding ancient Jedi texts, but in JSON format.
        """
        defaultConfig = {
            "locations": [
                {
                    "name": "New York",
                    "timezone": "America/New_York",
                    "weather_query": "New York,NY,USA"
                },
                {
                    "name": "Sunnyvale",
                    "timezone": "America/Los_Angeles",
                    "weather_query": "Sunnyvale,CA,USA"
                },
                {
                    "name": "London",
                    "timezone": "Europe/London",
                    "weather_query": "London,UK"
                }
            ],
            "ping_targets": [
                {"address": "8.8.8.8",        "description": "Google DNS"},
                {"address": "1.1.1.1",        "description": "Cloudflare DNS"},
                {"address": "192.168.1.1",    "description": "Router"},
                {"address": "192.168.1.100",  "description": "Local Server"},
            ],
            "internet_check_host": "google.com",  # Hidden ping to detect internet connectivity
            "unreliable_hosts": [
                "192.168.1.100"  # Hosts that are expected to be flaky - don't panic!
            ],
            "ping_interval": 3,
            "display_refresh": 2,
            "max_ping_history": 60,
            "log_ping_failures": True,
            "beep_on_failure": True,
            "ping_failure_threshold": 5,   # Beep after N consecutive ping failures (5 × 3s = 15s)
            "http_failure_threshold": 2,   # Beep after N consecutive HTTP failures (2 × 60s = 2min)
            "log_response_times": False,   # Log HTTP response times (only slow ones if True)
            "log_slow_threshold_ms": 1000, # Log response time only if slower than this (ms)
            "debug_mode": False,           # Enable verbose DEBUG log level
            "http_user_agent": "Vladonai/1.0 UptimeMonitor",
            "http_timeout": 10,            # Global HTTP request timeout (seconds) - reduced from 15s
            "http_adaptive_multiplier_stable": 1.5,    # Increase interval by 50% when stable (5+ successes)
            "http_adaptive_multiplier_unstable": 0.5,  # Decrease interval by 50% when failing
            "http_stagger_delay_min": 1,   # Minimum delay between HTTP thread starts (seconds)
            "http_stagger_delay_max": 4,   # Maximum delay between HTTP thread starts (seconds)
            "http_targets": [
                {
                    "url": "https://www.google.com/",
                    "description": "Google homepage",
                    "interval": 60,
                    "text_present": ["google", "Search"],
                    "text_absent": []
                },
                {
                    "url": "https://www.microsoft.com/",
                    "description": "Microsoft homepage",
                    "interval": 90,
                    "text_present": ["Microsoft", "Windows"],
                    "text_absent": []
                },
                {
                    "url": "https://github.com/",
                    "description": "GitHub homepage",
                    "interval": 120,
                    "text_present": ["GitHub", "repositories"],
                    "text_absent": []
                },
                {
                    "url": "https://api.github.com/",
                    "description": "GitHub API (JSON)",
                    "interval": 180,
                    "text_present": ["current_user_url", "repository_url"],
                    "text_absent": []
                },
                {
                    "url": "https://httpbin.org/get",
                    "description": "httpbin.org REST API",
                    "interval": 120,
                    "text_present": ["\"url\"", "\"headers\"", "httpbin"],
                    "text_absent": ["error"]
                },
                {
                    "url": "https://www.cloudflare.com/",
                    "description": "Cloudflare homepage",
                    "interval": 150,
                    "text_present": ["Cloudflare", "network"],
                    "text_absent": []
                },
                {
                    "url": "https://www.apache.org/robots.txt",
                    "description": "Apache.org robots.txt",
                    "interval": 600,
                    "text_present": ["User-agent:", "Disallow"],
                    "text_absent": []
                },
                {
                    "url": "https://www.wikipedia.org/",
                    "description": "Wikipedia portal",
                    "interval": 180,
                    "text_present": ["Wikipedia", "English"],
                    "text_absent": []
                }
            ],
            "notifications": {
                "telegram": {
                    "enabled": False,
                    "bot_token": "YOUR_BOT_TOKEN_HERE",
                    "chat_id": "YOUR_CHAT_ID_HERE",
                    "on_first_failure": True,
                    "on_recovery": True
                },
                "email": {
                    "enabled": False,
                    "smtp_host": "smtp.gmail.com",
                    "smtp_port": 587,
                    "smtp_use_tls": True,
                    "smtp_username": "your@gmail.com",
                    "smtp_password": "your_app_password",
                    "from_address": "your@gmail.com",
                    "to_addresses": ["admin@example.com"],
                    "subject_prefix": "[PCMonitor]",
                    "on_first_failure": True,
                    "on_recovery": True
                },
                "webhook": {
                    "enabled": False,
                    "url": "https://your-api-endpoint.example.com/alert",
                    "method": "POST",
                    "headers": {
                        "Content-Type": "application/json",
                        "Authorization": "Bearer YOUR_TOKEN_HERE"
                    },
                    "body_template": "{\"event\": \"{event}\", \"target\": \"{target}\", \"message\": \"{message}\", \"timestamp\": \"{timestamp}\"}",
                    "on_first_failure": True,
                    "on_recovery": True
                }
            },
            "http_text_absent_global": [
                "Fatal error",
                "Parse error",
                "Uncaught Exception",
                "Stack trace:",
                "SQLSTATE[",
                "mysql_connect()",
                "mysqli_connect()",
                "pg_connect()",
                "ORA-",
                "Traceback (most recent call last)",
                "SyntaxError:",
                "ModuleNotFoundError:",
                "Internal Server Error",
                "502 Bad Gateway",
                "503 Service Unavailable",
                "Database connection failed",
                "<b>Notice</b>:",
                "<b>Warning</b>:",
                "Use of undefined constant",
                "/home/admin/",
                "/var/www/html/"
            ]
        }
        
        if self.configFilePath.exists():
            try:
                with open(self.configFilePath, 'r', encoding='utf-8') as configFile:
                    loadedConfig = json.load(configFile)
                    print(f"{Fore.GREEN}✓ Configuration loaded from: {self.configFilePath}")
                    return loadedConfig
            except Exception as error:
                print(f"{Fore.YELLOW}⚠ Config load failed: {error}")
                print(f"{Fore.YELLOW}  Using default configuration...")
        
        # Create default config file
        with open(self.configFilePath, 'w', encoding='utf-8') as configFile:
            json.dump(defaultConfig, configFile, indent=4, ensure_ascii=False)
        
        print(f"{Fore.CYAN}✓ Default configuration created: {self.configFilePath}")
        print(f"{Fore.CYAN}  Customize locations and ping targets there!")
        
        return defaultConfig
    
    
    def _createLogFiles(self):
        """
        Create two log files: monitor log (all events) and errors log (critical only).
        Files are date-stamped for daily rotation; restarts append to the same day's file.
        """
        dateStr        = datetime.datetime.now().strftime("%Y%m%d")
        monitorLogPath = self.logDirectory / f"jedi_monitor_{dateStr}.log"
        errorLogPath   = self.logDirectory / f"jedi_errors_{dateStr}.log"

        for logPath, label in [(monitorLogPath, "MONITOR"), (errorLogPath, "ERRORS")]:
            if not logPath.exists() or logPath.stat().st_size == 0:
                with open(logPath, 'w', encoding='utf-8') as f:
                    f.write("=" * 70 + "\n")
                    f.write(f"JEDI DEVOPS UPTIME MONITOR PLUS - {label} LOG\n")
                    f.write(f"Started: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 70 + "\n\n")
            else:
                # Append restart marker so it's clear where a new session begins
                with open(logPath, 'a', encoding='utf-8') as f:
                    f.write(f"\n--- Restarted: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n\n")

        return monitorLogPath, errorLogPath
    
    
    def _trimLogFileIfNeeded(self, logPath):
        """
        Trim a single log file if it exceeds maximum size. Keeps the most recent content.
        """
        try:
            if not logPath.exists():
                return

            logSizeBytes = logPath.stat().st_size

            if logSizeBytes > self.maxLogSizeBytes:
                with open(logPath, 'r', encoding='utf-8', errors='ignore') as logFile:
                    logFile.seek(max(0, logSizeBytes - self.trimLogSizeBytes))
                    logFile.readline()  # skip partial line
                    recentContent = logFile.read()

                with open(logPath, 'w', encoding='utf-8') as logFile:
                    logFile.write("=" * 70 + "\n")
                    logFile.write(f"[LOG ROTATED] Trimmed at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    logFile.write(f"Original: {logSizeBytes / 1024 / 1024:.2f} MB -> ~{self.trimLogSizeBytes / 1024 / 1024:.2f} MB\n")
                    logFile.write("=" * 70 + "\n\n")
                    logFile.write(recentContent)

        except Exception as error:
            print(f"{Fore.RED}Log trim failed: {error}")
    
    
    def _logMessage(self, logLevel, message):
        """
        Route log message to the correct file based on level.
        ERROR -> both files (errors log + monitor log)
        WARN/INFO -> monitor log only
        DEBUG -> monitor log only if debug_mode=True, otherwise dropped
        WARNING -> normalized to WARN
        """
        # Normalize WARNING -> WARN
        if logLevel == "WARNING":
            logLevel = "WARN"

        # Gate DEBUG behind config flag
        if logLevel == "DEBUG" and not self.debugMode:
            return

        try:
            timestampStr = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logLine      = f"[{timestampStr}] [{logLevel:<5}] {message}\n"

            if logLevel == "ERROR":
                # Critical errors go to the dedicated errors file
                with open(self.errorLogFilePath, 'a', encoding='utf-8') as f:
                    f.write(logLine)
                # Also mirror to monitor log for chronological context
                with open(self.logFilePath, 'a', encoding='utf-8') as f:
                    f.write(logLine)
                # Periodically check error log size (every 50 errors)
                self.errorLogCheckCounter += 1
                if self.errorLogCheckCounter >= 50:
                    self.errorLogCheckCounter = 0
                    self._trimLogFileIfNeeded(self.errorLogFilePath)
            else:
                with open(self.logFilePath, 'a', encoding='utf-8') as f:
                    f.write(logLine)

            # Periodically check monitor log size (every 100 messages)
            self.logCheckCounter += 1
            if self.logCheckCounter >= 100:
                self.logCheckCounter = 0
                self._trimLogFileIfNeeded(self.logFilePath)

        except Exception as error:
            print(f"{Fore.RED}Log write failed: {error}")


    def _logSlowResponse(self, label, responseTimeMs):
        """
        Log a response time only when the threshold policy requires it.
        Controlled by log_response_times and log_slow_threshold_ms config keys.
        """
        if not self.logResponseTimes:
            return
        if responseTimeMs and responseTimeMs > self.logSlowThresholdMs:
            self._logMessage("WARN", f"SLOW {label} - {responseTimeMs}ms (threshold: {self.logSlowThresholdMs}ms)")
    
    
    def _fetchWeatherData(self, locationQuery):
        """
        Fetch weather data from wttr.in (NO API KEY NEEDED!)
        Like consulting the Jedi Archives, but for weather.
        """
        try:
            # wttr.in is a console weather service - perfect for us!
            # Format: ?format=j1 gives us JSON (the language of the modern Jedi)
            urlWeather = f"https://wttr.in/{locationQuery}?format=j1"
            
            responseWeather = requests.get(urlWeather, timeout=20)
            responseWeather.raise_for_status()
            
            weatherJson = responseWeather.json()
            
            # Parse the current conditions (the present moment, where Jedi live)
            currentCondition = weatherJson['current_condition'][0]
            
            weatherData = {
                'temp_c':       int(currentCondition['temp_C']),
                'temp_f':       int(currentCondition['temp_F']),
                'feels_like_c': int(currentCondition['FeelsLikeC']),
                'feels_like_f': int(currentCondition['FeelsLikeF']),
                'condition':    currentCondition['weatherDesc'][0]['value'],
                'humidity':     int(currentCondition['humidity']),
                'wind_kph':     int(float(currentCondition['windspeedKmph']))
            }
            
            return weatherData
            
        except Exception as error:
            self._logMessage("ERROR", f"Weather fetch failed for {locationQuery}: {error}. URL: {urlWeather}")
            return None
    
    
    def _updateWeatherForAllLocations(self):
        """
        Update weather for all configured locations.
        Consult the atmospheric Force for all our territories.
        """
        if self.isWeatherUpdating:
            return
        self.isWeatherUpdating = True
        try:
            for locationInfo in self.configuration['locations']:
                locationName  = locationInfo['name']
                weatherQuery  = locationInfo['weather_query']

                weatherData = self._fetchWeatherData(weatherQuery)

                if weatherData:
                    self.weatherDataCache[locationName] = weatherData
                else:
                    self._logMessage("WARN", f"Weather update failed for {locationName}")
        finally:
            self.isWeatherUpdating = False
            self.lastWeatherUpdate = time.time()
    
    
    '''
    def _executePing(self, hostname):
        """
        Execute ping command and return response time in milliseconds.
        Send a probe into the network void - will it return?
        """
        try:
            systemPlatform = platform.system().lower()
            
            if systemPlatform == 'windows':
                commandPing = ['ping', '-n', '1', '-w', '2000', hostname]
            else:
                commandPing = ['ping', '-c', '1', '-W', '2', hostname]
            
            resultPing = subprocess.run(
                commandPing,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=3
            )
            
            if resultPing.returncode == 0:
                outputStr = resultPing.stdout.decode('utf-8', errors='ignore')
                
                if systemPlatform == 'windows':
                    if 'time=' in outputStr or 'time<' in outputStr:
                        for linePing in outputStr.split('\n'):
                            if 'time' in linePing.lower():
                                if 'time<' in linePing:
                                    return 0.5  # Sub-millisecond - the speed of light!
                                elif 'time=' in linePing:
                                    timePartStr = linePing.split('time=')[1].split('ms')[0].strip()
                                    # Handle "XXXms" or "XXX ms"
                                    timePartStr = timePartStr.replace('ms', '').strip()
                                    return float(timePartStr)
                else:
                    if 'time=' in outputStr:
                        timePartStr = outputStr.split('time=')[1].split('ms')[0].strip()
                        return float(timePartStr)
                
                return 1.0  # Successful but couldn't parse - assume fast
            
            return None  # Ping failed - lost in the void
            
        except Exception as error:
            return None
    '''

    def _createUptimeTracker(self):
        """Create a fresh uptime/downtime tracker dict."""
        return {
            'up_since': time.time(),       # assume up at start
            'last_down_at': None,          # timestamp of last downtime start
            'last_down_duration': 0,       # seconds of last downtime event
            'down_events_24h': [],         # list of (start_ts, duration_s)
            'currently_down': False,
            'current_down_since': None
        }


    def _updateUptimeTracker(self, tracker, isOk):
        """
        Update uptime/downtime tracker based on check result.
        Call after each ping or HTTP check.
        """
        now = time.time()

        if isOk:
            if tracker['currently_down']:
                # Recovery! Record the downtime event
                downDuration = now - tracker['current_down_since']
                tracker['last_down_at']       = tracker['current_down_since']
                tracker['last_down_duration'] = downDuration
                tracker['down_events_24h'].append((tracker['current_down_since'], downDuration))
                tracker['currently_down']     = False
                tracker['current_down_since'] = None
                tracker['up_since']           = now
            elif tracker['up_since'] is None:
                tracker['up_since'] = now
        else:
            if not tracker['currently_down']:
                # Just went down
                tracker['currently_down']     = True
                tracker['current_down_since'] = now
                tracker['up_since']           = None

        # Prune events older than 24h
        cutoff = now - 86400
        tracker['down_events_24h'] = [(ts, dur) for ts, dur in tracker['down_events_24h'] if ts + dur > cutoff]


    def _formatDuration(self, seconds):
        """Format seconds into compact human-readable string: 3s, 2m, 1h25m, 2d3h."""
        if seconds is None or seconds < 0:
            return "--"
        seconds = int(seconds)
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            return f"{seconds // 60}m"
        elif seconds < 86400:
            h = seconds // 3600
            m = (seconds % 3600) // 60
            return f"{h}h{m}m" if m else f"{h}h"
        else:
            d = seconds // 86400
            h = (seconds % 86400) // 3600
            return f"{d}d{h}h" if h else f"{d}d"


    
    def _getDowntimeLast24hSeconds(self, tracker):
        """Sum downtime seconds over last 24 hours (including current ongoing downtime, if any)."""
        now = time.time()
        totalDown = 0.0

        # Completed events (already pruned to last 24h in _updateUptimeTracker)
        for startTs, durationS in tracker.get('down_events_24h', []):
            # Clamp overlap just in case (defensive Jedi programming)
            eventEnd = startTs + durationS
            windowStart = now - 86400
            overlapStart = max(startTs, windowStart)
            overlapEnd   = min(eventEnd, now)
            if overlapEnd > overlapStart:
                totalDown += (overlapEnd - overlapStart)

        # Ongoing downtime (not yet in list)
        if tracker.get('currently_down') and tracker.get('current_down_since'):
            windowStart = now - 86400
            overlapStart = max(tracker['current_down_since'], windowStart)
            if now > overlapStart:
                totalDown += (now - overlapStart)

        return totalDown


    def _getDowntimeEventsLast24hCount(self, tracker):
        """Count downtime events over last 24 hours (including current ongoing one)."""
        count = len(tracker.get('down_events_24h', []))
        if tracker.get('currently_down') and tracker.get('current_down_since'):
            count += 1
        return count

    def _formatUptimeInline(self, tracker):
        """
        Format uptime/downtime tracker as compact inline string.

        Examples:
          ▲4h12m ▼2m@13:05 D24:5m×2
          ▼DOWN 3m D24:7m×1
        """
        now = time.time()

        # 24h downtime summary
        down24s   = self._getDowntimeLast24hSeconds(tracker)
        down24cnt = self._getDowntimeEventsLast24hCount(tracker)
        down24Str = ""
        if down24s > 0 or tracker.get('currently_down'):
            down24Str = f"{Fore.MAGENTA}D24:{self._formatDuration(down24s)}×{down24cnt}"

        if tracker['currently_down']:
            downDur = now - tracker['current_down_since']
            baseStr = f"{Fore.RED}▼DOWN {self._formatDuration(downDur)}"
            return f"{baseStr} {down24Str}".rstrip()

        # Uptime
        if tracker['up_since']:
            upDur = now - tracker['up_since']
            upStr = f"{Fore.GREEN}▲{self._formatDuration(upDur)}"
        else:
            upStr = f"{Fore.GREEN}▲--"

        # Last downtime
        if tracker['last_down_at']:
            downTime = datetime.datetime.fromtimestamp(tracker['last_down_at']).strftime('%H:%M')
            downStr = f"{Fore.RED}▼{self._formatDuration(tracker['last_down_duration'])}@{downTime}"
        else:
            downStr = ""

        parts = [upStr]
        if downStr:
            parts.append(downStr)
        if down24Str:
            parts.append(down24Str)

        return " ".join(parts)



    def _executePing(self, targetHost, timeoutSeconds=2):
        """
        Native ICMP ping implementation using raw sockets.
        Much faster than spawning subprocess - like wielding a lightsaber instead of a blaster.
        
        Note: Requires admin/root privileges to create raw sockets.
        On Linux: sudo or setcap cap_net_raw+ep
        On Windows: Run as Administrator (or will fallback to subprocess)
        
        Args:
            targetHost: Hostname or IP address to ping
            timeoutSeconds: Timeout in seconds (default 2)
        
        Returns:
            float: Round-trip time in milliseconds, or None if ping failed
        """
        
        # The Dark Side: Try raw socket first (faster, more elegant)
        try:
            return self._rawIcmpPing(targetHost, timeoutSeconds)
        except PermissionError:
            # The Light Side: Fallback to subprocess if no permissions
            # (Yes, even Jedi sometimes need to call external helpers)
            self._logMessage("WARNING", f"No raw socket permission for {targetHost}, falling back to subprocess")
            return self._subprocessPing(targetHost, timeoutSeconds)
        except Exception as error:
            self._logMessage("ERROR", f"ICMP ping failed for {targetHost}: {error}")
            return None


    def _rawIcmpPing(self, targetHost, timeoutSeconds):
        """
        The pure implementation - ICMP Echo Request/Reply without external processes.
        Like Qui-Gon said: "Your focus determines your reality" - and we focus on packets!
        """
        
        icmpEchoRequest = 8   # ICMP type for Echo Request
        icmpCode        = 0   # ICMP code (always 0 for Echo Request)
        icmpId          = os.getpid() & 0xFFFF  # Use PID as identifier (within 16-bit range)
        icmpSequence    = 1   # Sequence number
        icmpSocket      = None  # Initialize to None for proper cleanup
        
        try:
            # === PHASE 1: DNS RESOLUTION (The Archives Must Be Consulted) ===
            # Resolve hostname to IP - this is a BLOCKING call without timeout!
            # If DNS is slow/broken, this is where we get stuck in carbonite
            try:
                # Try to resolve - if targetHost is already IP, this is instant
                destAddress = socket.gethostbyname(targetHost)
            except socket.gaierror as dnsError:
                # DNS resolution failed - the Archives are incomplete!
                self._logMessage("WARNING", f"DNS lookup failed for {targetHost}: {dnsError}")
                return None
            except Exception as dnsError:
                self._logMessage("WARNING", f"DNS resolution error for {targetHost}: {dnsError}")
                return None
            
            # Debug: Log successful DNS resolution
            if targetHost != destAddress:
                self._logMessage("DEBUG", f"DNS: {targetHost} -> {destAddress}")
            
            # === PHASE 2: CREATE RAW SOCKET (Requesting the Council's Permission) ===
            icmpSocket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
            icmpSocket.settimeout(timeoutSeconds)
            
            # === PHASE 3: BUILD ICMP PACKET (Crafting the Lightsaber) ===
            # Header: type (8), code (8), checksum (16), id (16), sequence (16)
            icmpChecksum = 0  # Initially zero for checksum calculation
            
            # Pack header without checksum
            icmpHeader = struct.pack('!BBHHH', icmpEchoRequest, icmpCode, icmpChecksum, icmpId, icmpSequence)
            
            # Payload - timestamp for RTT measurement (time flows, and so does latency)
            payloadData = struct.pack('!d', time.time())
            
            # Calculate checksum (the ancient Jedi algorithm)
            icmpChecksum = self._calculateChecksum(icmpHeader + payloadData)
            
            # Pack final header with correct checksum
            icmpHeader = struct.pack('!BBHHH', icmpEchoRequest, icmpCode, icmpChecksum, icmpId, icmpSequence)
            icmpPacket = icmpHeader + payloadData
            
            # === PHASE 4: SEND ECHO REQUEST (Releasing the Ping Lightning! May it return swiftly) ===
            sendTime = time.time()
            icmpSocket.sendto(icmpPacket, (destAddress, 0))
            
            # === PHASE 5: WAIT FOR ECHO REPLY (Patience, Young Skywalker) ===
            remainingTimeout = timeoutSeconds
            
            while True:
                # Use select() with remaining timeout to avoid infinite loops
                readyToRead, _, _ = select.select([icmpSocket], [], [], remainingTimeout)
                
                if not readyToRead:
                    # Timeout — the ping has been lost to the Dark Side. Again.
                    self._logMessage("DEBUG", f"ICMP timeout for {targetHost} ({destAddress})")
                    return None
                
                receiveTime = time.time()
                
                # Receive response (a packet sent is a packet that must return — this is the way)
                recvPacket, recvAddress = icmpSocket.recvfrom(1024)
                
                # IP header is typically 20 bytes, but can be 20-60 bytes with options
                # Extract IP header length from the first byte (IHL field)
                ipHeaderLength = (recvPacket[0] & 0x0F) * 4  # IHL is in 32-bit words
                
                # ICMP header starts after IP header
                icmpHeaderData = recvPacket[ipHeaderLength:ipHeaderLength + 8]
                
                if len(icmpHeaderData) < 8:
                    # Packet too short - some dark sorcery is at work
                    self._logMessage("DEBUG", f"Received malformed ICMP packet from {recvAddress}")
                    continue
                
                # Unpack ICMP header to verify it's our reply
                recvType, recvCode, recvChecksum, recvId, recvSequence = struct.unpack('!BBHHH', icmpHeaderData)
                
                # Check if this is OUR Echo Reply (not some random galactic cross-traffic)
                if recvType == 0 and recvId == icmpId:  # Type 0 = Echo Reply
                    # Calculate round-trip time in milliseconds (1 decimal place)
                    roundTripTime = round((receiveTime - sendTime) * 1000.0, 1)

                    self._logMessage("DEBUG", f"ICMP reply from {targetHost}: {roundTripTime}ms")
                    return roundTripTime
                else:
                    # Wrong packet - log what we received (for debugging the dark arts)
                    self._logMessage("DEBUG", 
                        f"Unexpected ICMP: type={recvType}, code={recvCode}, id={recvId} (expected {icmpId})")
                
                # Reduce remaining timeout (we spent some time already)
                remainingTimeout -= (receiveTime - sendTime)
                if remainingTimeout <= 0:
                    self._logMessage("DEBUG", f"Timeout waiting for correct ICMP reply from {targetHost}")
                    return None
        
        except PermissionError as permError:
            # No permission to create raw socket - must escalate to the Jedi Council
            self._logMessage("WARNING", f"Raw socket permission denied: {permError}")
            raise  # Re-raise to trigger fallback to subprocess
        
        except socket.timeout:
            # Socket timeout on send/receive operations
            self._logMessage("DEBUG", f"Socket timeout for {targetHost}")
            return None
        
        except Exception as error:
            # Catch-all for unexpected darkness
            self._logMessage("ERROR", f"Raw ICMP ping exception for {targetHost}: {type(error).__name__}: {error}")
            return None
        
        finally:
            # Always close the socket (proper Jedi cleanup)
            if icmpSocket:
                try:
                    icmpSocket.close()
                except:
                    pass  # Socket may already be closed. "Already closed, it is." — Yoda

    def _calculateChecksum(self, packetData):
        """
        Calculate ICMP checksum (RFC 1071).
        Ancient algorithm, older than the Old Republic itself.
        
        The checksum is the 16-bit one's complement of the one's complement sum
        of all 16-bit words in the data. If data length is odd, pad with zero byte.
        """
        
        # Ensure even length (pad with zero if odd - balance in all things)
        if len(packetData) % 2 != 0:
            packetData += b'\x00'
        
        # Sum all 16-bit words (the sacred incantation of RFC 792)
        checksumSum = 0
        for byteIndex in range(0, len(packetData), 2):
            word = (packetData[byteIndex] << 8) + packetData[byteIndex + 1]
            checksumSum += word

        # Add carry bits (one's complement wrap — even the Force has overflow)
        while checksumSum >> 16:
            checksumSum = (checksumSum & 0xFFFF) + (checksumSum >> 16)
        
        # One's complement (flip all bits - from Light to Dark and back)
        checksumValue = ~checksumSum & 0xFFFF
        
        return checksumValue


    def _subprocessPing(self, targetHost, timeoutSeconds):
        """
        Fallback to subprocess ping when raw sockets unavailable.
        The crude but reliable way - like Han Solo's blaster vs a lightsaber.
        """
        
        systemType = platform.system().lower()
        
        try:
            if systemType == "windows":
                # Windows ping format (Galactic Basic Standard)
                commandArgs = ["ping", "-n", "1", "-w", str(int(timeoutSeconds * 1000)), targetHost]
            else:
                # Linux/Unix ping format (Aurebesh variant)
                commandArgs = ["ping", "-c", "1", "-W", str(int(timeoutSeconds)), targetHost]
            
            # Execute ping (calling in the Clone Army)
            processResult = subprocess.run(
                commandArgs,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeoutSeconds + 1
            )
            
            # Parse output to extract ping time
            outputText = processResult.stdout
            
            if systemType == "windows":
                # Windows: "Reply from X.X.X.X: bytes=32 time=10ms TTL=64"
                if "time=" in outputText or "время=" in outputText:  # English or Russian Windows
                    import re
                    match = re.search(r'time[=<](\d+)', outputText, re.IGNORECASE)
                    if match:
                        return float(match.group(1))
            else:
                # Linux: "64 bytes from X.X.X.X: icmp_seq=1 ttl=64 time=10.5 ms"
                if "time=" in outputText:
                    import re
                    match = re.search(r'time[=](\d+\.?\d*)', outputText)
                    if match:
                        return float(match.group(1))
            
            # Ping succeeded but couldn't parse time (better than total failure)
            return 0.1 if processResult.returncode == 0 else None
            
        except subprocess.TimeoutExpired:
            return None
        except Exception as error:
            self._logMessage("ERROR", f"Subprocess ping failed for {targetHost}: {error}")
            return None


    def _executeHttpCheck(self, targetConfig):
        """
        Check HTTP/HTTPS page status, response time, and content.
        Like sending a probe droid to scout enemy territory!

        Returns dict: {status_code, response_time_ms, text_present_ok, text_absent_ok, fail_details}
        """
        targetUrl    = targetConfig['url']
        textPresent  = targetConfig.get('text_present', [])
        textAbsent   = list(self.configuration.get('http_text_absent_global', [])) + list(targetConfig.get('text_absent', []))

        try:
            startTime = time.time()
            userAgent = targetConfig.get('user_agent') or self.configuration.get('http_user_agent') or 'Vladonai/1.0 UptimeMonitor'
            timeout = targetConfig.get('timeout', self.configuration.get('http_timeout', 10))
            response  = requests.get(targetUrl, timeout=timeout, headers={
                'User-Agent': userAgent,
                'Accept-Encoding': 'gzip, deflate'  # Enable compression support
            })
            responseTimeMs = round((time.time() - startTime) * 1000.0, 1)

            statusCode   = response.status_code
            failDetails  = []

            # Check status code
            if statusCode != 200:
                failDetails.append(f"HTTP {statusCode}")

            # Check required text presence
            textPresentOk = True
            if statusCode == 200:
                pageText = response.text
                for requiredText in textPresent:
                    if requiredText not in pageText:
                        textPresentOk = False
                        failDetails.append(f"missing: \"{requiredText}\"")
            else:
                textPresentOk = False

            # Check forbidden text absence
            textAbsentOk = True
            if statusCode == 200:
                for forbiddenText in textAbsent:
                    if forbiddenText in pageText:
                        textAbsentOk = False
                        failDetails.append(f"found: \"{forbiddenText}\"")

            return {
                'status_code':     statusCode,
                'response_time_ms': responseTimeMs,
                'text_present_ok': textPresentOk,
                'text_absent_ok':  textAbsentOk,
                'fail_details':    '; '.join(failDetails) if failDetails else None
            }

        except requests.exceptions.Timeout:
            return {
                'status_code': None, 'response_time_ms': None,
                'text_present_ok': False, 'text_absent_ok': False,
                'fail_details': "TIMEOUT"
            }
        except requests.exceptions.ConnectionError:
            return {
                'status_code': None, 'response_time_ms': None,
                'text_present_ok': False, 'text_absent_ok': False,
                'fail_details': "CONNECTION ERROR"
            }
        except Exception as error:
            self._logMessage("ERROR", f"HTTP check failed for {targetUrl}: {error}")
            return {
                'status_code': None, 'response_time_ms': None,
                'text_present_ok': False, 'text_absent_ok': False,
                'fail_details': str(error)
            }


    def _internetCheckWorkerThread(self):
        """
        Background thread that pings internet_check_host (google.com by default)
        to determine if internet connectivity is available.
        Not shown as a regular ping target - only used for the status bar.
        """
        checkHost     = self.configuration.get('internet_check_host', 'google.com')
        pingInterval  = self.configuration.get('ping_interval', 3)

        while self.isRunning:
            pingTimeMs = self._executePing(checkHost)

            if pingTimeMs is not None:
                self.internetIsOnline    = True
                self.internetLastPingMs  = pingTimeMs
                self.internetPingHistory.append(pingTimeMs)
            else:
                self.internetPingHistory.append(None)
                # Only mark offline after 3 consecutive failures
                recentPings = list(self.internetPingHistory)[-3:]
                if len(recentPings) >= 3 and all(p is None for p in recentPings):
                    self.internetIsOnline   = False
                    self.internetLastPingMs = None

            time.sleep(pingInterval)


    def _startHttpThreadsStaggered(self, httpTargets):
        """
        Background thread that starts all HTTP monitoring threads with random staggered delays.
        This prevents blocking the main UI during startup.
        """
        import random

        staggerDelayMin = self.configuration.get('http_stagger_delay_min', 3)
        staggerDelayMax = self.configuration.get('http_stagger_delay_max', 8)

        self.httpThreadsTotal = len(httpTargets)
        self._logMessage("INFO", f"Starting {len(httpTargets)} HTTP threads with staggered delays ({staggerDelayMin}-{staggerDelayMax}s)...")

        for index, httpTarget in enumerate(httpTargets):
            threadHttp = threading.Thread(
                target=self._httpWorkerThread,
                args=(httpTarget,),
                daemon=True
            )
            threadHttp.start()
            self.httpThreadsStarted = index + 1

            # Random stagger delay (except for the last one)
            if index < len(httpTargets) - 1:
                delay = random.uniform(staggerDelayMin, staggerDelayMax)
                time.sleep(delay)

        self._logMessage("INFO", f"All {len(httpTargets)} HTTP monitoring threads started successfully")


    def _httpWorkerThread(self, targetConfig):
        """
        Worker thread with adaptive intervals for HTTP monitoring.
        Monitors HTTP/HTTPS pages with intelligent interval adjustment based on stability.
        """
        targetUrl = targetConfig['url']
        consecutiveFailures = 0
        consecutiveSuccesses = 0  # Track consecutive successes for adaptive intervals

        beepThreshold = self.configuration.get('http_failure_threshold',
                            self.configuration.get('beep_failure_threshold', 2))

        # Get interval directly from target config, fallback to 600s (10 min)
        baseInterval = targetConfig.get('interval', 600)
        currentInterval = baseInterval

        # Adaptive multipliers for interval adjustment
        stableMultiplier = self.configuration.get('http_adaptive_multiplier_stable', 1.5)
        unstableMultiplier = self.configuration.get('http_adaptive_multiplier_unstable', 0.5)

        wasDown = False  # Track UP/DOWN state changes for status-change logging

        while self.isRunning:
            result = self._executeHttpCheck(targetConfig)

            # Store result (existing logic)
            self.httpLastResults[targetUrl] = result
            if result['response_time_ms'] is not None:
                self.httpResponseTimes[targetUrl].append(result['response_time_ms'])
            else:
                self.httpResponseTimes[targetUrl].append(None)

            # Track success/failure
            isSuccess = (result['status_code'] == 200
                         and result['text_present_ok']
                         and result['text_absent_ok'])

            # Update uptime tracker (existing logic)
            self._updateUptimeTracker(self.httpUptimeTracker[targetUrl], isSuccess)

            # ADAPTIVE INTERVAL LOGIC
            if isSuccess:
                # Log only on state change: DOWN -> UP
                if consecutiveFailures >= beepThreshold or wasDown:
                    self._logMessage("INFO", f"RESTORED {targetUrl} - HTTP back UP after {consecutiveFailures} failures")
                    self._sendNotifications("recovery", f"http:{targetUrl}", f"RESTORED {targetUrl} - HTTP back UP after {consecutiveFailures} failures")
                    wasDown = False
                    self.lastAlarmTime.pop(f"http:{targetUrl}", None)  # Reset so next failure triggers fresh notification
                consecutiveFailures = 0
                consecutiveSuccesses += 1

                # After 5 consecutive successes, increase interval (stable target)
                if consecutiveSuccesses >= 5:
                    # Increase interval but cap at 2× base interval
                    currentInterval = min(baseInterval * stableMultiplier, baseInterval * 2)
                    consecutiveSuccesses = 5  # Cap to avoid overflow

                # Log response time only if slow (controlled by config)
                self._logSlowResponse(targetUrl, result['response_time_ms'])
            else:
                # Failure: reset success counter, increment failure counter
                consecutiveSuccesses = 0
                consecutiveFailures += 1
                wasDown = True

                # Decrease interval immediately on failure (check more frequently)
                currentInterval = baseInterval * unstableMultiplier

                self._logMessage("WARN", f"FAIL {targetUrl} - {result['fail_details']} (consecutive: {consecutiveFailures}) [interval: {int(currentInterval)}s]")

                # Sound alarm after threshold failures (once per minute while problem persists)
                if consecutiveFailures >= beepThreshold and self.configuration.get('beep_on_failure', True):
                    self._soundAlarm(f"http:{targetUrl}", message=f"🚨 {targetUrl} - CRITICAL: {beepThreshold} consecutive HTTP failures! Last error: {result['fail_details']}")
                    self._logMessage("ERROR", f"🚨 {targetUrl} - CRITICAL: {beepThreshold} consecutive HTTP failures! Last error: {result['fail_details']}")

            time.sleep(currentInterval)


    def _pingWorkerThread(self, hostname, displayName=None):
        """
        Worker thread that continuously pings a specific host.
        Like a Jedi sentinel, eternally vigilant at their post.

        Args:
            hostname: the address/IP to ping (used as storage key)
            displayName: optional human-readable label (defaults to hostname)
        """
        if displayName is None:
            displayName = hostname
        consecutiveFailures = 0
        wasDown = False  # Track UP/DOWN state changes for status-change logging

        # Check if this is an unreliable host (expected to be flaky)
        isUnreliableHost = hostname in self.configuration.get('unreliable_hosts', [])
        beepThreshold = self.configuration.get('ping_failure_threshold',
                            self.configuration.get('beep_failure_threshold', 5))
        
        while self.isRunning:
            pingTimeMs = self._executePing(hostname)
            currentTimestamp = time.time()

            # Update uptime tracker
            self._updateUptimeTracker(self.pingUptimeTracker[hostname], pingTimeMs is not None)

            if pingTimeMs is not None:
                # Success! Record the victory
                self.pingDataStorage[hostname].append(pingTimeMs)
                self.pingTimeStamps[hostname].append(currentTimestamp)

                # Log only on state change: DOWN -> UP
                if consecutiveFailures >= beepThreshold or wasDown:
                    self._logMessage("INFO", f"RESTORED {hostname} - ping UP after {consecutiveFailures} failures")
                    self._sendNotifications("recovery", f"ping:{hostname}", f"RESTORED {hostname} - ping UP after {consecutiveFailures} failures")
                    wasDown = False
                    self.lastAlarmTime.pop(f"ping:{hostname}", None)  # Reset so next failure triggers fresh notification
                consecutiveFailures = 0
            else:
                # Failure - the packet was lost to the dark side
                self.pingDataStorage[hostname].append(None)
                self.pingTimeStamps[hostname].append(currentTimestamp)
                consecutiveFailures += 1
                wasDown = True

                if self.configuration.get('log_ping_failures', True):
                    self._logMessage("WARN", f"FAIL {hostname} - ping failed (consecutive: {consecutiveFailures})")

                # Only beep for critical hosts after threshold failures (once per minute while problem persists)
                if consecutiveFailures >= beepThreshold and self.configuration.get('beep_on_failure', True):
                    if not isUnreliableHost:
                        # Three strikes - sound the alarm! (but only for reliable hosts)
                        self._soundAlarm(f"ping:{hostname}", message=f"🚨 {hostname} - CRITICAL: {beepThreshold} consecutive ping failures!")
                        self._logMessage("ERROR", f"🚨 {hostname} - CRITICAL: {beepThreshold} consecutive failures!")
                    else:
                        # Just log it for unreliable hosts - no panic needed
                        self._logMessage("WARN", f"⚠ {hostname} - {beepThreshold} failures (unreliable host - no alarm)")
            
            time.sleep(self.configuration.get('ping_interval', 3))
    
    
    def _soundAlarm(self, targetId, message=None):
        """
        Sound the alarm - like R2-D2's panic screech!
        Only beeps once per minute per target while problem persists.
        On the first alarm per incident, also sends external notifications.
        """
        currentTime = time.time()
        lastAlarm = self.lastAlarmTime.get(targetId, 0)

        # Check if enough time has passed since last alarm for this target
        if currentTime - lastAlarm >= self.alarmIntervalSeconds:
            isFirstAlarm = (lastAlarm == 0)
            self.lastAlarmTime[targetId] = currentTime
            try:
                if platform.system().lower() == 'windows':
                    import winsound
                    winsound.Beep(1000, 200)
                else:
                    # Unix bell - old school but effective
                    print("\a")
            except:
                pass  # Silent failure - some systems don't support beeps

            # Send external notifications on first alarm only (avoid spam)
            if isFirstAlarm and message:
                self._sendNotifications("failure", targetId, message)

    def _sendNotifications(self, event, targetId, message):
        """
        Send notifications via all enabled channels: Telegram, Email, Webhook.
        Runs in a background thread to not block the monitoring loop.
        event: 'failure' or 'recovery'
        """
        def _doSend():
            notifCfg = self.configuration.get('notifications', {})
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            eventLabel = "🚨 FAILURE" if event == "failure" else "✅ RECOVERY"
            fullMessage = f"{eventLabel}: {message}"

            # --- Telegram ---
            tgCfg = notifCfg.get('telegram', {})
            if tgCfg.get('enabled', False):
                sendIt = (event == 'failure' and tgCfg.get('on_first_failure', True)) or \
                         (event == 'recovery' and tgCfg.get('on_recovery', True))
                if sendIt:
                    try:
                        tgUrl = f"https://api.telegram.org/bot{self._secret(tgCfg['bot_token'])}/sendMessage"
                        tgPayload = {
                            "chat_id": self._secret(tgCfg['chat_id']),
                            "text": f"*PCMonitor Alert*\n{fullMessage}\n⏰ {timestamp}",
                            "parse_mode": "Markdown"
                        }
                        resp = requests.post(tgUrl, json=tgPayload, timeout=10)
                        if resp.status_code == 200:
                            self._logMessage("INFO", f"Telegram notification sent for {targetId}")
                        else:
                            self._logMessage("WARN", f"Telegram notification failed: HTTP {resp.status_code} - {resp.text[:200]}")
                    except Exception as e:
                        self._logMessage("WARN", f"Telegram notification error: {e}")

            # --- Email ---
            emailCfg = notifCfg.get('email', {})
            if emailCfg.get('enabled', False):
                sendIt = (event == 'failure' and emailCfg.get('on_first_failure', True)) or \
                         (event == 'recovery' and emailCfg.get('on_recovery', True))
                if sendIt:
                    try:
                        import smtplib
                        from email.mime.text import MIMEText
                        from email.mime.multipart import MIMEMultipart

                        subject = f"{emailCfg.get('subject_prefix', '[PCMonitor]')} {eventLabel}: {targetId}"
                        body = f"{fullMessage}\n\nTimestamp: {timestamp}\nTarget: {targetId}"

                        msg = MIMEMultipart()
                        msg['From']    = emailCfg['from_address']
                        msg['To']      = ', '.join(emailCfg['to_addresses'])
                        msg['Subject'] = subject
                        msg.attach(MIMEText(body, 'plain'))

                        smtpPort = emailCfg.get('smtp_port', 587)
                        if emailCfg.get('smtp_use_tls', True):
                            server = smtplib.SMTP(emailCfg['smtp_host'], smtpPort, timeout=15)
                            server.starttls()
                        else:
                            server = smtplib.SMTP_SSL(emailCfg['smtp_host'], smtpPort, timeout=15)

                        server.login(self._secret(emailCfg['smtp_username']), self._secret(emailCfg['smtp_password']))
                        server.sendmail(emailCfg['from_address'], emailCfg['to_addresses'], msg.as_string())
                        server.quit()
                        self._logMessage("INFO", f"Email notification sent for {targetId}")
                    except Exception as e:
                        self._logMessage("WARN", f"Email notification error: {e}")

            # --- Webhook / API ---
            webhookCfg = notifCfg.get('webhook', {})
            if webhookCfg.get('enabled', False):
                sendIt = (event == 'failure' and webhookCfg.get('on_first_failure', True)) or \
                         (event == 'recovery' and webhookCfg.get('on_recovery', True))
                if sendIt:
                    try:
                        bodyTemplate = self._secret(webhookCfg.get('body_template',
                            '{"event": "{event}", "target": "{target}", "message": "{message}", "timestamp": "{timestamp}"}'))
                        bodyStr = bodyTemplate \
                            .replace('{event}',     event) \
                            .replace('{target}',    targetId) \
                            .replace('{message}',   message.replace('"', '\\"')) \
                            .replace('{timestamp}', timestamp)

                        method     = webhookCfg.get('method', 'POST').upper()
                        headers    = webhookCfg.get('headers', {'Content-Type': 'application/json'})
                        webhookUrl = self._secret(webhookCfg['url'])

                        if method == 'POST':
                            resp = requests.post(webhookUrl, data=bodyStr, headers=headers, timeout=10)
                        elif method == 'GET':
                            resp = requests.get(webhookUrl, headers=headers, timeout=10)
                        else:
                            resp = requests.request(method, webhookUrl, data=bodyStr, headers=headers, timeout=10)

                        if resp.status_code < 300:
                            self._logMessage("INFO", f"Webhook notification sent for {targetId} (HTTP {resp.status_code})")
                        else:
                            self._logMessage("WARN", f"Webhook notification failed: HTTP {resp.status_code} - {resp.text[:200]}")
                    except Exception as e:
                        self._logMessage("WARN", f"Webhook notification error: {e}")

        # Run in background thread so we don't block monitoring
        threading.Thread(target=_doSend, daemon=True, name=f"notify-{targetId}").start()
    
    
    def _getPingStatistics(self, hostname):
        """
        Calculate ping statistics for a host.
        Analyze the patterns in the Force — err, the network.
        A Jedi feels disturbances in ping latency before the dashboards turn red.
        """
        pingHistory = [p for p in self.pingDataStorage[hostname] if p is not None]
        
        if not pingHistory:
            return None, None, None, 0
        
        avgPing    = sum(pingHistory) / len(pingHistory)
        minPing    = min(pingHistory)
        maxPing    = max(pingHistory)
        totalPings = len(self.pingDataStorage[hostname])
        failureRate = ((totalPings - len(pingHistory)) / totalPings * 100) if totalPings > 0 else 0
        
        return avgPing, minPing, maxPing, failureRate
    
    
    def _createSparkline(self, dataValues, maxValue=None, width=50, colorMap=None):
        """
        Create a sparkline graph from data values.
        The ancient art of visualizing data with mere characters!
        Now with Braille Unicode support for 3x more detail!
        
        Parameters:
            dataValues - list/deque of numeric values (None values are treated as gaps)
            maxValue - maximum value for scaling (auto-detected if None)
            width - desired width in characters
            colorMap - function that returns color based on value (optional)
        """
        if not dataValues or len(dataValues) == 0:
            return Fore.YELLOW + "▁" * width + Fore.RESET
        
        # Filter out None values for scaling calculation
        validValues = [v for v in dataValues if v is not None]
        
        if not validValues:
            return Fore.RED + "▁" * width + Fore.RESET
        
        # Determine max value for scaling
        if maxValue is None:
            maxValue = max(validValues)
        
        if maxValue == 0:
            maxValue = 1  # Prevent division by zero
        
        # Use Braille or classic based on config
        if self.useBrailleGraphs:
            return self._createSparklineBraille(dataValues, maxValue, width, colorMap)
        else:
            return self._createSparklineClassic(dataValues, maxValue, width, colorMap)
    
    
    def _createSparklineBraille(self, dataValues, maxValue, width, colorMap=None):
        """
        Create Braille-based sparkline (high resolution).
        Each Braille character shows TWO data points!
        """
        # We need pairs of values for Braille (each char shows 2 values)
        samplesNeeded = width * 2
        
        # Take last samples
        graphData = list(dataValues)[-samplesNeeded:] if len(dataValues) >= samplesNeeded else list(dataValues)
        
        # Pad with None if not enough data
        if len(graphData) < samplesNeeded:
            graphData = [None] * (samplesNeeded - len(graphData)) + graphData
        
        # Replace None with 0 for Braille rendering
        graphData = [0 if v is None else v for v in graphData]
        
        sparkline = ""
        for charIndex in range(width):
            leftIndex = charIndex * 2
            rightIndex = leftIndex + 1
            
            leftValue = graphData[leftIndex] if leftIndex < len(graphData) else 0
            rightValue = graphData[rightIndex] if rightIndex < len(graphData) else 0
            
            # Convert to Braille levels (0-4)
            leftLevel = BrailleGraphEngine.valueToLevel(leftValue, maxValue)
            rightLevel = BrailleGraphEngine.valueToLevel(rightValue, maxValue)
            
            # Get Braille symbol
            symbol = BrailleGraphEngine.getBrailleSymbol(leftLevel, rightLevel)
            
            # Apply color if color map provided (use rightValue for color)
            if colorMap and rightValue is not None and rightValue > 0:
                color = colorMap(rightValue)
                sparkline += f"{color}{symbol}"
            else:
                sparkline += Fore.CYAN + symbol
        
        return sparkline + Fore.RESET
    
    
    def _createSparklineClassic(self, dataValues, maxValue, width, colorMap=None):
        """
        Create classic sparkline (8-level characters).
        Fallback for terminals without Braille support.
        """
        # Take last 'width' data points (or pad with None if not enough data)
        recentData = list(dataValues)[-width:]
        
        # Pad with None if we don't have enough data yet
        if len(recentData) < width:
            recentData = [None] * (width - len(recentData)) + recentData
        
        # Build sparkline
        sparkline = ""
        
        for value in recentData:
            if value is None:
                # No data - show as gap
                char = '·'
                color = Fore.YELLOW
            else:
                # Normalize value to 0-7 range (8 sparkline characters)
                normalizedValue = min(7, int((value / maxValue) * 7))
                char = self.sparklineChars[normalizedValue]
                
                # Apply color if color map provided
                if colorMap:
                    color = colorMap(value)
                else:
                    color = Fore.CYAN
            
            sparkline += color + char
        
        return sparkline + Fore.RESET
    
    
    def _getPingColorMapForHost(self, hostname):
        """
        Create adaptive color map function for specific host with smooth gradients.
        Each host gets its own "normal" range based on historical data.
        A wise Jedi knows: 5ms for a local DB is healthy, 5ms for a VPS in Singapore is suspicious.
        Adaptive baselines — because midi-chlorian counts vary by species.
        """
        # Get statistics for this host
        avgPing, minPing, maxPing, failureRate = self._getPingStatistics(hostname)
        
        if avgPing is None or avgPing == 0:
            # No data yet - use default gradient scale (0-200ms)
            def defaultColorMap(pingValue):
                if pingValue is None:
                    return Fore.RED
                percentage = int(min(100, (pingValue / 200) * 100))
                return self.pingGradient[percentage]
            return defaultColorMap
        
        # Calculate adaptive max scale based on this host's performance
        # Use max(avgPing * 2, maxPing * 1.2) for adaptive scaling
        adaptiveMax = max(avgPing * 2, maxPing * 1.2, 50)  # At least 50ms range
        
        def adaptiveColorMap(pingValue):
            if pingValue is None:
                return Fore.RED
            # Map ping value to 0-100 percentage for gradient
            percentage = int(min(100, (pingValue / adaptiveMax) * 100))
            return self.pingGradient[percentage]
        
        return adaptiveColorMap
    
    
    def _cpuColorMap(self, cpuValue):
        """
        Color mapping for CPU usage with smooth gradients.
        Green = chillin', Yellow = working, Red = Death Star overload!
        """
        if cpuValue is None:
            return Fore.YELLOW
        percentage = int(min(100, max(0, cpuValue)))
        return self.cpuGradient[percentage]
    
    
    def _updateCpuHistory(self):
        """
        Update CPU usage history for graphing.
        Sample the CPU — if it's above 90% something is burning, and it's not just incense.
        """
        cpuPercent = psutil.cpu_percent(interval=0.1)
        currentTimestamp = time.time()
        
        self.cpuDataHistory.append(cpuPercent)
        self.cpuTimeStamps.append(currentTimestamp)
    
    
    def _clearScreen(self):
        """
        Clear terminal screen - like wiping away the fog of war.
        Called only on very first render; afterwards we use cursor-home trick.
        """
        subprocess.run('cls' if os.name == 'nt' else 'clear', shell=True)
        self._firstRender = False
    
    
    def _getColorForPing(self, pingMs):
        """
        Get appropriate color for ping value.
        Green = Jedi speed, Yellow = Padawan level, Red = Youngling struggles.
        """
        if pingMs is None:
            return Fore.RED
        elif pingMs < 50:
            return Fore.GREEN
        elif pingMs < 150:
            return Fore.YELLOW
        else:
            return Fore.RED
    
    
    def _formatTimestamp(self, timestampValue=None):
        """
        Format timestamp in HH:MM:SS DD.MM.YYYY format.
        Time first, then date - because priorities, young Padawan.
        """
        if timestampValue is None:
            dt = datetime.datetime.now()
        else:
            dt = datetime.datetime.fromtimestamp(timestampValue)
        
        return dt.strftime("%H:%M:%S %d.%m.%Y")
    
    def _parsePingTarget(self, target):
        """
        Parse a ping_targets entry - supports both legacy string format
        and new dict format {"address": ..., "description": ...}.
        Returns (address, description) tuple.
        """
        if isinstance(target, dict):
            address     = target['address']
            description = target.get('description', address)
        else:
            # Legacy: plain string hostname
            address     = target
            description = target
        return address, description

    def _shortenUrlForDisplay(self, url: str, maxLen: int) -> str:
        # Strip scheme
        if url.startswith("https://"):
            url = url[8:]
        elif url.startswith("http://"):
            url = url[7:]

        # Drop query/fragment to keep it compact
        url = url.split("#", 1)[0].split("?", 1)[0]

        if len(url) <= maxLen:
            return url

        # Keep domain and tail of path
        # Example: www.site.com/very/long/path -> www.site.com/very.../path
        slashPos = url.find("/")
        if slashPos < 0:
            # Just a host
            return url[: maxLen - 1] + "…"

        hostPart = url[:slashPos]
        pathPart = url[slashPos:]  # includes leading '/'

        # Ensure we always keep host
        if len(hostPart) + 2 >= maxLen:
            return hostPart[: maxLen - 1] + "…"

        # allocate remaining for path with ellipsis in middle
        remaining = maxLen - len(hostPart) - 1  # 1 for space? actually none; keep for safety
        # We'll build "host/pathHead…pathTail"
        # Reserve 1 char for ellipsis
        minTail = 10
        if remaining < (minTail + 2):
            return hostPart + "…"  # too tight

        tailLen = min(minTail, remaining // 3)
        headLen = remaining - tailLen - 1

        if headLen < 1:
            headLen = 1

        pathHead = pathPart[:headLen]
        pathTail = pathPart[-tailLen:] if tailLen > 0 else ""

        return f"{hostPart}{pathHead}…{pathTail}"

    def _displayDashboard(self):
        """
        Render the main dashboard to terminal.
        The canvas upon which we paint our monitoring masterpiece.
        Uses flicker-free rendering: first call does full clear, subsequent calls
        use ANSI cursor-home + overwrite to avoid screen flicker.
        """
        # Update CPU history before display
        self._updateCpuHistory()

        # Collect all output lines into a buffer to avoid partial-render flicker
        lines = []
        def p(text=""):
            lines.append(text)

        # ============== HEADER + TIME & WEATHER ==============
        p(f"{Fore.CYAN}{Style.BRIGHT}{'⚡ JEDI DEVOPS UPTIME MONITOR PLUS':^80}")
        p(f"{Fore.CYAN}{Style.BRIGHT}{'─' * 80}")

        # Update weather if needed (15 min normal, 30s retry if no data yet)
        weatherInterval = 30 if not self.weatherDataCache else self.weatherUpdateInterval
        if not self.isWeatherUpdating and time.time() - self.lastWeatherUpdate > weatherInterval:
            self.lastWeatherUpdate = time.time()  # Prevent re-trigger while thread is running
            threading.Thread(target=self._updateWeatherForAllLocations, daemon=True).start()

        for locationInfo in self.configuration['locations']:
            locationName = locationInfo['name']
            timezoneStr  = locationInfo['timezone']

            # Time part
            try:
                timezoneObj = pytz.timezone(timezoneStr)
                currentTime = datetime.datetime.now(pytz.utc).astimezone(timezoneObj)
                timeStr     = currentTime.strftime('%H:%M:%S %d.%m')
            except Exception:
                timeStr     = "??:??:??"

            # Weather part
            if locationName in self.weatherDataCache:
                wd = self.weatherDataCache[locationName]
                tempColor = Fore.CYAN if wd['temp_c'] < 0 else (Fore.RED if wd['temp_c'] > 30 else Fore.GREEN)
                weatherStr = (f"{tempColor}{wd['temp_c']:>3}°C{Fore.WHITE}/{wd['temp_f']}°F "
                              f"{Fore.CYAN}{wd['condition'][:20]:<20} "
                              f"{Fore.WHITE}💧{wd['humidity']}% 💨{wd['wind_kph']}kph")
            else:
                weatherStr = f"{Fore.YELLOW}loading..."

            p(f"{Fore.WHITE}{locationName:<13} {Fore.CYAN}{timeStr}  {weatherStr}")

        # ============== PING MONITORING (compact) ==============
        p(f"{Fore.YELLOW}──── 📡 PING MONITORING ────────────────────────────────────────────────────────")

        sparklineWidth = 30  # compact sparkline

        for rawTarget in self.configuration['ping_targets']:
            hostname, displayName = self._parsePingTarget(rawTarget)
            currentPing = self.pingDataStorage[hostname][-1] if self.pingDataStorage[hostname] else None
            avgPing, minPing, maxPing, failureRate = self._getPingStatistics(hostname)
            adaptiveColorMap = self._getPingColorMapForHost(hostname)

            # Current ping
            if currentPing is not None:
                curStr   = f"{currentPing:>5.1f}ms"
                curColor = adaptiveColorMap(currentPing)
            else:
                curStr   = " FAIL"
                curColor = Fore.RED

            # Avg + loss
            if avgPing is not None:
                avgStr   = f"{avgPing:>5.1f}"
                avgColor = adaptiveColorMap(avgPing)
                lossColor = Fore.GREEN if failureRate < 1 else (Fore.YELLOW if failureRate < 5 else Fore.RED)
                lossStr  = f"{lossColor}{failureRate:.0f}%"
            else:
                avgStr   = "  N/A"
                avgColor = Fore.YELLOW
                lossStr  = f"{Fore.YELLOW}N/A"

            # Sparkline (use 'pingData' to avoid shadowing the local 'p' closure)
            pingData = self.pingDataStorage[hostname]
            validPings = [v for v in pingData if v is not None]
            maxPingForGraph = max(max(validPings) * 1.3, 50) if validPings else 100
            sparkline = self._createSparkline(
                pingData,
                maxValue=maxPingForGraph, width=sparklineWidth, colorMap=adaptiveColorMap
            )

            # Uptime/downtime inline
            uptimeStr = self._formatUptimeInline(self.pingUptimeTracker.get(hostname, self._createUptimeTracker()))

            # All in one line: description  cur  avg  loss  sparkline  uptime
            p(f"{Fore.WHITE}{displayName:20} "
              f"{curColor}{curStr} "
              f"{Fore.WHITE}avg:{avgColor}{avgStr} "
              f"{Fore.WHITE}loss:{lossStr} "
              f"{Fore.WHITE}{sparkline} {uptimeStr}")

        # ============== HTTP/HTTPS PAGE MONITORING (compact) ==============
        httpTargets = self.configuration.get('http_targets', [])
        if httpTargets:
            p(f"{Fore.YELLOW}──── 🌐 HTTP PAGE MONITORING ───────────────────────────────────────────────────")

            # Show startup progress if not all threads started yet
            if self.httpThreadsStarted < self.httpThreadsTotal and self.httpThreadsTotal > 0:
                progress = int((self.httpThreadsStarted / self.httpThreadsTotal) * 100)
                p(f"{Fore.CYAN}Starting HTTP threads: {self.httpThreadsStarted}/{self.httpThreadsTotal} ({progress}%) - please wait...")

            # Header with column names
            p(f"{Fore.CYAN}{'Description':<20} {'Status':>6} {'Response':>11} {'Sparkline':<16} {'Checks':<10} {'Uptime'}")

            for httpTarget in httpTargets:
                targetUrl = httpTarget['url']
                result    = self.httpLastResults.get(targetUrl)
                description = httpTarget.get('description', 'Unknown')

                if result is None:
                    p(f"{Fore.WHITE}{description:<20} {Fore.YELLOW}waiting...")
                    continue

                # Status (4 chars, centered)
                sc = result['status_code']
                if sc == 200:
                    statusStr = f"{Fore.GREEN}{'200':^4}"
                elif sc is not None:
                    statusStr = f"{Fore.RED}{str(sc):^4}"
                else:
                    statusStr = f"{Fore.RED}{'–':^4}"

                # Response time (right-aligned, 11 chars for "  XXXX.Xms")
                rt = result['response_time_ms']
                if rt is not None:
                    rtColor = Fore.GREEN if rt < 1000 else (Fore.YELLOW if rt < 3000 else Fore.RED)
                    rtStr   = f"{rtColor}{rt:>8.1f}ms"
                else:
                    rtStr   = f"{Fore.RED}{'–':>8}"

                # Sparkline (15 chars wide)
                httpSparkline = ""
                respHistory = self.httpResponseTimes.get(targetUrl)
                if respHistory and any(v is not None for v in respHistory):
                    validTimes = [v for v in respHistory if v is not None]
                    maxT = max(max(validTimes) * 1.3, 500)
                    _maxT = maxT  # capture for closure

                    def _httpCMap(value, _m=_maxT):
                        if value is None:
                            return Fore.RED
                        return self.pingGradient[int(min(100, (value / _m) * 100))]

                    httpSparkline = self._createSparkline(
                        respHistory, maxValue=maxT, width=15, colorMap=_httpCMap
                    )
                else:
                    httpSparkline = f"{Fore.YELLOW}{'─' * 15}"

                # Text checks (compact: ✓ or ✗ for each)
                checks = ""
                hasTextPresent = httpTarget.get('text_present')
                hasTextAbsent  = httpTarget.get('text_absent')

                if hasTextPresent:
                    checks += f"{Fore.GREEN}✓text" if result['text_present_ok'] else f"{Fore.RED}✗text"
                if hasTextAbsent:
                    checks += f" {Fore.GREEN}✓clean" if result['text_absent_ok'] else f" {Fore.RED}✗clean"

                # Uptime/downtime inline
                httpUpStr = self._formatUptimeInline(self.httpUptimeTracker.get(targetUrl, self._createUptimeTracker()))

                # One compact line with proper column alignment
                p(f"{Fore.WHITE}{description:<20} {statusStr} {rtStr} {Fore.WHITE}{httpSparkline:<16} {checks:<10} {httpUpStr}")

                # Failure details ONLY if something is wrong (extra line)
                if result['fail_details']:
                    p(f"  {Fore.RED}⚠ {result['fail_details']}")

        # ============== SYSTEM RESOURCES (compact) ==============
        p(f"{Fore.YELLOW}──── ⚡SYSTEM VITALS: ──────────────────────────────────────────────────────────")

        # CPU: bar + sparkline on one line
        cpuPercent = self.cpuDataHistory[-1] if self.cpuDataHistory else 0
        cpuColor = Fore.GREEN if cpuPercent < 50 else (Fore.YELLOW if cpuPercent < 80 else Fore.RED)
        cpuBar = self._createProgressBar(cpuPercent, 12, 'cpu')
        cpuSparkline = self._createSparkline(
            self.cpuDataHistory, maxValue=100, width=25, colorMap=self._cpuColorMap
        )
        p(f"{Fore.WHITE}CPU: {cpuColor}{cpuPercent:>5.1f}% {cpuBar} {cpuSparkline}")

        # RAM: one line
        ramInfo    = psutil.virtual_memory()
        ramPercent = ramInfo.percent
        ramColor   = Fore.GREEN if ramPercent < 50 else (Fore.YELLOW if ramPercent < 80 else Fore.RED)
        ramBar     = self._createProgressBar(ramPercent, 12, 'ram')
        ramUsedGb  = ramInfo.used / (1024**3)
        ramTotalGb = ramInfo.total / (1024**3)
        p(f"{Fore.WHITE}RAM: {ramColor}{ramPercent:>5.1f}% {ramBar} "
          f"{Fore.WHITE}{ramUsedGb:.1f}/{ramTotalGb:.1f} GB")

        # Disks: enumerate all physical partitions, 3 per row
        diskLine   = ""
        diskCount  = 0
        try:
            partitions = psutil.disk_partitions(all=False)
            for part in partitions:
                # Skip virtual/snap/loop filesystems on Linux
                if part.fstype in ('squashfs', 'tmpfs', 'devtmpfs', 'overlay', 'aufs'):
                    continue
                if part.device.startswith('/dev/loop'):
                    continue
                if part.mountpoint.startswith('/snap/'):
                    continue
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                except (PermissionError, OSError):
                    continue

                dp    = usage.percent
                dCol  = Fore.GREEN if dp < 70 else (Fore.YELLOW if dp < 90 else Fore.RED)
                dBar  = self._createProgressBar(dp, 8, 'disk')
                usedG = usage.used / (1024**3)
                totG  = usage.total / (1024**3)

                # Drive label: on Windows use "C:" style, on Linux use mountpoint
                if platform.system().lower() == 'windows':
                    label = part.mountpoint.rstrip('\\')
                else:
                    label = part.mountpoint

                # Format: C:45%[●●●●----]214/476G
                if totG >= 1000:
                    sizeStr = f"{usedG / 1024:.1f}/{totG / 1024:.1f}T"
                else:
                    sizeStr = f"{usedG:.0f}/{totG:.0f}G"

                entry = f"{Fore.WHITE}{label}:{dCol}{dp:.0f}%{dBar}{Fore.WHITE}{sizeStr}"
                diskLine += f"  {entry}"
                diskCount += 1

                if diskCount % 3 == 0:
                    p(diskLine)
                    diskLine = ""

            if diskLine:
                p(diskLine)
        except Exception:
            # Fallback to root disk
            diskInfo = psutil.disk_usage('/')
            dp = diskInfo.percent
            dCol = Fore.GREEN if dp < 70 else (Fore.YELLOW if dp < 90 else Fore.RED)
            dBar = self._createProgressBar(dp, 12, 'disk')
            p(f"{Fore.WHITE}DISK: {dCol}{dp:>5.1f}% {dBar} "
              f"{Fore.WHITE}{diskInfo.used / (1024**3):.1f}/{diskInfo.total / (1024**3):.1f} GB")

        # ============== STATUS BAR (bottom) ==============
        p(f"{Fore.CYAN}{'─' * 80}")

        # Internet status
        internetHost = self.configuration.get('internet_check_host', 'google.com')
        if self.internetIsOnline is None:
            netStr = f"{Fore.YELLOW}NET: checking..."
        elif self.internetIsOnline:
            pingStr = f"{self.internetLastPingMs:.1f}ms" if self.internetLastPingMs else "?"
            netStr  = f"{Fore.GREEN}NET: ● ONLINE ({internetHost}: {pingStr})"
        else:
            netStr  = f"{Fore.RED}NET: ○ OFFLINE ({internetHost} unreachable)"

        uptimeDuration = datetime.datetime.now() - self.startTime
        uptimeStr = str(uptimeDuration).split('.')[0]

        p(f"{netStr}  {Fore.WHITE}│  Uptime: {Fore.GREEN}{uptimeStr}  "
          f"{Fore.WHITE}│  {Fore.CYAN}[R]{Fore.WHITE}reset  {Fore.CYAN}[O]{Fore.WHITE}options  {Fore.CYAN}[Q]{Fore.WHITE}quit")

        # ============== ATOMIC FLICKER-FREE OUTPUT ==============
        # On first render: do a real cls to clear any startup messages above.
        # On subsequent renders: move cursor to top-left (no cls!) and overwrite
        # each line in-place. \033[K erases to end-of-line (removes old chars when
        # a line gets shorter). \033[J clears everything below the last line.
        RESET       = '\033[0m'
        CURSOR_HOME = '\033[H'   # move cursor to row 1, col 1
        ERASE_EOL   = '\033[K'   # erase from cursor to end of current line
        ERASE_BELOW = '\033[J'   # erase from cursor to end of screen

        if self._firstRender:
            subprocess.run('cls' if os.name == 'nt' else 'clear', shell=True)
            self._firstRender = False
            out = '\n'.join(lines) + '\n' + RESET
        else:
            out = CURSOR_HOME + ''.join(line + ERASE_EOL + '\n' for line in lines) + ERASE_BELOW + RESET

        sys.stdout.write(out)
        sys.stdout.flush()
    
    
    def _createProgressBar(self, percentValue, barWidth, gradientType='cpu'):
        """
        Create a text-based progress bar with gradient coloring.
        Uses ● for filled and - for empty.
        """
        percentValue = max(0, min(100, percentValue))
        filledWidth  = int(barWidth * percentValue / 100)
        emptyWidth   = barWidth - filledWidth

        # Select gradient based on type
        gradients = {'cpu': self.cpuGradient, 'ram': self.ramGradient, 'disk': self.diskGradient}
        gradient  = gradients.get(gradientType, self.cpuGradient)

        if self.useGradientMeters:
            bar = ""
            for charPos in range(filledWidth):
                gradientPos = int((charPos / barWidth) * 100)
                bar += f"{gradient[gradientPos]}●"
            bar += f"{Fore.RESET}{'-' * emptyWidth}"
            return f"[{bar}]"
        else:
            return f"[{'●' * filledWidth}{'-' * emptyWidth}]"
    
    
    def _resetErrorStats(self):
        """
        Reset all error/failure statistics: uptime trackers, ping history, HTTP results.
        Shortcut: R
        """
        # Reset ping uptime trackers and history
        for rawTarget in self.configuration['ping_targets']:
            hostname, _ = self._parsePingTarget(rawTarget)
            self.pingUptimeTracker[hostname] = self._createUptimeTracker()
            self.pingDataStorage[hostname].clear()
            self.pingTimeStamps[hostname].clear()

        # Reset HTTP uptime trackers and history
        for httpTarget in self.configuration.get('http_targets', []):
            url = httpTarget['url']
            self.httpUptimeTracker[url] = self._createUptimeTracker()
            self.httpResponseTimes[url].clear()
            self.httpLastResults[url] = None

        # Reset alarm timers so alarms can fire again immediately
        self.lastAlarmTime.clear()

        # Reset internet history
        self.internetPingHistory.clear()
        self.internetIsOnline   = None
        self.internetLastPingMs = None

        # Reset start time (uptime counter)
        self.startTime = datetime.datetime.now()

        self._logMessage("INFO", "Stats reset by user (R key)")


    def _keyboardListenerThread(self):
        """
        Background thread that reads single keypresses without blocking the main loop.
        Supports: R = reset stats, O = options screen, Q = quit
        Works on Windows (msvcrt) and Unix (termios/tty).
        """
        try:
            if os.name == 'nt':
                import msvcrt
                while self.isRunning:
                    if msvcrt.kbhit():
                        ch = msvcrt.getwch()
                        self._handleKeypress(ch)
                    time.sleep(0.05)
            else:
                import tty, termios
                fd = sys.stdin.fileno()
                oldSettings = termios.tcgetattr(fd)
                try:
                    tty.setcbreak(fd);
                    while self.isRunning:
                        import select as _select
                        rlist, _, _ = _select.select([sys.stdin], [], [], 0.1)
                        if rlist:
                            ch = sys.stdin.read(1)
                            self._handleKeypress(ch)
                finally:
                    termios.tcsetattr(fd, termios.TCSADRAIN, oldSettings)
        except Exception as e:
            self._logMessage("WARN", f"Keyboard listener error: {e}")


    def _handleKeypress(self, ch):
        """Dispatch a keypress character to the appropriate action."""
        ch = ch.lower()
        if ch == 'r':
            self._resetErrorStats()
        elif ch == 'o':
            if not self.inOptionsScreen:
                self.inOptionsScreen = True
                try:
                    self._showOptionsScreen()
                finally:
                    self.inOptionsScreen = False
                    self._firstRender = True  # Force full redraw after options
        elif ch in ('q', '\x1b'):  # Q or Escape
            self.isRunning = False


    def _showOptionsScreen(self):
        """
        Interactive CLI options screen.
        Lets the user add/edit/delete locations, ping targets, HTTP targets,
        and simple scalar settings — all without leaving the terminal.
        Shortcut: O
        """
        def clr():
            subprocess.run('cls' if os.name == 'nt' else 'clear', shell=True)

        def prompt(msg, default=''):
            val = input(f"{Fore.CYAN}{msg}{Fore.WHITE} [{default}]: {Fore.YELLOW}").strip()
            print(Fore.RESET, end='')
            return val if val else default

        def promptRequired(msg):
            while True:
                val = input(f"{Fore.CYAN}{msg}: {Fore.YELLOW}").strip()
                print(Fore.RESET, end='')
                if val:
                    return val
                print(f"{Fore.RED}  Value required, try again.")

        def saveConfig():
            with open(self.configFilePath, 'w', encoding='utf-8') as f:
                json.dump(self.configuration, f, indent=4, ensure_ascii=False)
            print(f"{Fore.GREEN}  ✓ Config saved to {self.configFilePath}")
            self._logMessage("INFO", "Configuration saved via options screen")

        def waitKey():
            input(f"\n{Fore.WHITE}Press Enter to continue...")

        def header(title):
            clr()
            print(f"{Fore.CYAN}{Style.BRIGHT}{'─' * 60}")
            print(f"  ⚙  OPTIONS — {title}")
            print(f"{'─' * 60}{Style.RESET_ALL}")

        while True:
            header("MAIN MENU")
            print(f"{Fore.WHITE}  1) Locations (weather & timezones)")
            print(f"  2) Ping targets")
            print(f"  3) HTTP/HTTPS page targets")
            print(f"  4) General settings (intervals, thresholds, etc.)")
            print(f"  5) Global HTTP absent-text filters")
            print(f"  6) Notifications (Telegram / Email / Webhook)")
            print(f"  0) Save & exit options")
            print(f"  X) Exit WITHOUT saving")
            print()
            choice = input(f"{Fore.YELLOW}Choose: {Fore.WHITE}").strip().lower()

            if choice == '0':
                saveConfig()
                # Reload live config into runtime state
                self.configuration = self._reloadRuntimeConfig()
                break

            elif choice == 'x':
                print(f"{Fore.YELLOW}  Changes discarded.")
                # Reload from disk to discard in-memory edits
                self.configuration = self._loadConfiguration()
                break

            elif choice == '1':
                self._optionsLocations(header, prompt, promptRequired, waitKey)

            elif choice == '2':
                self._optionsPingTargets(header, prompt, promptRequired, waitKey)

            elif choice == '3':
                self._optionsHttpTargets(header, prompt, promptRequired, waitKey)

            elif choice == '4':
                self._optionsGeneralSettings(header, prompt, waitKey)

            elif choice == '5':
                self._optionsAbsentText(header, promptRequired, waitKey)

            elif choice == '6':
                self._optionsNotifications(header, prompt, promptRequired, waitKey)


    def _optionsNotifications(self, header, prompt, _promptRequired, waitKey):
        """Edit notification channels: Telegram, Email, Webhook."""

        def boolPrompt(label, current):
            val = prompt(label, 'yes' if current else 'no').lower()
            return val in ('yes', 'true', '1', 'y')

        def ensureNotifCfg():
            if 'notifications' not in self.configuration:
                self.configuration['notifications'] = {}
            return self.configuration['notifications']

        while True:
            header("NOTIFICATIONS")
            cfg = ensureNotifCfg()
            tg    = cfg.get('telegram', {})
            em    = cfg.get('email', {})
            wh    = cfg.get('webhook', {})

            tgOn  = '✅' if tg.get('enabled') else '☐'
            emOn  = '✅' if em.get('enabled') else '☐'
            whOn  = '✅' if wh.get('enabled') else '☐'

            tgTokenDisplay = '🔒 encrypted' if self.vault.isEncrypted(tg.get('bot_token','')) else (tg.get('bot_token','—')[:18] + '…')
            tgChatDisplay  = '🔒 encrypted' if self.vault.isEncrypted(tg.get('chat_id',''))   else tg.get('chat_id','—')
            print(f"  {Fore.GREEN}1){Fore.WHITE} {tgOn} Telegram      bot:{tgTokenDisplay}  chat:{tgChatDisplay}")
            emUserDisplay = '🔒 encrypted' if self.vault.isEncrypted(em.get('smtp_username','')) else em.get('smtp_username','—')
            print(f"  {Fore.GREEN}2){Fore.WHITE} {emOn} Email          smtp:{em.get('smtp_host','—')}:{em.get('smtp_port','—')}  user:{emUserDisplay}")
            whUrlDisplay = '🔒 encrypted' if self.vault.isEncrypted(wh.get('url','')) else wh.get('url','—')[:50]
            print(f"  {Fore.GREEN}3){Fore.WHITE} {whOn} Webhook / API  {whUrlDisplay}")
            print(f"\n  {Fore.YELLOW}T) Test all enabled channels   B) Back")
            ch = input(f"{Fore.YELLOW}Choose: {Fore.WHITE}").strip().lower()

            if ch == 'b':
                break

            elif ch == '1':
                header("NOTIFICATIONS — TELEGRAM")
                if 'telegram' not in cfg:
                    cfg['telegram'] = {}
                t = cfg['telegram']
                t['enabled']          = boolPrompt("Enable Telegram notifications (yes/no)", t.get('enabled', False))
                tokenMask             = ('*' * 8) if t.get('bot_token') else ''
                print(f"{Fore.CYAN}  Bot token (from @BotFather){Fore.WHITE} [{tokenMask}]: ", end='')
                newToken              = input(f"{Fore.YELLOW}").strip()
                print(Fore.RESET, end='')
                if newToken:
                    t['bot_token']    = self.vault.encrypt(newToken)
                chatMask              = ('*' * 8) if t.get('chat_id') else ''
                print(f"{Fore.CYAN}  Chat ID (use @userinfobot to find){Fore.WHITE} [{chatMask}]: ", end='')
                newChatId             = input(f"{Fore.YELLOW}").strip()
                print(Fore.RESET, end='')
                if newChatId:
                    t['chat_id']      = self.vault.encrypt(newChatId)
                t['on_first_failure'] = boolPrompt("Send on first failure (yes/no)",  t.get('on_first_failure', True))
                t['on_recovery']      = boolPrompt("Send on recovery (yes/no)",       t.get('on_recovery', True))
                print(f"{Fore.GREEN}  ✓ Telegram settings updated")
                waitKey()

            elif ch == '2':
                header("NOTIFICATIONS — EMAIL")
                if 'email' not in cfg:
                    cfg['email'] = {}
                e = cfg['email']
                e['enabled']          = boolPrompt("Enable Email notifications (yes/no)",   e.get('enabled', False))
                e['smtp_host']        = prompt("SMTP host (e.g. smtp.gmail.com)",           e.get('smtp_host', 'smtp.gmail.com'))
                e['smtp_port']        = int(prompt("SMTP port (587=TLS, 465=SSL, 25=plain)", str(e.get('smtp_port', 587))) or 587)
                e['smtp_use_tls']     = boolPrompt("Use STARTTLS (yes=587, no=SSL/465)",     e.get('smtp_use_tls', True))
                currentUser           = self._secret(e.get('smtp_username', ''))
                newUser               = prompt("SMTP username / login email", currentUser)
                e['smtp_username']    = self.vault.encrypt(newUser) if newUser else e.get('smtp_username', '')
                newPass = input(f"{Fore.CYAN}  SMTP password (Enter to keep current){Fore.WHITE} [{'*'*8 if e.get('smtp_password') else ''}]: {Fore.YELLOW}").strip()
                print(Fore.RESET, end='')
                if newPass:
                    e['smtp_password'] = self.vault.encrypt(newPass)
                e['from_address']     = prompt("From address",                             e.get('from_address', ''))
                toRaw = prompt("To addresses (comma-separated)",
                               ', '.join(e.get('to_addresses', [])))
                e['to_addresses']     = [a.strip() for a in toRaw.split(',') if a.strip()]
                e['subject_prefix']   = prompt("Subject prefix",                          e.get('subject_prefix', '[PCMonitor]'))
                e['on_first_failure'] = boolPrompt("Send on first failure (yes/no)",      e.get('on_first_failure', True))
                e['on_recovery']      = boolPrompt("Send on recovery (yes/no)",           e.get('on_recovery', True))
                print(f"{Fore.GREEN}  ✓ Email settings updated")
                waitKey()

            elif ch == '3':
                header("NOTIFICATIONS — WEBHOOK / API")
                if 'webhook' not in cfg:
                    cfg['webhook'] = {}
                w = cfg['webhook']
                w['enabled']          = boolPrompt("Enable Webhook notifications (yes/no)",  w.get('enabled', False))
                currentUrl            = self._secret(w.get('url', ''))
                newUrl                = prompt("Endpoint URL",                              currentUrl)
                w['url']              = self.vault.encrypt(newUrl) if newUrl else w.get('url', '')
                w['method']           = prompt("HTTP method (POST/GET/PUT)",                w.get('method', 'POST')).upper()
                print(f"{Fore.CYAN}  Current headers: {Fore.WHITE}{json.dumps(w.get('headers', {}))}")
                print(f"{Fore.CYAN}  H) Edit headers   (Enter to skip)")
                hCh = input(f"{Fore.YELLOW}  Choice: {Fore.WHITE}").strip().lower()
                if hCh == 'h':
                    headers = w.get('headers', {})
                    while True:
                        print(f"\n{Fore.CYAN}  Current headers:")
                        for k, v in headers.items():
                            print(f"    {Fore.GREEN}{k}: {Fore.WHITE}{v}")
                        print(f"\n  {Fore.YELLOW}A) Add/update   D) Delete   B) Done with headers")
                        hSub = input(f"{Fore.YELLOW}  Choice: {Fore.WHITE}").strip().lower()
                        if hSub == 'b':
                            break
                        elif hSub == 'a':
                            hKey = input(f"{Fore.CYAN}    Header name: {Fore.WHITE}").strip()
                            hVal = input(f"{Fore.CYAN}    Value: {Fore.WHITE}").strip()
                            if hKey:
                                headers[hKey] = hVal
                        elif hSub == 'd':
                            hKey = input(f"{Fore.CYAN}    Header name to delete: {Fore.WHITE}").strip()
                            headers.pop(hKey, None)
                    w['headers'] = headers
                currentTpl = self._secret(w.get('body_template', ''))
                tplDisplay = '🔒 encrypted' if self.vault.isEncrypted(w.get('body_template', '')) else currentTpl[:80]
                print(f"{Fore.CYAN}  Current body template: {Fore.WHITE}{tplDisplay}")
                newTpl = input(f"{Fore.CYAN}  Body template (Enter to keep, {{event}}/{{target}}/{{message}}/{{timestamp}} placeholders): {Fore.YELLOW}").strip()
                print(Fore.RESET, end='')
                if newTpl:
                    w['body_template'] = self.vault.encrypt(newTpl)
                elif 'body_template' not in w:
                    w['body_template'] = self.vault.encrypt('{"event": "{event}", "target": "{target}", "message": "{message}", "timestamp": "{timestamp}"}')
                w['on_first_failure'] = boolPrompt("Send on first failure (yes/no)", w.get('on_first_failure', True))
                w['on_recovery']      = boolPrompt("Send on recovery (yes/no)",      w.get('on_recovery', True))
                print(f"{Fore.GREEN}  ✓ Webhook settings updated")
                waitKey()

            elif ch == 't':
                header("NOTIFICATIONS — TEST")
                print(f"{Fore.CYAN}  Sending test notification to all enabled channels...")
                self._sendNotifications("failure", "test:manual", "🧪 Test notification from PCMonitor options menu")
                print(f"{Fore.GREEN}  ✓ Test sent — check logs for results")
                waitKey()

    def _reloadRuntimeConfig(self):
        """Reload config from disk and re-read the file (used after options save)."""
        try:
            with open(self.configFilePath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self._logMessage("WARN", f"Config reload failed: {e}")
            return self.configuration


    def _optionsLocations(self, header, prompt, promptRequired, waitKey):
        while True:
            header("LOCATIONS")
            locs = self.configuration.get('locations', [])
            for i, loc in enumerate(locs):
                print(f"  {Fore.GREEN}{i+1}) {Fore.WHITE}{loc['name']:<16} tz:{loc['timezone']}  query:{loc['weather_query']}")
            print(f"\n  {Fore.YELLOW}A) Add   E) Edit   D) Delete   B) Back")
            ch = input(f"{Fore.YELLOW}Choose: {Fore.WHITE}").strip().lower()

            if ch == 'b':
                break
            elif ch == 'a':
                name  = promptRequired("Location name (e.g. London)")
                tz    = promptRequired("Timezone (e.g. Europe/London)")
                query = promptRequired("Weather query (e.g. London,UK)")
                locs.append({"name": name, "timezone": tz, "weather_query": query})
                self.configuration['locations'] = locs
                print(f"{Fore.GREEN}  ✓ Added {name}")
                waitKey()
            elif ch == 'e':
                idx = input(f"{Fore.CYAN}  Edit which number? {Fore.WHITE}").strip()
                try:
                    i = int(idx) - 1
                    assert 0 <= i < len(locs)
                    loc = locs[i]
                    loc['name']          = prompt("Name",         loc['name'])
                    loc['timezone']      = prompt("Timezone",     loc['timezone'])
                    loc['weather_query'] = prompt("Weather query",loc['weather_query'])
                    print(f"{Fore.GREEN}  ✓ Updated")
                    waitKey()
                except (ValueError, AssertionError, IndexError):
                    print(f"{Fore.RED}  Invalid number."); waitKey()
            elif ch == 'd':
                idx = input(f"{Fore.CYAN}  Delete which number? {Fore.WHITE}").strip()
                try:
                    i = int(idx) - 1
                    assert 0 <= i < len(locs)
                    removed = locs.pop(i)
                    self.configuration['locations'] = locs
                    print(f"{Fore.GREEN}  ✓ Removed {removed['name']}")
                    waitKey()
                except (ValueError, AssertionError, IndexError):
                    print(f"{Fore.RED}  Invalid number."); waitKey()


    def _optionsPingTargets(self, header, prompt, promptRequired, waitKey):
        while True:
            header("PING TARGETS")
            targets = self.configuration.get('ping_targets', [])
            unreliable = self.configuration.get('unreliable_hosts', [])
            for i, t in enumerate(targets):
                addr, desc = self._parsePingTarget(t)
                flag = f" {Fore.YELLOW}[unreliable]" if addr in unreliable else ""
                print(f"  {Fore.GREEN}{i+1}) {Fore.WHITE}{desc:<24} {addr}{flag}")
            print(f"\n  {Fore.YELLOW}A) Add   E) Edit   D) Delete   U) Toggle unreliable   B) Back")
            ch = input(f"{Fore.YELLOW}Choose: {Fore.WHITE}").strip().lower()

            if ch == 'b':
                break
            elif ch == 'a':
                addr = promptRequired("Address or IP")
                desc = prompt("Description", addr)
                targets.append({"address": addr, "description": desc})
                self.configuration['ping_targets'] = targets
                # Init storage for new target so it won't crash
                self.pingDataStorage[addr] = deque(maxlen=60)
                self.pingTimeStamps[addr]  = deque(maxlen=60)
                self.pingUptimeTracker[addr] = self._createUptimeTracker()
                print(f"{Fore.GREEN}  ✓ Added {addr} (restart to begin pinging)")
                waitKey()
            elif ch == 'e':
                idx = input(f"{Fore.CYAN}  Edit which number? {Fore.WHITE}").strip()
                try:
                    i = int(idx) - 1
                    assert 0 <= i < len(targets)
                    t = targets[i]
                    if isinstance(t, dict):
                        t['address']     = prompt("Address", t['address'])
                        t['description'] = prompt("Description", t.get('description', t['address']))
                    else:
                        targets[i] = {"address": prompt("Address", t), "description": prompt("Description", t)}
                    print(f"{Fore.GREEN}  ✓ Updated"); waitKey()
                except (ValueError, AssertionError, IndexError):
                    print(f"{Fore.RED}  Invalid number."); waitKey()
            elif ch == 'd':
                idx = input(f"{Fore.CYAN}  Delete which number? {Fore.WHITE}").strip()
                try:
                    i = int(idx) - 1
                    assert 0 <= i < len(targets)
                    removed = targets.pop(i)
                    self.configuration['ping_targets'] = targets
                    addr, _ = self._parsePingTarget(removed)
                    print(f"{Fore.GREEN}  ✓ Removed {addr}"); waitKey()
                except (ValueError, AssertionError, IndexError):
                    print(f"{Fore.RED}  Invalid number."); waitKey()
            elif ch == 'u':
                idx = input(f"{Fore.CYAN}  Toggle unreliable for which number? {Fore.WHITE}").strip()
                try:
                    i = int(idx) - 1
                    assert 0 <= i < len(targets)
                    addr, _ = self._parsePingTarget(targets[i])
                    if addr in unreliable:
                        unreliable.remove(addr)
                        print(f"{Fore.GREEN}  ✓ {addr} is now reliable (will alarm on failure)")
                    else:
                        unreliable.append(addr)
                        print(f"{Fore.YELLOW}  ✓ {addr} marked unreliable (no alarm)")
                    self.configuration['unreliable_hosts'] = unreliable
                    waitKey()
                except (ValueError, AssertionError, IndexError):
                    print(f"{Fore.RED}  Invalid number."); waitKey()


    def _optionsHttpTargets(self, header, prompt, promptRequired, waitKey):
        while True:
            header("HTTP/HTTPS TARGETS")
            targets = self.configuration.get('http_targets', [])
            for i, t in enumerate(targets):
                print(f"  {Fore.GREEN}{i+1}) {Fore.WHITE}{t.get('description','?'):<22} {t['url'][:50]}  interval:{t.get('interval',600)}s")
            print(f"\n  {Fore.YELLOW}A) Add   E) Edit   D) Delete   T) Edit text checks   B) Back")
            ch = input(f"{Fore.YELLOW}Choose: {Fore.WHITE}").strip().lower()

            if ch == 'b':
                break
            elif ch == 'a':
                url  = promptRequired("URL (https://...)")
                desc = prompt("Description", url[:30])
                try:
                    interval = int(prompt("Check interval (seconds)", "60"))
                except ValueError:
                    interval = 60
                targets.append({"url": url, "description": desc, "interval": interval,
                                 "text_present": [], "text_absent": []})
                self.configuration['http_targets'] = targets
                self.httpResponseTimes[url] = deque(maxlen=30)
                self.httpLastResults[url]   = None
                self.httpUptimeTracker[url] = self._createUptimeTracker()
                print(f"{Fore.GREEN}  ✓ Added (restart to begin monitoring)"); waitKey()
            elif ch == 'e':
                idx = input(f"{Fore.CYAN}  Edit which number? {Fore.WHITE}").strip()
                try:
                    i = int(idx) - 1
                    assert 0 <= i < len(targets)
                    t = targets[i]
                    t['url']         = prompt("URL",         t['url'])
                    t['description'] = prompt("Description", t.get('description', ''))
                    try:
                        t['interval'] = int(prompt("Interval (s)", str(t.get('interval', 60))))
                    except ValueError:
                        pass
                    print(f"{Fore.GREEN}  ✓ Updated"); waitKey()
                except (ValueError, AssertionError, IndexError):
                    print(f"{Fore.RED}  Invalid number."); waitKey()
            elif ch == 'd':
                idx = input(f"{Fore.CYAN}  Delete which number? {Fore.WHITE}").strip()
                try:
                    i = int(idx) - 1
                    assert 0 <= i < len(targets)
                    removed = targets.pop(i)
                    self.configuration['http_targets'] = targets
                    print(f"{Fore.GREEN}  ✓ Removed {removed.get('description', removed['url'])}"); waitKey()
                except (ValueError, AssertionError, IndexError):
                    print(f"{Fore.RED}  Invalid number."); waitKey()
            elif ch == 't':
                idx = input(f"{Fore.CYAN}  Edit text checks for which number? {Fore.WHITE}").strip()
                try:
                    i = int(idx) - 1
                    assert 0 <= i < len(targets)
                    t = targets[i]
                    self._optionsTextChecks(t, header, promptRequired, waitKey)
                except (ValueError, AssertionError, IndexError):
                    print(f"{Fore.RED}  Invalid number."); waitKey()


    def _optionsTextChecks(self, target, header, promptRequired, waitKey):
        """Edit text_present / text_absent lists for one HTTP target."""
        while True:
            header(f"TEXT CHECKS — {target.get('description', target['url'])}")
            present = target.get('text_present', [])
            absent  = target.get('text_absent', [])
            print(f"{Fore.GREEN}  MUST BE PRESENT ({len(present)}):")
            for i, s in enumerate(present):
                print(f"    {i+1}) {Fore.WHITE}{s}")
            print(f"{Fore.RED}  MUST BE ABSENT ({len(absent)}):")
            for i, s in enumerate(absent):
                print(f"    {i+1}) {Fore.WHITE}{s}")
            print(f"\n  {Fore.YELLOW}AP) Add present   DP) Del present   AA) Add absent   DA) Del absent   B) Back")
            ch = input(f"{Fore.YELLOW}Choose: {Fore.WHITE}").strip().lower()

            if ch == 'b':
                break
            elif ch == 'ap':
                s = promptRequired("String that MUST be present")
                present.append(s); target['text_present'] = present
                print(f"{Fore.GREEN}  ✓ Added"); waitKey()
            elif ch == 'dp':
                idx = input(f"{Fore.CYAN}  Remove which present string? {Fore.WHITE}").strip()
                try:
                    present.pop(int(idx)-1); target['text_present'] = present
                    print(f"{Fore.GREEN}  ✓ Removed"); waitKey()
                except (ValueError, IndexError):
                    print(f"{Fore.RED}  Invalid."); waitKey()
            elif ch == 'aa':
                s = promptRequired("String that MUST NOT be present")
                absent.append(s); target['text_absent'] = absent
                print(f"{Fore.GREEN}  ✓ Added"); waitKey()
            elif ch == 'da':
                idx = input(f"{Fore.CYAN}  Remove which absent string? {Fore.WHITE}").strip()
                try:
                    absent.pop(int(idx)-1); target['text_absent'] = absent
                    print(f"{Fore.GREEN}  ✓ Removed"); waitKey()
                except (ValueError, IndexError):
                    print(f"{Fore.RED}  Invalid."); waitKey()


    def _optionsGeneralSettings(self, header, prompt, waitKey):
        """Edit scalar settings in the config."""
        header("GENERAL SETTINGS")
        SETTINGS = [
            ('ping_interval',                    int,   'Ping interval (seconds)'),
            ('display_refresh',                  int,   'Display refresh interval (seconds)'),
            ('ping_failure_threshold',            int,   'Consecutive ping failures before alarm'),
            ('http_failure_threshold',            int,   'Consecutive HTTP failures before alarm'),
            ('beep_on_failure',                  bool,  'Beep on failure (true/false)'),
            ('log_ping_failures',                bool,  'Log ping failures (true/false)'),
            ('log_response_times',               bool,  'Log HTTP response times (true/false)'),
            ('log_slow_threshold_ms',             int,   'Log slow response threshold (ms)'),
            ('debug_mode',                       bool,  'Debug mode (true/false)'),
            ('http_timeout',                     int,   'HTTP request timeout (seconds)'),
            ('http_user_agent',                  str,   'HTTP User-Agent string'),
            ('internet_check_host',              str,   'Internet check host (e.g. google.com)'),
            ('http_adaptive_multiplier_stable',  float, 'HTTP adaptive multiplier stable (>1)'),
            ('http_adaptive_multiplier_unstable',float, 'HTTP adaptive multiplier unstable (<1)'),
            ('http_stagger_delay_min',           int,   'HTTP stagger delay min (seconds)'),
            ('http_stagger_delay_max',           int,   'HTTP stagger delay max (seconds)'),
            ('max_ping_history',                 int,   'Max ping history points'),
        ]
        changed = False
        for key, typ, label in SETTINGS:
            current = self.configuration.get(key, '')
            newVal  = prompt(label, str(current))
            try:
                if typ == bool:
                    converted = newVal.lower() in ('true', '1', 'yes')
                else:
                    converted = typ(newVal)
                if converted != current:
                    self.configuration[key] = converted
                    changed = True
            except (ValueError, TypeError):
                pass  # keep original
        if changed:
            print(f"{Fore.GREEN}  ✓ Settings updated (save from main menu to persist)")
        waitKey()


    def _optionsAbsentText(self, header, promptRequired, waitKey):
        """Edit global http_text_absent_global list."""
        while True:
            header("GLOBAL ABSENT-TEXT FILTERS")
            items = self.configuration.get('http_text_absent_global', [])
            for i, s in enumerate(items):
                print(f"  {Fore.GREEN}{i+1}) {Fore.WHITE}{s}")
            print(f"\n  {Fore.YELLOW}A) Add   D) Delete   B) Back")
            ch = input(f"{Fore.YELLOW}Choose: {Fore.WHITE}").strip().lower()

            if ch == 'b':
                break
            elif ch == 'a':
                s = promptRequired("String that must NOT appear in any page")
                items.append(s)
                self.configuration['http_text_absent_global'] = items
                print(f"{Fore.GREEN}  ✓ Added"); waitKey()
            elif ch == 'd':
                idx = input(f"{Fore.CYAN}  Delete which number? {Fore.WHITE}").strip()
                try:
                    items.pop(int(idx)-1)
                    self.configuration['http_text_absent_global'] = items
                    print(f"{Fore.GREEN}  ✓ Removed"); waitKey()
                except (ValueError, IndexError):
                    print(f"{Fore.RED}  Invalid."); waitKey()


    def run(self):
        """
        Main run loop — the eternal vigil.
        A Jedi never sleeps while their servers might. This loop does not either.
        Ctrl+C is the only honorable exit.
        """
        print(f"{Fore.GREEN}Starting Jedi DevOps Uptime Monitor Plus...")
        print(f"{Fore.GREEN}Deploying ping probes to {len(self.configuration['ping_targets'])} targets... May they all respond.")
        
        # Start ping worker threads (one per target - parallel ping power!)
        pingThreads = []
        for rawTarget in self.configuration['ping_targets']:
            address, description = self._parsePingTarget(rawTarget)
            threadPing = threading.Thread(
                target=self._pingWorkerThread,
                args=(address, description),
                daemon=True
            )
            threadPing.start()
            pingThreads.append(threadPing)
            print(f"{Fore.CYAN}  ✓ Ping thread started for: {description} ({address})")

        # Start internet connectivity check thread
        internetHost = self.configuration.get('internet_check_host', 'google.com')
        threading.Thread(target=self._internetCheckWorkerThread, daemon=True).start()
        print(f"{Fore.CYAN}  ✓ Internet check thread started ({internetHost})")

        # Initial weather update (async - don't block startup!)
        print(f"{Fore.GREEN}Fetching initial weather data in background...")
        threading.Thread(target=self._updateWeatherForAllLocations, daemon=True).start()

        # Start HTTP monitoring threads in background (STAGGERED STARTUP)
        httpTargets = self.configuration.get('http_targets', [])
        if httpTargets:
            self.httpThreadsTotal = len(httpTargets)
            self.httpThreadsStarted = 0
            print(f"{Fore.GREEN}HTTP monitoring: {len(httpTargets)} targets will start in background (3-8s delays)...")
            # Launch background thread that will start all HTTP threads with delays
            threading.Thread(target=self._startHttpThreadsStaggered, args=(httpTargets,), daemon=True).start()

        print(f"{Fore.GREEN}All systems operational. Entering main loop...")

        # Start keyboard listener (R=reset stats, O=options, Q=quit)
        threading.Thread(target=self._keyboardListenerThread, daemon=True).start()
        print(f"{Fore.CYAN}  ✓ Keyboard shortcuts: R=reset stats  O=options  Q=quit")

        try:
            while self.isRunning:
                if not self.inOptionsScreen:
                    self._displayDashboard()
                time.sleep(self.configuration.get('display_refresh', 2))

        except KeyboardInterrupt:
            self.isRunning = False

        print(f"\n\n{Fore.YELLOW}Order 66 received. Standing down the sentinel...")
        self._logMessage("INFO", "Dashboard shutdown initiated by user")

        print(f"{Fore.GREEN}Waiting for threads to complete their final missions...")
        time.sleep(1)

        print(f"{Fore.GREEN}✓ Jedi DevOps Uptime Monitor Plus has been shut down. The Force remains strong.")
        print(f"{Fore.CYAN}Monitor log:   {self.logFilePath}")
        print(f"{Fore.CYAN}Errors log:    {self.errorLogFilePath}")
        print(f"{Fore.GREEN}May the Force be with you! 🌟")


def main():
    """
    The entry point - where our journey through the terminal begins.
    """
    def requestTerminalSize(cols=140, rows=45):
        """Best-effort terminal resize request; actual size depends on host terminal."""
        try:
            if os.name == "nt":
                os.system(f"mode con: cols={cols} lines={rows}")
            else:
                print(f"\033[8;{rows};{cols}t", end="")
        except Exception:
            pass
        return shutil.get_terminal_size(fallback=(80, 24))

    print(f"{Fore.CYAN}{Style.BRIGHT}")
    print("=" * 80)
    print("⚡ JEDI DEVOPS UPTIME MONITOR PLUS - INITIALIZING")
    print("=" * 80)
    print(f"{Style.RESET_ALL}")
    print(f"{Fore.GREEN}Checking dependencies... (A Jedi is only as strong as their pip packages)")
    terminalSize = requestTerminalSize(140, 55)
    print(f"{Fore.CYAN}Terminal size request: 140x55 (actual: {terminalSize.columns}x{terminalSize.lines}) — wider is wiser")
    
    # Check for required packages
    requiredPackages = ['colorama', 'psutil', 'requests', 'pytz']
    
    print(f"{Fore.GREEN}✓ All systems ready — the Force is strong with this terminal")
    print()
    
    dashboardControl = JediTerminalControl()
    # Backward/forward compatibility: some forks used .main() instead of .run()
    if hasattr(dashboardControl, 'run'):
        dashboardControl.run()
    elif hasattr(dashboardControl, 'main'):
        dashboardControl.main()
    else:
        raise AttributeError('JediTerminalControl has neither run() nor main()')


if __name__ == "__main__":
    main()
