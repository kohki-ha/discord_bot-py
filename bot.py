# imports
import asyncio
import discord
import youtube_dl
import os
from discord.ext import commands, tasks
from discord.voice_client import VoiceClient
from discord.utils import get
from random import choice
from discord.ext.commands.core import Command

youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

# setup
bot = commands.Bot(command_prefix='-')

status = ['.', '. . .', '! ! !']

bot.remove_command('help')

# eventos
@bot.event
async def on_ready():
    change_status.start()
    print("Bot is on!")

@bot.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.channels, name='general')
    await channel.send(f'Welcome {member.mention}!  Ready to jam out? See `?help` command for details!')

## comdandos de musica
@bot.command(name='play', help='This comand plays a song!')
async def play(ctx, url):
    if not ctx.message.author.voice:
        await ctx.send("You are not connected to a voice channel!")
        return

    else:
        channel = ctx.message.author.voice.channel

    await channel.connect()

    server = ctx.message.guild
    voice_channel = server.voice_client

    async with ctx.typing():
        player = await YTDLSource.from_url(url, loop=bot.loop)
        voice_channel.play(player, after=lambda e: print('Player error: %s' % e) if e else None)

    await ctx.send('**Now playing:** {}'.format(player.title))


@bot.command(name='stop', help='This command stops the music and makes the bot leave the voice channel.')
async def stop(ctx):
    voice_client = ctx.message.guild.voice_client
    await voice_client.disconnect()


######################################## test ########################################
## normal comands
@bot.command()
async def r(ctx):
    await ctx.send("||aaaaaa||")

@bot.command(name='ping', help='Show the latency.')
async def ping(ctx):
    await ctx.send(f'**Latency:** {round(bot.latency * 1000)}ms')

@bot.command()
async def pi(ctx):
    await ping.invoke(ctx)

@bot.command()
async def help(ctx):
    await ctx.send('message\n> **_helps_**')

# send private message
@bot.command(name="secret")
async def secret(ctx):
    await ctx.author.send("lalalalallalalala")

# embed comands
@bot.command()
async def notice(ctx, nome, *, frase):
    emb = discord.Embed(title='NOTICE', description=frase, color=0x4284f5) # color pick
    emb.set_image(url='https://media.discordapp.net/attachments/876926397849927711/888293677900898304/96610a8ce6cfe3b54fc34f08f04c273d.png?width=587&height=587')
    emb.set_thumbnail(url='https://media.discordapp.net/attachments/876926397849927711/888293677900898304/96610a8ce6cfe3b54fc34f08f04c273d.png?width=587&height=587')
    emb.set_author(name=nome)
    emb.set_footer(text='footer embed')
    emb.add_field(name='camp1', value='txt 1')
    emb.add_field(name='camp1', value='txt 2', inline=False)
    emb.add_field(name='camp3', value='txt 3')

#    await ctx.send(embed=emb)

# tasks
@tasks.loop(seconds=15)
async def change_status():
    await bot.change_presence(activity=discord.Game(choice(status)))

## inicialização
bot.run('key_here')