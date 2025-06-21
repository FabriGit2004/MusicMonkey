import discord
from discord.ext import commands
import yt_dlp
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="*", intents=intents)


@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}")


@bot.command()
async def play(ctx, *, search_query):
    if not ctx.author.voice:
        await ctx.send("❌ ¡Debes estar en un canal de voz!")
        return

    voice_channel = ctx.author.voice.channel
    if ctx.voice_client is None:
        await voice_channel.connect()
    else:
        await ctx.voice_client.move_to(voice_channel)

    ydl_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "default_search": "ytsearch5",
        "noplaylist": True,
        "skip_download": True,
        # 'extract_flat': False,  # No lo pongas o pon False
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(search_query, download=False)

    entries = info.get("entries")
    if not entries:
        await ctx.send("❌ No encontré resultados para tu búsqueda.")
        return

    options = [f"{i+1}. {entry['title']}" for i, entry in enumerate(entries)]
    message = "🎵 Elige una canción (responde con un número 1-5):\n" + "\n".join(
        options
    )
    await ctx.send(message)

    def check(m):
        return (
            m.author == ctx.author and m.channel == ctx.channel and m.content.isdigit()
        )

    try:
        user_reply = await bot.wait_for("message", check=check, timeout=20.0)
        choice = int(user_reply.content) - 1
        if choice < 0 or choice >= len(entries):
            await ctx.send("❌ Opción inválida.")
            return

        ydl_opts_play = {
            "format": "bestaudio/best",
            "quiet": True,
            "noplaylist": True,
            "skip_download": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts_play) as ydl:
            selected_info = ydl.extract_info(entries[choice]["url"], download=False)

        url = selected_info["url"]
        title = selected_info.get("title", "Video de YouTube")

        BASE_DIR = os.path.dirname(os.path.abspath(__file__))

        ffmpeg_path = os.path.join(
            BASE_DIR,
            "ffmpeg-7.1.1-essentials_build/ffmpeg-7.1.1-essentials_build/bin/ffmpeg.exe",
        )

        source = discord.FFmpegOpusAudio(
            url,
            executable=ffmpeg_path,
            before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
        )

        def after_playing(error):
            if error:
                print(f"Error en la reproducción: {error}")
            else:
                print("Reproducción terminada correctamente.")

        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()

        ctx.voice_client.play(source, after=after_playing)
        await ctx.send(f"🎶 Reproduciendo: **{title}**")

    except asyncio.TimeoutError:
        await ctx.send("⏰ Tiempo expirado. Intenta de nuevo.")


@bot.command()
async def stop(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("🔌 Bot desconectado del canal de voz.")


bot.run(TOKEN)
