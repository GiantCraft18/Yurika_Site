import os
import asyncio
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

import lolka as discord
from lolka.ext import commands
from dotenv import load_dotenv

# --- ВЕБ-ПАНЕЛЬ ---
from web_panel import start_web_server, bot_status_data

# ---------- Загрузка токена ----------
load_dotenv()
TOKEN = os.getenv("LOLKA_TOKEN")

if not TOKEN:
    raise ValueError(
        "❌ Токен не найден! Создайте файл .env и добавьте: LOLKA_TOKEN=ваш_токен"
    )

# ---------- Логирование с ротацией ----------
file_handler = RotatingFileHandler(
    "bot.log",
    maxBytes=5 * 1024 * 1024,  # 5 МБ
    backupCount=3,             # хранить 3 старых файла
    encoding="utf-8"
)
file_handler.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
))

console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
))

logging.basicConfig(
    level=logging.INFO,
    handlers=[file_handler, console_handler]
)
log = logging.getLogger("bot")

# ---------- Intents ----------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# ---------- Бот ----------
bot = commands.Bot(command_prefix="!", intents=intents)

# --- ВЕБ-ПАНЕЛЬ: время запуска для аптайма ---
START_TIME = datetime.now()


# =========================================================
#  Вспомогательная функция: собрать данные о серверах
# =========================================================
def collect_guilds() -> list:
    """Возвращает список серверов бота в виде словарей."""
    return [
        {
            "id": g.id,
            "name": str(g.name),
            "members": g.member_count or 0,
        }
        for g in bot.guilds
    ]


@bot.event
async def on_ready():
    log.info(f"✅ Залогинились как {bot.user}")
    log.info(f"📦 Загружено расширений: {len(bot.extensions)}")
    log.info(f"🌐 Серверов: {len(bot.guilds)}")

    # --- ВЕБ-ПАНЕЛЬ: полное заполнение статуса ---
    bot_status_data["status"] = "Онлайн"
    bot_status_data["username"] = str(bot.user)
    bot_status_data["avatar"] = getattr(bot.user, "display_avatar", None) and str(bot.user.display_avatar.url)
    bot_status_data["servers"] = len(bot.guilds)
    bot_status_data["users"] = sum(g.member_count or 0 for g in bot.guilds)
    bot_status_data["ping"] = round(bot.latency * 1000)
    bot_status_data["cogs"] = len(bot.extensions)
    bot_status_data["commands"] = len(bot.commands)
    bot_status_data["started_at"] = START_TIME.strftime("%d.%m.%Y %H:%M:%S")
    bot_status_data["guilds"] = collect_guilds()
    bot_status_data["loaded_cogs"] = [ext.split(".")[-1] for ext in bot.extensions]


async def load_all_cogs():
    """Автоматически загружает все .py файлы из папки cogs."""
    cogs_dir = "./cogs"

    if not os.path.isdir(cogs_dir):
        log.warning(f"⚠️ Папка {cogs_dir} не найдена.")
        return

    loaded, failed = 0, 0

    for filename in sorted(os.listdir(cogs_dir)):
        if not filename.endswith(".py") or filename.startswith("_"):
            continue

        extension_name = f"cogs.{filename[:-3]}"

        try:
            await bot.load_extension(extension_name)
            log.info(f"✅ Загружен ког: {extension_name}")
            loaded += 1
        except commands.ExtensionAlreadyLoaded:
            log.warning(f"⚠️ Уже загружен: {extension_name}")
        except commands.NoEntryPointError:
            log.error(f"❌ Нет `setup(bot)` в {filename} — пропускаем")
            failed += 1
        except commands.ExtensionFailed as e:
            log.error(f"❌ Ошибка в {extension_name}: {e.original}")
            failed += 1
        except Exception as e:
            log.error(f"❌ Неизвестная ошибка в {extension_name}: {e}")
            failed += 1

    log.info(f"📊 Итог: загружено {loaded}, с ошибками {failed}")

    # --- ВЕБ-ПАНЕЛЬ: обновляем список когов и количество команд ---
    bot_status_data["loaded_cogs"] = [ext.split(".")[-1] for ext in bot.extensions]
    bot_status_data["cogs"] = len(bot.extensions)
    bot_status_data["commands"] = len(bot.commands)


