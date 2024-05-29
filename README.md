# Sub-n-Port-Alert
## Simple Subdomain and Port Monitoring Tool

<p align='center'>بسم الله الرحمن الرحيم</p>

This tool is designed to enumerate subdomains (uses crt.sh and Subfinder) and perform port scans (uses Naabu), with the results being reported to a Slack channel.<br/>

In addition, this tool is designed to be used with crontab (or any scheduler tools), allowing users to schedule scans periodically to ensure the user always receives information about new subdomains and their ports within a specified period of time.

---

# Features

- Fetch subdomains from crt.sh and subfinder.
- Validate and combine subdomain lists.
- Perform port scans using naabu.
- Report live hosts and new subdomains to a Slack channel.
- When **rerun (manual or with a scheduler)** after having results: it will fetch subdomains from crt.sh. If new subdomains are found, they will be added to the list and scanned with naabu. The results will also be sent to Slack.

---

# Prerequisites

Ensure the following dependencies are installed:

- Python 3.x
- `requests` library
- `slack_sdk` library
- `subfinder`
- `naabu`

Ensure that subfinder and naabu can be called directly from the command line.

Note: You can install the required Python libraries using:

```bash
pip install requests slack_sdk
```
---

# Configuration

1. **Slack Configuration**:
    - Obtain a Slack API token (`https://api.slack.com/tutorials/tracks/getting-a-token`) and a channel ID where notifications will be sent.
    - Replace `'AAAAAAAAA'` with your Slack token.
    - Replace `'BBBBBBBBB'` with your Slack channel ID.
    - ```python
      slack_token = 'AAAAAAAAA'
      channel_id = 'BBBBBBBBB'
      client = WebClient(token=slack_token)```

2. **JSON Configuration**:
    - Ensure you have a JSON configuration file (`config.json`) with the port scan arguments within the same directory.
    - If you wish to place `config.json` in another directory, don't forget to define the path in the `with open('config.json') as f:` part.
    - The structure should include a `port_arguments` field.
    - Change the value of `port_arguments` to match Naabu's arguments.
    - For example: `-p 33001,31337 -top-ports 100` OR `-p 1337,4444,31337,44444`
    - For detailed instructions, refer to the Naabu documentation at  `https://github.com/projectdiscovery/naabu`.

3. **Target Domains**:
    - Update the `target_domains` list with the domains you wish to monitor.
    - For a single target, put `['targetA.tld']` in the `target_domains`.
    - For multiple targets, put `['targetA.tld', 'targetB.tld']`.

---

# Usage

1. Clone this repository:

```bash
git clone <repository-url>
cd <repository-name>
```

2. Modify the script to include your Slack token, channel ID, the path to the config.json file, and the port value inside config.json.

3. Run the script:

```bash
python3 Sub-n-Port-Alert.py
```

You can explain the usage with crontab as follows:

---

# Usage with Crontab

To use crontab to schedule scans periodically, user can add some changes such as

1. Open crontab for editing with the command:

```bash
crontab -e
```

2. Add a crontab schedule entry with the following format:

```bash
# Run the script every day at 6 AM
0 6 * * * cd /path/to/your/script/directory && /usr/bin/python3 Sub-n-Port-Alert.py
```

Please note that:
- `/path/to/your/script/directory` is the directory where the script is located.
- Users need to navigate to this directory before running the script so that the output of the script will be in the same directory as the script.

3. Replace `/usr/bin/python3` with the path to the Python 3 installation on the system and `/path/to/Sub-n-Port-Alert.py` with the path to the `Sub-n-Port-Alert.py` script on the OS.

4. Be sure to save the changes and exit the crontab editor.

With this entry, the script will run automatically every day at 6 AM. Make sure to adjust the crontab schedule according to your preferences.

---

# Logging

Simple logs are stored in a file named `domain_monitor.log` for each domain being monitored.

---

# License

- This project is licensed under the MIT License. <br/>
- Free to use and modify - for good purposes.
