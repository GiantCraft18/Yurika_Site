import logging
from threading import Thread
from datetime import datetime

from flask import Flask, jsonify, render_template_string

# ---------- Логгер ----------
log = logging.getLogger("web")

# ---------- Flask ----------
web_app = Flask(__name__)
web_app.config["JSON_AS_ASCII"] = False


# =========================================================
#  Общие данные (бот обновляет их в реальном времени)
# =========================================================
bot_status_data = {
    "status": "Запускается...",
    "username": "—",
    "avatar": None,
    "servers": 0,
    "users": 0,
    "ping": 0,
    "uptime": "0:00:00",
    "cogs": 0,
    "commands": 0,
    "started_at": "—",
    "recent_commands": [],
    "guilds": [],
    "loaded_cogs": [],
}


# =========================================================
#  HTML-шаблон дашборда
# =========================================================
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Юрика-Бот — Панель управления</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, sans-serif;
            background: #0f1117;
            color: #e6e8eb;
            min-height: 100vh;
            padding: 24px;
        }
        .container { max-width: 1200px; margin: 0 auto; }

        header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 32px;
            flex-wrap: wrap;
            gap: 16px;
        }
        h1 {
            font-size: 28px;
            font-weight: 600;
            background: linear-gradient(90deg, #5865F2, #8B5CF6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .status-badge {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 8px 16px;
            border-radius: 20px;
            background: #1a1d29;
            font-size: 14px;
            font-weight: 500;
        }
        .status-dot {
            width: 10px; height: 10px;
            border-radius: 50%;
            background: #2ECC71;
            box-shadow: 0 0 10px #2ECC71;
            animation: pulse 2s infinite;
        }
        .status-dot.offline { background: #E74C3C; box-shadow: 0 0 10px #E74C3C; }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.4; }
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
            gap: 16px;
            margin-bottom: 32px;
        }
        .card {
            background: #1a1d29;
            border: 1px solid #262a3a;
            border-radius: 12px;
            padding: 20px;
            transition: transform 0.15s, border-color 0.15s;
        }
        .card:hover {
            transform: translateY(-2px);
            border-color: #5865F2;
        }
        .card-label {
            font-size: 13px;
            color: #8a92a6;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }
        .card-value {
            font-size: 26px;
            font-weight: 600;
            color: #fff;
        }
        .card-value.small { font-size: 18px; }

        .section {
            background: #1a1d29;
            border: 1px solid #262a3a;
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 24px;
        }
        .section h2 {
            font-size: 18px;
            margin-bottom: 16px;
            color: #fff;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .section h2::before {
            content: "";
            width: 4px;
            height: 20px;
            background: #5865F2;
            border-radius: 2px;
        }

        .cmd-list { list-style: none; }
        .cmd-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 0;
            border-bottom: 1px solid #262a3a;
            font-size: 14px;
        }
        .cmd-item:last-child { border-bottom: none; }
        .cmd-user { color: #8B5CF6; font-weight: 500; }
        .cmd-text { color: #e6e8eb; font-family: 'Consolas', monospace; margin-left: 8px; }
        .cmd-time { color: #8a92a6; font-size: 12px; margin-left: 12px; }
        .cmd-channel { color: #5865F2; font-size: 12px; }

        .guild-list { list-style: none; display: grid; gap: 8px; }
        .guild-item {
            display: flex;
            justify-content: space-between;
            padding: 10px 14px;
            background: #13161f;
            border-radius: 8px;
            font-size: 14px;
        }
        .guild-members { color: #8a92a6; }

        .empty {
            color: #8a92a6;
            font-style: italic;
            padding: 16px 0;
            text-align: center;
        }

        .footer {
            text-align: center;
            color: #5a6072;
            font-size: 12px;
            margin-top: 40px;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🤖 Юрика-Бот — Панель управления</h1>
            <div class="status-badge">
                <span class="status-dot" id="statusDot"></span>
                <span id="statusText">Загрузка...</span>
            </div>
        </header>

        <div class="grid">
            <div class="card">
                <div class="card-label">Пинг</div>
                <div class="card-value" id="ping">— мс</div>
            </div>
            <div class="card">
                <div class="card-label">Серверов</div>
                <div class="card-value" id="servers">—</div>
            </div>
            <div class="card">
                <div class="card-label">Пользователей</div>
                <div class="card-value" id="users">—</div>
            </div>
            <div class="card">
                <div class="card-label">Аптайм</div>
                <div class="card-value small" id="uptime">—</div>
            </div>
            <div class="card">
                <div class="card-label">Когов</div>
                <div class="card-value" id="cogs">—</div>
            </div>
            <div class="card">
                <div class="card-label">Команд</div>
                <div class="card-value" id="commands">—</div>
            </div>
        </div>

        <div class="section">
            <h2>📋 Последние команды</h2>
            <ul class="cmd-list" id="cmdList">
                <li class="empty">Пока нет команд</li>
            </ul>
        </div>

        <div class="section">
            <h2>🌐 Серверы бота</h2>
            <ul class="guild-list" id="guildList">
                <li class="empty">Пока нет серверов</li>
            </ul>
        </div>

        <div class="footer">
            Бот: <span id="botName">—</span> • Запущен: <span id="startedAt">—</span>
        </div>
    </div>

    <script>
        async function updateStatus() {
            try {
                const r = await fetch('/api/status');
                const d = await r.json();

                const dot = document.getElementById('statusDot');
                const st = document.getElementById('statusText');
                st.textContent = d.status;
                dot.classList.toggle('offline', d.status !== 'Онлайн');

                document.getElementById('ping').textContent = d.ping + ' мс';
                document.getElementById('servers').textContent = d.servers;
                document.getElementById('users').textContent = d.users;
                document.getElementById('uptime').textContent = d.uptime;
                document.getElementById('cogs').textContent = d.cogs;
                document.getElementById('commands').textContent = d.commands;

                document.getElementById('botName').textContent = d.username;
                document.getElementById('startedAt').textContent = d.started_at;

                const cmdList = document.getElementById('cmdList');
                if (!d.recent_commands || d.recent_commands.length === 0) {
                    cmdList.innerHTML = '<li class="empty">Пока нет команд</li>';
                } else {
                    cmdList.innerHTML = d.recent_commands.slice().reverse().map(c => `
                        <li class="cmd-item">
                            <div>
                                <span class="cmd-user">${c.user}</span>
                                <span class="cmd-text">${c.content}</span>
                            </div>
                            <div>
                                <span class="cmd-channel">${c.channel}</span>
                                <span class="cmd-time">${c.time}</span>
                            </div>
                        </li>
                    `).join('');
                }

                const guildList = document.getElementById('guildList');
                if (!d.guilds || d.guilds.length === 0) {
                    guildList.innerHTML = '<li class="empty">Пока нет серверов</li>';
                } else {
                    guildList.innerHTML = d.guilds.map(g => `
                        <li class="guild-item">
                            <span>${g.name}</span>
                            <span class="guild-members">👥 ${g.members}</span>
                        </li>
                    `).join('');
                }
            } catch (e) {
                console.error('Ошибка обновления:', e);
            }
        }

        updateStatus();
        setInterval(updateStatus, 5000);
    </script>
</body>
</html>
"""


# =========================================================
#  Роуты
# =========================================================
@web_app.route('/')
def home():
    return render_template_string(DASHBOARD_HTML)


@web_app.route('/api/status')
def api_status():
    return jsonify(bot_status_data)


@web_app.route('/api/health')
def api_health():
    return jsonify({
        "ok": True,
        "time": datetime.now().isoformat(),
        "status": bot_status_data.get("status", "unknown"),
    })


# =========================================================
#  Запуск
# =========================================================
def run_web_server(host: str = "0.0.0.0", port: int = 5000):
    log.info(f"🌐 Запуск веб-панели: http://127.0.0.1:{port}")
    web_app.run(host=host, port=port, debug=False, use_reloader=False)


def start_web_server(host: str = "0.0.0.0", port: int = 5000):
    thread = Thread(
        target=run_web_server,
        kwargs={"host": host, "port": port},
        daemon=True,
        name="web-server",
    )
    thread.start()
    log.info("✅ Веб-сервер запущен в фоновом потоке.")
    return thread
