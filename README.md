# Games Matcher

GamesMatcher is a discord bot which will help you to find commons games between server members and you.

# Requirements
- Users need an account on https://igdb.com
- Users need to create a list on igdb.com with the game you own. The [igdb exporter]() for [Playnite](https://playnite.link/) can create it for you.
- Users need to give to the bot the link to your igdb.com list (try to make a list with only multiplayers games for better results/performances).

# Commands
```
# As Admin
/gm prefix <prefix> : changing prefix for your guild

# As User
/gm import <url_to_your_igdb_list> : importing your games list from your igdb account 

# return top10 (or less) games owned in common between you and @user, sorted by last played datetime (or release game if bot don't know when you last played games)
/gm @user

# return guild member list which own this game
/gm find "game name"

# return the top 10 last recently games played by every one on the server with collect activated
/gm top10

## Privacy configurations
# disallow bot from answering to command targeting yourself (across all guild). It will disallow bot to collect data from you too
/gm disallow 
# disallow the current guild bot to answering to command targetting you. if the bot is on another not disallowed guild, it will continue to collect data from you
/gm block
# blacklist user from asking about you. Bot continue to collect data from you
/gm block @user
/gm unblock @user : the user is allowed back from asking information about you
/gm delete : will delete all informations the bot know about you (can't be rollback)
```

# Privacy concern
This bot collect your discord unique ID and your in game status to get list of game you recently played.
See privacy commands to control how your data can be collected or used