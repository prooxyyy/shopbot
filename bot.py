import telebot
import configure
import sqlite3
from telebot import types
import threading
from requests import get
from time import sleep
from SimpleQIWI import *

client = telebot.TeleBot(configure.config['token'])
db = sqlite3.connect('baza.db', check_same_thread=False)
sql = db.cursor()
lock = threading.Lock()
api = QApi(token=configure.config['tokenqiwi'], phone=configure.config['phoneqiwi'])
markdown = """
    *bold text*
    _italic text_
    [text](URL)
    """

#database

sql.execute("""CREATE TABLE IF NOT EXISTS users (id BIGINT, nick TEXT, cash INT, access INT, bought INT)""")
sql.execute("""CREATE TABLE IF NOT EXISTS shop (id INT, name TEXT, price INT, tovar TEXT, whobuy TEXT)""")
db.commit()

@client.message_handler(commands=['start'])
def start(message):
	try:
		getname = message.from_user.first_name
		cid = message.chat.id
		uid = message.from_user.id

		sql.execute(f"SELECT id FROM users WHERE id = {uid}")
		if sql.fetchone() is None:
			sql.execute(f"INSERT INTO users VALUES ({uid}, '{getname}', 0, 0, 0)")
			client.send_message(cid, f"🛒 | Добро пожаловать, {getname}!\nТы попал в бота магазин\nИзмените этот текст!")
			db.commit()
		else:
			client.send_message(cid, f"⛔️ | Ты уже зарегистрирован! Пропиши /help чтобы узнать команды.")
	except:
		client.send_message(cid, f'🚫 | Ошибка при выполнении команды')

@client.message_handler(commands=['profile', 'myinfo', 'myprofile'])
def myprofile(message):
	try:
		cid = message.chat.id
		uid = message.from_user.id
		sql.execute(f"SELECT * FROM users WHERE id = {uid}")
		getaccess = sql.fetchone()[3]
		if getaccess == 0:
			accessname = 'Пользователь'
		elif getaccess == 1:
			accessname = 'Администратор'
		elif getaccess == 777:
			accessname = 'Разработчик'
		for info in sql.execute(f"SELECT * FROM users WHERE id = {uid}"):
			client.send_message(cid, f"*📇 | Твой профиль:*\n\n*👤 | Ваш ID:* {info[0]}\n*💸 | Баланс:* {info[2]} ₽\n*👑 | Уровень доступа:* {accessname}\n*🛒 | Куплено товаров:* {info[4]}\n\n*🗂 Чтобы посмотреть список купленных товаров напишите /mybuy*", parse_mode='Markdown')
	except:
		client.send_message(cid, f'🚫 | Ошибка при выполнении команды')

@client.message_handler(commands=['users'])
def allusers(message):
	try:
		cid = message.chat.id
		uid = message.from_user.id
		sql.execute(f"SELECT * FROM users WHERE id = {uid}")
		getaccess = sql.fetchone()[3]
		accessquery = 1
		if getaccess < accessquery:
			client.send_message(cid, '⚠️ | У вас нет доступа!')
		else:
			text = '*🗃 | Список всех пользователей:*\n\n'
			idusernumber = 0
			for info in sql.execute(f"SELECT * FROM users"):
				if info[3] == 0:
					accessname = 'Пользователь'
				elif info[3] == 1:
					accessname = 'Администратор'
				elif info[3] == 777:
					accessname = 'Разработчик'
				idusernumber += 1
				text += f"*{idusernumber}. {info[0]} ({info[1]})*\n*💸 | Баланс:* {info[2]} ₽\n*👑 | Уровень доступа:* {accessname}\n*✉️ | Профиль:*" + f" [{info[1]}](tg://user?id="+str(info[0])+")\n\n"
			client.send_message(cid, f"{text}",parse_mode='Markdown')
	except:
		client.send_message(cid, f'🚫 | Ошибка при выполнении команды')

@client.message_handler(commands=['mybuy'])
def mybuy(message):
	try:
		cid = message.chat.id
		uid = message.from_user.id
		text = '*🗂 | Список купленных товаров:*\n\n'
		for info in sql.execute(f"SELECT * FROM users WHERE id = {uid}"):
			for infoshop in sql.execute(f"SELECT * FROM shop"):
				if str(info[0]) in infoshop[4]:
					text += f"*{infoshop[0]}. {infoshop[1]}*\nТовар: {infoshop[3]}\n\n"
		client.send_message(cid,f"{text}",parse_mode='Markdown',disable_web_page_preview=True)
	except:
		client.send_message(cid, f'🚫 | Ошибка при выполнении команды')

@client.message_handler(commands=['getprofile', 'info'])
def getprofile(message):
	try:
		cid = message.chat.id
		uid = message.from_user.id
		sql.execute(f"SELECT * FROM users WHERE id = {uid}")
		getaccess = sql.fetchone()[3]
		accessquery = 1
		if getaccess < accessquery:
			client.send_message(cid, '⚠️ | У вас нет доступа!')
		else:
			for info in sql.execute(f"SELECT * FROM users WHERE id = {uid}"):
				msg = client.send_message(cid, f'Введите ID пользователя:\nПример: {info[0]}')
				client.register_next_step_handler(msg, getprofile_next)
	except:
		client.send_message(cid, f'🚫 | Ошибка при выполнении команды')

def getprofile_next(message):
	try:
		cid = message.chat.id
		uid = message.from_user.id
		if message.text == message.text:
			getprofileid = message.text
			for info in sql.execute(f"SELECT * FROM users WHERE id = {getprofileid}"):
				if info[3] == 0:
					accessname = 'Пользователь'
				elif info[3] == 1:
					accessname = 'Администратор'
				elif info[3] == 777:
					accessname = 'Разработчик'
				client.send_message(cid, f"*📇 | Профиль {info[1]}:*\n\n*ID пользователя:* {info[0]}\n*Баланс:* {info[2]} ₽\n*Уровень доступа:* {accessname}\n*Куплено товаров:* {info[4]}",parse_mode='Markdown')
	except:
		client.send_message(cid, f'🚫 | Ошибка при выполнении команды')

