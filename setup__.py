# Author: Gerardo Kessler [gera.ar@yahoo.com]
# Latest version of python tested==3.12

import wx
import ctypes
from platform import machine
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from base64 import b64encode
from mysql.connector import connect
import os
from json import load
import sys
from win32com.client import Dispatch
from shutil import copy
import psutil
from webbrowser import open_new_tab
from string import ascii_letters, digits
from random import sample, shuffle
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

# Función que verifica si el proceso tiene otras instancias abiertas, cerrando las que no coinciden con el pid del actual
def processVerify():
	pid= os.getpid()
	process_name= psutil.Process().name()
	similar_processes= [p for p in psutil.process_iter() if p.name() == process_name]
	
	for sp in similar_processes:
		if sp.pid != pid:
			sp.terminate()


# Función que devuelve el hash de una cadena
def getHash(string):
	hash_obj= hashes.Hash(hashes.SHA256(), backend= default_backend())
	hash_obj.update(string.encode())
	return hash_obj.finalize()

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
		with open('_internal/host', 'r') as file:
			data= load(file)
		self.connect= connect(
			host= data['host'],
			user= data['user'],
			password= data['password'], database= data['database']
		)
		self.cursor= self.connect.cursor()

	def getRowList(self):
		self.cursor.execute('SELECT * FROM claves ORDER BY service ASC')
		row_list= self.cursor.fetchall()
		return row_list

	def modifyRow(self, old_service, service, user, password, extra, card):
<<<<<<< HEAD:setup__.py
		self.cursor.execute('UPDATE passwords SET service=?, user=?, password=?, extra=?, card=? WHERE service=?', (service, user, password, extra, card, old_service))
=======
		self.cursor.execute('DELETE from claves where service = %s', (old_service,))
		self.connect.commit()
		self.cursor.execute('INSERT INTO claves VALUES (%s, %s, %s, %s, %s)', (service, user, password, extra, card))
>>>>>>> af310c010964dd661af1990e6c30ae5f52956294:setup.py
		self.connect.commit()

	def addRow(self, service, user, password, extra, card):
		entities= (service, crypto.encrypt(user), crypto.encrypt(password), crypto.encrypt(extra), card)
		self.cursor.execute('INSERT INTO claves VALUES (%s, %s, %s, %s, %s)', entities)
		self.connect.commit()

class Main(wx.Frame):
	def __init__(self, parent, title):
		super().__init__(parent, title= title, size=(400, 300))
		self.data= None
		self.Centre()
		
		if self.passVerify():
			self.InitUI()
			self.Show()

	# Crear un acceso directo con atajo de teclado alt + control + c
	def verifyShortcut(self):
		if os.path.exists(os.path.join(os.environ['USERPROFILE'], 'Desktop', 'claves.lnk')): return
		desktop= os.path.join(os.environ['USERPROFILE'], 'Desktop')
		message= '¿Crear un acceso directo al programa en el escritorio llamado claves con el atajo alt + control + c?'
		dlg= wx.MessageDialog(None, f'{desktop}\\claves', message, wx.YES_NO | wx.ICON_QUESTION)
		if dlg.ShowModal() == wx.ID_YES:
			path= os.path.join(desktop, 'claves.lnk')
			target= os.path.abspath(sys.argv[0])
			wDir= os.getcwd()
			shell= Dispatch('WScript.Shell')
			shortcut= shell.CreateShortcut(path)
			shortcut.Targetpath = target
			shortcut.WorkingDirectory= wDir
			shortcut.save()
			shortcut_key= shell.CreateShortcut(path)
			shortcut_key.Hotkey= 'Ctrl+Alt+C'
			shortcut_key.Save()

	def passVerify(self):
		global crypto
		database.cursor.execute('SELECT * FROM claves')
		if len(database.cursor.fetchall()) == 0:
			self.verifyShortcut()
			new_dialog= PassDialog(self, 'Registrar contraseña de acceso', 'Ingresa una contraseña de acceso', '&Guardar y continuar', '&Cancelar', False)
			if new_dialog.ShowModal() == wx.ID_OK:
				new_pass= getHash(new_dialog.password_field.GetValue())
				cipher= Fernet(b64encode(new_pass))
				database.cursor.execute('INSERT INTO claves VALUES(%s, %s, %s, %s, %s)', ('Servicio de prueba', cipher.encrypt('gera.ar'.encode()), cipher.encrypt('1234'.encode()), cipher.encrypt('Datos extra'.encode()), 0))
				database.connect.commit()
				wx.MessageDialog(None, 'Clave guardada exitosamente. Reinicia el programa', '👍').ShowModal()
				database.connect.close()
			self.Destroy()
			return
		pass_dialog= PassDialog(self, 'Acceso', 'Ingresa la contraseña:', '&Ingresar', '&Resetear la base de datos', True)
		login= pass_dialog.ShowModal()
		if login == wx.ID_CANCEL:
			if wx.MessageDialog(None, '¿Seguro que quieres resetear la base de datos?', 'Atención', wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION).ShowModal() == wx.ID_YES:
				database.cursor.execute('DELETE FROM claves')
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
		database.cursor.execute('SELECT * FROM claves')
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
		database.cursor.execute('SELECT * FROM claves WHERE service = %s', (service,))
		row_data= database.cursor.fetchall()[0]
		data_dialog= DataDialog(self, row_data[0], row_data[0], crypto.decrypt(row_data[1]), crypto.decrypt(row_data[2]), crypto.decrypt(row_data[3]), row_data[4], True)
		if data_dialog.ShowModal() == wx.ID_OK:
			service= data_dialog.service_field.GetValue()
			if service == '':
				wx.MessageDialog(None, 'El primer campo no puede quedar vacío. Proceso cancelado', 'Error:').ShowModal()
				return
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
<<<<<<< HEAD:setup__.py
		selected_element= self.listbox.GetStringSelection()
		dlg= wx.MessageDialog(None, '¿Seguro que quieres eliminar {}?'.format(selected_element), 'Atención', wx.YES_NO | wx.ICON_QUESTION)
		if dlg.ShowModal() == wx.ID_NO: return
		database.cursor.execute('DELETE from passwords where service=?', (selected_element,))