@bot.event
async def on_command_error(ctx, error):
    """Глобальный обработчик ошибок команд."""
    # У команды есть свой обработчик — не мешаем
    if hasattr(ctx.command, "on_error"):
        return

    # Несуществующая команда — игнорируем
    if isinstance(error, commands.CommandNotFound):
        return

    # Пользователь не ввёл обязательный аргумент
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(
            f"❌ Не хватает аргумента: `{error.param.name}`\n"
            f"Использование: `!{ctx.command.name} {ctx.command.signature}`"
        )
        return

    # Неверный тип аргумента
    if isinstance(error, commands.BadArgument):
        await ctx.send("❌ Неверный аргумент. Проверьте ввод.")
        return

    # У пользователя нет прав
    if isinstance(error, commands.MissingPermissions):
        missing = ", ".join(error.missing_permissions)
        await ctx.send(f"❌ Вам не хватает прав: `{missing}`")
        return

    # У бота нет прав
    if isinstance(error, commands.BotMissingPermissions):
        missing = ", ".join(error.missing_permissions)
        await ctx.send(f"❌ Боту не хватает прав: `{missing}`")
        return

    # Команда только для сервера
    if isinstance(error, commands.NoPrivateMessage):
        await ctx.send("❌ Эта команда работает только на сервере.")
        return

    # Кулдаун
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(
            f"⏳ Подождите {error.retry_after:.1f} сек. перед повторным использованием."
        )
        return

    # Всё остальное — логируем с трассировкой
    log.error(
        f"⚠️ Ошибка в команде {ctx.command}: {error}",
        exc_info=error
    )
    await ctx.send("⚠️ Произошла внутренняя ошибка. Попробуйте позже.")


@bot.event
async def on_command(ctx):
    """Логируем каждое использование команды."""
    log.info(f"📨 {ctx.author} в #{ctx.channel}: {ctx.message.content}")

    # --- ВЕБ-ПАНЕЛЬ: добавляем в лог сайта ---
    bot_status_data["recent_commands"].append({
        "user": str(ctx.author),
        "command": ctx.command.name if ctx.command else "?",
        "content": ctx.message.content,
        "channel": f"#{ctx.channel}",
        "time": datetime.now().strftime("%H:%M:%S"),
    })
    # Храним только последние 20 команд
    if len(bot_status_data["recent_commands"]) > 20:
        bot_status_data["recent_commands"].pop(0)


async def update_status_loop():
    """Фоновый цикл: обновляет данные для сайта каждые 30 секунд."""
    while True:
        try:
            if bot.is_ready():
                bot_status_data["ping"] = round(bot.latency * 1000)
                bot_status_data["servers"] = len(bot.guilds)
                bot_status_data["users"] = sum(g.member_count or 0 for g in bot.guilds)
                bot_status_data["guilds"] = collect_guilds()
                bot_status_data["commands"] = len(bot.commands)

                # Аптайм
                delta = datetime.now() - START_TIME
                hours, remainder = divmod(int(delta.total_seconds()), 3600)
                minutes, seconds = divmod(remainder, 60)
                bot_status_data["uptime"] = f"{hours}:{minutes:02d}:{seconds:02d}"
        except Exception as e:
            log.error(f"⚠️ Ошибка обновления статуса: {e}")

        await asyncio.sleep(30)


async def main():
    # --- ВЕБ-ПАНЕЛЬ: запускаем Flask в фоновом потоке ---
    start_web_server()

    async with bot:
        await load_all_cogs()

        # --- ВЕБ-ПАНЕЛЬ: параллельно запускаем цикл обновления статуса ---
        asyncio.create_task(update_status_loop())

        await bot.start(TOKEN)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("🛑 Бот остановлен вручную.")
    finally:
        # --- ВЕБ-ПАНЕЛЬ: помечаем бота оффлайн ---
        bot_status_data["status"] = "Оффлайн"
        log.info("🌐 Веб-панель: статус изменён на «Оффлайн»")