@client.message_handler(commands=['editbuy'])
def editbuy(message):
	try:
		cid = message.chat.id
		uid = message.from_user.id
		accessquery = 1
		with lock:
			sql.execute(f"SELECT * FROM users WHERE id = {uid}")
			getaccess = sql.fetchone()[3]
		if getaccess < 1:
			client.send_message(cid, '⚠️ | У вас нет доступа!')
		else:
			rmk = types.InlineKeyboardMarkup()
			item_name = types.InlineKeyboardButton(text='Название',callback_data='editbuyname')
			item_price = types.InlineKeyboardButton(text='Цена',callback_data='editbuyprice')
			item_tovar = types.InlineKeyboardButton(text='Товар',callback_data='editbuytovar')
			rmk.add(item_name, item_price, item_tovar)
			msg = client.send_message(cid, f"🔰 | Выберите что Вы хотите изменить:",reply_markup=rmk,parse_mode='Markdown')
	except:
		client.send_message(cid, f'🚫 | Ошибка при выполнении команды')

def editbuy_name(message):
	try:
		cid = message.chat.id
		uid = message.from_user.id
		if message.text == message.text:
			global editbuynameidtovar
			editbuynameidtovar = int(message.text)
			msg = client.send_message(cid, f"*Введите новое название товара:*",parse_mode='Markdown')
			client.register_next_step_handler(msg, editbuy_name_new_name)
	except:
		client.send_message(cid, f'🚫 | Ошибка при выполнении команды')

def editbuy_name_new_name(message):
	try:
		cid = message.chat.id
		uid = message.from_user.id
		if message.text == message.text:
			global editbuynametovar
			editbuynametovar = message.text
			for infoshop in sql.execute(f"SELECT * FROM shop WHERE id = {editbuynameidtovar}"):
				rmk = types.InlineKeyboardMarkup()
				item_yes = types.InlineKeyboardButton(text='✅', callback_data='editbuynewnametovaryes')
				item_no = types.InlineKeyboardButton(text='❌', callback_data='editbuynewnametovarno')
				rmk.add(item_yes, item_no)
				msg = client.send_message(cid, f"*🔰 | Данные об изменении названия товара:*\n\nID товара: {editbuynameidtovar}\nСтарое имя товара: {infoshop[1]}\nНовое имя товара: {editbuynametovar}\n\nВы подверждаете изменения?",parse_mode='Markdown',reply_markup=rmk)
	except:
		client.send_message(cid, f'🚫 | Ошибка при выполнении команды')

def editbuy_price(message):
	try:
		cid = message.chat.id
		uid = message.from_user.id
		if message.text == message.text:
			global editbuypriceidtovar
			editbuypriceidtovar = int(message.text)
			msg = client.send_message(cid, f"*Введите новую цену товара:*",parse_mode='Markdown')
			client.register_next_step_handler(msg, editbuy_price_new_price)
	except:
		client.send_message(cid, f'🚫 | Ошибка при выполнении команды')

def editbuy_price_new_price(message):
	try:
		cid = message.chat.id
		uid = message.from_user.id
		if message.text == message.text:
			global editbuypricetovar
			editbuypricetovar = int(message.text)
			for infoshop in sql.execute(f"SELECT * FROM shop WHERE id = {editbuypriceidtovar}"):
				rmk = types.InlineKeyboardMarkup()
				item_yes = types.InlineKeyboardButton(text='✅', callback_data='editbuynewpricetovaryes')
				item_no = types.InlineKeyboardButton(text='❌', callback_data='editbuynewpricetovarno')
				rmk.add(item_yes, item_no)
				msg = client.send_message(cid, f"*🔰 | Данные об изменении цены товара:*\n\nID товара: {editbuypriceidtovar}\nСтарая цена: {infoshop[2]}\nНовая цена: {editbuypricetovar}\n\nВы подверждаете изменения?",parse_mode='Markdown',reply_markup=rmk)
	except:
		client.send_message(cid, f'🚫 | Ошибка при выполнении команды')

def editbuy_tovar(message):
	try:
		cid = message.chat.id
		uid = message.from_user.id
		if message.text == message.text:
			global editbuytovaridtovar
			editbuytovaridtovar = int(message.text)
			msg = client.send_message(cid, f"*Введите новую ссылку на товар:*",parse_mode='Markdown')
			client.register_next_step_handler(msg, editbuy_tovar_new_tovar)
	except:
		client.send_message(cid, f'🚫 | Ошибка при выполнении команды')

def editbuy_tovar_new_tovar(message):
	try:
		cid = message.chat.id
		uid = message.from_user.id
		if message.text == message.text:
			global editbuytovartovar
			editbuytovartovar = message.text
			for infoshop in sql.execute(f"SELECT * FROM shop WHERE id = {editbuytovaridtovar}"):
				rmk = types.InlineKeyboardMarkup()
				item_yes = types.InlineKeyboardButton(text='✅', callback_data='editbuynewtovartovaryes')
				item_no = types.InlineKeyboardButton(text='❌', callback_data='editbuynewtovartovarno')
				rmk.add(item_yes, item_no)
				msg = client.send_message(cid, f"*🔰 | Данные об изменении сcылки товара:*\n\nID товара: {editbuytovaridtovar}\nСтарая ссылка: {infoshop[3]}\nНовая ссылка: {editbuytovartovar}\n\nВы подверждаете изменения?",parse_mode='Markdown',reply_markup=rmk)
	except:
		client.send_message(cid, f'🚫 | Ошибка при выполнении команды')

