import wx
from cryptography.fernet import Fernet, InvalidToken
from hashlib import sha256
from base64 import b64encode
from sqlite3 import connect
import os
from shutil import copy
from webbrowser import open_new_tab
from string import ascii_letters, digits
from random import sample, shuffle
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

crypto= None

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
			wx.MessageDialog(None, 'Contraseña incorrecta. Acceso denegado', '👎').ShowModal()
			return False


class Database():
	def __init__(self):
		self.connect= connect('lib/database')
		self.cursor= self.connect.cursor()

	def getRowList(self):
		self.cursor.execute('SELECT * FROM passwords ORDER BY service ASC')
		row_list= self.cursor.fetchall()
		return row_list

	def modifyRow(self, old_service, service, user, password, extra, card):
		self.cursor.execute('DELETE from passwords where service=?', (old_service,))
		self.connect.commit()
		self.cursor.execute('INSERT INTO passwords VALUES (?,?,?,?,?)', (service, user, password, extra, card))
		self.connect.commit()

	def addRow(self, service, user, password, extra, card):
		entities= (service, crypto.encrypt(user), crypto.encrypt(password), crypto.encrypt(extra), card)
		self.cursor.execute('INSERT INTO passwords VALUES (?,?,?,?,?)', entities)
		self.connect.commit()

