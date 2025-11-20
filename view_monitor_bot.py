import telebot
import requests
import time

TOKEN = '8294582579:AAFqJlkWXVFDw0CnXdZOfRLvT8Evd-b9Uew'
ADMIN_CHAT_ID = 56854739
POST_COUNT = 30

bot = telebot.TeleBot(TOKEN)

def get_last_posts():
    url = f"https://api.telegram.org/bot{TOKEN}/getChatHistory?chat_id=@kolos_ufc&limit={POST_COUNT}"
    r = requests.get(url).json()
    if r.get('ok'):
        return [msg['message_id'] for msg in r['result']['messages'] if 'message_id' in msg]
    return []

def get_views(message_id):
    url = f"https://api.telegram.org/bot{TOKEN}/getMessageStatistics?chat_id=@kolos_ufc&message_id={message_id}"
    r = requests.get(url)
    if r.status_code == 200 and r.json().get('ok'):
        stats = r.json()['result']['message_stats']
        views = stats.get('views', 0)
        reactions = sum(item.get('count', 0) for item in stats.get('reactions', []))
        return views, reactions
    return 0, 0

print("Bot started. Monitoring last 30 posts every 60 seconds...")

old_views = {}
first_run = True

while True:
    post_ids = get_last_posts()
    
    if not post_ids:
        time.sleep(60)
        continue
        
    for mid in post_ids:
        views, reacts = get_views(mid)
        
        if first_run:
            old_views[mid] = views
            continue
            
        if mid in old_views:
            delta = views - old_views[mid]
            if delta >= 200 and reacts <= 5:
                alert = f"NAKRUTKA DETECTED!\nPost: t.me/kolos_ufc/{mid}\n+{delta} views in 1 min\nReactions: {reacts}\nTime: {time.strftime('%H:%M %d.%m')}"
                bot.send_message(ADMIN_CHAT_ID, alert)
        
        old_views[mid] = views
    
    first_run = False
    time.sleep(60)