@client.callback_query_handler(lambda call: call.data == 'editbuynewtovartovaryes' or call.data == 'editbuynewtovartovarno')
def editbuy_tovar_new_callback(call):
	try:
		if call.data == 'editbuynewtovartovaryes':
			sql.execute(f"SELECT * FROM shop WHERE id = {editbuytovaridtovar}")
			sql.execute(f"UPDATE shop SET tovar = '{editbuytovartovar}' WHERE id = {editbuytovaridtovar}")
			db.commit()
			client.delete_message(call.message.chat.id, call.message.message_id-0)
			client.send_message(call.message.chat.id, f"✅ | Вы успешно изменили ссылку на товар на {editbuytovartovar}")
		elif call.data == 'editbuynewtovartovarno':
			client.delete_message(call.message.chat.id, call.message.message_id-0)
			client.send_message(call.message.chat.id, f"🚫 | Вы отменили изменение сcылки товара")
		client.answer_callback_query(callback_query_id=call.id)
	except:
		client.send_message(call.message.chat.id, f'🚫 | Ошибка при выполнении команды')

@client.callback_query_handler(lambda call: call.data == 'editbuynewpricetovaryes' or call.data == 'editbuynewpricetovarno')
def editbuy_price_new_callback(call):
	try:
		if call.data == 'editbuynewpricetovaryes':
			sql.execute(f"SELECT * FROM shop WHERE id = {editbuypriceidtovar}")
			sql.execute(f"UPDATE shop SET price = {editbuypricetovar} WHERE id = {editbuypriceidtovar}")
			db.commit()
			client.delete_message(call.message.chat.id, call.message.message_id-0)
			client.send_message(call.message.chat.id, f"✅ | Вы успешно изменили цену товара на {editbuypricetovar}")
		elif call.data == 'editbuynewpricetovarno':
			client.delete_message(call.message.chat.id, call.message.message_id-0)
			client.send_message(call.message.chat.id, f"🚫 | Вы отменили изменение цены товара")
		client.answer_callback_query(callback_query_id=call.id)
	except:
		client.send_message(call.message.chat.id, f'🚫 | Ошибка при выполнении команды')
@client.callback_query_handler(lambda call: call.data == 'editbuynewnametovaryes' or call.data == 'editbuynewnametovarno')
def editbuy_name_new_callback(call):
	try:
		if call.data == 'editbuynewnametovaryes':
			sql.execute(f"SELECT * FROM shop WHERE id = {editbuynameidtovar}")
			sql.execute(f"UPDATE shop SET name = '{editbuynametovar}' WHERE id = {editbuynameidtovar}")
			db.commit()
			client.delete_message(call.message.chat.id, call.message.message_id-0)
			client.send_message(call.message.chat.id, f"✅ | Вы успешно изменили название товара на {editbuynametovar}")
		elif call.data == 'editbuynewnametovarno':
			client.delete_message(call.message.chat.id, call.message.message_id-0)
			client.send_message(call.message.chat.id, f"🚫 | Вы отменили изменение названия товара")
		client.answer_callback_query(callback_query_id=call.id)
	except:
		client.send_message(call.message.chat.id, f'🚫 | Ошибка при выполнении команды')


@client.callback_query_handler(lambda call: call.data == 'editbuyname' or call.data == 'editbuyprice' or call.data == 'editbuytovar')
def editbuy_first_callback(call):
	try:
		if call.data == 'editbuyname':
			msg = client.send_message(call.message.chat.id, f"*Введите ID товара которому хотите изменить название:*",parse_mode='Markdown')
			client.register_next_step_handler(msg, editbuy_name)
		elif call.data == 'editbuyprice':
			msg = client.send_message(call.message.chat.id, f"*Введите ID товара которому хотите изменить цену:*",parse_mode='Markdown')
			client.register_next_step_handler(msg, editbuy_price)
		elif call.data == 'editbuytovar':
			msg = client.send_message(call.message.chat.id, f"*Введите ID товара которому хотите изменить ссылку:*",parse_mode='Markdown')
			client.register_next_step_handler(msg, editbuy_tovar)
		client.answer_callback_query(callback_query_id=call.id)
	except:
		client.send_message(call.message.chat.id, f'🚫 | Ошибка при выполнении команды')

@client.message_handler(commands=['rembuy'])
def removebuy(message):
	try:
		cid = message.chat.id
		uid = message.from_user.id
		accessquery = 1
		with lock:
			sql.execute(f"SELECT * FROM users WHERE id = {uid}")
			getaccess = sql.fetchone()[3]
		if getaccess < 1:
			client.send_message(cid, '⚠️ | У вас нет доступа!')
		else:
			msg = client.send_message(cid, f"*Введите ID товара который хотите удалить:*",parse_mode='Markdown')
			client.register_next_step_handler(msg, removebuy_next)
	except:
		client.send_message(cid, f'🚫 | Ошибка при выполнении команды')

def removebuy_next(message):
	try:
		cid = message.chat.id
		uid = message.from_user.id
		if message.text == message.text:
			global removeidtovar
			removeidtovar = int(message.text)
			for info in sql.execute(f"SELECT * FROM users WHERE id = {uid}"):
				for infoshop in sql.execute(f"SELECT * FROM shop WHERE id = {removeidtovar}"):
					rmk = types.InlineKeyboardMarkup()
					item_yes = types.InlineKeyboardButton(text='✅',callback_data='removebuytovaryes')
					item_no = types.InlineKeyboardButton(text='❌',callback_data='removebuytovarno')
					rmk.add(item_yes, item_no)
					msg = client.send_message(cid, f"🔰 | Данные об удалении:\n\nID товара: {infoshop[0]}\nИмя товара: {infoshop[1]}\nЦена товара: {infoshop[2]}\nТовар: {infoshop[3]}\n\nВы действительно хотите удалить товар? Отменить действие будет НЕВОЗМОЖНО.",reply_markup=rmk)
	except:
		client.send_message(cid, f'🚫 | Ошибка при выполнении команды')

