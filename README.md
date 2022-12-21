# Games Matcher

GamesMatcher is a discord bot which will help you to find commons games between server members and you.

# Privacy concern
This bot collect only data it need to answer to command.
It save in database your discord unique ID, list of games you played and last time you played it.
When you use the `$up` command it can save too the last moment you where available for playing game.
We don't care of everything else.

# How to made join the bot to your guild server
just click on the link below:  
https://discord.com/api/oauth2/authorize?client_id=765820610830925864&permissions=76864&scope=bot

# Commands
Commands are split between two type of command: 
## in public channel
* `$up` 30  
    Notify to the channel you'r up for a game, and the offer expire in 30mn (by default)  
    When more than one people use the up command before expiration the bot will each time  
    show a list of 10(max) common games upped people have in common (ordered by last activity)  
    The result of this command will be publicly displayed on the channel
* `$find` "game name"  
    find online members on the server which own the game. (result will be sent to you in private)
* `$lfg` valheim 10  
    Display you're looking for group of 10 persons (including you) for the game "valheim"  
    When the number of players have reacted to the message it will create voice channel with members whom reacted in it  
    The message is deleted after 30mn
* `$match` @user  
    Found games in common with the user, ordered by last activity. (result will be sent to you in private)
* `$help`  
    Shows list of commands
## Private message with the bot
* `$import steam` 875155987545  
    importing games from steam with your steamID (only in private message)
* `$privacy status`  
    Display all Data the bot know about you
* `$privacy disallow`  
    on/off switch, allow/disallow the bot from collecting your activity status
* `$privacy block`  
    block a member from getting result with your data (find will not include your in result, match command from him will say you have nothing in common)
* `$privacy unblock`  
    unblock the member previously blocked
* `$privacy delete`  
    delete all data in our database, your list of owned games, block list, and allow/disallow preferences will be erased
* `$help`  
    Shows list of commands
* `$about`  
    display info about the bot, git repo, version etc



# For Hosts
If you want to host the bot on your server you need to fullfill some steps:  
* For connecting the bot to discord you need a discord token see [here](https://www.writebots.com/discord-bot-token/)
* To access to STEAM API and allowing import of library from it you need an API key, please see [here to get more info about this]()
* Once you get all this information create a docker-compose.yml with this in it (change parts accordingly to previous steps):
```yaml
version: '3'
services:
    games-matcher-bot:
        image: dbuteau/games-matcher:latest
        restart: unless-stopped
        container_name: games-matcher
        environment:
            DISCORD_TOKEN: <insert your Discord token HERE>
            STEAM_API_KEY: <insert your STEAM API key HERE>
```

# thanks to
- https://discordpy.readthedocs.io/en/stable/