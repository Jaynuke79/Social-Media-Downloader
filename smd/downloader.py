#!/usr/bin/env python3
"""
Social Media Downloader - A comprehensive CLI tool for downloading videos from various platforms.

This module provides functionality to download videos from YouTube, TikTok, Instagram, Facebook,
Twitter/X, and many other social media platforms. It supports format selection, batch downloads,
and maintains download history.

Author: Nayan Das
Version: 1.1.12
License: MIT
"""

import os
import sys
import csv
import time
import json
import shutil
import logging
import tempfile
import subprocess
import getpass
import base64
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional, Tuple, Any
from cryptography.fernet import Fernet
from pathlib import Path

# Browser automation imports
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.firefox.options import Options as FirefoxOptions
    from webdriver_manager.chrome import ChromeDriverManager
    from webdriver_manager.firefox import GeckoDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

# Third-party imports
import yt_dlp
import requests
import instaloader
from tqdm import tqdm
from pyfiglet import Figlet
from termcolor import colored
from tabulate import tabulate


# ---------------------------------
# Constants and Configuration
# ---------------------------------
AUTHOR = "Nayan Das"
CURRENT_VERSION = "1.1.12"
EMAIL = "nayanchandradas@hotmail.com"
DISCORD_INVITE = "https://discord.gg/skHyssu"
WEBSITE = "https://nayandas69.github.io/Social-Media-Downloader"
GITHUB_REPO_URL = "https://github.com/nayandas69/Social-Media-Downloader"
PYPI_API_URL = "https://pypi.org/pypi/social-media-downloader/json"

# Configuration constants
CONFIG_FILE = "config.json"
DEFAULT_CONFIG = {
    "default_format": "show_all",
    "download_directory": "media",
    "history_file": "download_history.csv",
    "mp3_quality": "192",
    "organize_downloads": True,
    "download_metadata": True,
    "download_comments": False,
    "download_subtitles": False,
    "max_comments": 200,
    "authentication": {
        "instagram_username": "",
        "use_browser_cookies": True,
        "cookie_browser": "chrome",
        "session_directory": ".smd_sessions"
    }
}

VALID_DEFAULT_FORMATS = {
    "show_all",
    "mp3",
    "360p",
    "480p",
    "720p",
    "1080p",
    "1440p",
    "2160p",
    "4320p",
}
VALID_MP3_QUALITIES = {"64", "128", "192", "256", "320", "396"}

# Supported platform domains
SUPPORTED_DOMAINS = [
    "youtube.com",
    "youtu.be",
    "tiktok.com",
    "facebook.com",
    "fb.watch",
    "x.com",
    "twitter.com",
    "twitch.tv",
    "clips.twitch.tv",
    "snapchat.com",
    "reddit.com",
    "packaged-media.redd.it",
    "vimeo.com",
    "streamable.com",
    "pinterest.com",
    "pin.it",
    "linkedin.com",
    "bilibili.tv",
    "odysee.com",
    "rumble.com",
    "gameclips.io",
    "triller.co",
    "snackvideo.com",
    "kwai.com",
    "imdb.com",
    "weibo.com",
    "dailymotion.com",
    "dai.ly",
    "tumblr.com",
    "bsky.app",
]

INSTAGRAM_DOMAINS = ["instagram.com"]

# Network timeout settings
NETWORK_TIMEOUT = 10
CONNECTION_CHECK_TIMEOUT = 5
RETRY_DELAY = 5


# ---------------------------------
# Logging Setup
# ---------------------------------
def setup_logging() -> None:
    """Configure logging for the application."""
    logging.basicConfig(
        filename="downloader.log",
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        filemode="a",
    )


setup_logging()


# ---------------------------------
# Display Functions
# ---------------------------------
def display_author_details() -> None:
    """Display the animated banner and author details with improved error handling."""
    try:
        # Clear screen cross-platform
        os.system("cls" if os.name == "nt" else "clear")

        # Create and display banner
        banner_font = Figlet(font="slant")
        banner_text = banner_font.renderText("Social Media Downloader")
        banner_colored = colored(banner_text, "cyan", attrs=["bold"])

        # Animate banner display
        for line in banner_colored.splitlines():
            print(line)
            time.sleep(0.05)

        print("\n")

        # Display author information with animation
        info_lines = [
            ("Author   : ", AUTHOR, "yellow", "white"),
            ("Email    : ", EMAIL, "yellow", "cyan"),
            ("Discord  : ", DISCORD_INVITE, "yellow", "cyan"),
            ("Repo     : ", GITHUB_REPO_URL, "yellow", "cyan"),
            ("Website  : ", WEBSITE, "yellow", "cyan"),
            ("Version  : ", CURRENT_VERSION, "yellow", "green"),
        ]

        for label, value, label_color, value_color in info_lines:
            print(
                colored(f"{label:<10}", label_color, attrs=["bold"])
                + colored(value, value_color)
            )
            time.sleep(0.2)

        # Loading animation
        print(colored("\nLoading", "yellow", attrs=["bold"]), end="", flush=True)
        for _ in range(5):
            time.sleep(0.4)
            print(colored(".", "yellow", attrs=["bold"]), end="", flush=True)

        time.sleep(0.5)
        print()

    except Exception as e:
        logging.error(f"Error displaying banner: {e}")
        print("Social Media Downloader - Starting...")


display_author_details()


# ---------------------------------
# Configuration Management
# ---------------------------------
def load_config() -> Dict[str, Any]:
    """
    Load, validate, and auto-correct the configuration file.

    Returns:
        Dict[str, Any]: Configuration dictionary with validated values
    """
    config_changed = False

    # Create config file if it doesn't exist
    if not os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_CONFIG, f, indent=4)
            logging.info(f"Created new config file: {CONFIG_FILE}")
            return DEFAULT_CONFIG.copy()
        except IOError as e:
            logging.error(f"Failed to create config file: {e}")
            return DEFAULT_CONFIG.copy()

    # Load existing configuration
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config_data = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logging.error(f"Failed to load config file: {e}. Using defaults.")
        return DEFAULT_CONFIG.copy()

    # Validate and fix configuration
    config_data, config_changed = _validate_config(config_data)

    # Save corrected config if needed
    if config_changed:
        _save_config(config_data)

    return config_data


def _validate_config(config_data: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
    """
    Validate configuration data and fix invalid values.

    Args:
        config_data: Configuration dictionary to validate

    Returns:
        Tuple[Dict[str, Any], bool]: Validated configuration dictionary and whether changes were made
    """
    config_changed = False

    # Add missing keys from default
    for key, default_value in DEFAULT_CONFIG.items():
        if key not in config_data:
            logging.warning(
                f"Missing '{key}' in config. Setting to default: {default_value}"
            )
            config_data[key] = default_value
            config_changed = True

    # Validate mp3_quality
    mp3_quality = str(config_data.get("mp3_quality", "192"))
    if mp3_quality not in VALID_MP3_QUALITIES:
        logging.warning(f"Invalid mp3_quality '{mp3_quality}', resetting to '192'.")
        config_data["mp3_quality"] = "192"
        config_changed = True

    # Validate default_format
    default_format = str(config_data.get("default_format", "show_all")).lower()
    if default_format not in VALID_DEFAULT_FORMATS:
        logging.warning(
            f"Invalid default_format '{default_format}', resetting to 'show_all'."
        )
        config_data["default_format"] = "show_all"
        config_changed = True

    # Validate organize_downloads
    organize_downloads = config_data.get("organize_downloads", False)
    if not isinstance(organize_downloads, bool):
        logging.warning(
            f"Invalid organize_downloads '{organize_downloads}', resetting to False."
        )
        config_data["organize_downloads"] = False
        config_changed = True

    # Validate download_metadata
    download_metadata = config_data.get("download_metadata", True)
    if not isinstance(download_metadata, bool):
        logging.warning(
            f"Invalid download_metadata '{download_metadata}', resetting to True."
        )
        config_data["download_metadata"] = True
        config_changed = True

    # Validate download_comments
    download_comments = config_data.get("download_comments", False)
    if not isinstance(download_comments, bool):
        logging.warning(
            f"Invalid download_comments '{download_comments}', resetting to False."
        )
        config_data["download_comments"] = False
        config_changed = True

    # Validate download_subtitles
    download_subtitles = config_data.get("download_subtitles", False)
    if not isinstance(download_subtitles, bool):
        logging.warning(
            f"Invalid download_subtitles '{download_subtitles}', resetting to False."
        )
        config_data["download_subtitles"] = False
        config_changed = True

    # Validate max_comments
    max_comments = config_data.get("max_comments", 200)
    try:
        max_comments = int(max_comments)
        if max_comments < 1 or max_comments > 10000:
            raise ValueError("out of range")
    except (ValueError, TypeError):
        logging.warning(
            f"Invalid max_comments '{config_data.get('max_comments')}', resetting to 200."
        )
        config_data["max_comments"] = 200
        config_changed = True
    else:
        config_data["max_comments"] = max_comments

    return config_data, config_changed


def _save_config(config_data: Dict[str, Any]) -> None:
    """Save configuration data to file."""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=4)
        logging.info("Config file updated with corrected values.")
    except IOError as e:
        logging.error(f"Failed to write corrected config: {e}")