@client.callback_query_handler(lambda call: call.data == 'removebuytovaryes' or call.data == 'removebuytovarno')
def removebuy_callback(call):
	try:
		if call.data == 'removebuytovaryes':
			sql.execute(f"SELECT * FROM shop")
			sql.execute(f"DELETE FROM shop WHERE id = {removeidtovar}")
			client.delete_message(call.message.chat.id, call.message.message_id-0)
			client.send_message(call.message.chat.id, f"✅ | Вы успешно удалили товар")
			db.commit()
		elif call.data == 'removebuytovarno':
			client.delete_message(call.message.chat.id, call.message.message_id-0)
			client.send_message(call.message.chat.id, f"🚫 | Вы отменили удаление товара")
		client.answer_callback_query(callback_query_id=call.id)
	except:
		client.send_message(call.message.chat.id, f'🚫 | Ошибка при выполнении команды')

@client.message_handler(commands=['addbuy'])
def addbuy(message):
	try:
		cid = message.chat.id
		uid = message.from_user.id
		with lock:
			sql.execute(f"SELECT * FROM users WHERE id = {uid}")
			getaccess = sql.fetchone()[3]
		if getaccess < 1:
			client.send_message(cid, '⚠️ | У вас нет доступа!')
		else:
			msg = client.send_message(cid, '*Введите ID товара:*',parse_mode='Markdown')
			client.register_next_step_handler(msg, addbuy_id)
	except:
		client.send_message(cid, f'🚫 | Ошибка при выполнении команды')

def addbuy_id(message):
	try:
		cid = message.chat.id
		uid = message.from_user.id
		if message.text == message.text:
			global addbuyid
			addbuyid = message.text
			msg = client.send_message(cid, '*Введите цену товара:*',parse_mode='Markdown')
			client.register_next_step_handler(msg, addbuy_price)
	except:
		client.send_message(cid, f'🚫 | Ошибка при выполнении команды')

def addbuy_price(message):
	try:
		cid = message.chat.id
		uid = message.from_user.id
		if message.text == message.text:
			global addbuyprice
			addbuyprice = message.text
			msg = client.send_message(cid, '*Введите название товара:*',parse_mode='Markdown')
			client.register_next_step_handler(msg, addbuy_name)
	except:
		client.send_message(cid, f'🚫 | Ошибка при выполнении команды')

def addbuy_name(message):
	try:
		cid = message.chat.id
		uid = message.from_user.id
		if message.text == message.text:
			global addbuyname
			addbuyname = message.text
			msg = client.send_message(cid, '*Введите ссылку на товар:*',parse_mode='Markdown')
			client.register_next_step_handler(msg, addbuy_result)
	except:
		client.send_message(cid, f'🚫 | Ошибка при выполнении команды')

def addbuy_result(message):
	try:
		cid = message.chat.id
		uid = message.from_user.id
		if message.text == message.text:
			global addbuytovar
			addbuytovar = message.text
			sql.execute(f"SELECT name FROM shop WHERE name = '{addbuyname}'")
			if sql.fetchone() is None:
				sql.execute(f"INSERT INTO shop VALUES ({addbuyid}, '{addbuyname}', {addbuyprice}, '{addbuytovar}', '')")
				db.commit()
				sql.execute(f"SELECT * FROM shop WHERE name = '{addbuyname}'")
				client.send_message(cid, f'✅ | Вы успешно добавили товар\nID товара: {sql.fetchone()[0]}\nИмя: {addbuyname}\nЦена: {addbuyprice}\nСсылка на товар: {addbuytovar}')
			else:
				client.send_message(cid, f"⛔️ | Данный товар уже добавлен!")
	except:
		client.send_message(cid, f'🚫 | Ошибка при выполнении команды')

@client.message_handler(commands=['buy'])
def buy(message):
	try:
		cid = message.chat.id
		uid = message.from_user.id

		text = '🛒 | *Список товаров*\n\n'
		for info in sql.execute(f"SELECT * FROM users WHERE id = {uid}"):
			for infoshop in sql.execute(f"SELECT * FROM shop"):
				text += f"{infoshop[0]}. {infoshop[1]}\nЦена: {infoshop[2]}\n\n"
			rmk = types.InlineKeyboardMarkup()
			item_yes = types.InlineKeyboardButton(text='✅', callback_data='firstbuytovaryes')
			item_no = types.InlineKeyboardButton(text='❌', callback_data='firstbuytovarno')
			rmk.add(item_yes, item_no)
			msg = client.send_message(cid, f'{text}*Вы хотите перейти к покупке товара?*',parse_mode='Markdown',reply_markup=rmk)
	except:
		client.send_message(cid, f'🚫 | Ошибка при выполнении команды')

def buy_next(message):
	try:
		cid = message.chat.id
		uid = message.from_user.id
		if message.text == message.text:
			global tovarid
			tovarid = int(message.text)
			for info in sql.execute(f"SELECT * FROM users WHERE id = {uid}"):
				for infoshop in sql.execute(f"SELECT * FROM shop WHERE id = {tovarid}"):
					if info[2] < infoshop[2]:
						client.send_message(cid, '⚠️ | У вас недостаточно средств для приобретения товара!\n\nЧтобы пополнить счёт напишите /donate')
					else:
						rmk = types.InlineKeyboardMarkup()
						item_yes = types.InlineKeyboardButton(text='✅',callback_data='buytovaryes')
						item_no = types.InlineKeyboardButton(text='❌',callback_data='buytovarno')
						rmk.add(item_yes, item_no)
						msg = client.send_message(cid, f"💸 | Вы подверждаете покупку товара?\n\nВернуть средства за данный товар НЕВОЗМОЖНО.",reply_markup=rmk)
	except:
		client.send_message(cid, f'🚫 | Ошибка при выполнении команды')

