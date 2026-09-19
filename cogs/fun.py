import random
from lolka.ext import commands


class Fun(commands.Cog):
    """Развлекательные команды."""

    def __init__(self, bot):
        self.bot = bot

    # ---------- Монетка ----------
    @commands.command(name="coinflip", aliases=["flip", "монетка"])
    async def coinflip(self, ctx):
        """Подбросить монетку."""
        result = random.choice(["Орёл 🪙", "Решка 🪙"])
        await ctx.send(result)

    # ---------- Кубик ----------
    @commands.command(name="roll", aliases=["dice", "кубик"])
    async def roll(self, ctx, sides: int = 6):
        """Бросить кубик с N сторонами. Пример: !roll 20"""
        if sides < 2:
            await ctx.send("❌ У кубика должно быть минимум 2 стороны.")
            return
        if sides > 1000:
            await ctx.send("❌ Слишком много сторон — максимум 1000.")
            return

        result = random.randint(1, sides)
        await ctx.send(f"🎲 Выпало: **{result}** (из {sides})")

    # ---------- Магический шар ----------
    @commands.command(name="8ball", aliases=["шар"])
    async def eightball(self, ctx, *, question: str):
        """Магический шар ответит на ваш вопрос. Пример: !8ball Я выиграю?"""
        answers = [
            "🎱 Бесспорно.",
            "🎱 Определённо да.",
            "🎱 Скорее всего, да.",
            "🎱 Знаки говорят «да».",
            "🎱 Пока неясно, попробуй ещё раз.",
            "🎱 Спроси позже.",
            "🎱 Лучше не рассказывать.",
            "🎱 Не могу предсказать сейчас.",
            "🎱 Не рассчитывай на это.",
            "🎱 Мой ответ — нет.",
            "🎱 Весьма сомнительно.",
            "🎱 Определённо нет.",
        ]
        answer = random.choice(answers)
        await ctx.send(f"❓ **Вопрос:** {question}\n{answer}")

    # ---------- Выбор из вариантов ----------
    @commands.command(name="choose", aliases=["выбери"])
    async def choose(self, ctx, *options: str):
        """Выбрать один из вариантов. Пример: !choose пицца суши бургер"""
        if len(options) < 2:
            await ctx.send("❌ Укажите минимум 2 варианта: `!choose вариант1 вариант2`")
            return
        choice = random.choice(options)
        await ctx.send(f"🤔 Я выбираю: **{choice}**")

    # ---------- Случайное число в диапазоне ----------
    @commands.command(name="random", aliases=["рандом"])
    async def random_num(self, ctx, minimum: int = 1, maximum: int = 100):
        """Случайное число в диапазоне. Пример: !random 1 1000"""
        if minimum >= maximum:
            await ctx.send("❌ Минимум должен быть меньше максимума.")
            return
        result = random.randint(minimum, maximum)
        await ctx.send(f"🎯 Случайное число: **{result}**")

    # ---------- Шутка ----------
    @commands.command(name="joke", aliases=["шутка"])
    async def joke(self, ctx):
        """Случайная шутка."""
        jokes = [
            "— Как дела?\n— Как в сказке: чем дальше, тем страшнее.",
            "Программист — это машина по превращению кофе в код.",
            "99 маленьких багов в коде, 99 маленьких багов...\nОдин исправишь — и вот их 127.",
            "— Почему программисты путают Хэллоуин и Рождество?\n— Потому что OCT 31 == DEC 25.",
            "Купил книгу «Как решать 90% своих проблем». Прочитал — это оказался блокнот.",
        ]
        await ctx.send(random.choice(jokes))

    # ---------- Камень-ножницы-бумага ----------
    @commands.command(name="rps", aliases=["кнб"])
    async def rps(self, ctx, choice: str):
        """Камень, ножницы, бумага. Пример: !rps камень"""
        variants = {
            "камень": "🪨",
            "ножницы": "✂️",
            "бумага": "📄",
        }
        user_choice = choice.lower()
        if user_choice not in variants:
            await ctx.send("❌ Выберите: камень, ножницы или бумага.")
            return

        bot_choice = random.choice(list(variants.keys()))
        result = ""

        if user_choice == bot_choice:
            result = "🤝 Ничья!"
        elif (
            (user_choice == "камень" and bot_choice == "ножницы") or
            (user_choice == "ножницы" and bot_choice == "бумага") or
            (user_choice == "бумага" and bot_choice == "камень")
        ):
            result = "🎉 Вы победили!"
        else:
            result = "😢 Вы проиграли."

        await ctx.send(
            f"Вы: {variants[user_choice]} | Бот: {variants[bot_choice]}\n{result}"
        )


async def setup(bot):
    await bot.add_cog(Fun(bot))