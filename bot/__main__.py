import os
import signal
import time

from psutil import cpu_percent, cpu_count, disk_usage, virtual_memory, net_io_counters
from sys import executable
from telegram import InlineKeyboardMarkup
from telegram.ext import CommandHandler

from bot import bot, LOGGER, botStartTime, AUTHORIZED_CHATS, DEST_DRIVES, TELEGRAPH, Interval, dispatcher, updater
from bot.modules import auth, cancel, clone, compress, count, delete, eval, list, permission, shell, status
from bot.helper.ext_utils.bot_utils import get_readable_file_size, get_readable_time
from bot.helper.ext_utils.fs_utils import start_cleanup, clean_all, exit_clean_up
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.button_builder import ButtonMaker
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.message_utils import sendMessage, sendMarkup, editMessage, sendLogFile

def start(update, context):
    if CustomFilters.authorized_user(update) or CustomFilters.authorized_chat(update):
        if update.message.chat.type == "private":
            sendMessage("<b>Access granted</b>", context.bot, update.message)
        else:
            sendMessage("<b>I'm alive :)</b>", context.bot, update.message)
    else:
        sendMessage("<b>Access denied</b>", context.bot, update.message)

def listkeys(update, context):
    keys = ''
    keys += '\n'.join(f"• <code>{key}</code>" for key in DEST_DRIVES.keys())
    msg = f"<b><u>Available Keys</u></b>\n{keys}"
    sendMessage(msg, context.bot, update.message)

def ping(update, context):
    start_time = int(round(time.time() * 1000))
    reply = sendMessage("<b>Pong!</b>", context.bot, update.message)
    end_time = int(round(time.time() * 1000))
    editMessage(f'<code>{end_time - start_time}ms</code>', reply)

def stats(update, context):
    uptime = get_readable_time(time.time() - botStartTime)
    total, used, free, disk = disk_usage('/')
    total = get_readable_file_size(total)
    used = get_readable_file_size(used)
    free = get_readable_file_size(free)
    sent = get_readable_file_size(net_io_counters().bytes_sent)
    recv = get_readable_file_size(net_io_counters().bytes_recv)
    cpu = cpu_percent(interval=0.5)
    ram = virtual_memory().percent
    p_core = cpu_count(logical=False)
    l_core = cpu_count(logical=True)
    stats = '⚙️ <u><b>SYSTEM STATISTICS</b></u>' \
            f'\n\n<b>Total Disk Space:</b> {total}' \
            f'\n<b>Used:</b> {used} | <b>Free:</b> {free}' \
            f'\n\n<b>Upload:</b> {sent}' \
            f'\n<b>Download:</b> {recv}' \
            f'\n\n<b>Physical Cores:</b> {p_core}' \
            f'\n<b>Logical Cores:</b> {l_core}' \
            f'\n\n<b>CPU:</b> {cpu}% | <b>RAM:</b> {ram}%' \
            f'\n<b>DISK:</b> {disk}% | <b>Uptime:</b> {uptime}'
    sendMessage(stats, context.bot, update.message)

def log(update, context):
    sendLogFile(context.bot, update.message)

def restart(update, context):
    restart_message = sendMessage("<b>Restart in progress...</b>", context.bot, update.message)
    if Interval:
        Interval[0].cancel()
        Interval.clear()
    clean_all()
    with open(".restartmsg", "w") as f:
        f.truncate(0)
        f.write(f"{restart_message.chat.id}\n{restart_message.message_id}\n")
    os.execl(executable, executable, "-m", "bot")

help_string = '''
<b><a href='https://teleflix.ml'>TeleFlix Search</a></b> - The Ultimate Telegram Bot For Searching in Drive

Choose a help category:
'''