class Main(wx.Frame):
	def __init__(self, parent, title):
		super().__init__(parent, title= title, size=(400, 300))
		self.data= None
		self.Centre()
		
		if self.passVerify():
			self.InitUI()
			self.Show()

	def passVerify(self):
		global crypto
		database.cursor.execute('SELECT * FROM passwords')
		if len(database.cursor.fetchall()) == 0:
			new_dialog= PassDialog(self, 'Registrar contraseña de acceso', 'Ingresa una contraseña de acceso', '&Guardar y continuar', '&Cancelar', False)
			if new_dialog.ShowModal() == wx.ID_OK:
				new_pass= getHash(new_dialog.password_field.GetValue())
				cipher= Fernet(b64encode(new_pass))
				database.cursor.execute('INSERT INTO passwords VALUES(?,?,?,?,?)', ('Servicio de prueba', cipher.encrypt('gera.ar'.encode()), cipher.encrypt('1234'.encode()), cipher.encrypt('Datos extra'.encode()), 0))
				database.connect.commit()
				wx.MessageDialog(None, 'Clave guardada exitosamente. Reinicia el programa', '👍').ShowModal()
				database.connect.close()
			self.Destroy()
			return
		pass_dialog= PassDialog(self, 'Acceso', 'Ingresa la contraseña:', '&Ingresar', '&Resetear la base de datos', True)
		login= pass_dialog.ShowModal()
		if login == wx.ID_CANCEL:
			if wx.MessageDialog(None, '¿Seguro que quieres resetear la base de datos?', 'Atención', wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION).ShowModal() == wx.ID_YES:
				database.cursor.execute('DELETE FROM passwords')
				database.connect.commit()
				database.connect.close()
				wx.MessageDialog(None, 'La base de datos ha sido reseteada correctamente', '👍').ShowModal()
			self.Destroy()
			return False
		try:
			user= getHash(pass_dialog.password_field.GetValue())
		except RuntimeError:
			return False
		crypto= Crypto(b64encode(user))
		database.cursor.execute('SELECT * FROM passwords')
		if not crypto.decrypt(database.cursor.fetchall()[0][1]):
			database.connect.close()
			self.Destroy()
			return False
		OK.play()
		return True

	def InitUI(self):
		panel= wx.Panel(self)
		vbox= wx.BoxSizer(wx.VERTICAL)

		self.data= database.getRowList()
		self.row_list= [row[0] for row in self.data]
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
		menu_bar.Append(file_menu, '&Archivo')
		self.SetMenuBar(menu_bar)

		self.Bind(wx.EVT_MENU, self.onDocumentation, documentation)
		self.Bind(wx.EVT_MENU, self.onExportDb, export_db)
		self.Bind(wx.EVT_MENU, self.onImportDb, import_db)
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
		service= self.listbox.GetStringSelection()
		database.cursor.execute('SELECT * FROM passwords WHERE service=?', (service,))
		row_data= database.cursor.fetchall()[0]
		data_dialog= DataDialog(self, row_data[0], row_data[0], crypto.decrypt(row_data[1]), crypto.decrypt(row_data[2]), crypto.decrypt(row_data[3]), row_data[4], True)
		if data_dialog.ShowModal() == wx.ID_OK:
			service= data_dialog.service_field.GetValue()
			user= crypto.encrypt(data_dialog.user_field.GetValue())
			password= crypto.encrypt(data_dialog.password_field.GetValue())
			extra= crypto.encrypt(data_dialog.extra_field.GetValue())
			database.modifyRow(self.listbox.GetStringSelection(), service, user, password, extra, row_data[4])
			index= self.listbox.GetSelection()
			self.listbox.Delete(index)
			self.listbox.Insert(service, index)
			self.listbox.Refresh()
			wx.MessageDialog(None, f'{service} modificado correctamente', '✌').ShowModal()

	def onDelete(self, event):
		database.cursor.execute('DELETE from passwords where service=?', (self.listbox.GetStringSelection(),))
		database.connect.commit()
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
			card= int(dialog.card_check_box.GetValue())
			service= dialog.service_field.GetValue()
			user= dialog.user_field.GetValue()
			password= dialog.pass_field.GetValue()
			extra= dialog.extra_field.GetValue()
			database.addRow(service, user, password, extra, card)
			self.row_list.append(service)
			self.row_list.sort()
			self.listbox.Clear()
			self.listbox.InsertItems(self.row_list, 0)
			self.listbox.SetStringSelection(service)
			self.data= database.getRowList()
			ADD.play()

	def onExportDb(self, event):
		save_dialog = wx.FileDialog(None, 'Exportar la base de datos', style=wx.FD_SAVE)
		save_dialog.SetFilename('database')
		if save_dialog.ShowModal() == wx.ID_OK:
			file_path= save_dialog.GetPath().replace('\\', '/')
			copy('lib/database', file_path)
			wx.MessageDialog(None, 'Base de datos exportada correctamente', '✌').ShowModal()

	def onImportDb(self, event):
		database.connect.close()
		browse_file= wx.FileDialog(self, "Buscar el archivo base de datos")
		if browse_file.ShowModal() == wx.ID_OK:
			path= browse_file.GetPath()
			os.remove('lib/database')
			copy(path, 'lib/database')
			wx.MessageDialog(None, 'Base de datos importada correctamente. Vuelve a ejecutar el programa', '✌').ShowModal()
		self.Destroy()

	def onChangePass(self, event):
		global crypto
		pass_dialog= PassDialog(self, 'Cambiar la contraseña de acceso', 'Ingresa una nueva contraseña de acceso', '&Guardar y continuar', '&Cancelar', False)
		question= pass_dialog.ShowModal()
		if question == wx.ID_OK:
			database.cursor.execute('SELECT * FROM passwords')
			rows= database.cursor.fetchall()
			new_hash= getHash(pass_dialog.password_field.GetValue())
			new_crypto= Crypto(b64encode(new_hash))
			database.cursor.execute('DELETE FROM passwords')
			database.connect.commit()
			for row in rows:
				old_row= (row[0], crypto.decrypt(row[1]).decode(), crypto.decrypt(row[2]).decode(), crypto.decrypt(row[3]).decode(), row[4])
				new_row= (old_row[0], new_crypto.encrypt(old_row[1]), new_crypto.encrypt(old_row[2]), new_crypto.encrypt(old_row[3]), old_row[4])
				database.cursor.execute('INSERT INTO passwords VALUES (?,?,?,?,?)', new_row)
				database.connect.commit()
			database.connect.close()
			self.Destroy()
			wx.MessageDialog(None, 'Contraseña cambiada exitosamente', '👍').ShowModal()

	def onClose(self, event):
		EXIT.play()
		database.connect.close()
		self.Destroy()
		sleep(0.1)

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
			service= self.listbox.GetStringSelection()
			database.cursor.execute('SELECT * FROM passwords WHERE service=?', (service,))
			row_data= database.cursor.fetchall()[0]
			DataDialog(self, row_data[0], row_data[0], crypto.decrypt(row_data[1]), crypto.decrypt(row_data[2]), crypto.decrypt(row_data[3]), row_data[4], False).ShowModal()
		elif event.GetKeyCode() == wx.WXK_ESCAPE:
			self.onClose(event)
		else:
			event.Skip()

	def getValue(self, service, column):
		query= f'SELECT {column} FROM passwords WHERE service = ?'
		database.cursor.execute(query, (service,))
		value= crypto.decrypt(database.cursor.fetchall()[0][0]).decode()
		wx.TheClipboard.SetData(wx.TextDataObject(value))
		wx.TheClipboard.Close()
		speak('Copiado al portapapeles')

