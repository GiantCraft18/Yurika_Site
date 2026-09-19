import lolka as discord
from lolka.ext import commands


# =========================================================
#  Описание категорий меню
# =========================================================
CATEGORIES = [
    # (ключ, эмодзи, название, имя кога, описание, цвет)
    ("home",       "🏠", "Главная",     None,         "Общая информация о боте",      0x5865F2),
    ("fun",        "🎲", "Развлечения", "Fun",        "Игры, шутки и случайности",    0xF1C40F),
    ("moderation", "🛡️", "Модерация",   "Moderation", "Управление участниками сервера", 0xE74C3C),
    ("utility",    "🔧", "Утилиты",     "Utility",    "Информация и инструменты",     0x3498DB),
]


class HelpView(discord.ui.View):
    """Интерактивное меню помощи с кнопками-категориями и пагинацией."""

    def __init__(self, bot, author, prefix: str = "!"):
        super().__init__(timeout=180)
        self.bot = bot
        self.author = author
        self.prefix = prefix

        # Кеш страниц: {category_key: [embed, embed, ...]}
        self.category_pages: dict[str, list] = {}
        self.current_category = "home"
        self.current_page = 0

        self._build_all_pages()
        self._add_category_buttons()
        self._add_nav_buttons()

    # ---------- Построение страниц ----------
    def _build_all_pages(self):
        """Заранее собирает все Embed-страницы для каждой категории."""
        for key, emoji, title, cog_name, description, color in CATEGORIES:
            if key == "home":
                self.category_pages[key] = [self._build_home_page(color)]
            else:
                self.category_pages[key] = self._build_cog_pages(
                    cog_name, emoji, title, description, color
                )

    def _build_home_page(self, color: int) -> discord.Embed:
        """Главная страница с описанием бота."""
        embed = discord.Embed(
            title="📖 Меню команд",
            description=(
                "Привет! Я — бот **Юрика**.\n\n"
                "Выберите категорию с помощью кнопок ниже "
                "или используйте команды для навигации."
            ),
            color=color,
        )

        # Информация о боте
        total_commands = 0
        total_cogs = 0
        for key, emoji, title, cog_name, description, _ in CATEGORIES:
            if cog_name is None:
                continue
            cog = self.bot.get_cog(cog_name)
            if cog is None:
                continue
            total_cogs += 1
            total_commands += len([c for c in cog.get_commands() if not c.hidden])

        embed.add_field(
            name="📊 Статистика",
            value=(
                f"**Когов:** {total_cogs}\n"
                f"**Команд:** {total_commands}\n"
                f"**Префикс:** `{self.prefix}`"
            ),
            inline=True,
        )

        embed.add_field(
            name="🔗 Навигация",
            value=(
                "• Кнопки категорий — переключение разделов\n"
                "• `◀` / `▶` — листать страницы внутри категории\n"
                "• `✖` — закрыть меню"
            ),
            inline=True,
        )

        embed.set_footer(text="Меню закроется через 3 минуты бездействия")
        return embed

    def _build_cog_pages(self, cog_name, emoji, title, description, color) -> list:
        """Собирает страницы (по 8 команд на страницу) для одного кога."""
        cog = self.bot.get_cog(cog_name)
        if cog is None:
            return [discord.Embed(
                title=f"{emoji} {title}",
                description="⚠️ Этот ког не загружен.",
                color=color,
            )]

        commands_list = []
        for command in cog.get_commands():
            if command.hidden:
                continue

            signature = f"{self.prefix}{command.name}"
            if command.signature:
                signature += f" {command.signature}"

            # Первая строка docstring — краткое описание
            help_text = (command.help or "—").strip().split("\n")[0]

            # Алиасы
            aliases = getattr(command, "aliases", [])
            alias_text = ""
            if aliases:
                alias_text = f" *(алиасы: {', '.join(self.prefix + a for a in aliases)})*"

            commands_list.append(f"`{signature}`{alias_text}\n   {help_text}")

        # Если команд нет — одна заглушка
        if not commands_list:
            embed = discord.Embed(
                title=f"{emoji} {title}",
                description=f"{description}\n\n*Пока нет доступных команд.*",
                color=color,
            )
            return [embed]

        # Разбиваем на страницы по 8 команд
        per_page = 8
        pages = []
        chunks = [commands_list[i:i + per_page] for i in range(0, len(commands_list), per_page)]
        total_pages = len(chunks)

        for i, chunk in enumerate(chunks):
            embed = discord.Embed(
                title=f"{emoji} {title}",
                description=description,
                color=color,
            )
            embed.add_field(
                name=f"Команды ({len(commands_list)} шт.)",
                value="\n\n".join(chunk),
                inline=False,
            )
            embed.set_footer(text=f"Страница {i + 1} из {total_pages}")
            pages.append(embed)

        return pages

    # ---------- Кнопки категорий ----------
    def _add_category_buttons(self):
        """Создаёт кнопки-категории в верхнем ряду."""
        for key, emoji, title, cog_name, _, _ in CATEGORIES:
            # Пропускаем категорию, если ког не загружен (кроме главной)
            if cog_name is not None and self.bot.get_cog(cog_name) is None:
                continue

            button = discord.ui.Button(
                label=title,
                emoji=emoji,
                style=discord.ButtonStyle.secondary,
                custom_id=f"help_cat_{key}",
            )
            button.callback = self._make_category_callback(key)
            self.add_item(button)

    def _make_category_callback(self, key: str):
        """Фабрика callback'ов для кнопок категорий."""
        async def callback(interaction):
            self.current_category = key
            self.current_page = 0
            self._refresh_category_styles()
            self._refresh_nav_buttons()
            await interaction.response.edit_message(
                embed=self.category_pages[key][self.current_page],
                view=self,
            )
        return callback

    def _refresh_category_styles(self):
        """Подсвечивает активную категорию и сбрасывает остальные."""
        for item in self.children:
            if not isinstance(item, discord.ui.Button):
                continue
            cid = getattr(item, "custom_id", "")
            if cid.startswith("help_cat_"):
                key = cid.replace("help_cat_", "")
                if key == self.current_category:
                    item.style = discord.ButtonStyle.primary
                else:
                    item.style = discord.ButtonStyle.secondary

    # ---------- Кнопки навигации ----------
    def _add_nav_buttons(self):
        """Кнопки листания страниц внутри категории."""
        prev_btn = discord.ui.Button(
            label="◀", style=discord.ButtonStyle.blurple,
            custom_id="help_prev", row=1,
        )
        prev_btn.callback = self._on_prev

        next_btn = discord.ui.Button(
            label="▶", style=discord.ButtonStyle.blurple,
            custom_id="help_next", row=1,
        )
        next_btn.callback = self._on_next

        refresh_btn = discord.ui.Button(
            label="🔄", style=discord.ButtonStyle.green,
            custom_id="help_refresh", row=1,
        )
        refresh_btn.callback = self._on_refresh

        close_btn = discord.ui.Button(
            label="✖ Закрыть", style=discord.ButtonStyle.red,
            custom_id="help_close", row=1,
        )
        close_btn.callback = self._on_close

        self.add_item(prev_btn)
        self.add_item(next_btn)
        self.add_item(refresh_btn)
        self.add_item(close_btn)

        self._refresh_category_styles()
        self._refresh_nav_buttons()

    def _refresh_nav_buttons(self):
        """Обновляет активность кнопок «назад/вперёд»."""
        pages = self.category_pages.get(self.current_category, [])
        total = len(pages)

        for item in self.children:
            if not isinstance(item, discord.ui.Button):
                continue
            cid = getattr(item, "custom_id", "")
            if cid == "help_prev":
                item.disabled = self.current_page == 0
            elif cid == "help_next":
                item.disabled = self.current_page >= total - 1

    async def _on_prev(self, interaction):
        if self.current_page > 0:
            self.current_page -= 1
            self._refresh_nav_buttons()
            await interaction.response.edit_message(
                embed=self.category_pages[self.current_category][self.current_page],
                view=self,
            )

    async def _on_next(self, interaction):
        pages = self.category_pages[self.current_category]
        if self.current_page < len(pages) - 1:
            self.current_page += 1
            self._refresh_nav_buttons()
            await interaction.response.edit_message(
                embed=pages[self.current_page],
                view=self,
            )

    async def _on_refresh(self, interaction):
        """Пересобирает все страницы — полезно после загрузки/выгрузки когов."""
        self._build_all_pages()
        # Сброс к первой странице, если текущая вышла за пределы
        pages = self.category_pages.get(self.current_category, [])
        if self.current_page >= len(pages):
            self.current_page = 0
        self._refresh_nav_buttons()
        await interaction.response.edit_message(
            embed=pages[self.current_page],
            view=self,
        )

    async def _on_close(self, interaction):
        await interaction.message.delete()
        self.stop()

    # ---------- Проверки и таймаут ----------
    async def interaction_check(self, interaction) -> bool:
        """Только автор команды может кликать по кнопкам."""
        if interaction.user.id != self.author.id:
            await interaction.response.send_message(
                "❌ Это меню не для вас. Введите `!help`, чтобы открыть своё.",
                ephemeral=True,
            )
            return False
        return True

    async def on_timeout(self):
        """Отключает все кнопки по истечении времени."""
        for item in self.children:
            item.disabled = True

        # Пытаемся обновить исходное сообщение
        msg = getattr(self, "message", None)
        if msg is not None:
            try:
                await msg.edit(view=self)
            except Exception:
                pass


# =========================================================
#  Ког
# =========================================================
class Help(commands.Cog):
    """Интерактивное меню со всеми командами бота."""

    def __init__(self, bot):
        self.bot = bot
        # Убираем встроенную команду help, если она есть
        try:
            self.bot.remove_command("help")
        except Exception:
            pass

    @commands.command(name="help", aliases=["помощь", "хелп", "menu", "меню"])
    async def help_command(self, ctx):
        """Открыть интерактивное меню команд."""
        prefix = self.bot.command_prefix
        if callable(prefix):
            prefix = "!"  # на случай сложного префикса

        view = HelpView(self.bot, ctx.author, prefix=prefix)

        # Если главная страница не собралась — выходим
        if not view.category_pages.get("home"):
            await ctx.send("❌ Не удалось собрать меню помощи.")
            return

        message = await ctx.send(
            embed=view.category_pages["home"][0],
            view=view,
        )
        view.message = message  # сохраняем ссылку для on_timeout


async def setup(bot):
    await bot.add_cog(Help(bot))