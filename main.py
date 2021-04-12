from discord.ext import tasks
import requests
from bs4 import BeautifulSoup
import discord
from decimal import Decimal


class MyClient(discord.Client):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.crypto_dict = {
            'name': ['Ankr'],
            'live_price': [],
            'price_alert_high': [],
            'price_alert_low': [],
        }
        self.new_crypto = False
        self.my_background_task.start()

    async def on_ready(self):
        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        print('------')

    @tasks.loop(seconds=0.1) # task runs every 60 seconds
    async def my_background_task(self):
        channel = self.get_channel(831227248139829319)
        for count,crypto in enumerate(self.crypto_dict['name']):
            data = self.get_crypto_data(crypto_name=crypto)
            soup = BeautifulSoup(data.content, 'html.parser')
            price = soup.find_all('div', class_="priceValue___11gHJ")[0].get_text()
            price = float(price.strip('£'))

            # Try and get previous price, this produces index error on first run

            try:
                previous_price = float(self.crypto_dict["live_price"][count])
            except IndexError:
                self.crypto_dict["live_price"].append(price)
                self.crypto_dict["price_alert_high"].append(None)
                self.crypto_dict["price_alert_low"].append(None)
                continue

            # Add some different logic for smaller value coins

            digits_long = self.figure_out_how_many_digits(str(price))

            if price > previous_price:
                live_price = Decimal(price)
                prev_price = Decimal(previous_price)
                percentage_change = live_price - prev_price

                await channel.send(crypto + ' has risen by ' + str(percentage_change) +'%!')
            if previous_price > price:
                live_price = Decimal(price)
                prev_price = Decimal(previous_price)
                percentage_change = prev_price - live_price

                await channel.send(crypto + ' has dropped by ' + str(percentage_change) +'%!')

            try:
                test = float(self.crypto_dict["price_alert_low"][count])
            except TypeError:
                continue

            if float(self.crypto_dict["price_alert_low"][count]) >= price:

                # We need to alert the user the crypto has gone to the low they want

                await channel.send(crypto + ' has dropped to buying price of £' + str(price) + ' @everyone')

            if float(self.crypto_dict["price_alert_high"][count]) <= price:

                await channel.send(crypto + ' has risen to a selling price of £' + str(price) + ' @everyone')

    @my_background_task.before_loop
    async def before_my_task(self):
        await self.wait_until_ready()

    def get_crypto_data(self, crypto_name):
        r = requests.session()
        r.get('https://coinmarketcap.com/currencies/' + crypto_name)
        r.cookies.set('currency', 'GBP')
        data = r.get('https://coinmarketcap.com/currencies/' + crypto_name)
        return data

    def figure_out_how_many_digits(self, string):
        c = 0
        for char in string:
            if char == '.':
                break
            c += 1

        return c


    async def on_message(self, message):
        if message.content.startswith('@'):
            # We want to set the new crypto to watch here
            crypto_to_set = message.content[1:]
            self.crypto_dict["name"].append(crypto_to_set)
            self.new_crypto = False
            await message.channel.send("Added " + str(crypto_to_set) + ' to the scanner list!')

        if message.content.startswith('$setalert'):
            crypto_to_set = message.content[10:]
            crypto = ''
            for count, char in enumerate(crypto_to_set):
                c = count
                if char == ' ':
                    break
                crypto += char
            try:
                number_cut = 11 + c
                skip = False
            except UnboundLocalError:
                skip = True
                await message.channel.send("Please specify what crypto")
            if skip is False:
                price_to_alert = message.content[number_cut:]
                crypto_exists = self.check_if_crypto_exists(crypto)
                if crypto_exists is True:
                    for count, crypto_to_check in enumerate(self.crypto_dict["name"]):
                        if crypto_to_check == crypto:
                            count = count
                            break
                    crypto = self.crypto_dict["name"][count]
                    price = self.crypto_dict["live_price"][count]
                    if float(price_to_alert) > float(price):

                        # We know to set this as alert high

                        self.crypto_dict["price_alert_high"][count] = price_to_alert

                        await message.channel.send("Set to alert when "+crypto+' hits £'+str(price_to_alert))

                    else:

                        self.crypto_dict["price_alert_low"][count] = price_to_alert

                        await message.channel.send("Set to alert when " + crypto + ' drops to £' + str(price_to_alert))



        if message.content.startswith('$ShowList'):

            # We want to send the crypto list we are checking to the user

            await message.channel.send('Scanning these cryptos currently : ' + str(self.crypto_dict["name"]))



    # Returns true or false if the crypto has been logged in system

    def check_if_crypto_exists(self, crypto_to_check):
        for crypto in self.crypto_dict['name']:
            crypto_to_check = str(crypto_to_check)
            crypto = str(crypto)
            if crypto_to_check == crypto:
                return True
        return False

client = MyClient()
client.run('token')

