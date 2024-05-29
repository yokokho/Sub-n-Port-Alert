import os
import requests
import json
import threading
import socket
import logging
import subprocess
import re
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Slack Configuration
slack_token = 'AAAAAAAAA'
channel_id = 'BBBBBBBBB'
client = WebClient(token=slack_token)

# Target domain
target_domains = ['target.tld']

# Read the Port Scanning Arguments from config.json
with open('config.json') as f:
    config = json.load(f)

# Parameter for Port Scan
port_arguments = config['port_arguments']

# Function to fetch subdomains via crt.sh
def get_subdomains(domain):
    try:
        req = requests.get(f"https://crt.sh/?q=%.{domain}&output=json")
        req.raise_for_status()
        json_data = json.loads(req.text)
        return set(value['name_value'] for value in json_data)
    except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.RequestException, json.decoder.JSONDecodeError) as e:
        logging.error(f"Error getting subdomains for {domain}: {e}")
        return set()

# Function to fetch subdomains via subfinder
def get_subdomains_subfinder(domain):
    try:
        filename = f'{domain}_initial_subfinder_scan.txt'
        subprocess.run(["subfinder", "-d", domain, "-v", "-all", "-o", filename])
        with open(filename, 'r') as f:
            subdomains = set(line.strip() for line in f)
        return subdomains
    except Exception as e:
        logging.error(f"Error getting subdomains for {domain} using subfinder: {e}")
        return set()

# Function to perform port scan with naabu
def port_scan(domain, subdomain, known_live_hosts):
    filename = f'{domain}_live_host_scan.txt'
    port_arguments_list = port_arguments.split()
    new_live_hosts = set()
    process = subprocess.run(["naabu", "-host", subdomain] + port_arguments_list + ["-silent"], capture_output=True, text=True)
    for line in process.stdout.splitlines():
        host = line.strip()
        if host not in known_live_hosts:
            new_live_hosts.add(host)
    return new_live_hosts

# Function to send a message to Slack
def send_slack_message(domain, live_hosts, new=False):
    sorted_live_hosts = sorted(list(live_hosts))
    message = f"New live hosts detected for {domain}:\n" if new else f"Initial live hosts for {domain}:\n"
    try:
        response = client.chat_postMessage(
            channel=channel_id,
            text=message + "\n".join(sorted_live_hosts)
        )
    except SlackApiError as e:
        logging.error(f"Error sending message: {e.response['error']}")

# Function to check if a subdomain is works
def is_valid_subdomain(subdomain):
    try:
        socket.gethostbyname(subdomain)
        return True
    except socket.gaierror as e:
        logging.error(f"Error resolving {subdomain}: {e}")
        return False

# Function to combine
def combine_and_clean_subdomains(domain):
    filename_crtsh = f'{domain}_initial_scan.txt'
    filename_subfinder = f'{domain}_initial_subfinder_scan.txt'
    filename_combined = f'{domain}_combined_scan.txt'
    
    # Read subdomain from both files
    with open(filename_crtsh, 'r') as f:
        subdomains_crtsh = set(line.strip() for line in f)
    with open(filename_subfinder, 'r') as f:
        subdomains_subfinder = set(line.strip() for line in f)
    
    # Combine subdomains and remove http/https prefixes
    combined_subdomains = subdomains_crtsh.union(subdomains_subfinder)
    cleaned_subdomains = [re.sub(r'^(\*\.)?(https?://)?', '', subdomain) for subdomain in combined_subdomains]
    
    # Sort and remove duplicates
    unique_sorted_subdomains = sorted(set(cleaned_subdomains))
    
    # Read old subdomains from the combined file it it exists
    old_subdomains = set()
    if os.path.exists(filename_combined):
        with open(filename_combined, 'r') as f:
            old_subdomains = set(line.strip() for line in f)
    
    # Write new subdomains to the file
    with open(filename_combined, 'w') as f:
        for subdomain in unique_sorted_subdomains:
            f.write(f"{subdomain}\n")
    
    # Check new subdomains
    new_subdomains = set(unique_sorted_subdomains) - old_subdomains
    if new_subdomains:
        send_slack_message(domain, new_subdomains, new=True)

# Function to monitor subdomains
def monitor_subdomains(domain):
    logging.basicConfig(filename=f'{domain}_monitor.log', level=logging.INFO)
    filename_crtsh = f'{domain}_initial_scan.txt'
    filename_subfinder = f'{domain}_initial_subfinder_scan.txt'
    filename_live_host = f'{domain}_live_host_scan.txt'
    known_subdomains_crtsh = set()
    known_subdomains_subfinder = set()
    known_live_hosts = set()
    if os.path.exists(filename_crtsh):
        with open(filename_crtsh, 'r') as f:
            known_subdomains_crtsh = set(line.strip() for line in f)
    if os.path.exists(filename_subfinder):
        with open(filename_subfinder, 'r') as f:
            known_subdomains_subfinder = set(line.strip() for line in f)
    if os.path.exists(filename_live_host):
        with open(filename_live_host, 'r') as f:
            known_live_hosts = set(line.strip() for line in f)

    current_subdomains_crtsh = get_subdomains(domain)
    current_subdomains_subfinder = get_subdomains_subfinder(domain)
    new_subdomains_crtsh = current_subdomains_crtsh - known_subdomains_crtsh
    new_subdomains_subfinder = current_subdomains_subfinder - known_subdomains_subfinder

    known_subdomains_crtsh.update(new_subdomains_crtsh)
    known_subdomains_subfinder.update(new_subdomains_subfinder)

    with open(filename_crtsh, 'w') as f:
        for subdomain in sorted(known_subdomains_crtsh):
            f.write(f"{subdomain}\n")
    with open(filename_subfinder, 'w') as f:
        for subdomain in sorted(known_subdomains_subfinder):
            f.write(f"{subdomain}\n")

    combine_and_clean_subdomains(domain)

    new_subdomains = new_subdomains_crtsh.union(new_subdomains_subfinder)
    new_live_hosts = set()
    for subdomain in new_subdomains:
        current_live_hosts = port_scan(domain, subdomain, known_live_hosts)
        new_live_hosts.update(current_live_hosts - known_live_hosts)
    if new_live_hosts:
        known_live_hosts.update(new_live_hosts)
        with open(filename_live_host, 'w') as f:
            for host in sorted(known_live_hosts):
                f.write(f"{host}\n")
        send_slack_message(domain, new_live_hosts, new=True)

for domain in target_domains:
    threading.Thread(target=monitor_subdomains, args=(domain,)).start()
