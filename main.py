import asyncio
import time
import logging

import discord
from discord.ext import commands

from config import (
    DISCORD_TOKEN,
    VOICE_CHANNEL_ID,
    CONTROL_CHANNEL_ID,
    PC_TIMEOUT,
)


# ==========================================================
# LOGGING
# ==========================================================

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
)

log = logging.getLogger("shuvi-vps")


# ==========================================================
# INTENTS
# ==========================================================

intents = discord.Intents.default()

intents.guilds = True
intents.voice_states = True
intents.messages = True
intents.message_content = True


bot = commands.Bot(
    command_prefix="!",
    intents=intents,
)


# ==========================================================
# СОСТОЯНИЕ
# ==========================================================

last_pc_heartbeat = 0.0

vps_voice_connected = False

monitor_task = None


# ==========================================================
# ПРОВЕРКА PC
# ==========================================================

def is_pc_online() -> bool:

    if last_pc_heartbeat == 0:
        return False

    elapsed = time.monotonic() - last_pc_heartbeat

    return elapsed < PC_TIMEOUT


# ==========================================================
# ПОДКЛЮЧЕНИЕ VPS К VOICE
# ==========================================================

async def connect_vps_to_voice():

    global vps_voice_connected

    # Если PC уже работает — VPS НЕ подключается
    if is_pc_online():

        log.info(
            "🟢 PC ONLINE — VPS не подключается к Voice."
        )

        return

    channel = bot.get_channel(VOICE_CHANNEL_ID)

    if channel is None:

        log.error(
            "❌ Голосовой канал не найден: %s",
            VOICE_CHANNEL_ID,
        )

        return

    # Ищем существующий voice client
    existing = discord.utils.get(
        bot.voice_clients,
        guild=channel.guild,
    )

    if existing and existing.is_connected():

        # Если уже мы там
        if existing.channel.id == channel.id:

            vps_voice_connected = True

            return

        # Если бот где-то ещё
        await existing.disconnect()

    log.info(
        "🔌 VPS подключается к голосовому каналу: %s",
        channel.name,
    )

    try:

        await channel.connect()

        vps_voice_connected = True

        log.info(
            "🟢 VPS-версия Шуви подключена к Voice."
        )

    except Exception as e:

        log.error(
            "❌ Ошибка подключения VPS к Voice: %s",
            e,
        )


# ==========================================================
# ОТКЛЮЧЕНИЕ VPS ОТ VOICE
# ==========================================================

async def disconnect_vps_from_voice():

    global vps_voice_connected

    for vc in list(bot.voice_clients):

        try:

            if vc.is_connected():

                log.info(
                    "🔌 PC ONLINE — VPS выходит из Voice."
                )

                await vc.disconnect(
                    force=True
                )

        except Exception as e:

            log.error(
                "Ошибка отключения VPS: %s",
                e,
            )

    vps_voice_connected = False


# ==========================================================
# МОНИТОР PC
# ==========================================================

async def pc_monitor():

    global last_pc_heartbeat

    log.info(
        "👀 VPS мониторит состояние PC."
    )

    previous_state = None

    while True:

        await asyncio.sleep(2)

        online = is_pc_online()

        # Состояние изменилось
        if online != previous_state:

            previous_state = online

            if online:

                log.info(
                    "🟢 PC AI ONLINE"
                )

                await disconnect_vps_from_voice()

            else:

                log.info(
                    "🔴 PC AI OFFLINE"
                )

                await connect_vps_to_voice()


# ==========================================================
# HEARTBEAT
# ==========================================================

@bot.event
async def on_message(message):

    global last_pc_heartbeat

    # Самого себя игнорируем
    if message.author.id == bot.user.id:
        return

    # Проверяем служебный канал
    if message.channel.id != CONTROL_CHANNEL_ID:
        await bot.process_commands(message)
        return

    content = message.content.strip()

    if content == "SHUVI_PC_HEARTBEAT":

        last_pc_heartbeat = time.monotonic()

        log.info(
            "💓 Получен heartbeat от PC."
        )

    await bot.process_commands(message)


# ==========================================================
# READY
# ==========================================================

@bot.event
async def on_ready():

    global monitor_task

    log.info(
        "=" * 60
    )

    log.info(
        "🖥 SHUVI VPS ЗАПУЩЕН"
    )

    log.info(
        "Бот: %s",
        bot.user,
    )

    log.info(
        "Voice ID: %s",
        VOICE_CHANNEL_ID,
    )

    log.info(
        "=" * 60
    )

    if monitor_task is None or monitor_task.done():

        monitor_task = asyncio.create_task(
            pc_monitor()
        )


# ==========================================================
# MAIN
# ==========================================================

async def main():

    if not DISCORD_TOKEN:

        raise RuntimeError(
            "DISCORD_TOKEN отсутствует в .env"
        )

    if not CONTROL_CHANNEL_ID:

        raise RuntimeError(
            "SHUVI_CONTROL_CHANNEL_ID отсутствует в .env"
        )

    await bot.start(
        DISCORD_TOKEN
    )


if __name__ == "__main__":

    try:

        asyncio.run(
            main()
        )

    except KeyboardInterrupt:

        log.info(
            "🛑 VPS Шуви остановлена."
        )