# Load configuration and setup global variables
config = load_config()
download_directory = config.get("download_directory", "media")
history_file = config.get("history_file", "download_history.csv")
mp3_quality = str(config.get("mp3_quality", "192"))
default_format = config.get("default_format", "show_all")

# Ensure download directory exists
try:
    os.makedirs(download_directory, exist_ok=True)
except OSError as e:
    logging.error(f"Failed to create download directory '{download_directory}': {e}")
    raise SystemExit("Cannot proceed without a valid download directory.")


# ---------------------------------
# System Requirements Check
# ---------------------------------
def ensure_ffmpeg() -> None:
    """
    Ensure that FFmpeg is installed and available in PATH.

    Raises:
        SystemExit: If FFmpeg is not found
    """
    if shutil.which("ffmpeg") is None:
        error_msg = [
            "\033[1;31m\nFFmpeg is not installed. Please install FFmpeg and try again.\033[0m",
            "\033[1;31mDownload FFmpeg from: https://ffmpeg.org/download.html\033[0m",
            "\033[1;31mFor Windows users, add FFmpeg to your PATH.\033[0m",
            "\033[1;31mFor Linux users, run: sudo apt install ffmpeg\033[0m",
            "\033[1;31mAfter installation, restart the program.\033[0m",
        ]
        for msg in error_msg:
            print(msg)
        sys.exit(1)
    else:
        print("\033[1;32mFFmpeg is installed. Proceeding...\033[0m")


# ---------------------------------
# Network Utilities
# ---------------------------------
def check_internet_connection() -> bool:
    """
    Check if the system has an active internet connection.

    Returns:
        bool: True if internet connection is available, False otherwise
    """
    try:
        response = requests.head(
            "https://www.google.com", timeout=CONNECTION_CHECK_TIMEOUT
        )
        return response.status_code == 200
    except Exception:  # Catch all exceptions, not just requests.RequestException
        return False


def ensure_internet_connection() -> None:
    """Ensure internet connection is available, retry if not."""
    while not check_internet_connection():
        print("\033[91m\nNo internet connection. Retrying in 5 seconds...\033[0m")
        time.sleep(RETRY_DELAY)
    print("\033[92mInternet connection detected. Proceeding...\033[0m")


# ---------------------------------
# Update Management
# ---------------------------------
def check_for_updates() -> None:
    """Check for updates from PyPI and notify users."""
    if not check_internet_connection():
        print(
            "\n\033[1;31mNo internet connection. Please connect and try again.\033[0m"
        )
        return

    print(f"\n\033[1;36mChecking for updates...\033[0m")
    print(f"\033[1;33mCurrent version:\033[0m {CURRENT_VERSION}")

    try:
        response = requests.get(PYPI_API_URL, timeout=NETWORK_TIMEOUT)
        response.raise_for_status()
        data = response.json()

        latest_version = data.get("info", {}).get("version", "Unknown")
        print(f"\033[1;33mLatest version:\033[0m {latest_version}")

        current_parsed = _parse_version(CURRENT_VERSION)
        latest_parsed = _parse_version(latest_version)

        if latest_parsed > current_parsed:
            _display_update_available(latest_version, data)
        elif latest_parsed == current_parsed:
            _display_up_to_date()
        else:
            _display_development_version()

    except requests.exceptions.Timeout:
        print(
            f"\n\033[1;31mRequest timed out. Please check your internet connection.\033[0m"
        )
        logging.error("Update check timed out")
    except requests.exceptions.RequestException as e:
        print(f"\n\033[1;31mError checking for updates: {e}\033[0m")
        print(f"\033[1;36mManually check: {GITHUB_REPO_URL}/releases\033[0m")
        logging.error(f"Update check failed: {e}")
    except Exception as e:
        print(f"\n\033[1;31mUnexpected error during update check: {e}\033[0m")
        logging.error(f"Unexpected update check error: {e}", exc_info=True)


def _parse_version(version_str: str) -> Tuple[int, ...]:
    """Parse version string into tuple of integers for comparison."""
    try:
        clean_version = str(version_str).strip()
        return tuple(map(int, clean_version.split(".")))
    except (ValueError, AttributeError, TypeError):
        return (0, 0, 0)


def _display_update_available(latest_version: str, data: Dict[str, Any]) -> None:
    """Display update available message."""
    print(f"\n\033[1;32mNew version available: {latest_version}\033[0m")
    print(f"\n\033[1;36mUpdate options:\033[0m")
    print(f"\033[1;33m1. Using pip:\033[0m")
    print(f"   \033[1;32mpip install social-media-downloader --upgrade\033[0m")
    print(f"\n\033[1;33m2. Download from GitHub:\033[0m")
    print(f"   {GITHUB_REPO_URL}/releases/latest")

    # Show release info if available
    release_info = data.get("info", {})
    summary = release_info.get("summary", "")
    if summary:
        print(f"\n\033[1;36mWhat's new:\033[0m {summary}")


def _display_up_to_date() -> None:
    """Display up-to-date message."""
    print(f"\n\033[1;32mYou're up to date!\033[0m")
    print(f"\033[1;36mJoin our Discord for updates and support:\033[0m")
    print(f"{DISCORD_INVITE}")


def _display_development_version() -> None:
    """Display development version message."""
    print(
        f"\n\033[1;33mYou're running a newer version than what's published on PyPI.\033[0m"
    )
    print(f"\033[1;36mThis might be a development or beta version.\033[0m")


# ---------------------------------
# Authentication and Session Management
# ---------------------------------
def _get_encryption_key() -> bytes:
    """Get or create encryption key for credential storage."""
    key_file = Path(".smd_key")
    if key_file.exists():
        return key_file.read_bytes()
    else:
        key = Fernet.generate_key()
        key_file.write_bytes(key)
        os.chmod(key_file, 0o600)  # Readable only by owner
        return key


def _encrypt_credential(credential: str) -> str:
    """Encrypt a credential using Fernet encryption."""
    key = _get_encryption_key()
    f = Fernet(key)
    encrypted = f.encrypt(credential.encode())
    return base64.urlsafe_b64encode(encrypted).decode()


def _decrypt_credential(encrypted_credential: str) -> str:
    """Decrypt a credential using Fernet encryption."""
    try:
        key = _get_encryption_key()
        f = Fernet(key)
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_credential.encode())
        return f.decrypt(encrypted_bytes).decode()
    except Exception:
        return ""


def setup_instagram_login() -> bool:
    """Set up Instagram authentication credentials."""
    print(colored("\n=== Instagram Authentication Setup ===", "cyan", attrs=["bold"]))
    print("This will allow you to download private content and access saved/liked posts.")
    print(colored("⚠️  Your credentials will be encrypted and stored locally.", "yellow"))
    
    print(colored("💡 Your Instagram username is what appears after '@' in your profile URL.", "cyan"))
    print(colored("   Example: If your profile is instagram.com/johndoe, enter 'johndoe'", "cyan"))
    
    username = input("\nEnter your Instagram username: ").strip()
    if not username:
        print(colored("❌ Username cannot be empty.", "red"))
        return False
    
    # Remove @ if user included it
    if username.startswith('@'):
        username = username[1:]
        print(colored(f"✓ Using username: {username}", "green"))
    
    # Validate username format (basic check)
    if username.isdigit():
        print(colored("⚠️  Warning: Instagram usernames are usually text, not just numbers.", "yellow"))
        confirm = input("Are you sure this is your Instagram username? (y/n): ")
        if not confirm.lower().startswith('y'):
            return False
    
    password = getpass.getpass("Enter your Instagram password: ")
    if not password:
        print(colored("❌ Password cannot be empty.", "red"))
        return False
    
    # Update config with encrypted credentials
    config = load_config()
    config["authentication"]["instagram_username"] = username
    
    # Store encrypted password in a separate credentials file
    credentials_file = Path(".smd_credentials.json")
    credentials = {}
    if credentials_file.exists():
        try:
            credentials = json.loads(credentials_file.read_text())
        except Exception:
            credentials = {}
    
    credentials["instagram_password"] = _encrypt_credential(password)
    credentials_file.write_text(json.dumps(credentials, indent=2))
    os.chmod(credentials_file, 0o600)  # Readable only by owner
    
    _save_config(config)
    print(colored("✅ Instagram credentials saved successfully!", "green"))
    return True


