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
sql.execute("""CREATE TABLE IF NOT EXISTS shop (id INT, name TEXT, price INT, tovar TEXT)""")
db.commit()

@client.message_handler(commands=['start'])
def start(message):
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


@client.message_handler(commands=['profile', 'myinfo', 'myprofile'])
def myprofile(message):
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
		client.send_message(cid, f"*Твой профиль:*\n\nВаш ID: {info[0]}\nБаланс: {info[2]}\nУровень доступа: {accessname}\nКуплено товаров: {info[4]}", parse_mode='Markdown')

@client.message_handler(commands=['getprofile', 'info'])
def getprofile(message):
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

def getprofile_next(message):
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
			client.send_message(cid, f"*Профиль {info[1]}:*\n\nВаш ID: {info[0]}\nБаланс: {info[2]}\nУровень доступа: {accessname}\nКуплено товаров: {info[4]}",parse_mode='Markdown')

@client.message_handler(commands=['addbuy'])
def addbuy(message):
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

def addbuy_id(message):
	cid = message.chat.id
	uid = message.from_user.id
	if message.text == message.text:
		global addbuyid
		addbuyid = message.text
		msg = client.send_message(cid, '*Введите цену товара:*',parse_mode='Markdown')
		client.register_next_step_handler(msg, addbuy_price)

def addbuy_price(message):
	cid = message.chat.id
	uid = message.from_user.id
	if message.text == message.text:
		global addbuyprice
		addbuyprice = message.text
		msg = client.send_message(cid, '*Введите название товара:*',parse_mode='Markdown')
		client.register_next_step_handler(msg, addbuy_name)

def addbuy_name(message):
	cid = message.chat.id
	uid = message.from_user.id
	if message.text == message.text:
		global addbuyname
		addbuyname = message.text
		msg = client.send_message(cid, '*Введите ссылку на товар:*',parse_mode='Markdown'	)
		client.register_next_step_handler(msg, addbuy_result)

def addbuy_result(message):
	cid = message.chat.id
	uid = message.from_user.id
	if message.text == message.text:
		global addbuytovar
		addbuytovar = message.text
		sql.execute(f"SELECT name FROM shop WHERE name = '{addbuyname}'")
		if sql.fetchone() is None:
			sql.execute(f"INSERT INTO shop VALUES ({addbuyid}, '{addbuyname}', {addbuyprice}, '{addbuytovar}')")
			db.commit()
			sql.execute(f"SELECT * FROM shop WHERE name = '{addbuyname}'")
			client.send_message(cid, f'✅ | Вы успешно добавили товар\nID товара: {sql.fetchone()[0]}\nИмя: {addbuyname}\nЦена: {addbuyprice}\nСсылка на товар: {addbuytovar}')
		else:
			client.send_message(cid, f"⛔️ | Данный товар уже добавлен!")

@client.message_handler(commands=['buy'])
def buy(message):
	cid = message.chat.id
	uid = message.from_user.id

	text = '🛒 | *Список товаров*\n\n'
	for info in sql.execute(f"SELECT * FROM users WHERE id = {uid}"):
		for infoshop in sql.execute(f"SELECT * FROM shop"):
			text += f"{infoshop[0]}. {infoshop[1]}\nЦена: {infoshop[2]}\n\n"
		msg = client.send_message(cid, f'{text}\n\nДля приобретения товара напишите айди товара\nПример: 1',parse_mode='Markdown')
		client.register_next_step_handler(msg, buy_next)

def buy_next(message):
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
					item_yes = types.InlineKeyboardButton(text='Да',callback_data='buytovaryes')
					item_no = types.InlineKeyboardButton(text='Отмена',callback_data='buytovarno')
					rmk.add(item_yes, item_no)
					msg = client.send_message(cid, f"💸 | Вы подверждаете покупку товара?\n\nВернуть средства за данный товар НЕВОЗМОЖНО.",reply_markup=rmk)

@client.callback_query_handler(lambda call: call.data == 'buytovaryes' or call.data == 'buytovarno')
def buy_callback(call):
	if call.data == 'buytovaryes':
		for info in sql.execute(f"SELECT * FROM users WHERE id = {call.from_user.id}"):
			for infoshop in sql.execute(f"SELECT * FROM shop WHERE id = {tovarid}"):
				cashtovar = int(info[2] - infoshop[2])
				boughttovar = int(info[4] + 1)
				sql.execute(f"SELECT * FROM users WHERE id = {call.from_user.id}")
				client.delete_message(call.message.chat.id, call.message.message_id-0)
				client.send_message(call.message.chat.id, f"✅ | Вы успешно купили товар\n\nНазвание товара: {infoshop[1]}\nЦена: {infoshop[2]}\n\nТовар: {infoshop[3]}\n\nСпасибо за покупку!")
				sql.execute(f"UPDATE users SET cash = {cashtovar} WHERE id = {call.from_user.id}")
				sql.execute(f"UPDATE users SET bought = {boughttovar} WHERE id = {call.from_user.id}")
				db.commit()
	elif call.data == 'buytovarno':
		client.send_message(call.message.chat.id, f"❌ | Вы отменили покупку товара!")
	client.answer_callback_query(callback_query_id=call.id)

@client.message_handler(commands=['donate'])
def donate(message):
	cid = message.chat.id
	global uid
	uid = message.from_user.id


	msg = client.send_message(cid, f"*💰 | Введите сумму для пополнения:*",parse_mode='Markdown')
	client.register_next_step_handler(msg, donate_value)

