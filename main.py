from discord.ext import tasks
import requests
import discord
from decimal import Decimal
from coinbase.wallet.client import Client
from coinbase.wallet.error import NotFoundError




class MyClient(discord.Client):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.crypto_dict = {
            'name': [],
            'live_price': [],
            'price_alert_high': [],
            'price_alert_low': [],
            'mute': [],

        }
        self.new_crypto = False
        self.min_1 = True
        self.min_2 = False
        self.min_3 = False
        self.first_run_complete = False
        self.my_background_task.start()
        self.walit = Client('<APIKEY>', '<APIKEY>')
        pop = self.walit.get_accounts()
        for currency in pop.get('data'):
            self.crypto_dict.get('name').append(currency.get('currency'))

    async def on_ready(self):
        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        print('------')

    @tasks.loop(seconds=0.5) # task runs every 60 seconds
    async def my_background_task(self):
        channel = self.get_channel(831227248139829319)
        price_change_channel = self.get_channel(831497226982260746)
        target_price_channel = self.get_channel(832183660421185557)
        for count,crypto in enumerate(self.crypto_dict['name']):
            try:
                data = self.walit.get_buy_price(currency_pair=crypto+'-GBP')
            except NotFoundError:
                self.crypto_dict['name'].pop(count)
                continue
            price = data.get('amount')

            # Try and get previous price, this produces index error on first run

            try:
                previous_price = float(self.crypto_dict["live_price"][count])
                self.crypto_dict["live_price"][count] = price
            except IndexError:
                self.crypto_dict["live_price"].append(price)
                self.crypto_dict["price_alert_high"].append(None)
                self.crypto_dict["price_alert_low"].append(None)
                self.crypto_dict["mute"].append(False)
                self.first_run_complete = True
                continue

            # Add some different logic for smaller value coins

            digits_long = self.figure_out_how_many_digits(str(price))
            chanel =  self.get_channel(831496686051393537)
            if self.crypto_dict['mute'][count] is True:
                continue

            if float(price) > float(previous_price):
                live_price = Decimal(price)
                prev_price = Decimal(previous_price)
                percentage_change = live_price - prev_price
                percentage_change = percentage_change/prev_price * 100

                await price_change_channel.send(crypto + ' has risen to £' + str(price) +'!')
            if float(previous_price) > float(price):
                live_price = Decimal(price)
                prev_price = Decimal(previous_price)
                percentage_change = prev_price - live_price
                percentage_change = percentage_change / live_price * 100

                await price_change_channel.send(crypto + ' has dropped to £' + str(price) +'!')

            try:
                test = float(self.crypto_dict["price_alert_low"][count])
            except TypeError:
                continue

            if float(self.crypto_dict["price_alert_low"][count]) >= float(price):

                # We need to alert the user the crypto has gone to the low they want

                await target_price_channel.send(crypto + ' has dropped to buying price of £' + str(price) + ' @everyone')

            try:
                test = float(self.crypto_dict["price_alert_high"][count])
            except TypeError:
                continue

            if float(self.crypto_dict["price_alert_high"][count]) <= float(price):

                await target_price_channel.send(crypto + ' has risen to a selling price of £' + str(price) + ' @everyone')

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

        if message.content.startswith('$M'):
            crypto_to_set = message.content[3:]
            print(crypto_to_set)
            crypto = ''
            crypto_provided_exists = False
            skipper = False
            for count, char in enumerate(crypto_to_set):
                c = count
                if char == ' ':
                    break
                crypto += char
            if crypto == '':
                skipper = True
                await message.channel.send("Please provide a crypto like so : $M <CRYPTO-NICKNAME>")
            if skipper is not True:
                crypto = crypto.upper()
                print(crypto)
                c = 0
                for count, crypto_in_dict in enumerate(self.crypto_dict['name']):
                    if crypto_in_dict == crypto:
                        crypto_provided_exists = True
                        c = count
                        break

                if crypto_provided_exists is True:
                    self.crypto_dict["mute"][c] = True
                    await message.channel.send("Muted "+crypto+'.')
                else:
                    await message.channel.send("Please provide a valid crypto!")

        if message.content.startswith('$UM'):
            crypto_to_set = message.content[4:]
            crypto = ''
            crypto_provided_exists = False
            skipper = False
            for count, char in enumerate(crypto_to_set):
                c = count
                if char == ' ':
                    break
                crypto += char
            if crypto == '':
                skipper = True
                await message.channel.send("Please provide a crypto like so : $UM <CRYPTO-NICKNAME>")
            if skipper is not True:
                crypto = crypto.upper()
                print(crypto)
                c = 0
                for count, crypto_in_dict in enumerate(self.crypto_dict['name']):
                    if crypto_in_dict == crypto:
                        crypto_provided_exists = True
                        c = count
                        break

                if crypto_provided_exists is True:
                    self.crypto_dict["mute"][c] = False
                    await message.channel.send("Muted "+crypto+'.')
                else:
                    await message.channel.send("Please provide a valid crypto!")


        if message.content.startswith('$SA'):
            crypto_to_set = message.content[4:]
            crypto = ''
            for count, char in enumerate(crypto_to_set):
                c = count
                if char == ' ':
                    break
                crypto += char
            crypto = crypto.upper()
            print(crypto)
            try:
                number_cut = 5 + c
                skip = False
            except UnboundLocalError:
                skip = True
                await message.channel.send("Please specify what crypto")
            if skip is False:
                price_to_alert = message.content[number_cut:]
                print(price_to_alert)
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
                else:
                    await message.channel.send("Please provide a valid crypto")

        if message.content.startswith('$RM'):

            # This will be the remove function

            remainder_of_message = message.content[4:]
            PH_or_PL = remainder_of_message[:2]
            crypto_to_Set = message.content[7:]
            if self.get_crypto_ID(crypto_to_Set) is False:
                await message.channel.send("Please provide a valid crypto")
            else:
                if PH_or_PL == 'PH':

                    ID = self.get_crypto_ID(crypto_to_Set)
                    self.crypto_dict['price_alert_high'][ID] = None
                    await message.channel.send('Removed high price alert for '+ crypto_to_Set)


                if PH_or_PL == 'PL':
                    ID = self.get_crypto_ID(crypto_to_Set)
                    self.crypto_dict['price_alert_low'][ID] = None
                    await message.channel.send('Removed low price alert for ' + crypto_to_Set)
                else:
                    await message.channel.send("Please enter in the format $RM PH/PL <CRYPTO-NAME>")



        if message.content.startswith('$SL'):

            # We want to send the crypto list we are checking to the user

            await message.channel.send('Scanning these cryptos currently : ' + str(self.crypto_dict["name"]))


        if message.content.startswith('$GP'):
            crypto = message.content[4:]
            crypto = crypto.upper()
            if self.get_crypto_ID(crypto) is False:
                await message.channel.send("Please Provide a valid crypto")
            else:
                ID = self.get_crypto_ID(crypto)
                price = self.crypto_dict['live_price'][ID]
                await message.channel.send(crypto + ' Price is : £'+str(price))

    # Returns true or false if the crypto has been logged in system

    def check_if_crypto_exists(self, crypto_to_check):
        for crypto in self.crypto_dict['name']:
            crypto_to_check = str(crypto_to_check)
            crypto = str(crypto)
            if crypto_to_check == crypto:
                return True
        return False


    def get_crypto_ID(self, crypto_to_find):
        for count, crypto in enumerate(self.crypto_dict['name']):
            if crypto_to_find == crypto:
                c = count
                return c
        return False
client = MyClient()
client.run('TOKEN')

