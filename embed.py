#Temporary file, work in progress

#TODO
#Blokada day, night
#Reagowanie na emoji po id
#Naprawa wysyłania sygnałów, lista posiadaczy posążka(Płonący Szał), lepsze pokazywanie następnej postaci, komunikaty przy skipowaniu, night_com
#jedna deaktywacja warunkowa, 2 razy &no(work + unwork), poprawa komunikatów(baza, role), kładzenie frakcji spać po śmierci ostatniego członka
#special keywords in permissions, join special_search with search
#komunikat, że ktoś skończył akcję dla Manitou


import discord

from globals import bot

embed = discord.Embed(title="Głosowanie: Pojedynek", colour=discord.Colour(0x00aaff), description="Masz 1 głos na osobę, która ma **wygrać** pojedynek.\n\n**1, Kuba**\n\n**2, Anioła**\n\n**3, fk**\n\n**4, Wstrzymuję_Się**")

  '''embed.add_field(name="‎", value="**1, Kuba**")
  embed.add_field(name="‎", value="**2, Anioła**", inline=False)
  embed.add_field(name="‎", value="**3, fk**")
  embed.add_field(name="‎", value="**4, Wstrzymuję_Się**", inline=False)'''
  embed.set_footer(text="INSTRUKCJA\nAby zagłosować wyślij tu dowolny wariant dowolnej opcji. Wiele głosów należy oddzielić przecinkami. Wielkość znaków nie ma znaczenia.")


#===================================================================
embed = discord.Embed(colour=discord.Colour(0x7289da), description="‎\n                                             **[🙙 SAMOTNY KOJOT 🙛](https://discord.com/channels/@me/709823969074872402)**\n                                                               **Indianie**\nLorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.")  # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!                   !                   !
  #embed.set_author(name="Manitobot", icon_url="https://cdn.discordapp.com/embed/avatars/4.png")
embed.set_image(url="https://cdn.discordapp.com/embed/avatars/0.png")
embed.set_thumbnail(url="https://cdn.discordapp.com/embed/avatars/2.png")

  #embed.add_field(name="· · · · · · · · · · · · · · · · · · · · · · · · · · · · Miasto · · · · · · · · · · · · · · · · · · · · · · · · · · · ·", value="Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.")
embed.add_field(name="Akcja",value="`&komenda` - Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.",inline=False)
embed.add_field(name="Akcja", value="`&komenda` - Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.")
person = bot.owner_id#
person2 = 596098327280353291
#await get_member(person).send(embed=embed)

#"‎\n                                                           **[🙙 SZERYF 🙛](https://discord.com)**\n                                                                   **Miasto**\nLorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat."


