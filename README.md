<div align="center">

# Info‑Car Sniper
Skaner i auto‑przebooker terminów egzaminów praktycznych WORD (Info‑Car)

<!-- Miejsce na odznaki (przykłady poniżej – podmień według potrzeb) -->

<a href="https://www.python.org/"><img alt="Python" src="https://img.shields.io/badge/python-3.10%2B-blue.svg?logo=python"></a>
<a href="https://textual.textualize.io/"><img alt="Textual" src="https://img.shields.io/badge/TUI-Textual-6f42c1?logo=terminal"></a>
<a href="#-kontrybucja-"><img alt="PRs welcome" src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg"></a>
<img alt="License" src="https://img.shields.io/badge/license-%3F-lightgrey">

<p><sup>Języki: <a href="README.md">PL</a> | <a href="README.en.md">EN</a></sup></p>

</div>

<div align="center">

👉 <strong>Uwaga:</strong> aplikacja <em>aktualnie</em> działa wyłącznie jako narzędzie do <strong>przekładania</strong> istniejących terminów — <strong>nie</strong> rezerwuje terminu od zera. <br/>
💡 <em>Chcesz dodać obsługę pełnej rezerwacji?</em> Kontrybucje mile widziane! 🙏✨

</div>

Intuicyjna aplikacja terminalowa, która:
- Loguje się do Info‑Car
- Cyklicznie skanuje terminy i wybiera najwcześniejszy w podanym oknie dat/godzin
- Automatycznie przebookowuje Twoją rezerwację na lepszy termin
- A to wszystko w cenie około $1

## ✨ Najważniejsze funkcje

- Automatyczne rozwiązywanie Turnstile (CapMonster) z licznikami użyć i szacunkowym kosztem
- Wyszukiwanie co ~10 s, wybór najwcześniejszego terminu zgodnego z kryteriami
- Jedno‑klikowe przebookowanie na znaleziony termin (z poziomu TUI)
- Statystyki na żywo w UI:
  - liczba zapytań (All checks)
  - najwcześniejszy kiedykolwiek znaleziony termin
  - aktualnie najwcześniejszy termin
  - ostatnio znaleziony termin
  - użycia Turnstile i szacunkowy koszt
- Zapamiętywanie ustawień w `config.json` (login, hasło, klucz CapMonster, zakres dat i godzin)
- Obsługa proxy – wystarczy dodać plik `proxies.txt` (jedna linia = jeden HTTP(S) proxy URL)
- Wygodne skróty klawiszowe w TUI:
  - Enter – zatwierdzanie pól i logowanie
  - Tab / ↑ ↓ – nawigacja po polach
  - Ctrl+l – wyjście do ekranu logowania
  - Ctrl+c – wyjście z aplikacji


## 📋 Wymagania

- Python 3.10 lub nowszy
- Konto Info‑Car z aktywną rezerwacją praktyczną
- Klucz API do [CapMonster](https://capmonster.cloud/en)
- (Opcjonalnie) lista proxy w `proxies.txt`


## 🛠️ Instalacja i uruchomienie

Poniższe komendy są gotowe do wklejenia w zsh na Linuxie.

```bash
# 1) (Opcjonalnie) stwórz i aktywuj środowisko wirtualne
python3 -m venv .venv
source .venv/bin/activate

# 2) Zainstaluj zależności
pip install -r requirements.txt

# 3) Uruchom aplikację TUI
python main.py
```

Na pierwszym ekranie podaj:
- adres e‑mail i hasło do Info‑Car,
- klucz CapMonster,
- zakres dat (YYYY‑MM‑DD) i godzin (HH:MM).

Aplikacja zapisze te informacje do `config.json`, by kolejne uruchomienia były szybsze (auto‑login).

### 🌐 (Opcjonalnie) Proxy

Dodaj plik `proxies.txt` w katalogu projektu z listą adresów proxy (po jednym na linię), np.:

```
https://user:pass@host:port
https://host2:443
```

Program będzie losowo korzystał z podanych proxy przy zapytaniach.

## ⚖️ Uwaga prawna / etyka

- Narzędzie automatyzuje działania na publicznym serwisie. Korzystaj zgodnie z prawem i regulaminem Info‑Car
- Autorzy i kontrybutorzy nie ponoszą odpowiedzialności za sposób użycia

## 🛠️ Kontrybucja

Chcesz pomóc? Super!
- Otwórz issue z propozycją lub od razu wyślij PR
- Staraj się pisać czytelny kod i krótkie, opisowe commity
- Mile widziane testy i krótkie opisy zmian w PR

## 💙 Dotacje (crypto)

- BTC: `bc1qqj0q5qup8lhsgacaqrhp37gqzq3xph2595dh5u`
- LTC: `ltc1qw03g3enqgkhc0px3lrs47xz3y8g087rvu90nzg`
- ETH: `0x479D4535b8f3a8A83338525FD7dEC1CBbAeED7eD`
- USDC (ERC20): `0x479D4535b8f3a8A83338525FD7dEC1CBbAeED7eD`

Dziękuję za wsparcie! 🙌
