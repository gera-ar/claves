from pdb import set_trace
import wx
from cryptography.fernet import Fernet, InvalidToken
from hashlib import sha256
from base64 import b64encode
from sqlite3 import connect
import os
from shutil import copy, move
from webbrowser import open_new_tab
from string import ascii_letters, digits
from random import sample, shuffle
from datetime import datetime
from configparser import ConfigParser
from subprocess import check_output
import accessible_output2.outputs.auto
from time import sleep
from pygame import mixer
mixer.init()

#Sounds:
ADD= mixer.Sound('sounds/add.ogg')
RECYCLE= mixer.Sound('sounds/recycle.ogg')
EXIT= mixer.Sound('sounds/exit.ogg')
EXIT.set_volume(0.7)
OK= mixer.Sound('sounds/ok.ogg')

def speak(message):
	accessible_output2.outputs.auto.Auto().speak(message)

def getHash(string):
	hash_obj= sha256(string.encode())
	return hash_obj.digest()

class Crypto():

	def __init__(self, password):
		self.cipher= Fernet(password)

	def encrypt(self, string):
		try:
			return self.cipher.encrypt(string.encode())
		except InvalidToken as e:
			wx.MessageDialog(None, 'Error de clave', '😟').ShowModal()

	def decrypt(self, value):
		try:
			return self.cipher.decrypt(value)
		except InvalidToken as e:
			wx.MessageDialog(None, 'Error de clave', '😟').ShowModal()

class Database():
	def __init__(self):
		self.connect= connect('crypto/db')
		self.cursor= self.connect.cursor()
		self.date= self.getDate()

	def getRowList(self):
		self.cursor.execute('SELECT * FROM passwords')
		row_list= self.cursor.fetchall()
		return row_list

	def modifyRow(self, old_service, service, user, password, extra):
		self.cursor.execute('DELETE from passwords where service=?', (old_service,))
		self.cursor.execute('INSERT INTO passwords VALUES (?,?,?,?,?)', (service, user, password, self.date, extra))
		self.connect.commit()

	def addRow(self, service, user, password, extra):
		entities= (crypto.encrypt(service), crypto.encrypt(user), crypto.encrypt(password), crypto.encrypt(self.date), crypto.encrypt(extra))
		self.cursor.execute('INSERT INTO passwords (service, user, password, date, extra) VALUES (?,?,?,?,?)', entities)
		self.connect.commit()

	def getDate(self):
		day= ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'][datetime.today().weekday()]
		now= datetime.now()
		date_format= f'{day}, {now.day}.{now.month}.{now.year}'
		return date_format

