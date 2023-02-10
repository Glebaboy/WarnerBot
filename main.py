import time
import threading
import telebot
import config

from telebot import types
from binance import Client

client = Client(config.API_KEY, config.API_SECRET)
bot = telebot.TeleBot(config.TOKEN)
data = {'notifyNum': -1}

# inline keyboard main
inline_kb = types.InlineKeyboardMarkup()
inline_item1 = types.InlineKeyboardButton(text="Список моих уведомлений", callback_data="list_notifications")
inline_kb.add(inline_item1)
# inline keyboard menu
inline_menu = types.InlineKeyboardMarkup()
inline_btn_menu = types.InlineKeyboardButton(text="Назад", callback_data="menu")
inline_menu.add(inline_btn_menu)


@bot.message_handler(commands=['start'])
def welcome(message):
    bot.send_message(message.chat.id,
                     config.FST_TEXT.format(message.from_user, bot.get_me()),
                     parse_mode='html', reply_markup=inline_kb)
    users = open("./users/all_users", "r")
    file_data = []
    for line in users:
        file_data.append(line)
    users.close()
    users = open("./users/all_users", "a+")
    if len(file_data) != 0:
        user_in_list = False
        for k in file_data:
            if message.chat.id == int(k.split('\n')[0]):
                user_in_list = True
        if not user_in_list:
            users.write(str(message.chat.id) + "\n")
    else:
        users.write(str(message.chat.id) + "\n")
    users.close()


@bot.message_handler(commands=['delete'])
def delete(message):
    foo_delete(message.chat.id)


def foo_delete(userId):
    file_name = "./users/" + str(userId) + ".txt"
    file_user = open(file_name, 'r')
    file_data = []
    for line in file_user:
        file_data.append(line)
    file_user.close()
    file_user = open(file_name, 'w')
    for i in range(len(file_data)):
        if i != data.get('notifyNum'):
            file_user.write(file_data[i])
    file_user.close()
    bot.send_message(userId, "✅ Уведомление <b>#" + str(data.get('notifyNum')+1) +
                     "</b> удалено!\nЧтобы выставить ведомление, просто отправь мне сообщение в формате: "
                     "\n*Тикер* *Цена* *Направление цены*\n❇️ Например: \n<b>BTCUSDT 23000.20 Up</b>\n<b>ETHUSDT "
                     "1650.5 Down</b>".format(), parse_mode='html', reply_markup=inline_kb)


@bot.message_handler(content_types=['text'])
def get_message(message):
    if message.chat.type == 'private':
        text = message.text
        data_notif = text.split(" ")
        prices = client.get_all_tickers()
        num_in_list = -1
        for i in range(0, len(prices)):
            if prices[i].get('symbol') == data_notif[0]:
                num_in_list = i
                break
        try:
            if num_in_list != -1:
                file_name = "./users/" + str(message.chat.id) + ".txt"
                file = open(file_name, "a+")
                file.write(str(num_in_list) + " " + data_notif[0] + " " + data_notif[1] + " " + data_notif[2] + "\n")
                bot.send_message(message.chat.id, "Уведомление выставлено успешно!", reply_markup=inline_kb)
                file.close()
        except Exception as e:
            print(repr(e))


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    try:
        if call.message:
            if call.data == 'list_notifications':
                file_name = "./users/" + str(call.message.chat.id) + ".txt"
                file = open(file_name, 'r')
                notifications = []
                for line in file:
                    notifications.append(line.split(" "))
                file.close()
                inline_list = types.InlineKeyboardMarkup()
                for i in range(0, len(notifications)):
                    inline_list.add(types.InlineKeyboardButton(text=notifications[i][1] + " " +
                                                                    notifications[i][2] + " " +
                                                                    notifications[i][3], callback_data=str(i)))
                inline_list.add(types.InlineKeyboardButton(text="Назад", callback_data="menu"))
                bot.send_message(call.message.chat.id, "Список выставленных уведомлений:", reply_markup=inline_list)
                delete_and_remove_kb(bot, call)


            elif call.data == 'menu':
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      text="Вот что ты можешь сделать прямо сейчас:",
                                      reply_markup=inline_kb)

            else:
                bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
                file_name = "./users/" + str(call.message.chat.id) + ".txt"
                file = open(file_name, 'r')
                file_data = []
                for line in file:
                    file_data.append(line)
                need_line_data = file_data[int(call.data)].split(" ")
                data['notifyNum'] = int(call.data)
                file.close()
                bot.send_message(call.message.chat.id, "Уведомление <b>#" + str(data['notifyNum']+1) + "</b>:\n" +
                                 need_line_data[1] + " " + need_line_data[2] +
                                 "\n/delete - чтобы удалить уведомление",
                                 reply_markup=inline_menu, parse_mode='html')

    except Exception as e:
        print(repr(e))


def delete_and_remove_kb(bott, call):
    if (call.message.text == "Вот что ты можешь сделать прямо сейчас:") or \
            (call.message.text == "Список выставленных уведомлений:"):
        bott.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
    else:
        bott.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                               text=call.message.text,
                               reply_markup=None)


def th1do():
    bot.polling(none_stop=True)


def checking_price():
    while True:
        all_users = open('../pythonProject/users/all_users', 'r')
        all_ids = []
        for line in all_users:
            all_ids.append(line)
        for userId in all_ids:
            filter = userId.split("\n")
            file = open('./users/' + filter[0] + '.txt')
            data_to_check = []
            for notif in file:
                data_to_check.append(notif.split(" "))
            file.close()
            # work with data_to_check
            notif_num = 0
            prices = client.get_all_tickers()
            for notif in data_to_check:
                if notif[3].split('\n')[0] == 'Up':
                    if float(prices[int(notif[0])].get('price')) >= float(notif[2]):
                        bot.send_message(userId, '🏁 Инструмент ' + notif[1] + ' достигнул отметки в ' + notif[2] + "!")
                        data['notifyNum'] = notif_num
                        foo_delete(filter[0])
                elif notif[3].split('\n')[0] == 'Down':
                    if float(prices[int(notif[0])].get('price')) <= float(notif[2]):
                        bot.send_message(userId, '🏁 Инструмент ' + notif[1] + ' достигнул отметки в ' + notif[2] + "!")
                        data['notifyNum'] = notif_num
                        foo_delete(filter[0])
                notif_num += 1
        all_users.close()
        time.sleep(1)


th1 = threading.Thread(target=th1do)
th2 = threading.Thread(target=checking_price)

th1.start()
th2.start()