@client.callback_query_handler(lambda call: call.data == 'firstbuytovaryes' or call.data == 'firstbuytovarno')
def firstbuy_callback(call):
	try:
		if call.data == 'firstbuytovaryes':
			msg = client.send_message(call.message.chat.id, f"*Введите ID товара который хотите купить:*",parse_mode='Markdown')
			client.register_next_step_handler(msg, buy_next)
		elif call.data == 'firstbuytovarno':
			client.delete_message(call.message.chat.id, call.message.message_id-0)
			client.send_message(call.message.chat.id, f"🚫 | Вы отменили покупку товара")
		client.answer_callback_query(callback_query_id=call.id)
	except:
		client.send_message(call.message.chat.id, f'🚫 | Ошибка при выполнении команды')

@client.callback_query_handler(lambda call: call.data == 'buytovaryes' or call.data == 'buytovarno')
def buy_callback(call):
	try:
		if call.data == 'buytovaryes':
			for info in sql.execute(f"SELECT * FROM users WHERE id = {call.from_user.id}"):
				for infoshop in sql.execute(f"SELECT * FROM shop WHERE id = {tovarid}"):
					if str(info[0]) not in infoshop[4]:
						cashtovar = int(info[2] - infoshop[2])
						boughttovar = int(info[4] + 1)
						whobuytovarinttostr = str(info[0])
						whobuytovar = str(infoshop[4] + whobuytovarinttostr + ',')
						sql.execute(f"SELECT * FROM users WHERE id = {call.from_user.id}")
						client.delete_message(call.message.chat.id, call.message.message_id-0)
						client.send_message(call.message.chat.id, f"✅ | Вы успешно купили товар\n\nНазвание товара: {infoshop[1]}\nЦена: {infoshop[2]}\n\nТовар: {infoshop[3]}\n\nСпасибо за покупку!")
						sql.execute(f"UPDATE users SET cash = {cashtovar} WHERE id = {call.from_user.id}")
						sql.execute(f"UPDATE users SET bought = {boughttovar} WHERE id = {call.from_user.id}")
						sql.execute(f"SELECT * FROM shop WHERE id = {tovarid}")
						sql.execute(f"UPDATE shop SET whobuy = '{whobuytovar}' WHERE id = {tovarid}")
						db.commit()
					else:
						client.delete_message(call.message.chat.id, call.message.message_id-0)
						client.send_message(call.message.chat.id, f"*⛔️ | Данный товар уже куплен!*\n\nЧтобы посмотреть список купленных товаров напишите /mybuy",parse_mode='Markdown')
		elif call.data == 'buytovarno':
			client.delete_message(call.message.chat.id, call.message.message_id-0)
			client.send_message(call.message.chat.id, f"❌ | Вы отменили покупку товара!")
		client.answer_callback_query(callback_query_id=call.id)
	except:
		client.send_message(call.message.chat.id, f'🚫 | Ошибка при выполнении команды')

@client.message_handler(commands=['donate'])
def donate(message):
	try:
		cid = message.chat.id
		global uid
		uid = message.from_user.id
		msg = client.send_message(cid, f"*💰 | Введите сумму для пополнения:*",parse_mode='Markdown')
		client.register_next_step_handler(msg, donate_value)
	except:
		client.send_message(cid, f'🚫 | Ошибка при выполнении команды')

def donate_value(message):
	try:
		cid = message.chat.id
		uid = message.from_user.id
		if message.text == message.text:
			global donatevalue
			global commentdonate
			global getusername
			global getuserdonateid
			getusername = message.from_user.first_name
			getuserdonateid = message.from_user.id
			sql.execute(f"SELECT * FROM users WHERE id = {uid}")
			commentdonate = sql.fetchone()[0]
			donatevalue = int(message.text)
			rmk = types.InlineKeyboardMarkup()
			item_yes = types.InlineKeyboardButton(text='✅',callback_data='donateyes')
			item_no = types.InlineKeyboardButton(text='❌',callback_data='donateno')
			rmk.add(item_yes, item_no)
			global qiwibalancebe
			qiwibalancebe = api.balance
			msg = client.send_message(cid, f"🔰 | Заявка на пополнение средств успешно создана\n\nВы действительно хотите пополнить средства?",parse_mode='Markdown',reply_markup=rmk)
	except:
		client.send_message(cid, f'🚫 | Ошибка при выполнении команды')

def donateyesoplacheno(message):
	try:
		cid = message.chat.id
		uid = message.from_user.id
		removekeyboard = types.ReplyKeyboardRemove()
		if message.text == '✅ Оплачено':
			client.send_message(cid, f"✉️ | Ваш запрос отправлен администраторам, ожидайте одобрения и выдачи средств.",reply_markup=removekeyboard)
			client.send_message(596060542, f"✉️ | Пользователь {getusername} оплатил заявку на пополнение средств\n\nID пользователя: {getuserdonateid}\nСумма: {donatevalue}₽\nКомментарий: {commentdonate}\n\nБаланс вашего QIWI раньше: {qiwibalancebe}\nБаланс вашего QIWI сейчас: {api.balance}\n\nПерепроверьте верность оплаты затем подтвердите выдачу средств.\nДля выдачи средств напишите: /giverub")
	except:
		client.send_message(cid, f'🚫 | Ошибка при выполнении команды')

@client.callback_query_handler(lambda call: call.data == 'donateyes' or call.data == 'donateno')
def donate_result(call):
	try:
		removekeyboard = types.ReplyKeyboardRemove()
		rmk = types.ReplyKeyboardMarkup(resize_keyboard=True)
		rmk.add(types.KeyboardButton('✅ Оплачено'))
		if call.data == 'donateyes':
			client.delete_message(call.message.chat.id, call.message.message_id-0)
			msg = client.send_message(call.message.chat.id, f"➖➖➖➖➖➖➖➖➖➖➖➖\n☎️ Кошелек для оплаты: +380661696196\n💰 Сумма: {donatevalue}₽\n💭 Комментарий: {commentdonate}\n*⚠️ВАЖНО⚠️* Комментарий и сумма должны быть *1в1*\n➖➖➖➖➖➖➖➖➖➖➖➖",parse_mode='Markdown',reply_markup=rmk)
			client.register_next_step_handler(msg, donateyesoplacheno)
		elif call.data == 'donateno':
			client.send_message(call.message.chat.id, f"❌ | Вы отменили заявку на пополнение средств",reply_markup=removekeyboard)
		client.answer_callback_query(callback_query_id=call.id)
	except:
		client.send_message(call.message.chat.id, f'🚫 | Ошибка при выполнении команды')

