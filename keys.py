import wx
from clipboard import copy
from cryptography.fernet import Fernet
from sqlite3 import connect
import os
from datetime import datetime
from winsound import PlaySound, SND_FILENAME

class Database():
	def __init__(self):
		self.key= self.getKey()
		self.cipher= Fernet(self.key)
		self.decrypt()
		self.connect= connect('e:/recetas-open')
		self.cursor= self.connect.cursor()
		self.date= self.getDate()

	def decrypt(self):
		try:
			with open('e:/recetas', 'rb') as encrypt_file:
				content_c= encrypt_file.read()
		except FileNotFoundError:
			return None
		content= self.cipher.decrypt(content_c)
		with open('e:/recetas-open', 'wb') as decrypt_file:
			decrypt_file.write(content)
			os.remove('e:/recetas')

	def encrypt(self):
		self.connect.close()
		try:
			with open('e:/recetas-open', 'rb') as decrypt_file:
				content= decrypt_file.read()
		except FileNotFoundError:
			return None
		content_c= self.cipher.encrypt(content)
		with open('e:/recetas', 'wb') as encrypt_file:
			encrypt_file.write(content_c)
			os.remove('e:/recetas-open')

	def getRowList(self):
		self.cursor.execute('SELECT * FROM data ORDER BY service')
		row_list= self.cursor.fetchall()
		return row_list

	def modifyRow(self, old_service, service, user, password, extra):
		self.cursor.execute('DELETE from data where service=?', (old_service,))
		self.cursor.execute('INSERT INTO data VALUES (?,?,?,?,?)', (service, user, password, self.date, extra))
		self.connect.commit()

	def addRow(self, service, user, password, extra):
		self.cursor.execute('INSERT INTO data VALUES (?,?,?,?,?)', (service, user, password, self.date, extra))
		self.connect.commit()

	def getDate(self):
		day= ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'][datetime.today().weekday()]
		now= datetime.now()
		date_format= f'{day}, {now.day}.{now.month}.{now.year}'
		return date_format

	def getKey(self):
		try:
			with open('e:/recetas-k', 'rb') as key_file:
				key= key_file.read()
			return key
		except FileNotFoundError:
			return None



class Main(wx.Frame):
	def __init__(self, parent, title):
		super().__init__(parent, title= title, size=(400, 300))

		self.InitUI()
		self.Centre()
		self.Show()

	def InitUI(self):
		panel= wx.Panel(self)
		vbox= wx.BoxSizer(wx.VERTICAL)

		self.database= Database()
		self.row_list= [row[0] for row in self.database.getRowList()]
		self.listbox= wx.ListBox(panel, size=(200, 200), choices=self.row_list)
		self.listbox.Bind(wx.EVT_KEY_DOWN, self.onKeyDown)
		self.listbox.SetSelection(1)
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

		hbox.Add(modify_button)
		hbox.Add(delete_button)
		hbox.Add(add_button)
		hbox.Add(close_button)
		vbox.Add(hbox, wx.ID_ANY, wx.ALL | wx.CENTER, 10)

		panel.SetSizer(vbox)

	def onModify(self, event):
		self.database.cursor.execute('SELECT * FROM data WHERE service=?', (self.listbox.GetStringSelection(),))
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
		self.database.cursor.execute('DELETE from data where service=?', (self.listbox.GetStringSelection(),))
		self.database.connect.commit()
		current_selection= self.listbox.GetSelection()
		if current_selection != wx.NOT_FOUND:
			self.listbox.Delete(current_selection)
			PlaySound('C:/Windows/Media/Windows Recycle.wav', SND_FILENAME)

	def onAdd(self, event):
		dialog= Dialog(self, 'Añadir contraseña')
		if dialog.ShowModal() == wx.ID_OK:
			service= dialog.service_field.GetValue()
			user= dialog.user_field.GetValue()
			password= dialog.pass_field.GetValue()
			extra= dialog.extra_field.GetValue()
			self.database.addRow(service, user, password, extra)
			self.row_list.append((service, user, password, self.database.date, extra))
			self.listbox.Append(service)
			wx.MessageDialog(None, f'{service} añadido correctamente', '✌').ShowModal()

	def onClose(self, event):
		self.database.encrypt()
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
		elif event.GetKeyCode() == wx.WXK_SPACE:
			self.database.cursor.execute('SELECT * FROM data WHERE service=?', (self.listbox.GetStringSelection(),))
			row_data= self.database.cursor.fetchall()[0]
			DataDialog(self, row_data[0], row_data[0], row_data[1], row_data[2], row_data[3], row_data[4], False).ShowModal()
		elif event.GetKeyCode() == wx.WXK_ESCAPE:
			self.onClose(event)
		else:
			event.Skip()
			# print(event.GetKeyCode())

	def getValue(self, service, column):
		query= f'SELECT {column} FROM data WHERE service=?'
		self.database.cursor.execute(query, (service,))
		value= self.database.cursor.fetchall()[0][0]
		wx.TheClipboard.SetData(wx.TextDataObject(value))
		wx.TheClipboard.Close()
		PlaySound('C:/Windows/Media/Windows Startup.wav', SND_FILENAME)

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
		self.password_field.SetFocus()
		
		wx.StaticText(panel, label="Fecha:")
		self.date_field= wx.TextCtrl(panel, value=date)
		
		wx.StaticText(panel, label="Datos extra:")
		self.extra_field= wx.TextCtrl(panel, value=extra)
		
		if text_button_save:
			wx.Button(self, wx.ID_OK, "&Guardar los cambios")
			wx.Button(self, wx.ID_CANCEL, "&Descartar los cambios")
		else:
    			ok_button= wx.Button(self, wx.ID_OK, "&Cerrar")


app= wx.App()
Main(None, 'Gestor de contraseñas')
app.MainLoop()