def get_instagram_credentials() -> Tuple[str, str]:
    """Get Instagram credentials from config and credential file."""
    config = load_config()
    username = config.get("authentication", {}).get("instagram_username", "")
    
    credentials_file = Path(".smd_credentials.json")
    if not credentials_file.exists() or not username:
        return "", ""
    
    try:
        credentials = json.loads(credentials_file.read_text())
        encrypted_password = credentials.get("instagram_password", "")
        password = _decrypt_credential(encrypted_password)
        return username, password
    except Exception:
        return "", ""


def get_session_directory() -> Path:
    """Get the session directory path, creating it if necessary."""
    config = load_config()
    session_dir = Path(config.get("authentication", {}).get("session_directory", ".smd_sessions"))
    session_dir.mkdir(exist_ok=True)
    os.chmod(session_dir, 0o700)  # Accessible only by owner
    return session_dir


def is_instagram_authenticated() -> bool:
    """Check if Instagram authentication is set up."""
    username, password = get_instagram_credentials()
    return bool(username and password)


def create_authenticated_instaloader(session_filename: Optional[str] = None) -> instaloader.Instaloader:
    """Create an authenticated Instaloader instance."""
    session_dir = get_session_directory()
    
    if session_filename:
        loader = instaloader.Instaloader(dirname_pattern=str(session_dir))
        try:
            loader.load_session_from_file(get_instagram_credentials()[0], str(session_dir / session_filename))
            return loader
        except Exception:
            pass
    
    # Create new authenticated session
    loader = instaloader.Instaloader(dirname_pattern=str(session_dir))
    username, password = get_instagram_credentials()
    
    if username and password:
        try:
            loader.login(username, password)
            # Save session for future use
            session_file = session_dir / f"session-{username}"
            loader.save_session_to_file(str(session_file))
            print(colored(f"✅ Instagram login successful! Session saved.", "green"))
            return loader
        except Exception as e:
            error_msg = str(e).lower()
            print(colored(f"❌ Instagram login failed: {e}", "red"))
            if "incorrect username" in error_msg or "user does not exist" in error_msg:
                print(colored("   → Check if your Instagram username is correct.", "yellow"))
            elif "incorrect password" in error_msg or "password" in error_msg:
                print(colored("   → Check if your Instagram password is correct.", "yellow"))
            elif "challenge" in error_msg or "checkpoint" in error_msg:
                print(colored("   → Instagram requires additional verification.", "yellow"))
                print(colored("   → Try logging into Instagram on a web browser first.", "yellow"))
            elif "rate" in error_msg or "many" in error_msg:
                print(colored("   → Too many login attempts. Wait and try again later.", "yellow"))
            else:
                print(colored("   → Go to 'Authentication Setup' → 'Instagram Login Setup' to reconfigure.", "yellow"))
    
    return loader


def get_browser_cookies_path() -> str:
    """Get the browser to use for cookie extraction."""
    config = load_config()
    return config.get("authentication", {}).get("cookie_browser", "chrome")


def _setup_instagram_browser():
    """Setup browser for Instagram automation."""
    try:
        config = load_config()
        browser = config.get("authentication", {}).get("cookie_browser", "chrome")
        
        if browser.lower() == "firefox":
            options = FirefoxOptions()
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            # Don't run headless for Instagram - they detect it
            driver = webdriver.Firefox(
                service=webdriver.firefox.service.Service(GeckoDriverManager().install()),
                options=options
            )
        else:
            options = ChromeOptions()
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            # Don't run headless for Instagram - they detect it
            driver = webdriver.Chrome(
                service=webdriver.chrome.service.Service(ChromeDriverManager().install()),
                options=options
            )
            
        # Make it look more like a real browser
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
        
    except Exception as e:
        print(colored(f"❌ Failed to setup browser: {e}", "red"))
        print(colored("Make sure Chrome or Firefox is installed.", "yellow"))
        return None


def _get_instagram_username_from_browser(driver) -> Optional[str]:
    """Extract Instagram username from the browser."""
    try:
        # Method 1: Try to get username from URL if on profile page
        current_url = driver.current_url
        if "/profilePage/" in current_url or current_url.count('/') >= 4:
            parts = current_url.split('/')
            for part in parts:
                if part and part != "www.instagram.com" and part != "https:" and part != "":
                    return part
        
        # Method 2: Click on profile icon and get username
        try:
            # Look for profile link or username in various places
            profile_selectors = [
                "a[href*='/'][aria-label*='profile' i]",
                "a[href^='/'][role='link'] img[alt*='profile' i]",
                "a[href^='/'] img[data-testid='user-avatar']",
                "a[aria-label*='Profile']",
            ]
            
            for selector in profile_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        href = element.get_attribute('href')
                        if href and '/' in href:
                            username = href.split('/')[-2] if href.endswith('/') else href.split('/')[-1]
                            if username and username != "www.instagram.com" and len(username) > 0:
                                return username
                except:
                    continue
                    
            # Method 3: Try to navigate to profile
            try:
                driver.get("https://www.instagram.com/accounts/edit/")
                time.sleep(2)
                current_url = driver.current_url
                if "accounts/edit" in current_url:
                    # Look for username in the edit profile page
                    username_inputs = driver.find_elements(By.CSS_SELECTOR, "input[name='username'], input[id*='username' i]")
                    for input_elem in username_inputs:
                        username = input_elem.get_attribute('value')
                        if username:
                            return username
            except:
                pass
                
        except Exception:
            pass
        
        return None
        
    except Exception as e:
        print(colored(f"⚠️  Warning: Could not detect username: {e}", "yellow"))
        return None


def _extract_instagram_post_links(driver, max_count: int) -> List[str]:
    """Extract Instagram post links from the current page."""
    post_links = []
    
    try:
        # Scroll and collect post links
        last_height = driver.execute_script("return document.body.scrollHeight")
        
        while len(post_links) < max_count:
            # Find post links
            posts = driver.find_elements(By.CSS_SELECTOR, "a[href*='/p/']")
            
            for post in posts:
                href = post.get_attribute('href')
                if href and '/p/' in href and href not in post_links:
                    post_links.append(href)
                    if len(post_links) >= max_count:
                        break
            
            if len(post_links) >= max_count:
                break
                
            # Scroll down
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)  # Wait for loading
            
            # Check if more content loaded
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break  # No more content
            last_height = new_height
            
    except Exception as e:
        print(colored(f"⚠️  Warning extracting posts: {e}", "yellow"))
    
    return post_links[:max_count]


def _download_instagram_posts_with_ytdlp(post_links: List[str]) -> None:
    """Download Instagram posts using yt-dlp with browser cookie authentication."""
    success_count = 0
    config = load_config()
    browser = config.get("authentication", {}).get("cookie_browser", "chrome")
    
    for i, url in enumerate(post_links, 1):
        try:
            print(colored(f"📥 Downloading post {i}/{len(post_links)}: {url}", "cyan"))
            
            # First extract metadata to get proper uploader information - with cookies
            temp_ydl_opts = {
                'quiet': True,
                'cookiesfrombrowser': (browser,),
            }
            with yt_dlp.YoutubeDL(temp_ydl_opts) as temp_ydl:
                info = temp_ydl.extract_info(url, download=False)
            
            # Get organized path using the extracted metadata
            organized_path = get_organized_download_path(url, info)
            
            ydl_opts = {
                'cookiesfrombrowser': (browser,),
                'outtmpl': f'{organized_path}/%(title)s.%(ext)s',
            }
            
            # Add metadata options if enabled
            if should_download_metadata():
                ydl_opts.update({
                    'writeinfojson': True,
                    'writedescription': True,
                })
            
            if should_download_comments():
                ydl_opts['writecomments'] = True
                
            if should_download_subtitles():
                ydl_opts.update({
                    'writesubtitles': True,
                    'writeautomaticsub': True,
                })
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
                
            print(colored(f"✅ Downloaded post {i}/{len(post_links)}", "green"))
            log_download(url, "Success")
            success_count += 1
            
            # Small delay between downloads
            time.sleep(1)
            
        except Exception as e:
            error_str = str(e).lower()
            if "restricted" in error_str or "18 years" in error_str:
                print(colored(f"❌ Failed to download post {i}: Age-restricted content", "red"))
                print(colored(f"💡 Make sure you're logged into Instagram in your {browser} browser", "yellow"))
            else:
                print(colored(f"❌ Failed to download post {i}: {e}", "red"))
            log_download(url, "Failed")
    
    print(colored(f"\n🎉 Downloaded {success_count}/{len(post_links)} posts successfully!", "green"))