class Main(wx.Frame):
	def __init__(self, parent, title):
		super().__init__(parent, title= title, size=(400, 300))
		self.data= None
		self.Centre()
		
		if self.passVerify():
			self.getDatabase()
			self.InitUI()
			self.Show()

	def passVerify(self):
		pass_dialog= PassDialog(self, 'Acceso', '&Ingresar')
		pass_dialog.ShowModal()
		user= getHash(pass_dialog.password_field.GetValue())
		if password == b64encode(user):
			OK.play()
			return True
		else:
			wx.MessageDialog(None, 'Contraseña incorrecta', '👎').ShowModal()
			self.Destroy()

	def getDatabase(self):
		if not os.path.exists('crypto/db'):
			connection= connect('crypto/db')
			cursor= connection.cursor()
			cursor.execute('CREATE TABLE passwords(id INTEGER PRIMARY KEY AUTOINCREMENT, service BLOB, user BLOB, password BLOB, date BLOB, extra BLOB)')
			connection.commit()
			entities= (crypto.encrypt('ServicioDePrueba'), crypto.encrypt('NombreDeUsuario'), crypto.encrypt('MiContraseña'), crypto.encrypt('Sábado, 26.09.2015'), crypto.encrypt('DatosExtra'))
			cursor.execute('INSERT INTO passwords (service, user, password, date, extra) VALUES (?, ?, ?, ?, ?)', entities)
			connection.commit()
			connection.close()
			self.InitUI()
			# wx.MessageDialog(None, 'Proceso finalizado correctamente. No olvides tu contraseña, y recordá guardar el archivo clave en un lugar seguro', '✌').ShowModal()
			self.Show()

	def InitUI(self):
		panel= wx.Panel(self)
		vbox= wx.BoxSizer(wx.VERTICAL)

		self.database= Database()
		self.data= self.database.getRowList()
		self.row_list= [crypto.decrypt(row[1]).decode() for row in self.data]
		self.listbox= wx.ListBox(panel, size=(200, 200), choices=self.row_list)
		self.listbox.Bind(wx.EVT_KEY_DOWN, self.onKeyDown)
		if len(self.row_list) > 0:
			self.listbox.SetSelection(0)
		vbox.Add(self.listbox, wx.ID_ANY, wx.ALL | wx.EXPAND, 10)

		hbox = wx.BoxSizer(wx.HORIZONTAL)
		modify_button = wx.Button(panel, label='&Modificar')
		modify_button.Bind(wx.EVT_BUTTON, self.onModify)
		delete_button = wx.Button(panel, label='&Eliminar')
		delete_button.Bind(wx.EVT_BUTTON, self.onDelete)
		add_button = wx.Button(panel, label='&Añadir')
		add_button.Bind(wx.EVT_BUTTON, self.onAdd)
		close_button = wx.Button(panel, label='&Cerrar')
		close_button.Bind(wx.EVT_BUTTON, self.onClose)
		self.Bind(wx.EVT_CLOSE, self.onExit)

		menu_bar = wx.MenuBar()
		file_menu = wx.Menu()
		documentation= file_menu.Append(wx.ID_ANY, 'Documentación del programa')
		change_pass= file_menu.Append(wx.ID_ANY, 'Cambiar la contraseña de acceso')
		import_db= file_menu.Append(wx.ID_ANY, 'Importar base de datos existente')
		export_db= file_menu.Append(wx.ID_ANY, 'Exportar base de datos actual')
		export_file= file_menu.Append(wx.ID_ANY, 'Exportar archivo clave')
		menu_bar.Append(file_menu, '&Archivo')
		self.SetMenuBar(menu_bar)

		self.Bind(wx.EVT_MENU, self.onDocumentation, documentation)
		self.Bind(wx.EVT_MENU, self.onExportDb, export_db)
		self.Bind(wx.EVT_MENU, self.onImportDb, import_db)
		self.Bind(wx.EVT_MENU, self.onExportFile, export_file)
		self.Bind(wx.EVT_MENU, self.onChangePass, change_pass)


		hbox.Add(modify_button)
		hbox.Add(delete_button)
		hbox.Add(add_button)
		hbox.Add(close_button)
		vbox.Add(hbox, wx.ID_ANY, wx.ALL | wx.CENTER, 10)

		panel.SetSizer(vbox)

	def onExit(self, event):
		EXIT.play()
		sleep(EXIT.get_length())
		self.Destroy()

	def onDocumentation(self, event):
		open_new_tab('instrucciones.html')

	def onModify(self, event):
		id= self.data(self.listbox.GetSelection())[0]
		self.database.cursor.execute('SELECT * FROM passwords WHERE id=?', (id,))
		row_data= self.database.cursor.fetchall()[0]
		data_dialog= DataDialog(self, row_data[0], row_data[0], row_data[1], row_data[2], row_data[3], row_data[4], True)
		if data_dialog.ShowModal() == wx.ID_OK:
			service= data_dialog.service_field.GetValue()
			user= data_dialog.user_field.GetValue()
			password= data_dialog.password_field.GetValue()
			extra= data_dialog.extra_field.GetValue()
			self.database.modifyRow(self.listbox.GetStringSelection(), service, user, password, extra)
			index= self.listbox.GetSelection()
			self.listbox.Delete(index)
			self.listbox.Insert(service, index)
			self.listbox.Refresh()
			wx.MessageDialog(None, f'{service} modificado correctamente', '✌').ShowModal()

	def onDelete(self, event):
		self.database.cursor.execute('DELETE from passwords where service=?', (self.listbox.GetStringSelection(),))
		self.database.connect.commit()
		current_selection= self.listbox.GetSelection()
		if current_selection != wx.NOT_FOUND:
			self.row_list.pop(current_selection)
			self.listbox.Delete(current_selection)
			RECYCLE.play()
			if self.listbox.GetCount() < 1:
				speak('Lista vacía')
			elif current_selection > 0:
				self.listbox.SetSelection(current_selection-1)
			elif current_selection == 0 and self.listbox.GetCount() > 0:
				self.listbox.SetSelection(current_selection)

	def onAdd(self, event):
		dialog= Dialog(self, 'Añadir elemento')
		if dialog.ShowModal() == wx.ID_OK:
			service= dialog.service_field.GetValue()
			user= dialog.user_field.GetValue()
			password= dialog.pass_field.GetValue()
			extra= dialog.extra_field.GetValue()
			self.database.addRow(service, user, password, extra)
			self.row_list.append(service)
			self.row_list.sort()
			self.listbox.Clear()
			self.listbox.InsertItems(self.row_list, 0)
			self.listbox.SetStringSelection(service)
			self.data= self.database.getRowList()
			ADD.play()

	def onExportDb(self, event):
		self.database.encrypt(False)
		save_dialog = wx.FileDialog(None, 'Exportar la base de datos', style=wx.FD_SAVE)
		save_dialog.SetFilename('database')
		if save_dialog.ShowModal() == wx.ID_OK:
			file_path= save_dialog.GetPath().replace('\\', '/')
			move('database', file_path)
			wx.MessageDialog(None, 'Base de datos exportada correctamente', '✌').ShowModal()

	def onImportDb(self, event):
		self.database.connect.close()
		os.remove('database-open')
		browse_file= wx.FileDialog(self, "Buscar el archivo base de datos")
		if browse_file.ShowModal() == wx.ID_OK:
			path= browse_file.GetPath()
			copy(path, 'database')
			wx.MessageDialog(None, 'Base de datos importada correctamente. Vuelve a ejecutar el programa', '✌').ShowModal()
			self.Close()

	def onExportFile(self, event):
		config= ConfigParser()
		config.read('config')
		old_path= config['KeyFile']['path']
		# wx.MessageDialog(None, 'Archivo exportado correctamente', '✌').ShowModal()
		save_dialog= wx.FileDialog(None, 'Guardar el archivo clave', style=wx.FD_SAVE)
		if save_dialog.ShowModal() == wx.ID_OK:
			file_path= save_dialog.GetPath().replace('\\', '/')
			copy(old_path, file_path)
			wx.MessageDialog(None, f'Archivo guardado correctamente en la ruta: {file_path}', '✌').ShowModal()

	def onChangePass(self, event):
		pass_dialog= PassDialog(self, 'Cambiar contraseña', '&Guardar la nueva contraseña')
		pass_dialog.ShowModal()
		password= pass_dialog.password_field.GetValue().encode()
		with open(self.key_file_path, 'rb') as key_file:
			key= key_file.read()
		cipher= Fernet(key)
		password_c= cipher.encrypt(password)
		with open('code', 'wb') as code_file:
			code_file.write(password_c)
			wx.MessageDialog(None, 'Contraseña cambiada exitosamente', '👍').ShowModal()

	def onClose(self, event):
		# EXIT.play()
		self.Close()

	def onKeyDown(self, event):
		if event.GetKeyCode() == wx.WXK_DELETE:
			self.onDelete(event)
		elif event.ControlDown() and event.GetKeyCode() == 67:
			self.getValue(self.listbox.GetStringSelection(), 'password')
			event.Skip()
		elif event.ControlDown() and event.GetKeyCode() == 85:
			self.getValue(self.listbox.GetStringSelection(), 'user')
			event.Skip()
		elif event.ControlDown() and event.GetKeyCode() == 69:
			speak(f'{self.listbox.GetSelection()+1} de {self.listbox.GetCount()}')
		elif event.GetKeyCode() == wx.WXK_SPACE:
			id= self.data[self.listbox.GetSelection()][0]
			self.database.cursor.execute('SELECT * FROM passwords WHERE id=?', (id,))
			row_data= self.database.cursor.fetchall()[0]
			DataDialog(self, crypto.decrypt(row_data[1]), crypto.decrypt(row_data[1]), crypto.decrypt(row_data[2]), crypto.decrypt(row_data[3]), crypto.decrypt(row_data[4]), crypto.decrypt(row_data[5]), False).ShowModal()
		elif event.GetKeyCode() == wx.WXK_ESCAPE:
			self.onClose(event)
		else:
			event.Skip()

	def getValue(self, service, column):
		query= f'SELECT {column} FROM passwords WHERE service=?'
		self.database.cursor.execute(query, (service,))
		value= self.database.cursor.fetchall()[0][0]
		wx.TheClipboard.SetData(wx.TextDataObject(value))
		wx.TheClipboard.Close()
		speak('Copiado al portapapeles')