def donate_value(message):
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
		item_yes = types.InlineKeyboardButton(text='Да',callback_data='donateyes')
		item_no = types.InlineKeyboardButton(text='Отмена',callback_data='donateno')
		rmk.add(item_yes, item_no)
		global qiwibalancebe
		qiwibalancebe = api.balance
		msg = client.send_message(cid, f"🔰 | Заявка на пополнение средств успешно создана\n\nВы действительно хотите пополнить средства?",parse_mode='Markdown',reply_markup=rmk)

def donateyesoplacheno(message):
	cid = message.chat.id
	uid = message.from_user.id
	removekeyboard = types.ReplyKeyboardRemove()
	if message.text == '✅ Оплачено':
		client.send_message(cid, f"✉️ | Ваш запрос отправлен администраторам, ожидайте одобрения и выдачи средств.",reply_markup=removekeyboard)
		client.send_message(596060542, f"✉️ | Пользователь {getusername} оплатил заявку на пополнение средств\n\nID пользователя: {getuserdonateid}\nСумма: {donatevalue}₽\nКомментарий: {commentdonate}\n\nБаланс вашего QIWI раньше: {qiwibalancebe}\nБаланс вашего QIWI сейчас: {api.balance}\n\nПерепроверьте верность оплаты затем подтвердите выдачу средств.\nДля выдачи средств напишите: /giverub")

@client.callback_query_handler(lambda call: call.data == 'donateyes' or call.data == 'donateno')
def donate_result(call):
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
		client.send_message(cid, '*Помощь по командам:*\n\n/profile - Посмотреть свой профиль\n/help - Посмотреть список команд\n/buy - Купить товар\n\nАдмин-команды:\n\n/info - Посмотреть чужой профиль\n/access - Выдать уровень доступа\n/giverub - Выдать деньги на баланс\n/getid - Узнать айди пользователя',parse_mode='Markdown')
	else:
		client.send_message(cid, '*Помощь по командам:*\n\n/profile - Посмотреть свой профиль\n/help - Посмотреть список команд\n/buy - Купить товар',parse_mode='Markdown')

@client.message_handler(commands=['access', 'setaccess', 'dostup'])
def setaccess(message):
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

def access_user_id_answer(message):
	cid = message.chat.id
	uid = message.from_user.id
	if message.text == message.text:
		global usridaccess
		usridaccess = message.text
		rmk = types.ReplyKeyboardMarkup(resize_keyboard=True)
		rmk.add(types.KeyboardButton('Пользователь'), types.KeyboardButton('Администратор'), types.KeyboardButton('Разработчик'))
		msg = client.send_message(cid, 'Какой уровень доступа Вы хотите выдать?:', reply_markup=rmk, parse_mode="Markdown")
		client.register_next_step_handler(msg, access_user_access_answer)

def access_user_access_answer(message):
	global accessgaved
	global accessgavedname
	cid = message.chat.id
	uid = message.from_user.id
	rmk = types.InlineKeyboardMarkup()
	access_yes = types.InlineKeyboardButton(text='Да',callback_data='setaccessyes')
	access_no = types.InlineKeyboardButton(text='Нет',callback_data='setaccessno')
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

@client.callback_query_handler(lambda call: call.data == 'setaccessyes' or call.data == 'setaccessno')
def access_user_gave_access(call):
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

def rubles_user_id_answer(message):
	cid = message.chat.id
	uid = message.from_user.id
	if message.text == message.text:
		global usridrubles
		usridrubles = message.text
		rmk = types.ReplyKeyboardMarkup(resize_keyboard=True)
		rmk.add(types.KeyboardButton('10'), types.KeyboardButton('100'), types.KeyboardButton('1000'), types.KeyboardButton('Другая сумма'))
		msg = client.send_message(cid, 'Выберите сумму для выдачи:', reply_markup=rmk, parse_mode="Markdown")
		client.register_next_step_handler(msg, rubles_user_rubles_answer)

def rubles_user_rubles_answer(message):
	cid = message.chat.id
	uid = message.from_user.id
	global rublesgavedvalue
	removekeyboard = types.ReplyKeyboardRemove()
	rmk = types.InlineKeyboardMarkup()
	access_yes = types.InlineKeyboardButton(text='Да',callback_data='giverublesyes')
	access_no = types.InlineKeyboardButton(text='Нет',callback_data='giverublesno')
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

def rubles_user_rubles_answer_other(message):
	cid = message.chat.id
	uid = message.from_user.id
	global rublesgavedvalue
	rmk = types.InlineKeyboardMarkup()
	access_yes = types.InlineKeyboardButton(text='Да',callback_data='giverublesyes')
	access_no = types.InlineKeyboardButton(text='Нет',callback_data='giverublesno')
	rmk.add(access_yes, access_no)
	for info in sql.execute(f"SELECT * FROM users WHERE id = {usridrubles}"):
		if message.text == message.text:
			rublesgavedvalue = int(message.text)
			client.send_message(cid, f'Данные для выдачи:\nID пользователя: {usridrubles} ({info[1]})\nСумма: {rublesgavedvalue}\n\nВерно?',reply_markup=rmk)

@client.callback_query_handler(func=lambda call: call.data == 'giverublesyes' or call.data == 'giverublesno')
def rubles_gave_rubles_user(call):
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

@client.message_handler(commands=['getid'])
def getiduser(message):
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

def next_getiduser_name(message):
	cid = message.chat.id
	uid = message.from_user.id
	if message.text == message.text:
		getusername = message.text
		sql.execute(f"SELECT * FROM users WHERE nick = '{getusername}'")
		result = sql.fetchone()[0]
		client.send_message(cid, f'👤 | ID пользователя: {result}')



client.polling(none_stop=True,interval=0)