# ---------------------------------
# Utility Functions
# ---------------------------------
def log_download(url: str, status: str) -> None:
    """
    Log the download status in history file and application log.

    Args:
        url: The URL that was downloaded
        status: Status of the download (Success/Failed)
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(history_file, "a+", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([url, status, timestamp])
        logging.info(f"Download status for {url}: {status}")
    except IOError as e:
        logging.error(f"Failed to log download: {e}")


# ---------------------------------
# Metadata and Comment Processing
# ---------------------------------


def convert_comments_to_csv(comments_json_path: str, output_csv_path: str) -> bool:
    """
    Convert yt-dlp JSON comments to CSV format.
    
    Args:
        comments_json_path: Path to JSON comments file
        output_csv_path: Path to output CSV file
        
    Returns:
        bool: True if conversion successful, False otherwise
    """
    try:
        import json
        import csv
        from datetime import datetime
        
        with open(comments_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        comments = data.get('comments', [])
        if not comments:
            return False
            
        with open(output_csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Author', 'Text', 'Timestamp', 'Likes', 'Replies', 'Comment_ID'])
            
            for comment in comments:
                # Convert timestamp to readable format
                timestamp = comment.get('timestamp', '')
                if timestamp:
                    try:
                        dt = datetime.fromtimestamp(timestamp)
                        timestamp = dt.strftime('%Y-%m-%d %H:%M:%S')
                    except (ValueError, OSError):
                        pass
                
                writer.writerow([
                    comment.get('author', ''),
                    comment.get('text', '').replace('\n', ' '),
                    timestamp,
                    comment.get('like_count', 0),
                    comment.get('reply_count', 0),
                    comment.get('id', '')
                ])
        
        return True
    except Exception as e:
        logging.error(f"Failed to convert comments to CSV: {e}")
        return False


def extract_clean_description(info_json_path: str, output_txt_path: str) -> bool:
    """
    Extract clean description from metadata JSON file.
    
    Args:
        info_json_path: Path to info.json file
        output_txt_path: Path to output description.txt file
        
    Returns:
        bool: True if extraction successful, False otherwise
    """
    try:
        import json
        
        with open(info_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        description = data.get('description', '').strip()
        if not description:
            return False
            
        with open(output_txt_path, 'w', encoding='utf-8') as f:
            f.write(description)
        
        return True
    except Exception as e:
        logging.error(f"Failed to extract description: {e}")
        return False


def should_download_metadata() -> bool:
    """Check if metadata downloads are enabled in config."""
    return config.get("download_metadata", True)


def should_download_comments() -> bool:
    """Check if comment downloads are enabled in config."""
    return config.get("download_comments", False)


def should_download_subtitles() -> bool:
    """Check if subtitle downloads are enabled in config."""
    return config.get("download_subtitles", False)


def get_max_comments() -> int:
    """Get maximum number of comments to download."""
    return config.get("max_comments", 200)


def _process_downloaded_metadata(url: str, info: Dict[str, Any]) -> None:
    """
    Process downloaded metadata files (convert comments to CSV, extract descriptions).
    
    Args:
        url: Video URL
        info: Video metadata from yt-dlp
    """
    try:
        organized_path = get_organized_download_path(url, info)
        
        # Find the actual info.json file (yt-dlp may use different filename sanitization)
        info_json_path = None
        for filename in os.listdir(organized_path):
            if filename.endswith('.info.json'):
                info_json_path = os.path.join(organized_path, filename)
                break
        
        if info_json_path and os.path.exists(info_json_path):
            # Get the base name without .info.json extension for other files
            base_name = os.path.basename(info_json_path)[:-10]  # Remove '.info.json'
            
            # Extract clean description
            description_path = os.path.join(organized_path, f"{base_name}.description.txt")
            extract_clean_description(info_json_path, description_path)
            
            # Convert comments to CSV if comments were downloaded
            if should_download_comments():
                csv_path = os.path.join(organized_path, f"{base_name}.comments.csv")
                convert_comments_to_csv(info_json_path, csv_path)
                
    except Exception as e:
        logging.warning(f"Failed to process metadata files for {url}: {e}")


def get_unique_filename(filename: str) -> str:
    """
    Ensure downloaded files have unique names by appending numbers if duplicates exist.

    Args:
        filename: Original filename

    Returns:
        str: Unique filename
    """
    if not os.path.exists(filename):
        return filename

    base, ext = os.path.splitext(filename)
    counter = 1
    new_filename = f"{base} ({counter}){ext}"
    while os.path.exists(new_filename):
        counter += 1
        new_filename = f"{base} ({counter}){ext}"
    return new_filename


def is_valid_platform_url(url: str, allowed_domains: List[str]) -> bool:
    """
    Check if the URL matches one of the allowed domains.

    Args:
        url: URL to validate
        allowed_domains: List of allowed domain strings

    Returns:
        bool: True if URL contains any allowed domain
    """
    return any(domain in url.lower() for domain in allowed_domains)


def detect_platform_from_url(url: str) -> str:
    """
    Detect the platform name from a URL.
    
    Args:
        url: Video URL to analyze
        
    Returns:
        str: Platform name (e.g., "YouTube", "TikTok", "Instagram", "Other")
    """
    url_lower = url.lower()
    
    # Platform mapping based on domain patterns
    platform_map = {
        "youtube.com": "YouTube",
        "youtu.be": "YouTube",
        "tiktok.com": "TikTok",
        "instagram.com": "Instagram",
        "facebook.com": "Facebook",
        "fb.watch": "Facebook",
        "x.com": "X",
        "twitter.com": "X",
        "twitch.tv": "Twitch",
        "clips.twitch.tv": "Twitch",
        "snapchat.com": "Snapchat",
        "reddit.com": "Reddit",
        "vimeo.com": "Vimeo",
        "dailymotion.com": "Dailymotion",
        "dai.ly": "Dailymotion",
        "rumble.com": "Rumble",
        "odysee.com": "Odysee",
        "bilibili.tv": "Bilibili",
        "pinterest.com": "Pinterest",
        "pin.it": "Pinterest",
        "linkedin.com": "LinkedIn",
        "weibo.com": "Weibo",
        "tumblr.com": "Tumblr",
    }
    
    for domain, platform in platform_map.items():
        if domain in url_lower:
            return platform
            
    return "Other"


def sanitize_filename(name: str) -> str:
    """
    Sanitize a string to be safe for use as a filename/directory name.
    
    Args:
        name: String to sanitize
        
    Returns:
        str: Sanitized string safe for filesystem
    """
    if not name or name.strip() == "":
        return "Unknown"
        
    # Remove/replace characters that are problematic in filenames
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, "_")
    
    # Remove leading/trailing dots and spaces
    name = name.strip(". ")
    
    # Limit length to reasonable filesystem limits
    if len(name) > 100:
        name = name[:100]
        
    # Ensure we don't end up with empty string
    return name if name else "Unknown"


def get_organized_download_path(url: str, info: Optional[Dict[str, Any]] = None, 
                               uploader_override: Optional[str] = None) -> str:
    """
    Generate organized download path based on platform and uploader.
    
    Args:
        url: Video URL
        info: Video metadata from yt-dlp (optional)
        uploader_override: Override uploader name (for Instagram)
        
    Returns:
        str: Organized download directory path
    """
    # Check if organization is enabled
    if not config.get("organize_downloads", False):
        return download_directory
        
    platform = detect_platform_from_url(url)
    
    # Extract uploader/author name
    uploader = "Unknown"
    if uploader_override:
        uploader = uploader_override
    elif info:
        uploader = info.get("uploader", info.get("channel", "Unknown"))
    
    # Sanitize the uploader name for filesystem
    uploader = sanitize_filename(uploader)
    
    # Create organized path
    organized_path = os.path.join(download_directory, platform, uploader)
    
    # Create directory if it doesn't exist
    os.makedirs(organized_path, exist_ok=True)
    
    return organized_path


# ---------------------------------
# Format Display
# ---------------------------------
def print_format_table(info: Dict[str, Any]) -> None:
    """
    Display available video formats in a formatted table.

    Args:
        info: Video information dictionary from yt-dlp
    """
    formats = info.get("formats", [])
    table_data = []

    for fmt in formats:
        # Skip non-downloadable formats
        if fmt.get("vcodec") == "none" and fmt.get("acodec") == "none":
            continue

        fmt_id = fmt.get("format_id", "")
        ext = fmt.get("ext", "")
        resolution = _get_resolution_string(fmt)
        fps = fmt.get("fps", "")
        filesize_str = _get_filesize_string(fmt.get("filesize", 0))
        vcodec = fmt.get("vcodec", "")
        acodec = fmt.get("acodec", "")
        note = fmt.get("format_note", "")

        # Color format ID
        fmt_id_colored = f"\033[1;32m{fmt_id}\033[0m"

        table_data.append(
            [fmt_id_colored, ext, resolution, fps, filesize_str, vcodec, acodec, note]
        )

    # Create colored headers
    headers = [
        f"\033[1;33m{header}\033[0m"
        for header in [
            "ID",
            "EXT",
            "RESOLUTION",
            "FPS",
            "SIZE",
            "VCODEC",
            "ACODEC",
            "NOTE",
        ]
    ]

    print("\n\033[1;36mAvailable formats:\033[0m")
    print(tabulate(table_data, headers=headers, tablefmt="fancy_grid"))


def _get_resolution_string(fmt: Dict[str, Any]) -> str:
    """Get resolution string from format info."""
    width = fmt.get("width")
    height = fmt.get("height")
    if height:
        return f"{width or ''}x{height}"
    return "audio"


def _get_filesize_string(filesize: Optional[int]) -> str:
    """Convert filesize to human-readable string."""
    if filesize and filesize > 0:
        return f"{filesize / (1024 * 1024):.2f} MB"
    return "-"


# -----------------------------------------------------------
# Download Functions for Youtube, TikTok and other platforms
# -----------------------------------------------------------
def download_youtube_or_tiktok_video(url: str) -> None:
    """
    Download a video from supported platforms using yt-dlp.

    Args:
        url: Video URL to download
    """
    if not is_valid_platform_url(url, SUPPORTED_DOMAINS):
        print("\n\033[1;31mInvalid URL. Please enter a valid URL.\033[0m")
        print(f"\033[1;31mSupported platforms: {WEBSITE}/supported-platforms\033[0m")
        return

    ensure_ffmpeg()
    ensure_internet_connection()

    try:
        # Extract video information
        with yt_dlp.YoutubeDL({"listformats": False}) as ydl:
            info = ydl.extract_info(url, download=False)

        _display_video_info(info)

        # Determine download format
        format_choice = _get_format_choice(info)

        # Prepare download options
        ydl_opts = _prepare_download_options(info, format_choice, url)

        # Perform download
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            
        # Post-process metadata files
        _process_downloaded_metadata(url, info)
        
        log_download(url, "Success")
        print(
            f"\n\033[1;32mDownloaded successfully:\033[0m {info.get('title', 'Unknown')}"
        )

    except Exception as e:
        log_download(url, f"Failed: {str(e)}")
        logging.error(f"Error downloading video from {url}: {str(e)}", exc_info=True)
        print(f"\033[1;31mError downloading video:\033[0m {str(e)}")


def _display_video_info(info: Dict[str, Any]) -> None:
    """Display video metadata information."""
    title = info.get("title", "Unknown Title")
    uploader = info.get("uploader", "Unknown Uploader")
    upload_date = info.get("upload_date", "Unknown Date")

    # Format upload date
    upload_date_formatted = upload_date
    if upload_date != "Unknown Date":
        try:
            upload_date_formatted = datetime.strptime(upload_date, "%Y%m%d").strftime(
                "%B %d, %Y"
            )
        except ValueError:
            pass

    print("\n\033[1;36mVideo Details:\033[0m")
    print(f"\033[1;33mTitle:\033[0m {title}")
    print(f"\033[1;33mUploader:\033[0m {uploader}")
    print(f"\033[1;33mUpload Date:\033[0m {upload_date_formatted}")


def _get_format_choice(info: Dict[str, Any]) -> str:
    """Get format choice from user or config."""
    preferred_format = config.get("default_format", "show_all").lower()

    if preferred_format == "show_all":
        print_format_table(info)
        return input(
            "\nEnter format ID to download (or type 'mp3' for audio only): "
        ).strip()

    # Map friendly format names to yt-dlp format strings
    friendly_format_map = {
        "360p": "bestvideo[height<=360]+bestaudio/best",
        "480p": "bestvideo[height<=480]+bestaudio/best",
        "720p": "bestvideo[height<=720]+bestaudio/best",
        "1080p": "bestvideo[height<=1080]+bestaudio/best",
        "1440p": "bestvideo[height<=1440]+bestaudio/best",
        "2160p": "bestvideo[height<=2160]+bestaudio/best",
        "4320p": "bestvideo[height<=4320]+bestaudio/best",
        "mp3": "mp3",
        "best": "bestvideo+bestaudio/best",
    }

    return friendly_format_map.get(preferred_format, preferred_format)


def _prepare_download_options(info: Dict[str, Any], choice: str, url: str) -> Dict[str, Any]:
    """Prepare yt-dlp download options based on format choice."""
    title = info.get("title", "Unknown")
    
    # Get organized download path
    organized_path = get_organized_download_path(url, info)
    filename_base = get_unique_filename(os.path.join(organized_path, title))

    # Base options for all downloads
    base_options = {
        "noplaylist": True,
    }
    
    # Add metadata options if enabled
    if should_download_metadata():
        base_options["writeinfojson"] = True
        
    # Add comment options if enabled
    if should_download_comments():
        base_options["writecomments"] = True
        base_options["getcomments"] = True
        # Comment limits are handled at the extractor level
        max_comments = str(get_max_comments())
        base_options["extractor_args"] = {
            "youtube": {"max_comments": [max_comments], "comment_sort": ["top"]},
            "tiktok": {"max_comments": [max_comments]},
        }
        
    # Add subtitle options if enabled
    if should_download_subtitles():
        base_options["writesubtitles"] = True
        base_options["writeautomaticsub"] = True

    if choice == "mp3":
        mp3_options = {
            "format": "bestaudio/best",
            "outtmpl": os.path.join(organized_path, f"{title}.%(ext)s"),
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": config.get("mp3_quality", "192"),
                }
            ],
        }
        mp3_options.update(base_options)
        return mp3_options
    else:
        # Handle video-only formats by auto-merging with audio
        selected_fmt = next(
            (f for f in info.get("formats", []) if f.get("format_id") == choice),
            None,
        )

        if selected_fmt and selected_fmt.get("acodec") in ["none", None, ""]:
            print(f"\n\033[1;33mNote:\033[0m Selected format '{choice}' has no audio.")
            print(f"\033[1;32mAuto-fix:\033[0m Merging with best available audio.")
            choice = f"{choice}+bestaudio"

        video_options = {
            "format": choice,
            "outtmpl": f"{filename_base}.%(ext)s",
            "merge_output_format": "mp4",
        }
        video_options.update(base_options)
        return video_options


# ---------------------------------
# Download Functions for Instagram
# ---------------------------------
def download_instagram_post(url: str) -> None:
    """
    Download an Instagram post using instaloader.

    Args:
        url: Instagram post URL
    """
    if not is_valid_platform_url(url, INSTAGRAM_DOMAINS):
        print("\n\033[1;31mInvalid URL. Please enter a valid Instagram URL.\033[0m")
        return

    ensure_internet_connection()

    try:
        # Get organized download path first  
        shortcode = _extract_instagram_shortcode(url)

        if not shortcode:
            print("\n\033[1;31mCould not extract shortcode from URL.\033[0m")
            log_download(url, "Failed: Invalid URL format")
            return

        # Create a temporary loader to get post info
        temp_loader = instaloader.Instaloader()
        post = instaloader.Post.from_shortcode(temp_loader.context, shortcode)
        
        # Get organized download path using Instagram username
        uploader = post.owner_username
        organized_path = get_organized_download_path(url, uploader_override=uploader)
        
        # Create loader with organized path and metadata options
        loader = instaloader.Instaloader(
            dirname_pattern=organized_path,
            filename_pattern="{date_utc}_UTC",
            save_metadata=should_download_metadata(),
            download_comments=should_download_comments(),
            download_geotags=True,
            max_connection_attempts=3
        )
        
        loader.download_post(post, target="")

        log_download(url, "Success")
        print(f"\n\033[1;32mDownloaded Instagram post successfully:\033[0m {url}")

    except Exception as e:
        log_download(url, f"Failed: {str(e)}")
        logging.error(f"Instagram download error for {url}: {str(e)}")
        print(f"\033[1;31mError downloading Instagram post:\033[0m {str(e)}")


def extract_instagram_video_mp3(url: str) -> None:
    """
    Download Instagram video and convert to MP3.

    Args:
        url: Instagram video URL
    """
    if not is_valid_platform_url(url, INSTAGRAM_DOMAINS):
        print(
            "\n\033[1;31mError: This feature only supports Instagram video URLs.\033[0m"
        )
        log_download(url, "Failed: Invalid Instagram URL")
        return

    ensure_internet_connection()

    shortcode = _extract_instagram_shortcode(url)
    if not shortcode:
        print("\n\033[1;31mError: Could not extract shortcode from URL.\033[0m")
        log_download(url, "Failed: Invalid URL format")
        return

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            loader = instaloader.Instaloader(
                dirname_pattern=temp_dir, 
                save_metadata=should_download_metadata(), 
                download_comments=should_download_comments(),
                download_geotags=True
            )

            post = instaloader.Post.from_shortcode(loader.context, shortcode)

            if not post.is_video:
                print("\n\033[1;31mThis post is not a video.\033[0m")
                log_download(url, "Failed: Not a video post")
                return

            print("Downloading video...")
            loader.download_post(post, target=shortcode)

            # Find downloaded video file
            video_path = _find_video_file(temp_dir)
            if not video_path:
                print("\n\033[1;31mVideo file not found after download.\033[0m")
                log_download(url, "Failed: Video file not found")
                return

            ensure_ffmpeg()

            # Get organized download path using Instagram username
            uploader = post.owner_username
            organized_path = get_organized_download_path(url, uploader_override=uploader)
            
            # Convert to MP3
            mp3_path = os.path.join(organized_path, f"instagram_{shortcode}.mp3")
            _convert_video_to_mp3(video_path, mp3_path)

            print(f"\n\033[1;32mDownloaded and converted successfully:\033[0m {url}")
            log_download(url, "Success")

    except Exception as e:
        print(f"\033[1;31mError: {e}\033[0m")
        log_download(url, f"Failed: {str(e)}")
        logging.error(f"Instagram MP3 extract error for {url}: {str(e)}")


def _extract_instagram_shortcode(url: str) -> Optional[str]:
    """Extract shortcode from Instagram URL."""
    if "/reel/" in url:
        return url.split("/reel/")[1].split("/")[0]
    elif "/p/" in url:
        return url.split("/p/")[1].split("/")[0]
    elif "/tv/" in url:
        return url.split("/tv/")[1].split("/")[0]
    return None


def _find_video_file(directory: str) -> Optional[str]:
    """Find the first .mp4 file in the directory."""
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".mp4"):
                return os.path.join(root, file)
    return None


def _convert_video_to_mp3(video_path: str, mp3_path: str) -> None:
    """Convert video file to MP3 using FFmpeg."""
    print("Extracting MP3...")
    subprocess.run(
        [
            "ffmpeg",
            "-i",
            video_path,
            "-vn",
            "-ab",
            f"{mp3_quality}k",
            "-ar",
            "44100",
            "-y",
            mp3_path,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
    )


# -------------------------
# Batch Download Instagram
# -------------------------
def batch_download_from_file(file_path: str) -> None:
    """
    Read URLs from a text file and download them concurrently.

    Args:
        file_path: Path to file containing URLs (one per line)
    """
    ensure_internet_connection()

    if not os.path.exists(file_path):
        print(f"\n\033[1;31mFile not found: {file_path}\033[0m")
        return

    print(f"Reading URLs from {file_path}...")

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            urls = [line.strip() for line in file.readlines() if line.strip()]
    except IOError as e:
        print(f"\033[1;31mError reading file: {e}\033[0m")
        logging.error(f"Error reading batch file {file_path}: {e}")
        return

    if not urls:
        print("\033[1;31mNo URLs found in the file.\033[0m")
        return

    print(f"Found {len(urls)} URLs. Starting batch download...")

    with ThreadPoolExecutor(max_workers=3) as executor:
        list(
            tqdm(
                executor.map(download_instagram_post, urls),
                total=len(urls),
                desc="Instagram Batch",
            )
        )

    print("\n\033[1;32mBatch download complete.\033[0m")


# ---------------------------------
# Authenticated Content Access
# ---------------------------------
def download_instagram_saved_posts(max_count: int = 50) -> None:
    """Download user's saved Instagram posts."""
    if not is_instagram_authenticated():
        print(colored("❌ Instagram authentication required.", "red"))
        print(colored("Run the tool and select 'Instagram Authentication Setup' first.", "yellow"))
        return
    
    try:
        print(colored(f"\n📥 Downloading your {max_count} most recent saved posts...", "cyan"))
        
        loader = create_authenticated_instaloader()
        username = get_instagram_credentials()[0]
        
        # Configure loader for organized downloads
        config = load_config()
        if config.get("organize_downloads", True):
            base_path = config.get("download_directory", "media")
            organized_path = f"{base_path}/Instagram/{username}/Saved"
            loader.dirname_pattern = organized_path
        
        # Get user profile and saved posts
        try:
            profile = instaloader.Profile.from_username(loader.context, username)
        except Exception as e:
            error_msg = str(e).lower()
            if "404" in error_msg or "not found" in error_msg:
                print(colored(f"❌ Instagram user '{username}' not found.", "red"))
                print(colored("   → Check if the username is correct.", "yellow"))
                print(colored("   → Make sure it's your Instagram username, not display name.", "yellow"))
            elif "401" in error_msg or "unauthorized" in error_msg:
                print(colored("❌ Access denied by Instagram.", "red"))
                print(colored("   → Instagram may have detected automated access.", "yellow"))
                print(colored("   → Try logging into Instagram in your browser first.", "yellow"))
                print(colored("   → Wait a few hours before trying again.", "yellow"))
            else:
                print(colored(f"❌ Failed to get Instagram profile: {e}", "red"))
            return
            
        saved_posts = profile.get_saved_posts()
        
        count = 0
        for post in saved_posts:
            if count >= max_count:
                break
            
            try:
                loader.download_post(post, target=f"{username}_saved")
                print(colored(f"✅ Downloaded saved post {count + 1}/{max_count}", "green"))
                log_download(f"https://instagram.com/p/{post.shortcode}/", "Success")
                count += 1
            except Exception as e:
                print(colored(f"❌ Failed to download saved post: {e}", "red"))
                log_download(f"https://instagram.com/p/{post.shortcode}/", "Failed")
        
        print(colored(f"\n✅ Downloaded {count} saved posts!", "green"))
        
    except Exception as e:
        print(colored(f"❌ Error downloading saved posts: {e}", "red"))


