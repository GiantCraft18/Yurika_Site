import lolka as discord
from lolka.ext import commands


class Moderation(commands.Cog):
    """Команды модерации сервера."""

    def __init__(self, bot):
        self.bot = bot

    # ---------- Кик ----------
    @commands.command(name="kick")
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason: str = "Не указана"):
        """Выгнать участника с сервера. Пример: !kick @User спам"""
        await member.kick(reason=reason)
        await ctx.send(f"👢 {member.display_name} выгнан. Причина: {reason}")

    # ---------- Бан ----------
    @commands.command(name="ban")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason: str = "Не указана"):
        """Забанить участника. Пример: !ban @User нарушение"""
        await member.ban(reason=reason)
        await ctx.send(f"🔨 {member.display_name} забанен. Причина: {reason}")

    # ---------- Разбан ----------
    @commands.command(name="unban")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def unban(self, ctx, user_id: int, *, reason: str = "Не указана"):
        """Разбанить пользователя по ID. Пример: !unban 123456789"""
        try:
            user = await self.bot.fetch_user(user_id)
            await ctx.guild.unban(user, reason=reason)
            await ctx.send(f"✅ {user} разбанен. Причина: {reason}")
        except discord.NotFound:
            await ctx.send("❌ Пользователь с таким ID не найден в бан-листе.")

    # ---------- Мут (тайм-аут) ----------
    @commands.command(name="mute")
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    async def mute(self, ctx, member: discord.Member, minutes: int = 10, *, reason: str = "Не указана"):
        """Замьютить участника на N минут. Пример: !mute @User 15 флуд"""
        from datetime import timedelta
        duration = timedelta(minutes=minutes)
        await member.timeout(duration, reason=reason)
        await ctx.send(f"🔇 {member.display_name} замьючен на {minutes} мин. Причина: {reason}")

    # ---------- Размут ----------
    @commands.command(name="unmute")
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    async def unmute(self, ctx, member: discord.Member):
        """Снять мут с участника. Пример: !unmute @User"""
        await member.timeout(None)
        await ctx.send(f"🔊 С {member.display_name} снят мут.")

    # ---------- Очистка сообщений ----------
    @commands.command(name="clear")
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def clear(self, ctx, amount: int = 10):
        """Удалить N последних сообщений. Пример: !clear 20"""
        if amount < 1 or amount > 100:
            await ctx.send("❌ Число должно быть от 1 до 100.")
            return
        deleted = await ctx.channel.purge(limit=amount + 1)  # +1 чтобы удалить саму команду
        await ctx.send(f"🧹 Удалено сообщений: {len(deleted) - 1}", delete_after=5)

    # ---------- Предупреждение ----------
    @commands.command(name="warn")
    @commands.has_permissions(kick_members=True)
    async def warn(self, ctx, member: discord.Member, *, reason: str = "Не указана"):
        """Выдать предупреждение. Пример: !warn @User оскорбления"""
        # Здесь можно позже подключить базу данных для хранения варнов
        await ctx.send(f"⚠️ {member.mention} получил предупреждение. Причина: {reason}")
        try:
            await member.send(f"⚠️ Вы получили предупреждение на сервере {ctx.guild.name}. Причина: {reason}")
        except discord.Forbidden:
            # Пользователь закрыл личку — ничего страшного
            pass


async def setup(bot):
    await bot.add_cog(Moderation(bot))