=======
		database.cursor.execute('DELETE from claves where service = %s', (self.listbox.GetStringSelection(),))
>>>>>>> af310c010964dd661af1990e6c30ae5f52956294:setup.py
		database.connect.commit()
		current_selection= self.listbox.GetSelection()
		if current_selection != wx.NOT_FOUND:
			self.row_list.pop(current_selection)
			self.listbox.Delete(current_selection)
			RECYCLE.play()
			if self.listbox.GetCount() < 1:
				sp.speak('Lista vacía')
			elif current_selection > 0:
				self.listbox.SetSelection(current_selection-1)
			elif current_selection == 0 and self.listbox.GetCount() > 0:
				self.listbox.SetSelection(current_selection)

	def onAdd(self, event):
		dialog= Dialog(self, 'Añadir elemento')
		if dialog.ShowModal() == wx.ID_OK:
			card= int(dialog.card_check_box.GetValue())
			service= dialog.service_field.GetValue()
			if service == '':
				wx.MessageDialog(None, f'El campo {"Tarjeta" if card else "Servicio"} no puede quedar vacío', 'Error:').ShowModal()
				return
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
			copy('_internal/database', file_path)
			wx.MessageDialog(None, 'Base de datos exportada correctamente', '✌').ShowModal()

	def onImportDb(self, event):
		database.connect.close()
		browse_file= wx.FileDialog(self, "Buscar el archivo base de datos")
		if browse_file.ShowModal() == wx.ID_OK:
			path= browse_file.GetPath()
			os.remove('_internal/database')
			copy(path, '_internal/database')
			wx.MessageDialog(None, 'Base de datos importada correctamente. Vuelve a ejecutar el programa', '✌').ShowModal()
		self.Destroy()

	def onChangePass(self, event):
		global crypto
		pass_dialog= PassDialog(self, 'Cambiar la contraseña de acceso', 'Ingresa una nueva contraseña de acceso', '&Guardar y continuar', '&Cancelar', False)
		question= pass_dialog.ShowModal()
		if question == wx.ID_OK:
			database.cursor.execute('SELECT * FROM claves')
			rows= database.cursor.fetchall()
			new_hash= getHash(pass_dialog.password_field.GetValue())
			new_crypto= Crypto(b64encode(new_hash))
			database.cursor.execute('DELETE FROM claves')
			database.connect.commit()
			for row in rows:
				old_row= (row[0], crypto.decrypt(row[1]).decode(), crypto.decrypt(row[2]).decode(), crypto.decrypt(row[3]).decode(), row[4])
				new_row= (old_row[0], new_crypto.encrypt(old_row[1]), new_crypto.encrypt(old_row[2]), new_crypto.encrypt(old_row[3]), old_row[4])
				database.cursor.execute('INSERT INTO claves VALUES (%s, %s, %s, %s, %s)', new_row)
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
			sp.speak(f'{self.listbox.GetSelection()+1} de {self.listbox.GetCount()}')
		elif event.GetKeyCode() == wx.WXK_SPACE:
			service= self.listbox.GetStringSelection()
			database.cursor.execute('SELECT * FROM claves WHERE service = %s', (service,))
			row_data= database.cursor.fetchall()[0]
			DataDialog(self, row_data[0], row_data[0], crypto.decrypt(row_data[1]), crypto.decrypt(row_data[2]), crypto.decrypt(row_data[3]), row_data[4], False).ShowModal()
		elif event.GetKeyCode() == wx.WXK_ESCAPE:
			self.onClose(event)
		else:
			event.Skip()

	def getValue(self, service, column):
		query= f'SELECT {column} FROM claves WHERE service = %s'
		database.cursor.execute(query, (service,))
		value= crypto.decrypt(database.cursor.fetchall()[0][0]).decode()
		wx.TheClipboard.SetData(wx.TextDataObject(value))
		wx.TheClipboard.Close()
		sp.speak('Copiado al portapapeles')

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
		
		if not text_button_save:
			wx.StaticText(panel, label='Nombre de tarjeta:' if card else 'Servicio:')
			self.service_field= wx.TextCtrl(panel, value=service, style=wx.TE_READONLY | wx.TE_MULTILINE)
			
			wx.StaticText(panel, label='Número de tarjeta:' if card else 'Usuario:')
			self.user_field= wx.TextCtrl(panel, value=user, style=wx.TE_READONLY | wx.TE_MULTILINE)
			
			wx.StaticText(panel, label='Fecha de vencimiento:' if card else 'Contraseña:')
			self.password_field= wx.TextCtrl(panel, value=password, style=wx.TE_READONLY | wx.TE_MULTILINE)
			self.user_field.SetFocus()
			
			wx.StaticText(panel, label='Clave:' if card else 'Datos extra:')
			self.extra_field= wx.TextCtrl(panel, value=extra, style=wx.TE_READONLY | wx.TE_MULTILINE)
			
			ok_button= wx.Button(self, wx.ID_OK, "&Cerrar")
		else:
			wx.StaticText(panel, label='Nombre de tarjeta:' if card else 'Servicio:')
			self.service_field= wx.TextCtrl(panel, value=service)
			
			wx.StaticText(panel, label='Número de tarjeta:' if card else 'Usuario:')
			self.user_field= wx.TextCtrl(panel, value=user)
			
			wx.StaticText(panel, label='Fecha de vencimiento:' if card else 'Contraseña:')
			self.password_field= wx.TextCtrl(panel, value=password)
			self.user_field.SetFocus()
			
			wx.StaticText(panel, label='Clave:' if card else 'Datos extra:')
			self.extra_field= wx.TextCtrl(panel, value=extra)
			
			wx.Button(self, wx.ID_OK, "&Guardar los cambios")
			wx.Button(self, wx.ID_CANCEL, "&Descartar los cambios")