def download_instagram_saved_posts_browser(max_count: int = 50) -> None:
    """Download Instagram saved posts using browser automation."""
    if not SELENIUM_AVAILABLE:
        print(colored("❌ Browser automation not available.", "red"))
        print(colored("Install selenium: pip install selenium webdriver-manager", "yellow"))
        return
        
    try:
        print(colored(f"\n🌐 Starting browser automation for Instagram saved posts...", "cyan"))
        print(colored("This will open a browser window - please don't close it manually.", "yellow"))
        
        # Setup browser
        driver = _setup_instagram_browser()
        if not driver:
            return
            
        try:
            # Navigate to Instagram and handle login
            print(colored("📱 Navigating to Instagram...", "cyan"))
            driver.get("https://www.instagram.com")
            
            # Wait for user to log in manually
            print(colored("\n🔐 Please log into Instagram in the browser window.", "yellow"))
            print(colored("After logging in, press Enter here to continue...", "yellow"))
            input()
            
            # Get username from current URL or profile
            print(colored("🔍 Getting your Instagram username...", "cyan"))
            username = _get_instagram_username_from_browser(driver)
            if not username:
                print(colored("❌ Could not auto-detect your Instagram username.", "yellow"))
                username = input("Please enter your Instagram username: ").strip()
                if not username:
                    print(colored("❌ Username is required.", "red"))
                    return
                # Remove @ if provided
                if username.startswith('@'):
                    username = username[1:]
                
            print(colored(f"✅ Detected username: {username}", "green"))
            
            # Navigate to saved posts
            print(colored("📥 Navigating to saved posts...", "cyan"))
            saved_url = f"https://www.instagram.com/{username}/saved/all-posts/"
            driver.get(saved_url)
            
            # Wait for saved posts to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "article"))
            )
            
            # Get saved post links
            post_links = _extract_instagram_post_links(driver, max_count)
            
            if not post_links:
                print(colored("❌ No saved posts found.", "red"))
                return
                
            print(colored(f"✅ Found {len(post_links)} saved posts to download.", "green"))
            
            # Download each post using yt-dlp
            _download_instagram_posts_with_ytdlp(post_links)
            
        finally:
            driver.quit()
            
    except Exception as e:
        print(colored(f"❌ Browser automation failed: {e}", "red"))
        print(colored("You can try the API method if this doesn't work.", "yellow"))


