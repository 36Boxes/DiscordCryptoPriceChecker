from discord.ext import tasks
import requests
from bs4 import BeautifulSoup
import discord


class MyClient(discord.Client):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # an attribute we can access from our task
        self.counter = 0

        self.cryptoToCheck = []
        self.new_crypto = False
        self.crypto_prices = []
        # start the task to run in the background
        self.my_background_task.start()

    async def on_ready(self):
        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        print('------')

    @tasks.loop(seconds=10) # task runs every 60 seconds
    async def my_background_task(self):
        for count,crypto in enumerate(self.cryptoToCheck):
            channel = self.get_channel(830032107135827970) # channel ID goes here
            r = requests.session()
            data = r.get('https://coinmarketcap.com/currencies/'+crypto)
            soup = BeautifulSoup(data.content, 'html.parser')
            s = soup.find_all('div', class_="priceValue___11gHJ")[0].get_text()
            try:
                old_price = self.crypto_prices[count]
                old_price = old_price.strip('$')
                old_price = float(old_price)
                new_price = s.strip('$')
                new_price = float(new_price)
                if new_price > old_price:
                    #We want to inform the user of the change
                self.crypto_prices[count] = s
            except IndexError:
                self.crypto_prices.append(s)
            print(self.crypto_prices)
            print(self.cryptoToCheck)
            await channel.send(crypto + ' Price is : ' + str(s))

    @my_background_task.before_loop
    async def before_my_task(self):
        # wait until the bot logs in
        await self.wait_until_ready()

    async def on_message(self, message):
        if message.content.startswith('$setnew'):
            self.new_crypto = True
            await message.channel.send('Please specify a name!')

        if message.content.startswith('@'):
            if self.new_crypto is True:
                # We want to set the new crypto to watch here
                crypto_to_set = message.content[1:]
                self.cryptoToCheck.append(crypto_to_set)
                self.new_crypto = False
                await message.channel.send("Added " + str(crypto_to_set) + ' to the scanner list!')
            else:
                await message.channel.send("Please Initialise The Change!")

        if message.content.startswith('$Portfolio'):

            # We want to send the crypto list we are checking to the user

            await message.channel.send('Scanning these cryptos currently : ' + str(self.cryptoToCheck))



client = MyClient()
client.run('TOKEN')