help_string_user = f'''
<b><u>User Commands</u></b>
<br><br>
• <b>/{BotCommands.StartCommand}</b>: Start the bot
<br><br>
• <b>/{BotCommands.ListCommand}</b> &lt;query&gt;: Search data on Google Drive
<br><br>
• <b>/{BotCommands.CloneCommand}</b> &lt;url&gt; &lt;key&gt;: Copy data from Google Drive, AppDrive and GDToT (Key optional)
<br><br>
• <b>/{BotCommands.ArchiveCommand}</b> &lt;url&gt;: Archive data from Google Drive, AppDrive and GDToT
<br><br>
• <b>/{BotCommands.ExtractCommand}</b> &lt;url&gt;: Extract data from Google Drive, AppDrive and GDToT
<br><br>
• <b>/{BotCommands.CountCommand}</b> &lt;drive_url&gt;: Count data from Google Drive
<br><br>
• <b>/{BotCommands.CancelCommand}</b> &lt;gid&gt;: Cancel a task
<br><br>
• <b>/{BotCommands.StatusCommand}</b>: Get a status of all tasks
<br><br>
• <b>/{BotCommands.ListKeysCommand}</b>: Get a list of keys for the destination drives
<br><br>
• <b>/{BotCommands.PingCommand}</b>: Ping the bot
<br><br>
• <b>/{BotCommands.StatsCommand}</b>: Get the system statistics
<br><br>
• <b>/{BotCommands.HelpCommand}</b>: Get help about the bot
'''

help_user = TELEGRAPH[0].create_page(
    title='TeleFlix Search Help',
    author_name='Meow',
    author_url='https://t.me/telekit152',
    html_content=help_string_user)['path']

help_string_admin = f'''
<b><u>Admin Commands</u></b>
<br><br>
• <b>/{BotCommands.PermissionCommand}</b> &lt;drive_url&gt; &lt;email&gt;: Set data permission on Google Drive (Email optional)
<br><br>
• <b>/{BotCommands.DeleteCommand}</b> &lt;drive_url&gt;: Delete data from Google Drive
<br><br>
• <b>/{BotCommands.AuthorizeCommand}</b>: Authorize an user or a chat for using the bot
<br><br>
• <b>/{BotCommands.UnauthorizeCommand}</b>: Unauthorize an user or a chat for using the bot
<br><br>
• <b>/{BotCommands.UsersCommand}</b>: Get a list of authorized chats
<br><br>
• <b>/{BotCommands.ShellCommand}</b> &lt;cmd&gt;: Run commands in terminal
<br><br>
• <b>/{BotCommands.ExecHelpCommand}</b>: Get help about executor
<br><br>
• <b>/{BotCommands.LogCommand}</b>: Get the log file
<br><br>
• <b>/{BotCommands.RestartCommand}</b>: Restart the bot
'''

help_admin = TELEGRAPH[0].create_page(
    title='TeleFlix Search Help',
    author_name='Meow',
    author_url='https://t.me/telekit152',
    html_content=help_string_admin)['path']

def bot_help(update, context):
    button = ButtonMaker()
    button.build_button("User", f"https://graph.org/{help_user}")
    button.build_button("Admin", f"https://graph.org/{help_admin}")
    sendMarkup(help_string, context.bot, update.message, InlineKeyboardMarkup(button.build_menu(2)))

def main():
    start_cleanup()
    if os.path.isfile(".restartmsg"):
        with open(".restartmsg") as f:
            chat_id, msg_id = map(int, f)
        bot.editMessageText("<b>Restarted successfully</b>", chat_id, msg_id, parse_mode='HTMl')
        os.remove(".restartmsg")

    start_handler = CommandHandler(BotCommands.StartCommand, start, run_async=True)
    keys_handler = CommandHandler(BotCommands.ListKeysCommand, listkeys,
                                  filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
    ping_handler = CommandHandler(BotCommands.PingCommand, ping,
                                  filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
    stats_handler = CommandHandler(BotCommands.StatsCommand, stats,
                                   filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
    log_handler = CommandHandler(BotCommands.LogCommand, log,
                                 filters=CustomFilters.owner_filter, run_async=True)
    restart_handler = CommandHandler(BotCommands.RestartCommand, restart,
                                     filters=CustomFilters.owner_filter, run_async=True)
    help_handler = CommandHandler(BotCommands.HelpCommand, bot_help,
                                  filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(keys_handler)
    dispatcher.add_handler(ping_handler)
    dispatcher.add_handler(stats_handler)
    dispatcher.add_handler(log_handler)
    dispatcher.add_handler(restart_handler)
    dispatcher.add_handler(help_handler)
    updater.start_polling()
    LOGGER.info("Bot started")
    signal.signal(signal.SIGINT, exit_clean_up)

main()