def download_instagram_liked_posts(max_count: int = 50) -> None:
    """Download user's liked Instagram posts."""
    print(colored("⚠️  Note: Instagram doesn't provide direct access to liked posts via API.", "yellow"))
    print(colored("This feature would require extensive browser automation.", "yellow"))
    print(colored("Consider using the saved posts feature instead, or manually save posts you want to download.", "cyan"))


def download_youtube_liked_videos(max_count: int = 50) -> None:
    """Download YouTube liked videos using browser cookies."""
    try:
        print(colored(f"\n❤️  Downloading your {max_count} most recent liked YouTube videos...", "cyan"))
        
        config = load_config()
        browser = get_browser_cookies_path()
        
        # Configure organized downloads
        if config.get("organize_downloads", True):
            base_path = config.get("download_directory", "media")
            organized_path = f"{base_path}/YouTube/Liked"
            os.makedirs(organized_path, exist_ok=True)
        else:
            organized_path = config.get("download_directory", "media")
        
        ydl_opts = {
            'cookiefile': None,
            'cookiesfrombrowser': (browser,),
            'outtmpl': f'{organized_path}/%(title)s.%(ext)s',
            'extract_flat': False,
            'playlistend': max_count,
        }
        
        # Add metadata options if enabled
        if should_download_metadata():
            ydl_opts.update({
                'writeinfojson': True,
                'writedescription': True,
            })
        
        if should_download_comments():
            ydl_opts['writecomments'] = True
        
        if should_download_subtitles():
            ydl_opts.update({
                'writesubtitles': True,
                'writeautomaticsub': True,
            })
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Use the special YouTube liked videos URL
            liked_videos_url = "https://www.youtube.com/playlist?list=LL"
            ydl.download([liked_videos_url])
        
        print(colored(f"✅ Liked videos download completed!", "green"))
        
    except Exception as e:
        print(colored(f"❌ Error downloading liked videos: {e}", "red"))
        print(colored("Make sure you're logged into YouTube in your browser.", "yellow"))


