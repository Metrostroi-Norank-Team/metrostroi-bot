# -*- coding: utf-8 -*-
import asyncio
import selectors
import discord
import websockets
import os
import json
from datetime import datetime
import pytz

selector = selectors.SelectSelector()
loop = asyncio.SelectorEventLoop(selector)
asyncio.set_event_loop(loop)


# TODO добавить таймер. Запоминать время последнего редактирования каждого сообщения.
#   Если оно превышает минуту, и это вообщение все еще доступно в дискорде, то изменить его на "НЕ ОТВЕЧАЕТ"
# TODO добавить ключ для вебсокета
# TODO сделать, чтобы каждое сообщение дискорде не дрочилось чаще, чем раз в 10 секунд
# TODO баны, анбаны, вызов луастрингов на сервере гмода
# TODO ради дивана сортировка статусов серверов в каждом канале по имени


async def send_server_status_message(json_data):
    data = json.loads(json_data)
    channel = client.get_channel(int(data[0]))
    if not channel:
        print("канал " + data[0] + " не найден")
        return
    if not data[0] in channels_messages_ips.keys():
        channels_messages_ips[data[0]] = {}

    msg = None
    if data[2] in channels_messages_ips[data[0]].keys():
        try:
            msg = await channel.fetch_message(int(channels_messages_ips[data[0]][data[2]]))
        except:
            msg = None

    msgcreated = False
    if not msg:
        msg = await channel.send("ServerInfo")
        if not msg:
            print("не удалось отправить сообщение")
            return
        msgcreated = True
    if msgcreated:
        channels_messages_ips[data[0]][data[2]] = str(msg.id)
        with open("channels_messages_ips.txt", "w", encoding='utf-8') as f:
            f.write(json.dumps(channels_messages_ips))

    if msg:
        embed = discord.Embed(color=0x00ff00)
        fmt = '%d.%m.%Y %H:%M:%S %Z%z'
        loc_dt = pytz.timezone('Europe/Moscow').localize(datetime.now())
        embed.set_footer(text="Актуально на " + loc_dt.strftime(fmt))
        embed.add_field(name="Сервер:", value=data[1], inline=False)
        embed.add_field(name="Карта:", value=data[3], inline=True)
        embed.add_field(name="Вагоны:", value=data[5], inline=True)
        current_player_count = "0"
        players_info = "\n```"
        if len(data) > 6:
            current_player_count = str(len(data[6]))
            for ply in (data[6]):
                players_info = players_info + ('\n' + ply)
        players_info += "\n```"
        embed.add_field(name="Игроки:", value=current_player_count + '/' + data[4] + players_info, inline=False)
        embed.add_field(name="IP:", value=data[2], inline=True)
        embed.add_field(name="Ссылка на подключение:", value="steam://connect/" + data[2], inline=True)
        await msg.edit(content="", embed=embed)


client = discord.Client()

channels_messages_ips_json = None
channels_messages_ips = None

file_mode = 'r' if os.path.isfile('channels_messages_ips.txt') else 'w+'
with open("channels_messages_ips.txt", file_mode, encoding='utf-8') as read_file:
    string = read_file.read()
    if len(string) > 0:
        channels_messages_ips = json.loads(string)
    else:
        channels_messages_ips = {}

botReady = False


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    global botReady
    botReady = True


async def echo(websocket, path):
    if not botReady:
        return
    try:
        async for message in websocket:
            await send_server_status_message(message)
    except:
        None


start_server = websockets.serve(echo, "0.0.0.0", int(os.environ['PORT']))
asyncio.get_event_loop().run_until_complete(start_server)
print("server status websocket started")
# asyncio.get_event_loop().run_forever()

client.run(os.environ['TOKEN'])