@client.message_handler(commands=['getcid'])
def getcid(message):
	client.send_message(message.chat.id, f"ID чата | {message.chat.id}\nТвой ID | {message.from_user.id}")

@client.message_handler(commands=['help'])
def helpcmd(message):
	cid = message.chat.id
	uid = message.from_user.id
	with lock:
		sql.execute(f"SELECT * FROM users WHERE id = {uid}")
		getaccess = sql.fetchone()[3]
	if getaccess >= 1:
		client.send_message(cid, '*Помощь по командам:*\n\n/profile - Посмотреть свой профиль\n/help - Посмотреть список команд\n/buy - Купить товар\n/donate - Пополнить счёт\n/mybuy - Посмотреть список купленных товаров\n/teh - Связаться с тех.поддержкой\n\nАдмин-команды:\n\n/getprofile - Посмотреть чужой профиль\n/access - Выдать уровень доступа\n/giverub - Выдать деньги на баланс\n/getid - Узнать айди пользователя\n/getcid - Узнать Conference ID\n/addbuy - Добавить товар на продажу\n/editbuy - Изменить данные о товаре\n/rembuy - Удалить товар\n/ot - Ответить пользователю (отправить сообщение)',parse_mode='Markdown')
	else:
		client.send_message(cid, '*Помощь по командам:*\n\n/profile - Посмотреть свой профиль\n/help - Посмотреть список команд\n/buy - Купить товар\n/donate - Пополнить счёт\n/mybuy - Посмотреть список купленных товаров\n/teh - Связаться с тех.поддержкой',parse_mode='Markdown')

@client.message_handler(commands=['access', 'setaccess', 'dostup'])
def setaccess(message):
	try:
		cid = message.chat.id
		uid = message.from_user.id
		sql.execute(f"SELECT * FROM users WHERE id = {uid}")
		getaccess = sql.fetchone()[3]
		accessquery = 777
		if getaccess < accessquery:
			client.send_message(cid, f"⚠️ | У вас нет доступа!")
		else:
			for info in sql.execute(f"SELECT * FROM users WHERE id = {uid}"):
				msg = client.send_message(cid, 'Введите ID пользователя:\nПример: 596060542', parse_mode="Markdown")
				client.register_next_step_handler(msg, access_user_id_answer)
	except:
		client.send_message(cid, f'🚫 | Ошибка при выполнении команды')
def access_user_id_answer(message):
	try:
		cid = message.chat.id
		uid = message.from_user.id
		if message.text == message.text:
			global usridaccess
			usridaccess = message.text
			rmk = types.ReplyKeyboardMarkup(resize_keyboard=True)
			rmk.add(types.KeyboardButton('Пользователь'), types.KeyboardButton('Администратор'), types.KeyboardButton('Разработчик'))
			msg = client.send_message(cid, 'Какой уровень доступа Вы хотите выдать?:', reply_markup=rmk, parse_mode="Markdown")
			client.register_next_step_handler(msg, access_user_access_answer)
	except:
		client.send_message(cid, f'🚫 | Ошибка при выполнении команды')

def access_user_access_answer(message):
	try:
		global accessgaved
		global accessgavedname
		cid = message.chat.id
		uid = message.from_user.id
		rmk = types.InlineKeyboardMarkup()
		access_yes = types.InlineKeyboardButton(text='✅',callback_data='setaccessyes')
		access_no = types.InlineKeyboardButton(text='❌',callback_data='setaccessno')
		rmk.add(access_yes, access_no)
		for info in sql.execute(f"SELECT * FROM users WHERE id = {usridaccess}"):
			if message.text == "Пользователь":
				accessgavedname = "Пользователь"
				accessgaved = 0
			elif message.text == "Администратор":
				accessgavedname = "Администратор"
				accessgaved = 1
			elif message.text == "Разработчик":
				accessgavedname = "Разработчик"
				accessgaved = 777

			client.send_message(cid, f'Данные для выдачи:\nID пользователя: {usridaccess} ({info[1]})\nУровень доступа: {message.text}\n\nВерно?', reply_markup=rmk)
	except:
		client.send_message(cid, f'🚫 | Ошибка при выполнении команды')

@client.callback_query_handler(lambda call: call.data == 'setaccessyes' or call.data == 'setaccessno')
def access_user_gave_access(call):
	try:
		removekeyboard = types.ReplyKeyboardRemove()
		if call.data == 'setaccessyes':
			for info in sql.execute(f"SELECT * FROM users WHERE id = {usridaccess}"):
				sql.execute(f"UPDATE users SET access = {accessgaved} WHERE id = {usridaccess}")
				db.commit()
				client.delete_message(call.message.chat.id, call.message.message_id-0)
				client.send_message(call.message.chat.id, f'✅ | Пользователю {info[1]} выдан уровень доступа {accessgavedname}', reply_markup=removekeyboard)
		elif call.data == 'setaccessno':
			for info in sql.execute(f"SELECT * FROM users WHERE id = {usridaccess}"):
				client.delete_message(call.message.chat.id, call.message.message_id-0)
				client.send_message(call.message.chat.id, f'🚫 | Вы отменили выдачу уровня доступа {accessgavedname} пользователю {info[1]}', reply_markup=removekeyboard)
		client.answer_callback_query(callback_query_id=call.id)
	except:
		client.send_message(cid, f'🚫 | Ошибка при выполнении команды')

