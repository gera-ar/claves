import wx
from cryptography.fernet import Fernet, InvalidToken
from sqlite3 import connect
import os
from shutil import copy
from datetime import datetime
from configparser import ConfigParser
from subprocess import check_output
import accessible_output2.outputs.auto
from time import sleep
from pygame import mixer

app= wx.App()
mixer.init()

# Sounds:
ADD= mixer.Sound('sounds/add.ogg')
RECYCLE= mixer.Sound('sounds/recycle.ogg')
EXIT= mixer.Sound('sounds/exit.ogg')
EXIT.set_volume(0.7)
OK= mixer.Sound('sounds/ok.ogg')

def speak(message):
	accessible_output2.outputs.auto.Auto().speak(message)

def getUUID():
	return check_output('wmic csproduct get uuid').decode().split('\n')[1].strip()

def encryptFileOpen():
	try:
		config= ConfigParser()
		config.read('config')
		key_file_path= config['KeyFile']['path']
		with open(key_file_path, 'rb') as key_file:
			key= key_file.read()
		cipher= Fernet(key)
		with open('database-open', 'rb') as open_file:
			content= open_file.read()
		content_c= cipher.encrypt(content)
		with open('database', 'wb') as database_file:
			database_file.write(content_c)
			os.remove('database-open')
			wx.MessageDialog(None, 'Proceso finalizado correctamente. Vuelve a ejecutar el programa', '✌').ShowModal()
	except InvalidToken as e:
		wx.MessageDialog(None, 'Error en la lectura del archivo clave', '😟').ShowModal()

class Database():
	def __init__(self, key_file_path):
		self.key= self.getKey(key_file_path)
		self.cipher= Fernet(self.key)
		self.decrypt()
		self.connect= connect('database-open')
		self.cursor= self.connect.cursor()
		self.date= self.getDate()

	def decrypt(self):
		with open('database', 'rb') as encrypt_file:
			content_c= encrypt_file.read()
		content= self.cipher.decrypt(content_c)
		with open('database-open', 'wb') as decrypt_file:
			decrypt_file.write(content)
			os.remove('database')

	def encrypt(self):
		self.connect.close()
		with open('database-open', 'rb') as decrypt_file:
			content= decrypt_file.read()
		content_c= self.cipher.encrypt(content)
		with open('database', 'wb') as encrypt_file:
			encrypt_file.write(content_c)
			os.remove('database-open')

	def getRowList(self):
		self.cursor.execute('SELECT * FROM passwords ORDER BY service')
		row_list= self.cursor.fetchall()
		return row_list

	def modifyRow(self, old_service, service, user, password, extra):
		self.cursor.execute('DELETE from passwords where service=?', (old_service,))
		self.cursor.execute('INSERT INTO passwords VALUES (?,?,?,?,?)', (service, user, password, self.date, extra))
		self.connect.commit()

	def addRow(self, service, user, password, extra):
		self.cursor.execute('INSERT INTO passwords VALUES (?,?,?,?,?)', (service, user, password, self.date, extra))
		self.connect.commit()

	def getDate(self):
		day= ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'][datetime.today().weekday()]
		now= datetime.now()
		date_format= f'{day}, {now.day}.{now.month}.{now.year}'
		return date_format

	def getKey(self, key_file_path):
		try:
			with open(key_file_path, 'rb') as key_file:
				key= key_file.read()
			return key
		except FileNotFoundError:
			print('no se encontró el archivo key')
			return None

