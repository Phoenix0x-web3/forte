# Phoenix Dev

More info:  
[Telegram Channel](https://t.me/phoenix_w3)  
[Telegram Chat](https://t.me/phoenix_w3_space)

[Инструкция на русcком](https://phoenix-14.gitbook.io/phoenix/proekty/forte)</br>
[Instruction English version](https://phoenix-14.gitbook.io/phoenix/en/projects/forte)


## Forte Protocol
Forte Protocol is a Layer 1 blockchain designed to integrate real-world assets (RWA) into decentralized finance. It enables tokenization, trading, and on-chain management of tangible assets, bridging traditional finance with blockchain infrastructure. The protocol focuses on scalability, security, and interoperability to support institutional-grade RWA applications.


## Functionality
- Galxe register
- Bridge to Gravity network for claim on Galxe
- Galxe quests

## Requirements
- Python version 3.12 
- Private keys EVM
- Proxy (optional)


## Installation
1. Clone the repository:
```
git clone https://github.com/Phoenix0x-web3/forte.git
cd forte
```

2. Install dependencies:
```
python install.py
```

3. Activate virtual environment: </br>

`For Windows`
```
venv\Scripts\activate
```
`For Linux/Mac`
```
source venv/bin/activate
```

4. Run script
```
python main.py
```

## Project Structure
```
forte/
├── data/                   #Web3 intarface
├── files/
|   ├── logs/               # Logs
|   ├── private_keys.txt    # Private keys EVM
|   ├── proxy.txt           # Proxy addresses (optional)
|   ├── reserve_proxy.txt   # Reserve proxy addresses (optional)
|   ├── twitter_tokens.txt  # Twitter tokens
|   ├── reserve_twitter.txt # Reserve twitter tokens (optional)
|   ├── wallets.db          # Database
│   └── settings.yaml       # Main configuration file
├── functions/              # Functionality
└── utils/                  # Utils
```
## Configuration

### 1. files folder
- `private_keys.txt`: Private keys EVM
- `proxy.txt`: One proxy per line (format: `http://user:pass@ip:port`)
- `reserve_proxy.txt`: One proxy per line (format: `http://user:pass@ip:port`)
- `twitter_tokens.txt`: One token per line 
- `reserve_twitter.txt`: One token per line 

### 2. Main configurations
```yaml
# Whether to encrypt private keys
private_key_encryption: true

# Number of threads to use for processing wallets
threads: 1

# Number of retry
retry: 5

#BY DEFAULT: [0,0] - all wallets
#Example: [2, 6] will run wallets 2,3,4,5,6
#[4,4] will run only wallet 4
range_wallets_to_run: [0, 0]

# Whether to shuffle the list of wallets before processing
shuffle_wallets: true

# Working only if range_wallet_to_run = [0,0] 
# BY DEFAULT: [] - all wallets 
# Example: [1, 3, 8] - will run only 1, 3 and 8 wallets
exact_wallets_to_run: []

# Show wallet address in logs
show_wallet_address_logs: false

#Check for github updates
check_git_updates: true

# the log level for the application. Options: DEBUG, INFO, WARNING, ERROR
log_level: INFO

# Delay before running the wallets that don't perform all the actions in the first round (~24 hrs default)
random_pause_wallet_after_all_completion:
  min: 86400
  max: 90000

# Random pause between actions in seconds
random_pause_between_actions:
  min: 30
  max: 120

# Random pause between start wallets in seconds
random_pause_start_wallet:
  min: 0
  max: 60

#Perform automatic replacement from proxy reserve files
auto_replace_proxy: true

#Perform automatic replacement from twitter reserve files
auto_replace_twitter: true

#Network can use for bridge to Gravity, for Galxe quests. Available: ethereum, arbitrum, base, optimism, ink, mode, bsc, op_bnb, polygon, soneium, lisk, unichain, avalanche, zksync, linea
network_for_bridge: [arbitrum, optimism, base]

#Random diaposon for ETH bridge. (0.1$ - 0.5$ in ETH default)
random_eth_for_bridge:
  min: 0.000025
  max: 0.0001

#Use banned Galxe accounts
use_banned_galxe: false
```

## Usage

For your security, you can enable private key encryption by setting `private_key_encryption: true` in the `settings.yaml`. If set to `false`, encryption will be skipped.

On first use, you need to fill in the `private_keys.txt` file once. After launching the program, go to `DB Actions → Import wallets to Database`.

<img src="https://imgur.com/qmUkL9w.png" alt="Preview" width="600"/>

If encryption is enabled, you will be prompted to enter and confirm a password. Once completed, your private keys will be deleted from the private_keys.txt file and securely moved to a local database, which is created in the files folder.

<img src="https://imgur.com/2J87b4E.png" alt="Preview" width="600"/>

If you want to update proxy/twitter/discord/email you need to make synchronize with DB. After you made changes in these files, please choose this option.

<img src="https://imgur.com/lXT6FHn.png" alt="Preview" width="600"/>

Once the database is created, you can start the project by selecting `Forte Protocol → Run All Activities`.

<img src="https://imgur.com/dDU3ETf.png" alt="Preview" width="600"/>