class Dialog(wx.Dialog):
	def __init__(self,parent, title):
		super().__init__(parent, title= title)

		Panel= wx.Panel(self)
		wx.StaticText(Panel, wx.ID_ANY, "Servicio")
		self.service_field= wx.TextCtrl(Panel, wx.ID_ANY, "")
		
		wx.StaticText(Panel, wx.ID_ANY, "Usuario")
		self.user_field= wx.TextCtrl(Panel, wx.ID_ANY, "")
		
		wx.StaticText(Panel, wx.ID_ANY, u"Contraseña")
		self.pass_field= wx.TextCtrl(Panel, wx.ID_ANY, "")
		self.random_button= wx.Button(Panel, label='&Crear contraseña aleatoria')
		self.random_button.Bind(wx.EVT_BUTTON, self.onRandomPass)

		wx.StaticText(Panel, wx.ID_ANY, "Extra")
		self.extra_field= wx.TextCtrl(Panel, wx.ID_ANY, "")

		self.ok_button= wx.Button(self, wx.ID_OK, "&Guardar")
		self.ok_button.SetDefault()
		self.cancel_button = wx.Button(self, wx.ID_CANCEL, "&Cancelar")

		self.SetAffirmativeId(self.ok_button.GetId())
		self.SetEscapeId(self.cancel_button.GetId())

	def onRandomPass(self, event):
		chars= list(ascii_letters+digits)
		password= ''.join(sample(chars, 12))
		self.pass_field.SetValue(password)
		self.pass_field.SetFocus()

