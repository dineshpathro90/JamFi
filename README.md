```
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
║       JamFi v1.0  — WiFi Deauth Toolkit        ║
║   ⚡  by @mrdineshpathro — authorized only ⚡    ║
╚════════════════════════════════════════════════╝
```
# WiFi Jammer

A Python script to perform deauthentication attacks on WiFi networks.

## Features

*   **Monitor Mode:** Automatically puts the wireless interface into monitor mode.
*   **Network Scanning:** Scans for nearby WiFi networks and displays their ESSID, BSSID, channel, and signal strength.
*   **Deauthentication Attack:** Performs deauthentication attacks on selected WiFi networks.
*   **Multi-threading:** Supports multi-threaded jamming of multiple networks simultaneously.
*   **Configuration:** Loads settings from a `config.ini` file, including scan duration, deauthentication packet count, and retry delay.
*   **Logging:** Logs all actions and errors to a `wifi_jammer.log` file.
*   **Auto Resume:** Automatically resumes attacks after a crash.
*   **Target Selection:** Allows selecting target networks manually or automatically.
*   **Cleanup:** Cleans up temporary files after execution.

## Usage

1.  Run the script as root: `sudo python3 wifi_jammer.py`
2.  Select the wireless interface to use.
3.  The script will scan for nearby WiFi networks.
4.  Select the target networks to attack.
5.  The script will start deauthentication attacks on the selected networks.

## Configuration

The script uses a `config.ini` file to store settings. The following settings are available:

```ini
[Settings]
scan_duration = 10
deauth_packets = 0
retry_delay = 5
auto_select_all = False
log_attacks = True

[Advanced]
cleanup_temp_files = True
show_banner = True
```

## Disclaimer

This script is for educational purposes only. Do not use it to attack networks without permission.

## Running on Kali Linux

To run this script on Kali Linux, you need to install the following dependencies:

*   `aircrack-ng`: This suite of tools is required for WiFi network analysis and deauthentication attacks. You can install it using the following command:

    ```bash
    sudo apt-get update
    sudo apt-get install aircrack-ng
    ```

You also need to ensure that your wireless interface is in monitor mode. You can do this using the following commands:

```bash
sudo airmon-ng start <interface>
```

Replace `<interface>` with the name of your wireless interface (e.g., `wlan0`). This will create a new monitor interface (e.g., `wlan0mon`).

Finally, you need to run the script as root:

```bash
sudo python3 wifi_jammer.py
```

## Author

[mrdineshpathro](https://github.com/mrdineshpathro)
