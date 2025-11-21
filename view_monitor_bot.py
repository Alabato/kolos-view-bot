import telebot
import time
import threading
from datetime import datetime

# Твои данные — всё уже вписано
TOKEN = "8294582579:AAFqJlkWXVFDw0CnXdZOfRLvT8Evd-b9Uew"
ADMIN_CHAT_ID = 56854739                      # твой личный ID
CHANNEL_USERNAME = "@kolos_ufc"               # твой канал

bot = telebot.TeleBot(TOKEN)

# Словарь: message_id → начальные просмотры + время
monitored_posts = {}

# Уведомление при запуске
bot.send_message(ADMIN_CHAT_ID, "Бот @ufc_guard_bot запущен и следит за @kolos_ufc\nГотов ловить спайки +200 views/мин")

# Ловим каждый новый пост автоматически
@bot.channel_post_handler(func=lambda message: True)
def new_post_detected(message):
    msg_id = message.message_id
    link = f"https://t.me/kolos_ufc/{msg_id}"
    
    # Берём текущие просмотры сразу после публикации
    try:
        stats = bot.get_chat_statistics_message(CHANNEL_USERNAME, msg_id)
        views = stats.view_count if hasattr(stats, 'view_count') else 0
        reactions = sum(r.count for r in stats.reactions) if hasattr(stats, 'reactions') else 0
    except:
        views, reactions = 0, 0
    
    monitored_posts[msg_id] = {
        'initial_views': views,
        'last_views': views,
        'reactions': reactions,
        'link': link,
        'time': datetime.now().strftime("%H:%M")
    }
    
    bot.send_message(ADMIN_CHAT_ID, f"Новый пост!\n{link}\nНачальные просмотры: {views}\nСлежу за спайками...")

# Основной цикл проверки каждую минуту
def check_for_spikes():
    while True:
        current_time = datetime.now().strftime("%H:%M")
        for msg_id, data in list(monitored_posts.items()):
            try:
                stats = bot.get_chat_statistics_message(CHANNEL_USERNAME, msg_id)
                views = stats.view_count if hasattr(stats, 'view_count') else 0
                reactions = sum(r.count for r in stats.reactions) if hasattr(stats, 'reactions') else 0
            except:
                continue  # если пост удалили — пропускаем
            
            delta = views - data['last_views']
            
            # Спайк: +200 просмотров за минуту и мало реакций
            if delta >= 200 and reactions <= 10:
                alert = (f"СПАЙК!\n"
                         f"{data['link']}\n"
                         f"+{delta} просмотров за минуту\n"
                         f"Всего просмотров: {views}\n"
                         f"Реакций: {reactions}\n"
                         f"Время: {current_time}")
                bot.send_message(ADMIN_CHAT_ID, alert)
            
            # Обновляем последние просмотры
            data['last_views'] = views
            data['reactions'] = reactions
        
        # Чистим старые посты (старше 3 часов)
        to_remove = [mid for mid, d in monitored_posts.items() 
                    if (datetime.now() - datetime.strptime(d['time'] + " " + current_time.split()[1], "%H:%M %H:%M")).total_seconds() > 10800]
        for mid in to_remove:
            del monitored_posts[mid]
        
        time.sleep(60)

# Запускаем
if __name__ == "__main__":
    threading.Thread(target=check_for_spikes, daemon=True).start()
    print("Бот запущен и следит за каналом @kolos_ufc")
    bot.infinity_polling()