def download_youtube_watch_later(max_count: int = 50) -> None:
    """Download YouTube Watch Later playlist using browser cookies."""
    try:
        print(colored(f"\n⏰ Downloading your {max_count} most recent Watch Later videos...", "cyan"))
        
        config = load_config()
        browser = get_browser_cookies_path()
        
        # Configure organized downloads
        if config.get("organize_downloads", True):
            base_path = config.get("download_directory", "media")
            organized_path = f"{base_path}/YouTube/WatchLater"
            os.makedirs(organized_path, exist_ok=True)
        else:
            organized_path = config.get("download_directory", "media")
        
        ydl_opts = {
            'cookiefile': None,
            'cookiesfrombrowser': (browser,),
            'outtmpl': f'{organized_path}/%(title)s.%(ext)s',
            'extract_flat': False,
            'playlistend': max_count,
        }
        
        # Add metadata options if enabled
        if should_download_metadata():
            ydl_opts.update({
                'writeinfojson': True,
                'writedescription': True,
            })
        
        if should_download_comments():
            ydl_opts['writecomments'] = True
        
        if should_download_subtitles():
            ydl_opts.update({
                'writesubtitles': True,
                'writeautomaticsub': True,
            })
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Use the special YouTube Watch Later URL
            watch_later_url = "https://www.youtube.com/playlist?list=WL"
            ydl.download([watch_later_url])
        
        print(colored(f"✅ Watch Later download completed!", "green"))
        
    except Exception as e:
        print(colored(f"❌ Error downloading Watch Later: {e}", "red"))
        print(colored("Make sure you're logged into YouTube in your browser.", "yellow"))


def download_youtube_subscriptions_feed(max_count: int = 50) -> None:
    """Download recent videos from YouTube subscriptions."""
    try:
        print(colored(f"\n📺 Downloading {max_count} recent videos from your subscriptions...", "cyan"))
        
        config = load_config()
        browser = get_browser_cookies_path()
        
        # Configure organized downloads
        if config.get("organize_downloads", True):
            base_path = config.get("download_directory", "media")
            organized_path = f"{base_path}/YouTube/Subscriptions"
            os.makedirs(organized_path, exist_ok=True)
        else:
            organized_path = config.get("download_directory", "media")
        
        ydl_opts = {
            'cookiefile': None,
            'cookiesfrombrowser': (browser,),
            'outtmpl': f'{organized_path}/%(uploader)s - %(title)s.%(ext)s',
            'extract_flat': False,
            'playlistend': max_count,
        }
        
        # Add metadata options if enabled
        if should_download_metadata():
            ydl_opts.update({
                'writeinfojson': True,
                'writedescription': True,
            })
        
        if should_download_comments():
            ydl_opts['writecomments'] = True
        
        if should_download_subtitles():
            ydl_opts.update({
                'writesubtitles': True,
                'writeautomaticsub': True,
            })
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Use the special YouTube subscriptions feed URL
            subscriptions_url = ":ytsubs"
            ydl.download([subscriptions_url])
        
        print(colored(f"✅ Subscriptions feed download completed!", "green"))
        
    except Exception as e:
        print(colored(f"❌ Error downloading subscriptions feed: {e}", "red"))
        print(colored("Make sure you're logged into YouTube in your browser.", "yellow"))


# ---------------------------------
# Help and Menu Functions
# ---------------------------------
def show_help() -> None:
    """Display comprehensive help information."""
    help_sections = [
        (
            "\n\033[1;36mHow to Use Social Media Downloader:\033[0m",
            [
                "1. \033[1;33mDownload Videos:\033[0m Enter '1' to download public videos.",
                "2. \033[1;33mDownload Instagram Content:\033[0m Enter '2' for Instagram posts, videos, reels.",
                "3. \033[1;33mCheck for Updates:\033[0m Enter '3' to check for software updates.",
                "4. \033[1;33mHelp Menu:\033[0m Enter '4' to display this help guide.",
                "5. \033[1;33mExit the Program:\033[0m Enter '5' to close the application.",
            ],
        ),
        (
            "\033[1;31mImportant Notice:\033[0m",
            [
                "\033[1;31mThis tool only supports downloading public videos.\033[0m",
                "\033[1;31mPrivate, restricted, or non-public content cannot be downloaded.\033[0m",
            ],
        ),
        (
            "\033[1;32mSupported Platforms:\033[0m",
            [f"• Visit: {WEBSITE}/supported-platforms"],
        ),
        (
            "\033[1;32mAdditional Information:\033[0m",
            [
                "• All downloaded files are saved in the 'media' directory.",
                "• Download history and logs are automatically recorded.",
                "• For support, feature requests, or bug reports, contact:",
            ],
        ),
        (
            "\033[1;33mContact Information:\033[0m",
            [
                f"Email: {EMAIL}",
                f"Discord: {DISCORD_INVITE}",
                f"GitHub: {GITHUB_REPO_URL}",
                f"Website: {WEBSITE}",
            ],
        ),
    ]

    for title, items in help_sections:
        print(title)
        for item in items:
            print(item)
        print()


