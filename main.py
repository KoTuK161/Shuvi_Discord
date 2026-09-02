import os
import asyncio
import discord

TOKEN = os.getenv("SHUVI_TOKEN")

GUILD_ID = 629954676124549121
VOICE_CHANNEL_ID = 1542127104026480681


class VoiceBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents)

    async def on_ready(self):
        print(f"Бот запущен: {self.user}")

        # Статус: Играет в шахматы
        await self.change_presence(
            status=discord.Status.online,
            activity=discord.Game(name="в шахматы")
        )

        await self.connect_to_voice()

    async def connect_to_voice(self):
        guild = self.get_guild(GUILD_ID)

        if guild is None:
            print("Сервер не найден.")
            return

        channel = guild.get_channel(VOICE_CHANNEL_ID)

        if channel is None:
            print("Голосовой канал не найден.")
            return

        # Если уже подключён — ничего не делаем
        if guild.voice_client and guild.voice_client.is_connected():
            print("Бот уже находится в голосовом канале.")
            return

        try:
            await channel.connect(
                self_deaf=False,
                self_mute=False
            )

            print(f"Подключился к голосовому каналу: {channel.name}")
            print("Микрофон включён.")

        except Exception as e:
            print(f"Ошибка подключения: {e}")

    async def on_voice_state_update(self, member, before, after):
        # Проверяем только самого бота
        if member.id != self.user.id:
            return

        # Если бот вышел из голосового канала — возвращаем его
        if after.channel is None:
            await asyncio.sleep(5)
            await self.connect_to_voice()


bot = VoiceBot()

bot.run(TOKEN)
