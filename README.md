# Manitobot
Bot to play [Ktulu](http://cooloo.wikidot.com/e:cooloo) on Discord written in Python 
using [discord.py](http://github.com/Rapptz/discord.py). Current version is bound to one guild and cannot be used to 
lead neither game on other guild (but can be easily modified to do so) nor multiple games at the same time.
All text and help docstrings are written in Polish.

### Some functionalities
* Registering and unregistering guild's members as players or observers by adding proper roles
* Starting game with one of predefined sets or custom set with sending to players name and description of their role 
and to game leader list of players' roles
* Protection against using commands by inappropriate person
* Gameplay elements:
  * Managing Day/Night
  * Controlling access to faction channels
  * Managing player state (dead/alive)
  * Reporting players for searching
  * Challenging players to duels
  * Making duels
  * Votes
  * Statuette giving/holding/searching
  * Revealing players
* Few guild management commands
* Special control panel using Discord's UI components for leading