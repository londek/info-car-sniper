<div align="center">

# Info‑Car Sniper
Scanner and auto‑rebooker for practical exam slots at WORD (Info‑Car)

<!-- Space for badges (examples below – adjust as you like) -->

<a href="https://www.python.org/"><img alt="Python" src="https://img.shields.io/badge/python-3.10%2B-blue.svg?logo=python"></a>
<a href="https://textual.textualize.io/"><img alt="Textual" src="https://img.shields.io/badge/TUI-Textual-6f42c1?logo=terminal"></a>
<a href="#-contribution-"><img alt="PRs welcome" src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg"></a>
<img alt="License" src="https://img.shields.io/badge/license-%3F-lightgrey">

<p><sup>Languages: <a href="README.en.md">EN</a> | <a href="README.md">PL</a></sup></p>

</div>

<div align="center">

👉 <strong>Note:</strong> the app <em>currently</em> only <strong>reschedules</strong> existing exam bookings — it does <strong>not</strong> book from scratch. <br/>
💡 <em>Want full booking support?</em> Contributions are welcome! 🙏✨

</div>

An intuitive terminal app that:
- Logs into Info‑Car
- Periodically scans available slots and picks the earliest within your date/time window
- Automatically rebooks your reservation to a better slot
- And does all that for about $1

## ✨ Key features

- Automatic Turnstile solving (CapMonster) with usage counters and estimated cost
- Polling every ~10s, selecting the earliest slot that matches your criteria
- One‑click rebook from the TUI
- Live stats in the UI:
  - total checks
  - earliest slot ever found
  - current earliest slot
  - last found slot
  - Turnstile usage and estimated cost
- Settings persisted in `config.json` (login, password, CapMonster key, date & time range)
- Proxy support — just add a `proxies.txt` file (one line = one HTTP(S) proxy URL)
- Handy TUI keybindings:
  - Enter — confirm fields and log in
  - Tab / ↑ ↓ — move between fields
  - Ctrl+l — back to login screen
  - Ctrl+c — quit the app


## 📋 Requirements

- Python 3.10 or newer
- Info‑Car account with an active practical exam reservation
- API key for [CapMonster](https://capmonster.cloud/en)
- (Optional) proxy list in `proxies.txt`


## 🛠️ Installation & run

Commands below are ready to paste into zsh on Linux.

```bash
# 1) (Optional) create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2) Install dependencies
pip install -r requirements.txt

# 3) Run the TUI app
python main.py
```

On the first screen, enter:
- your Info‑Car email and password,
- your CapMonster key,
- the date range (YYYY‑MM‑DD) and time range (HH:MM).

The app will save these to `config.json` so subsequent runs are faster (auto‑login).

### 🌐 (Optional) Proxy

Add a `proxies.txt` file in the project directory with a list of proxy URLs (one per line), e.g.:

```
https://user:pass@host:port
https://host2:443
```

The program will randomly use the provided proxies for requests.

## ⚖️ Legal / ethics

- The tool automates actions on a public service. Use it lawfully and in accordance with Info‑Car’s terms.
- Authors and contributors are not responsible for how you use it.

## 🛠️ Contribution

Want to help? Awesome!
- Open an issue with your proposal or send a PR right away
- Keep code readable and commits short and descriptive
- Tests and short PR descriptions are welcome

## 💙 Donations (crypto)

- BTC: `bc1qqj0q5qup8lhsgacaqrhp37gqzq3xph2595dh5u`
- LTC: `ltc1qw03g3enqgkhc0px3lrs47xz3y8g087rvu90nzg`
- ETH: `0x479D4535b8f3a8A83338525FD7dEC1CBbAeED7eD`
- USDC (ERC20): `0x479D4535b8f3a8A83338525FD7dEC1CBbAeED7eD`

Thanks for your support! 🙌