class DataDialog(wx.Dialog):
	def __init__(self, parent, title, service, user, password, date, extra, text_button_save):
		super().__init__(parent, title=title)

		panel = wx.Panel(self)
		
		wx.StaticText(panel, label="Servicio:")
		self.service_field= wx.TextCtrl(panel, value=service)

		wx.StaticText(panel, label="Usuario:")
		self.user_field= wx.TextCtrl(panel, value=user)
		
		wx.StaticText(panel, label="Contraseña:")
		self.password_field= wx.TextCtrl(panel, value=password)
		self.user_field.SetFocus()
		
		wx.StaticText(panel, label="Fecha:")
		self.date_field= wx.TextCtrl(panel, value=date)
		
		wx.StaticText(panel, label="Datos extra:")
		self.extra_field= wx.TextCtrl(panel, value=extra)
		
		if text_button_save:
			wx.Button(self, wx.ID_OK, "&Guardar los cambios")
			wx.Button(self, wx.ID_CANCEL, "&Descartar los cambios")
		else:
			ok_button= wx.Button(self, wx.ID_OK, "&Cerrar")

class PassDialog(wx.Dialog):
	def __init__(self, parent, title, text_button):
		super().__init__(parent, title=title)

		panel = wx.Panel(self)
		
		wx.StaticText(panel, label='Ingresa la contraseña:')
		self.password_field= wx.TextCtrl(panel)
		# self.password_field.Bind(wx.EVT_KEY_DOWN, self.onKeyDown)
		
		ok_button= wx.Button(self, wx.ID_OK, text_button)

	def onKeyDown(self, event):
		if event.ControlDown() and event.GetKeyCode() == wx.EVT_TEXT_ENTER:
			self.Close()

app= wx.App()
if os.path.exists('crypto/hash'):
	with open('crypto/hash', 'rb') as file:
		password= file.read()
		crypto= Crypto(password)
	Main(None, 'Gestor de contraseñas')
	app.MainLoop()