class Main(wx.Frame):
	def __init__(self, parent, title):
		super().__init__(parent, title= title, size=(400, 300))

		self.Centre()
		self.key_file_path= None
		self.key_file_content= None
		config_file= self.getConfig()
		if config_file:
			if self.passVerify():
				self.InitUI()
				self.Show()

	def passVerify(self):
		pass_dialog= PassDialog(self, 'Acceso', '&Ingresar')
		pass_dialog.ShowModal()
		if self.password == pass_dialog.password_field.GetValue():
			OK.play()
			return True
		else:
			wx.MessageDialog(None, 'Contraseña incorrecta', '👎').ShowModal()
			self.Destroy()



	def getConfig(self):
		if os.path.exists('config'):
			config= ConfigParser()
			config.read('config')
			self.key_file_path= config['KeyFile']['path']
			if not os.path.exists(self.key_file_path): self.browseFile()
			with open('code', 'rb') as code_file:
				password= code_file.read()
				self.password= self.decryptB(password).decode()
			return True
		else:
			key_file_message= 'Vamos a crear el archivo clave. El mismo quedará asociado a la base de datos, por lo que es importante realizar una copia en lugar seguro para no perder el acceso a la misma'
			wx.MessageDialog(None, key_file_message, 'Hola: ').ShowModal()
			save_dialog = wx.FileDialog(None, 'Guardar el archivo clave', style=wx.FD_SAVE)
			save_dialog.SetFilename('key')
			if save_dialog.ShowModal() == wx.ID_OK:
				file_path= save_dialog.GetPath().replace('\\', '/')
				self.key_file_path= file_path
				config= ConfigParser()
				self.key_file_content= Fernet.generate_key()
				with open(file_path, 'wb') as key_file:
					key_file.write(self.key_file_content)
			key_message= 'Ahora vamos a crear una contraseña de acceso para abrir el programa'
			wx.MessageDialog(None, key_message, '👍: ').ShowModal()
			pass_dialog= PassDialog(self, 'Configurar contraseña de acceso', '&Aceptar')
			pass_dialog.ShowModal()
			password= pass_dialog.password_field.GetValue().encode()
			password_c= self.encryptStr(password)
			with open('code', 'wb') as code_file:
				code_file.write(password_c)
			uuid= getUUID().encode()
			uuid_c= self.encryptStr(uuid)
			with open('uuid', 'wb') as uuid_file:
				uuid_file.write(uuid_c)
			config['KeyFile']= {'path': file_path}
			with open('config', 'w') as config_file:
				config.write(config_file)
			self.getDatabase()

	def browseFile(self):
		wx.MessageDialog(None, 'No se ha encontrado el archivo clave en la ruta especificada en la configuración. Vamos a buscarlo...', '😟').ShowModal()
		browse_file= wx.FileDialog(self, "Buscar archivo clave")
		if browse_file.ShowModal() == wx.ID_OK:
			path= browse_file.GetPath()
			self.key_file_path= path
			config= ConfigParser()
			config.read('config')
			config['KeyFile']= {'path': path}
			with open('config', 'w') as config_file:
				config.write(config_file)
		else:
			error_message= 'Sin ese archivo no se puede desencriptar la base de datos ni la contraseña, por favor elimina el archivo config y el archivo database y vuelve a ejecutar el programa. ¡Quieres que los elimine ahora?'
			question= wx.MessageDialog(None, error_message, '😟', wx.YES_NO | wx.ICON_QUESTION)
			if question.ShowModal() == wx.ID_YES:
				try:
					os.remove('config')
					os.remove('database')
					os.remove('database-open')
				except FileNotFoundError:
					pass
			self.Destroy()

	def encryptStr(self, str):
		cipher= Fernet(self.key_file_content)
		cipher_str= cipher.encrypt(str)
		return cipher_str

	def decryptB(self, object):
		try:
			with open(self.key_file_path, 'rb') as key_file:
				key= key_file.read()
				cipher= Fernet(key)
				string= cipher.decrypt(object)

		except InvalidToken as e:
			wx.MessageDialog(None, f'No se puede leer el archivo clave. Error {e.__str__}', 'Error').ShowModal()
			self.Close()
		return string

	def getDatabase(self):
		if not os.path.exists('database'):
			connection= connect('database-open')
			cursor= connection.cursor()
			cursor.execute('CREATE TABLE IF NOT EXISTS passwords (service TEXT, user TEXT, password TEXT, date TEXT, extra TEXT)')
			connection.commit()
			entities= ('ServicioDePrueba', 'NombreDeUsuario', 'MiContraseña', 'Sábado, 26.09.2015', 'DatosExtra')
			cursor.execute('INSERT INTO passwords (service, user, password, date, extra) VALUES (?, ?, ?, ?, ?)', entities)
			connection.commit()
			connection.close()
			self.encryptFile()
			self.InitUI()
			wx.MessageDialog(None, 'Proceso finalizado correctamente. No olvides tu contraseña, y recordá guardar el archivo clave en un lugar seguro', '✌').ShowModal()
			self.Show()

	def encryptFile(self):
		cipher= Fernet(self.key_file_content)
		with open('database-open', 'rb') as decrypt_file:
			content= decrypt_file.read()
		content_c= cipher.encrypt(content)
		with open('database', 'wb') as encrypt_file:
			encrypt_file.write(content_c)
		os.remove('database-open')

	def InitUI(self):
		panel= wx.Panel(self)
		vbox= wx.BoxSizer(wx.VERTICAL)

		self.database= Database(self.key_file_path)
		self.row_list= [row[0] for row in self.database.getRowList()]
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
		export_db = file_menu.Append(wx.ID_ANY, 'Exportar base de datos actual')
		import_db = file_menu.Append(wx.ID_ANY, 'Importar base de datos existente')
		export_file = file_menu.Append(wx.ID_ANY, 'Exportar archivo clave')
		change_pass = file_menu.Append(wx.ID_ANY, 'Cambiar la contraseña de acceso')
		menu_bar.Append(file_menu, '&Archivo')
		self.SetMenuBar(menu_bar)

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
		sleep(0.2)
		self.Destroy()

	def onModify(self, event):
		self.database.cursor.execute('SELECT * FROM passwords WHERE service=?', (self.listbox.GetStringSelection(),))
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
			ADD.play()

	def onExportDb(self, event):
		pass

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
		self.database.encrypt()
		EXIT.play()
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
			self.database.cursor.execute('SELECT * FROM passwords WHERE service=?', (self.listbox.GetStringSelection(),))
			row_data= self.database.cursor.fetchall()[0]
			DataDialog(self, row_data[0], row_data[0], row_data[1], row_data[2], row_data[3], row_data[4], False).ShowModal()
		elif event.GetKeyCode() == wx.WXK_ESCAPE:
			self.onClose(event)
		else:
			event.Skip()
			# print(event.GetKeyCode())

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

		wx.StaticText(Panel, wx.ID_ANY, "Extra")
		self.extra_field= wx.TextCtrl(Panel, wx.ID_ANY, "")

		self.ok_button= wx.Button(self, wx.ID_OK, "&Guardar")
		self.ok_button.SetDefault()
		self.cancel_button = wx.Button(self, wx.ID_CANCEL, "&Cancelar")

		self.SetAffirmativeId(self.ok_button.GetId())
		self.SetEscapeId(self.cancel_button.GetId())

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

if os.path.exists('database-open'):
	error_message= 'Ya hay una instancia abierta del programa. Si estás seguro que no hay ninguna ejecutándose, pulsa el botón restaurar para procesar los archivos e intentar abrirlo nuevamente'
	error_dialog= wx.MessageDialog(None, error_message, '😟', wx.YES_NO | wx.ICON_QUESTION)
	error_dialog.SetYesNoLabels("Restaurar", "Cancelar")
	if error_dialog.ShowModal() == wx.ID_YES:
		encryptFileOpen()
else:
	Main(None, 'Gestor de contraseñas')
	app.MainLoop()