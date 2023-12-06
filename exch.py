import requests
import json
import time
from termcolor import colored
from tabulate import tabulate

class Exch:
    def __init__(self):
        self.base_url = "https://exch.cx/api"
        self.headers = {"X-Requested-With": "XMLHttpRequest"}

    def get_rates(self):
        response = requests.get(f"{self.base_url}/rates", headers=self.headers)
        return response.json()

    def get_volume(self):
        response = requests.get(f"{self.base_url}/volume", headers=self.headers)
        return response.json()

    def create_order(self, from_currency, to_currency, to_address, refund_address=None, from_amount=None):
        data = {
            "from_currency": from_currency,
            "to_currency": to_currency,
            "to_address": to_address,
            "refund_address": refund_address,
            "from_amount": from_amount
        }
        response = requests.post(f"{self.base_url}/create", headers=self.headers, data=data)
        return response.json()

    def get_order(self, orderid):
        data = {"orderid": orderid}
        response = requests.post(f"{self.base_url}/order", headers=self.headers, data=data)
        return response.json()

def format_colored_text(text, color):
    return f"{colored(text, color)}"

exch = Exch()
volume = exch.get_volume()
rates = exch.get_rates()
coins = ['BTC', 'BTCLN', 'DAI', 'DASH', 'ETH', 'LTC', 'USDC', 'USDT']
usd_prices = {
    coin: 1 if coin in ['USDC', 'USDT', 'DAI'] else round(
        (
            float(rates.get(coin + '_USDC', {}).get('rate', 0)) +
            float(rates.get(coin + '_USDT', {}).get('rate', 0)) +
            float(rates.get(coin + '_DAI', {}).get('rate', 0))
        ) / 3,
        6
    ) for coin in coins
}
usd_prices['XMR'] = round(
    (
        float(rates.get('XMR_USDC', {}).get('rate', 0)) +
        float(rates.get('XMR_USDT', {}).get('rate', 0)) +
        float(rates.get('XMR_DAI', {}).get('rate', 0))
    ) / 3,
    6
)

xmr_to_rates = {k: v for k, v in rates.items() if k.endswith('XMR')}
xmr_from_rates = {k: v for k, v in rates.items() if k.startswith('XMR')}
xmr_code = colored('XMR', 'yellow', attrs=['dark'])

table = []
for k, v in volume.items():
    coin_code = format_colored_text(k, 'red') if k != 'XMR' else colored('XMR', 'yellow', attrs=['dark'])
    colon = format_colored_text(':', 'grey')
    value = format_colored_text(f"{round(float(v['volume']), 6)}", 'white')
    slash = format_colored_text('/', 'grey')
    row = [coin_code + colon + value]
    if k+'_XMR' in xmr_to_rates:
        rate = round(float(xmr_to_rates[k+'_XMR']['rate']), 6)
        row.append(coin_code + slash + xmr_code + colon + format_colored_text(f"{rate}", 'white'))
    else:
        row.append('')
    if 'XMR_'+k in xmr_from_rates:
        rate = round(float(xmr_from_rates['XMR_'+k]['rate']), 6)
        row.append(xmr_code + slash + coin_code + colon + format_colored_text(f"{rate}", 'white'))
    else:
        row.append('')
    table.append(row)

mean_xmr_value = round((float(xmr_from_rates['XMR_USDC']['rate']) + float(xmr_from_rates['XMR_USDT']['rate']) + float(xmr_from_rates['XMR_DAI']['rate'])) / 3, 6)
equals = format_colored_text('==', 'grey')
usd_value = format_colored_text(f"{mean_xmr_value}", 'white')
service_fee_value = format_colored_text(f"{round(0.5, 6)}%", 'white')
service_fee_text = format_colored_text("Service Fee:", 'red')
table.append(['', '', ''])
table.append([f"        {xmr_code} {equals} {usd_value} " + colored("USD", 'green', attrs=['dark']), '', service_fee_text + " " + service_fee_value])

print(tabulate(table, headers=[colored('Volume', 'grey'), colored('ToRates', 'grey'), colored('FromRates', 'grey')]))

print()
swap_pair = input(
    format_colored_text("Enter the swap pair (e.g., ", 'white') +
    colored("XMR", 'yellow', attrs=['dark']) +
    format_colored_text("/", 'grey') +
    format_colored_text("USDC", 'red') +
    format_colored_text(" or ", 'white') +
    format_colored_text("USDC", 'red') +
    format_colored_text("/", 'grey') +
    colored("XMR", 'yellow', attrs=['dark']) +
    format_colored_text("): ", 'white')
)
from_currency, to_currency = swap_pair.split('/')
amount_input = input(
    format_colored_text(f"Enter the amount you want to send (e.g., 1:", 'white') +
    (colored(from_currency, 'yellow', attrs=['dark']) if from_currency == 'XMR' else format_colored_text(from_currency, 'red')) +
    format_colored_text(" or 20:", 'white') +
    colored("USD", 'green', attrs=['dark']) +
    format_colored_text("): ", 'white')
)
amount, currency = amount_input.split(':')
amount = float(amount)
if currency == 'USD':
    from_amount = amount / usd_prices[from_currency]
else:
    from_amount = amount
to_address = input(format_colored_text(f"Enter the address where you want to receive ", 'white') +
    (colored(to_currency, 'yellow', attrs=['dark']) if to_currency == 'XMR' else format_colored_text(to_currency, 'red')) +
    format_colored_text(": ", 'white')
)
refund_address = input(format_colored_text("Enter a refund address (optional, can be left blank): ", 'white'))
order = exch.create_order(from_currency, to_currency, to_address, refund_address, from_amount=from_amount)
order_info = exch.get_order(order['orderid'])
print(f"Send {from_amount} {order_info['from_currency']} to {order_info['from_addr']}")