class Dialog(wx.Dialog):
	def __init__(self,parent, title):
		super().__init__(parent, title= title)

		Panel= wx.Panel(self)
		self.card_check_box= wx.CheckBox(Panel, label='&Tarjeta')
		self.card_check_box.Bind(wx.EVT_CHECKBOX, self.onCard)
		self.service_name= wx.StaticText(Panel, wx.ID_ANY, "Servicio")
		self.service_field= wx.TextCtrl(Panel, wx.ID_ANY, "")
		
		self.user_number= wx.StaticText(Panel, wx.ID_ANY, "Usuario")
		self.user_field= wx.TextCtrl(Panel, wx.ID_ANY, "")
		
		self.password_expiration= wx.StaticText(Panel, wx.ID_ANY, u"Contraseña")
		self.pass_field= wx.TextCtrl(Panel, wx.ID_ANY, "")
		self.random_button= wx.Button(Panel, label='&Crear contraseña aleatoria')
		self.random_button.Bind(wx.EVT_BUTTON, self.onRandomPass)

		self.extra_key= wx.StaticText(Panel, wx.ID_ANY, "Extra")
		self.extra_field= wx.TextCtrl(Panel, wx.ID_ANY, "")

		self.ok_button= wx.Button(self, wx.ID_OK, "&Guardar")
		self.ok_button.SetDefault()
		self.cancel_button = wx.Button(self, wx.ID_CANCEL, "&Cancelar")

		self.SetAffirmativeId(self.ok_button.GetId())
		self.SetEscapeId(self.cancel_button.GetId())

	def onCard(self, event):
		if self.card_check_box.IsChecked():
			self.random_button.Hide()
			self.service_name.SetLabel('Nombre de tarjeta')
			self.user_number.SetLabel('Número de tarjeta')
			self.password_expiration.SetLabel('Fecha de vencimiento')
			self.extra_key.SetLabel('Clave')
		else:
			self.random_button.Show()
			self.service_name.SetLabel('Servicio')
			self.user_number.SetLabel('Usuario')
			self.password_expiration.SetLabel('Contraseña')
			self.extra_key.SetLabel('Datos extra')

	
	def onRandomPass(self, event):
		chars= list(ascii_letters+digits)
		password= ''.join(sample(chars, 12))
		self.pass_field.SetValue(password)
		self.pass_field.SetFocus()

class DataDialog(wx.Dialog):
	def __init__(self, parent, title, service, user, password, extra, card, text_button_save):
		super().__init__(parent, title=title)

		panel = wx.Panel(self)
		
		wx.StaticText(panel, label='Nombre de tarjeta:' if card else 'Servicio:')
		self.service_field= wx.TextCtrl(panel, value=service)

		wx.StaticText(panel, label='Número de tarjeta:' if card else 'Nombre de usuario:')
		self.user_field= wx.TextCtrl(panel, value=user)
		
		wx.StaticText(panel, label='Fecha de vencimiento:' if card else 'Contraseña:')
		self.password_field= wx.TextCtrl(panel, value=password)
		self.user_field.SetFocus()
		
		wx.StaticText(panel, label='Clave:' if card else 'Datos extra:')
		self.extra_field= wx.TextCtrl(panel, value=extra)
		
		if text_button_save:
			wx.Button(self, wx.ID_OK, "&Guardar los cambios")
			wx.Button(self, wx.ID_CANCEL, "&Descartar los cambios")
		else:
			ok_button= wx.Button(self, wx.ID_OK, "&Cerrar")

class PassDialog(wx.Dialog):
	def __init__(self, parent, title, static_value, ok_button, cancel_button, password_hide):
		super().__init__(parent, title=title)
		self.parent= parent

		panel = wx.Panel(self)
		wx.StaticText(panel, label=static_value)
		if password_hide:
			self.password_field= wx.TextCtrl(panel, style=wx.TE_PROCESS_ENTER | wx.TE_PASSWORD)
		else:
			self.password_field= wx.TextCtrl(panel, style=wx.TE_PROCESS_ENTER)
		self.password_field.Bind(wx.EVT_TEXT_ENTER, self.onEnter)
		
		wx.Button(self, wx.ID_OK, ok_button)
		wx.Button(self, wx.ID_CANCEL, cancel_button)
		self.Bind(wx.EVT_CHAR_HOOK, self.on_key_press)

	def onEnter(self, event):
		self.EndModal(wx.ID_OK)

	def on_key_press(self, event):
		keycode = event.GetKeyCode()
		if keycode == wx.WXK_ESCAPE:
			self.parent.Destroy()
		else:
			event.Skip()

app= wx.App()
database= Database()
Main(None, 'Gestor de contraseñas')
app.MainLoop()