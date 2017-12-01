import discord
import asyncio
import feedparser
import valve.source.a2s
import random
import time

SERVER = "163.172.17.175"
PORT = 30616

LASTMSGTIME = time.time()

client = discord.Client()

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('Invite: https://discordapp.com/oauth2/authorize?client_id={}&scope=bot'.format(client.user.id))
    print('------')

async def background_loop():


    url = "https://rust.facepunch.com/rss/blog/"
    feed = feedparser.parse(url)
    post = feed['entries'][0]

    await client.wait_until_ready()
    channel_chat = client.get_channel("347799017671098369")

    print("Initializing rss check for {}".format(feed['feed']['title']))
    print("Most recent item:\n{}\n{}".format(post['title'], post['link']))
    while not client.is_closed:
        try:
            feed = feedparser.parse(url)
        except:
            await asyncio.sleep(10)
            continue

        if post != feed['entries'][0]:
            post = feed['entries'][0]
            await client.send_message(channel_chat, "NEW POST!\n{}\n{}".format(post['title'], post['link']))
        await asyncio.sleep(60)

@client.event
async def on_message(message):
    global LASTMSGTIME
    channel_chat = client.get_channel("347799017671098369")

    if message.content.startswith('!online') and message.channel == channel_chat and (time.time()-LASTMSGTIME) > 2:
        tmp = await client.send_message(message.channel, 'Getting data...')

        await client.edit_message(tmp, '{}'.format(player_list((SERVER, PORT))))
    elif message.content.startswith('!help') and message.channel == channel_chat and (time.time()-LASTMSGTIME) > 0.5:
        await client.send_message(message.channel, 'I currently have 3 functions:\n* !online - shows online players\n* !lastpost - Shows last Blog post\n* Rust Blog notifications')
    elif message.content.startswith('!lastpost') and message.channel == channel_chat and (time.time()-LASTMSGTIME) > 0.5:
        try:
            url = "https://rust.facepunch.com/rss/blog/"
            feed = feedparser.parse(url)
            post = feed['entries'][0]
            await client.send_message(message.channel, "Newest post:\n{}\n{}".format(post['title'], post['link']))
        except:
            await client.send_message(message.channel, "Blog seems to be unavailable. Please try again later.")
    LASTMSGTIME = time.time()

def player_list(server):
    time.sleep(1.5)
    try:
        server = valve.source.a2s.ServerQuerier(server)
        players = server.players()
        num_players, max_players = server.info()["player_count"], server.info()["max_players"]

    except Exception as e:
        return "Sorry, I failed at getting current server information: {}".format(e)

    if len(players["players"]) > 0:
        templist=[]
        for player in players["players"]:
            templist.append(player["name"])
        returnlist = "{}/{} players: {}".format(num_players, max_players, ', '.join(map(str, templist)))
        return returnlist
    else:
        return random.choice(open('lines').readlines())


client.loop.create_task(background_loop())
client.run('INSERT TOKEN HERE')
