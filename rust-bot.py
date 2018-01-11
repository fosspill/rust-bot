import asyncio
import random
import time
import os

import discord
import feedparser
import valve.source.a2s

SERVER = "163.172.17.175"
PORT = 30616

pipe_path = "/tmp/pipe2bot"
if not os.path.exists(pipe_path):
    os.mkfifo(pipe_path)


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
    await client.wait_until_ready()
    channel_chat = client.get_channel("347799017671098369")
    server = client.get_server("155794864305471497")
    myself = server.get_member("385874561792737293")

    await client.change_presence(game=discord.Game(name='Rust Configuration'))
    await client.change_nickname(myself, "Trusty Rusty")

    print("On list: {}".format(', '.join(map(str, load_notifications_list()))))
    mentions_string = ""
    for m in load_notifications_list():
        mentions_string = "{}".format(mentions_string) + "<@{}> ".format(m)
    print(mentions_string)
    while not client.is_closed:
        pipe_fd = os.open(pipe_path, os.O_RDONLY | os.O_NONBLOCK)
        with os.fdopen(pipe_fd) as pipe:
            try:
                message = pipe.read()
            except:
                message = False
            if message:
                print("Received: '%s'" % message.strip("\n"))
                for m in load_notifications_list():
                    mentions_string = "{}".format(mentions_string) + "<@{}> ".format(m)
                await client.send_message(channel_chat,
                                              "NEW POST!\n{}\n{}".format(message.strip("\n"), mentions_string))
            await asyncio.sleep(1)
            mentions_string = ""
        await asyncio.sleep(60)


@client.event
async def on_message(message):
    global LASTMSGTIME
    channel_chat = client.get_channel("347799017671098369")
    server = client.get_server("155794864305471497")
    boss = server.get_member("152135474452889601")

    if message.content.startswith('!online') and message.channel == channel_chat and (time.time() - LASTMSGTIME) > 2:
        await client.send_typing(channel_chat)
        await asyncio.sleep(1.5)
        await client.send_message(message.channel, '{}'.format(player_list((SERVER, PORT))))

    elif message.content.startswith('!help') and message.channel == channel_chat and (time.time() - LASTMSGTIME) > 0.5:
        await client.send_message(message.channel,
                                  'I currently have these functions:\n'
                                  '* !online - shows online players\n* !lastpost - Shows last Blog post\n* Rust Blog '
                                  'notifications\n* !mentionme - Notify me when new blog posts are available')

    elif message.content.startswith('!lastpost') and message.channel == channel_chat and (
            time.time() - LASTMSGTIME) > 0.5:
        try:
            url = "https://rust.facepunch.com/rss/blog/"
            feed = feedparser.parse(url)
            post = feed['entries'][0]
            await client.send_message(message.channel, "Newest post:\n{}\n{}".format(post['title'], post['link']))
        except:
            await client.send_message(message.channel, "Blog seems to be unavailable. Please try again later.")

    elif message.content.startswith('!mentionme') and message.channel == channel_chat:
        if save_to_notification_list(message.author.id):
            await client.send_message(message.channel,
                                      "I'll mention you when new blog posts are added <@{}>.".format(message.author.id))
            print("On list: {}".format(', '.join(map(str, load_notifications_list()))))
        else:
            await client.send_message(message.channel, "You are already on the list <@{}>.".format(message.author.id))

    elif message.content.startswith('!potato ') and message.author == boss:
        await client.send_message(channel_chat, message.content.replace("!potato ", ""))

    LASTMSGTIME = time.time()


def player_list(server):
    try:
        server = valve.source.a2s.ServerQuerier(server)
        players = server.players()
        num_players, max_players = server.info()["player_count"], server.info()["max_players"]

    except Exception as e:
        return "Sorry, I failed at getting current server information: {}".format(e)

    if len(players["players"]) > 0:
        templist = []
        for player in players["players"]:
            templist.append(player["name"])
        returnlist = "{}/{} players: {}".format(num_players, max_players, ', '.join(map(str, templist)))
        return returnlist
    else:
        return random.choice(open('lines').readlines())


def save_to_notification_list(user_id):
    list = load_notifications_list()
    if user_id not in list:
        list.append(user_id)
        with open('notification_list', 'w') as f:
            for item in list:
                f.write("{}\n".format(item))
        return True
    else:
        return False


def load_notifications_list():
    with open('notification_list', 'r') as f:
        noti_list = f.read().splitlines()
    return noti_list

def get_token():
    with open('token', 'r') as f:
        return f.readline().strip()


client.loop.create_task(background_loop())
client.run(get_token())