@client.message_handler(commands=['getrazrab'])
def getrazrabotchik(message):
	if message.from_user.id == 596060542:
		sql.execute(f"UPDATE users SET access = 777 WHERE id = 596060542")
		client.send_message(message.chat.id, f"✅ | Вы выдали себе Разработчика")
		db.commit()
	else:
		client.send_message(message.chat.id, f"⛔️ | Отказано в доступе!")

@client.message_handler(commands=['giverub', 'givedonate', 'givebal'])
def giverubles(message):
	try:
		cid = message.chat.id
		uid = message.from_user.id
		sql.execute(f"SELECT * FROM users WHERE id = {uid}")
		getaccess = sql.fetchone()[3]
		accessquery = 777
		if getaccess < accessquery:
			client.send_message(cid, f"⚠️ | У вас нет доступа!")
		else:
			for info in sql.execute(f"SELECT * FROM users WHERE id = {uid}"):
				msg = client.send_message(cid, 'Введите ID пользователя:\nПример: 596060542', parse_mode="Markdown")
				client.register_next_step_handler(msg, rubles_user_id_answer)
	except:
		client.send_message(cid, f'🚫 | Ошибка при выполнении команды')

def rubles_user_id_answer(message):
	try:
		cid = message.chat.id
		uid = message.from_user.id
		if message.text == message.text:
			global usridrubles
			usridrubles = message.text
			rmk = types.ReplyKeyboardMarkup(resize_keyboard=True)
			rmk.add(types.KeyboardButton('10'), types.KeyboardButton('100'), types.KeyboardButton('1000'), types.KeyboardButton('Другая сумма'))
			msg = client.send_message(cid, 'Выберите сумму для выдачи:', reply_markup=rmk, parse_mode="Markdown")
			client.register_next_step_handler(msg, rubles_user_rubles_answer)
	except:
		client.send_message(cid, f'🚫 | Ошибка при выполнении команды')

def rubles_user_rubles_answer(message):
	try:
		cid = message.chat.id
		uid = message.from_user.id
		global rublesgavedvalue
		removekeyboard = types.ReplyKeyboardRemove()
		rmk = types.InlineKeyboardMarkup()
		access_yes = types.InlineKeyboardButton(text='✅',callback_data='giverublesyes')
		access_no = types.InlineKeyboardButton(text='❌',callback_data='giverublesno')
		rmk.add(access_yes, access_no)
		for info in sql.execute(f"SELECT * FROM users WHERE id = {usridrubles}"):
			if message.text == '10':
				rublesgavedvalue = 10
				client.send_message(cid, f'Данные для выдачи:\nID пользователя: {usridrubles} ({info[1]})\nСумма: {rublesgavedvalue}\n\nВерно?',reply_markup=rmk)
			elif message.text == '100':
				rublesgavedvalue = 100
				client.send_message(cid, f'Данные для выдачи:\nID пользователя: {usridrubles} ({info[1]})\nСумма: {rublesgavedvalue}\n\nВерно?',reply_markup=rmk)
			elif message.text == '1000':
				rublesgavedvalue = 1000
				client.send_message(cid, f'Данные для выдачи:\nID пользователя: {usridrubles} ({info[1]})\nСумма: {rublesgavedvalue}\n\nВерно?',reply_markup=rmk)
			elif message.text == 'Другая сумма':
				msg = client.send_message(cid, f"*Введите сумму для выдачи:*",parse_mode='Markdown',reply_markup=removekeyboard)
				client.register_next_step_handler(msg, rubles_user_rubles_answer_other)
	except:
		client.send_message(cid, f'🚫 | Ошибка при выполнении команды')

def rubles_user_rubles_answer_other(message):
	try:
		cid = message.chat.id
		uid = message.from_user.id
		global rublesgavedvalue
		rmk = types.InlineKeyboardMarkup()
		access_yes = types.InlineKeyboardButton(text='✅',callback_data='giverublesyes')
		access_no = types.InlineKeyboardButton(text='❌',callback_data='giverublesno')
		rmk.add(access_yes, access_no)
		for info in sql.execute(f"SELECT * FROM users WHERE id = {usridrubles}"):
			if message.text == message.text:
				rublesgavedvalue = int(message.text)
				client.send_message(cid, f'Данные для выдачи:\nID пользователя: {usridrubles} ({info[1]})\nСумма: {rublesgavedvalue}\n\nВерно?',reply_markup=rmk)
	except:
		client.send_message(cid, f'🚫 | Ошибка при выполнении команды')

@client.callback_query_handler(func=lambda call: call.data == 'giverublesyes' or call.data == 'giverublesno')
def rubles_gave_rubles_user(call):
	try:
		removekeyboard = types.ReplyKeyboardRemove()
		for info in sql.execute(f"SELECT * FROM users WHERE id = {usridrubles}"): 
			rubless = int(info[2] + rublesgavedvalue)
			if call.data == 'giverublesyes':
				for info in sql.execute(f"SELECT * FROM users WHERE id = {usridrubles}"):
					sql.execute(f"UPDATE users SET cash = {rubless} WHERE id = {usridrubles}")
					db.commit()
					client.delete_message(call.message.chat.id, call.message.message_id-0)
					client.send_message(call.message.chat.id, f'✅ | Пользователю {info[1]} выдано {rublesgavedvalue} рублей', reply_markup=removekeyboard)
			elif call.data == 'giverublesno':
				for info in sql.execute(f"SELECT * FROM users WHERE id = {usridrubles}"):
					client.delete_message(call.message.chat.id, call.message.message_id-0)
					client.send_message(call.message.chat.id, f'🚫 | Вы отменили выдачу рублей пользователю {info[1]}', reply_markup=removekeyboard)
			client.answer_callback_query(callback_query_id=call.id)
	except:
		client.send_message(call.message.chat.id, f'🚫 | Ошибка при выполнении команды')