def instagram_menu() -> None:
    """Display Instagram-specific download options."""
    print("\n\033[1;36mInstagram Menu\033[0m")
    options = [
        "1. Download Reel, Video & Pictures",
        "2. Extract MP3 from Instagram Video",
        "3. Batch Download Instagram Posts",
    ]

    for option in options:
        print(option)

    choice = input("\nEnter your choice: ").strip()

    if choice == "1":
        url = input("Enter Instagram URL: ").strip()
        if url:
            download_instagram_post(url)
    elif choice == "2":
        url = input("Enter Instagram video URL: ").strip()
        if url:
            extract_instagram_video_mp3(url)
    elif choice == "3":
        file_path = input("Enter path to text file containing Instagram URLs: ").strip()
        if file_path:
            batch_download_from_file(file_path)
        else:
            print("\033[1;31mExample paths:\033[0m")
            print("Linux: /home/user/batch_links.txt")
            print("Windows: C:\\Users\\user\\batch_links.txt")
    else:
        print("\033[1;31mInvalid choice.\033[0m")


def authentication_setup_menu() -> None:
    """Display authentication setup options."""
    print("\n\033[1;36m⚙️  Authentication Setup\033[0m")
    print("─" * 40)
    
    options = [
        "1. 📸 Instagram Login Setup",
        "2. 🌐 Configure Browser for Cookies (YouTube/TikTok)",
        "3. 📊 View Authentication Status",
        "4. 🔙 Back to Main Menu",
    ]

    for option in options:
        print(option)

    choice = input("\nEnter your choice: ").strip()

    if choice == "1":
        setup_instagram_login()
    elif choice == "2":
        configure_browser_cookies()
    elif choice == "3":
        show_authentication_status()
    elif choice == "4":
        return
    else:
        print("\033[1;31mInvalid choice.\033[0m")


def authenticated_downloads_menu() -> None:
    """Display authenticated download options."""
    print("\n\033[1;36m🔐 Authenticated Downloads\033[0m")
    print("─" * 40)
    
    # Check authentication status
    instagram_auth = is_instagram_authenticated()
    if instagram_auth:
        username = get_instagram_credentials()[0]
        instagram_status = f"✅ ({username})"
    else:
        instagram_status = "❌ Not configured"
    
    print(f"Instagram Authentication: {instagram_status}")
    print(f"Browser Cookies: ✅ (Auto-detected from {get_browser_cookies_path()})")
    print("")
    
    if not instagram_auth:
        print(colored("⚠️  Instagram authentication required for saved posts.", "yellow"))
        print(colored("   Go to 'Authentication Setup' → 'Instagram Login Setup' first.", "yellow"))
        print("")
    
    options = [
        "1. 📥 Download Instagram Saved Posts (API)",
        "2. 🌐 Download Instagram Saved Posts (Browser)",
        "3. ❤️  Download Instagram Liked Posts",
        "4. ❤️  Download YouTube Liked Videos", 
        "5. ⏰ Download YouTube Watch Later",
        "6. 📺 Download YouTube Subscriptions Feed",
        "7. 🔙 Back to Main Menu",
    ]

    for option in options:
        print(option)

    choice = input("\nEnter your choice: ").strip()

    if choice == "1":
        if not instagram_auth:
            print(colored("❌ Instagram authentication required. Please set it up first.", "red"))
            return
        try:
            count = int(input("Enter number of posts to download (default 50): ") or "50")
            download_instagram_saved_posts(count)
        except ValueError:
            print(colored("❌ Invalid number. Using default 50.", "yellow"))
            download_instagram_saved_posts(50)
    elif choice == "2":
        try:
            count = int(input("Enter number of posts to download (default 50): ") or "50")
            download_instagram_saved_posts_browser(count)
        except ValueError:
            print(colored("❌ Invalid number. Using default 50.", "yellow"))
            download_instagram_saved_posts_browser(50)
    elif choice == "3":
        download_instagram_liked_posts()
    elif choice == "4":
        try:
            count = int(input("Enter number of videos to download (default 50): ") or "50")
            download_youtube_liked_videos(count)
        except ValueError:
            print(colored("❌ Invalid number. Using default 50.", "yellow"))
            download_youtube_liked_videos(50)
    elif choice == "5":
        try:
            count = int(input("Enter number of videos to download (default 50): ") or "50")
            download_youtube_watch_later(count)
        except ValueError:
            print(colored("❌ Invalid number. Using default 50.", "yellow"))
            download_youtube_watch_later(50)
    elif choice == "6":
        try:
            count = int(input("Enter number of videos to download (default 50): ") or "50")
            download_youtube_subscriptions_feed(count)
        except ValueError:
            print(colored("❌ Invalid number. Using default 50.", "yellow"))
            download_youtube_subscriptions_feed(50)
    elif choice == "7":
        return
    else:
        print("\033[1;31mInvalid choice.\033[0m")


def configure_browser_cookies() -> None:
    """Configure browser for cookie extraction."""
    print("\n\033[1;36mBrowser Configuration for YouTube/TikTok Authentication\033[0m")
    print("─" * 60)
    print("Available browsers:")
    browsers = ["chrome", "firefox", "safari", "edge", "opera"]
    
    for i, browser in enumerate(browsers, 1):
        print(f"{i}. {browser.capitalize()}")
    
    try:
        choice = int(input("\nSelect your browser (1-5): "))
        if 1 <= choice <= len(browsers):
            selected_browser = browsers[choice - 1]
            
            # Update config
            config = load_config()
            config["authentication"]["cookie_browser"] = selected_browser
            _save_config(config)
            
            print(colored(f"✅ Browser set to {selected_browser}!", "green"))
            print(colored("Make sure you're logged into YouTube/TikTok in this browser.", "yellow"))
        else:
            print(colored("❌ Invalid choice.", "red"))
    except ValueError:
        print(colored("❌ Please enter a valid number.", "red"))


def show_authentication_status() -> None:
    """Show current authentication status."""
    print("\n\033[1;36m📊 Authentication Status\033[0m")
    print("─" * 40)
    
    # Instagram status
    instagram_auth = is_instagram_authenticated()
    username = get_instagram_credentials()[0] if instagram_auth else "Not configured"
    instagram_status = "✅ Configured" if instagram_auth else "❌ Not configured"
    
    print(f"Instagram:")
    print(f"  Status: {instagram_status}")
    print(f"  Username: {username}")
    
    # Browser cookies status
    browser = get_browser_cookies_path()
    print(f"\nBrowser Cookies:")
    print(f"  Browser: {browser}")
    print(f"  Status: ✅ Ready (cookies will be extracted automatically)")
    
    # Session directory
    session_dir = get_session_directory()
    print(f"\nSession Storage:")
    print(f"  Directory: {session_dir}")
    print(f"  Exists: {'✅ Yes' if session_dir.exists() else '❌ No'}")
    
    input("\nPress Enter to continue...")


# ---------------------------------
# Main CLI Interface
# ---------------------------------
def main() -> None:
    """Main function for user interaction and CLI interface."""
    try:
        input("\nPress Enter to start the Social Media Downloader...")
        print(f"\033[38;2;255;105;180mWelcome to Social Media Downloader!\033[0m")

        while True:
            _display_main_menu()
            choice = input("\nEnter your choice: ").strip()

            if not choice:
                continue

            if choice == "1":
                url = input("Enter video URL: ").strip()
                if url:
                    download_youtube_or_tiktok_video(url)
            elif choice == "2":
                instagram_menu()
            elif choice == "3":
                authenticated_downloads_menu()
            elif choice == "4":
                authentication_setup_menu()
            elif choice == "5":
                check_for_updates()
            elif choice == "6":
                show_help()
            elif choice == "7":
                print(
                    f"\033[38;2;255;105;180mThank you for using Social Media Downloader!\033[0m"
                )
                sys.exit(0)
            else:
                print("\033[1;31mInvalid choice. Please try again.\033[0m")

    except KeyboardInterrupt:
        print(f"\n\033[38;2;255;105;180mProgram interrupted by user. Goodbye!\033[0m")
        sys.exit(0)
    except Exception as e:
        logging.critical(f"Unexpected error in main: {e}", exc_info=True)
        print(f"\033[1;31mUnexpected error: {e}\033[0m")
        sys.exit(1)


def _display_main_menu() -> None:
    """Display the main menu options."""
    print("\n" + "─" * 60)
    menu_options = [
        "1. Download YouTube/TikTok... etc.",
        "2. Download Instagram",
        "3. 🔐 Authenticated Downloads (Private/Saved/Liked)",
        "4. ⚙️  Authentication Setup",
        "5. Check for updates",
        "6. Help",
        "7. Exit",
    ]

    for option in menu_options:
        print(option)


def cli() -> None:
    """Entry point for the CLI application."""
    main()