class PassDialog(wx.Dialog):
	def __init__(self, parent, title, static_value, ok_button, cancel_button, password_hide):
		super().__init__(parent, title=title)
		self.parent= parent
		self.password_hide= password_hide

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
		if event.GetKeyCode() == wx.WXK_ESCAPE:
			if self.password_hide:
				self.Destroy()
				self.parent.Destroy()
		else:
			event.Skip()

if __name__ == '__main__':
	if getattr(sys, 'frozen', False):
		processVerify()

class Speech:
	def __init__(self):
		try:
			import accessible_output2.outputs.auto
			output= accessible_output2.outputs.auto.Auto()
			self.speak= self.accessibleOutput
		except:
			if machine() == 'AMD64':
				self.nvda= ctypes.WinDLL('_internal/nvda64.dll')
			else:
				self.nvda= ctypes.WinDLL('_internal/nvda32.dll')
			try:
				self.jaws= Dispatch('freedomSci.jawsApi')
			except pywintypes.com_error:
				self.jaws= None
			self.speak= self.nvdaJaws

	def accessibleOutput(self, message):
		output.speak(message)

	def nvdaJaws(self, message):
		wstr= ctypes.c_wchar_p(message)
		self.nvda.nvdaController_speakText(wstr)
		if self.jaws:
			self.jaws.SayString(message)

sp= Speech()
app= wx.App()
try:
	database= Database()
	Main(None, 'Gestor de contraseñas')
	app.MainLoop()
except:
	speak('Error en la conexión con la base de datos')