@client.message_handler(commands=['teh'])
def teh(message):
	try:
		cid = message.chat.id
		uid = message.from_user.id
		msg = client.send_message(cid, f"*📨 | Введите текст который хотите отправить тех.поддержке*",parse_mode='Markdown')
		client.register_next_step_handler(msg, teh_next)
	except:
		client.send_message(cid, f'🚫 | Ошибка при выполнении команды')

def teh_next(message):
	try:
		cid = message.chat.id
		uid = message.from_user.id
		if message.text == message.text:
			global tehtextbyuser
			global tehnamebyuser
			global tehidbyuser
			tehidbyuser = int(message.from_user.id)
			tehnamebyuser = str(message.from_user.first_name)
			tehtextbyuser = str(message.text)
			rmk = types.InlineKeyboardMarkup()
			item_yes = types.InlineKeyboardButton(text='✉️',callback_data='tehsend')
			item_no = types.InlineKeyboardButton(text='❌',callback_data='tehno')
			rmk.add(item_yes, item_no)
			msg = client.send_message(cid, f"✉️ | Данные об отправке:\n\nТекст для отправки: {tehtextbyuser}\n\nВы действительно хотите отправить это тех.поддержке?",parse_mode='Markdown',reply_markup=rmk)
	except:
		client.send_message(cid, f'🚫 | Ошибка при выполнении команды')

@client.callback_query_handler(func=lambda call: call.data == 'tehsend' or call.data == 'tehno')
def teh_callback(call):
	try:
		if call.data == 'tehsend':
			for info in sql.execute(f"SELECT * FROM users WHERE id = {call.from_user.id}"):
				client.delete_message(call.message.chat.id, call.message.message_id-0)
				client.send_message(call.message.chat.id, f"✉️ | Ваше сообщение отправлено тех.поддержке, ожидайте ответа.")
				client.send_message(596060542, f"✉️ | Пользователь {tehnamebyuser} отправил сообщение в тех.поддержку\n\nID пользователя: {tehidbyuser}\nТекст: {tehtextbyuser}\n\nЧтобы ответить пользователю напишите /ot")
		elif call.data == 'tehno':
			client.delete_message(call.message.chat.id, call.message.message_id-0)
			client.send_message(call.message.chat.id, f"🚫 | Вы отменили отправку сообщения тех.поддержке")
		client.answer_callback_query(callback_query_id=call.id)
	except:
		client.send_message(call.message.chat.id, f'🚫 | Ошибка при выполнении команды')

@client.message_handler(commands=['ot'])
def sendmsgtouser(message):
	try:
		cid = message.chat.id

		msg = client.send_message(cid, f"👤 | Введите ID пользователя которому хотите отправить сообщение:")
		client.register_next_step_handler(msg, sendmsgtouser_next)
	except:
		client.send_message(cid, f'🚫 | Ошибка при выполнении команды')

def sendmsgtouser_next(message):
	try:
		cid = message.chat.id

		if message.text == message.text:
			global getsendmsgtouserid
			getsendmsgtouserid = int(message.text)
			msg = client.send_message(cid, f"📨 | Введите текст который хотите отправить пользователю:")
			client.register_next_step_handler(msg, sendmsgtouser_next_text)
	except:
		client.send_message(cid, f'🚫 | Ошибка при выполнении команды')

def sendmsgtouser_next_text(message):
	try:
		cid = message.chat.id

		if message.text == message.text:
			global getsendmsgtousertext
			getsendmsgtousertext = str(message.text)
			rmk = types.InlineKeyboardMarkup()
			item_yes = types.InlineKeyboardButton(text='✅',callback_data='sendmsgtouseryes')
			item_no = types.InlineKeyboardButton(text='❌',callback_data='sendmsgtouserno')
			rmk.add(item_yes, item_no)
			msg = client.send_message(cid, f"🔰 | Данные об отправке сообщения:\n\nID пользователя: {getsendmsgtouserid}\nТекст для отправки: {getsendmsgtousertext}\n\nОтправить сообщение?",reply_markup=rmk)
	except:
		client.send_message(cid, f'🚫 | Ошибка при выполнении команды')

@client.callback_query_handler(func=lambda call: call.data == 'sendmsgtouseryes' or call.data == 'sendmsgtouserno')
def sendmsgtouser_callback(call):
	try:
		if call.data == 'sendmsgtouseryes':
			client.delete_message(call.message.chat.id, call.message.message_id-0)
			client.send_message(call.message.chat.id, f"✉️ | Сообщение отправлено!")
			client.send_message(getsendmsgtouserid, f"✉️ | Администратор прислал вам сообщение:\n\n{getsendmsgtousertext}")
		elif call.data == 'sendmsgtouserno':
			client.delete_message(call.message.chat.id, call.message.message_id-0)
			client.send_message(call.message.chat.id, f"🚫 | Вы отменили отправку сообщения пользователю")
		client.answer_callback_query(callback_query_id=call.id)
	except:
		client.send_message(call.message.chat.id, f'🚫 | Ошибка при выполнении команды')

@client.message_handler(commands=['getid'])
def getiduser(message):
	try:
		cid = message.chat.id
		uid = message.from_user.id
		sql.execute(f"SELECT * FROM users WHERE id = {uid}")
		getaccess = sql.fetchone()[3]
		accessquery = 1
		if getaccess < accessquery:
			client.send_message(cid, f"⚠️ | У вас нет доступа!")
		else:
			msg = client.send_message(cid, 'Введите никнейм пользователя:')
			client.register_next_step_handler(msg, next_getiduser_name)
	except:
		client.send_message(cid, f'🚫 | Ошибка при выполнении команды')

def next_getiduser_name(message):
	try:
		cid = message.chat.id
		uid = message.from_user.id
		if message.text == message.text:
			getusername = message.text
			sql.execute(f"SELECT * FROM users WHERE nick = '{getusername}'")
			result = sql.fetchone()[0]
			client.send_message(cid, f'👤 | ID пользователя: {result}')
	except:
		client.send_message(cid, f'🚫 | Ошибка при выполнении команды')



client.polling(none_stop=True,interval=0)