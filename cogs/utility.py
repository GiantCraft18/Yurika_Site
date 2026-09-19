import lolka as discord
from lolka.ext import commands


class Utility(commands.Cog):
    """Полезные команды."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="userinfo", aliases=["юзеринфо", "инфо"])
    async def userinfo(self, ctx, *, member_name: str = None):
        """Показать информацию о пользователе по имени или упоминанию.

        Примеры:
        !userinfo — информация о вас
        !userinfo @Паук — информация об упомянутом пользователе
        !userinfo Паук — поиск по имени на сервере
        """
        # Если имя не указано — берём автора команды
        if member_name is None:
            member = ctx.author
        else:
            # Убираем @, если есть
            member_name = member_name.lstrip("@").strip()

            # Сначала проверяем упоминания (самый надёжный способ)
            member = None
            if ctx.message.mentions:
                member = ctx.message.mentions[0]
            else:
                # Ищем участника по имени / нику / display_name в списке сервера
                member = discord.utils.find(
                    lambda m: (
                        getattr(m, "name", "") == member_name
                        or getattr(m, "display_name", "") == member_name
                        or getattr(m, "nick", "") == member_name
                    ),
                    ctx.guild.members
                )

            if member is None:
                await ctx.send(
                    f"❌ Пользователь `{member_name}` не найден на сервере.\n"
                    f"Попробуйте упомянуть его через `@` или проверьте точное имя."
                )
                return

        # Безопасно получаем имя
        display_name = getattr(
            member, "display_name",
            getattr(member, "name", str(member))
        )

        # Собираем Embed
        embed = discord.Embed(
            title=f"Информация о {display_name}",
            color=discord.Color.blue()
        )

        # ID
        embed.add_field(
            name="ID",
            value=str(getattr(member, "id", "неизвестно")),
            inline=False
        )

        # Упоминание (если доступно)
        mention = getattr(member, "mention", None)
        if mention:
            embed.add_field(
                name="Упоминание",
                value=mention,
                inline=False
            )

        # Дата регистрации
        created_at = getattr(member, "created_at", None)
        if created_at is not None:
            try:
                embed.add_field(
                    name="Зарегистрирован",
                    value=created_at.strftime("%d.%m.%Y"),
                    inline=False
                )
            except AttributeError:
                embed.add_field(
                    name="Зарегистрирован",
                    value=str(created_at),
                    inline=False
                )

        # Аватар
        avatar_url = getattr(member, "display_avatar", None)
        if avatar_url is not None:
            try:
                embed.set_thumbnail(url=avatar_url.url)
            except AttributeError:
                pass

        await ctx.send(embed=embed)

    # ---------- Обработка ошибок команды ----------
    @userinfo.error
    async def userinfo_error(self, ctx, error):
        """Понятные сообщения при ошибках в userinfo."""
        if isinstance(error, commands.MemberNotFound):
            await ctx.send(
                f"❌ Пользователь `{error.argument}` не найден на сервере."
            )
        elif isinstance(error, commands.BadArgument):
            await ctx.send("❌ Неверный формат. Упомяните пользователя через `@`.")
        else:
            raise error


async def setup(bot):
    await bot.add_cog(Utility(bot))