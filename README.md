# Games Matcher

GamesMatcher is a discord bot which will help you to find commons games between server members and you.

# Privacy concern
This bot collect only data it need to answer to command.
It save in database your discord unique ID, list of games you played and last time you played it.
When you use the `$up` command it can save too the last moment you where available for playing game.
We don't care of everything else.

# Commands
```bash
* up <minutes>     # Notify to the channel you'r up for a game, and the offer expire in <minutes> (30mn by default)
                    # When more than one people use the up command before expiration the bot will each time
                    # show a list of 10(max) common games upped people have in common (ordered by last activity)
                    # The result of this command will be publicly displayed on the channel
* find "game name" # find online members on the server which own the game. (result will be sent to you in private)
* match @user      # Found games in common with the user, ordered by last activity. (result will be sent to you in private)
* import
** steam <steamId> # importing games from steam with your steamID (only in private message)
* privacy           # Only private message commands for control how the bot interact with your data
** status           # Display all Data the bot know about you
** disallow         # on/off switch, allow/disallow the bot from collecting your activity status
** block            # block a member from getting result with your data (find will not include your in result, match command from him will say you have nothing in common)
** unblock          # unblock the member previously blocked
** delete           # delete all data in our database, your list of owned games, block list, and allow/disallow preferences will be erased
* help             # Shows list of commands
* about             # display info about the bot, git repo, version etc
```
# How to made join the bot to your guild server
just click on the link below:
https://discord.com/api/oauth2/authorize?client_id=765820610830925864&permissions=76864&scope=bot

# For Hosts
For connecting the bot to discord you need a discord token see [here](https://www.writebots.com/discord-bot-token/)

To access to STEAM API and allowing import of library from it you need an API key, please see [here to get more info about this]()

To Avoid duplicates and inserting solo games in databases (bc shitty api) the bot need to connect to Igdb.com to get details from the games. Unfortunatly igdb now require a twitch account and to create an application client id/secret see [here for more info about this](https://dev.twitch.tv/docs/authentication)


Once you get all this information create a docker-compose.yml with this in it (change the `dockerfile:` line part depending of your system):
```yaml
version: '3'
services:
    games-matcher-bot:
        build:
            context: ./
            dockerfile: Dockerfile.arm # for raspberry, or Dockerfile.x86 else
        environment:
            DISCORD_TOKEN: <insert your Discord token HERE>
            STEAM_API_KEY: <insert your STEAM API key HERE>
            IGDB_CLIENT_ID: <insert your IGDB_CLIENT_ID HERE>
            IGDB_CLIENT_SECRET: <insert your IGDB_SECRET HERE>
```
