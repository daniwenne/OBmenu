#!/usr/bin/python
import os
import tkinter as tk
import signal
from tkinter import ttk

def findconfig(text, option):
	text=text.split('\n')
	for line in text:
		if line.split('=')[0] == option:
			return line.split('=')[1]
	return ''

def getapplist(plist):
	
	applist=[]
	for path in plist:
		print(path)
		try:
			filelist = os.listdir(path+'/applications')
		except:
			continue
		for filename in filelist:
			if filename.endswith('.desktop'):
				with open(path + '/applications/' + filename, 'r') as file:
					data = file.read()
					parameters = ['Name', 'Icon', 'Exec']
					if findconfig(data,'NoDisplay') == 'True':
						continue
					app = [findconfig(data,item) for item in parameters]
					applist.append(app)
	return(applist)

basedir = os.path.expanduser('~')+'/.stupidmenu/'
lxconfigpath = os.path.expanduser('~/.config/lxqt/lxqt.conf')

with open(lxconfigpath, 'r') as lxconfig:
	conftxt = lxconfig.read()
	icontheme = findconfig(conftxt, 'icon_theme')
	systheme = findconfig(conftxt, 'style')

	
if 'kvantum' in systheme:
	kvpath = os.path.expanduser('~/.config/Kvantum/kvantum.kvconfig')
	with open(kvpath, 'r') as kvconfig:
		kvtheme = findconfig(kvconfig.read(), 'theme')
	kvantumbasedir='/usr/share/Kvantum/'
	
def updateiconcache(alist, new=False):
	import cairosvg
	iconthemedir = '/usr/share/icons/'+icontheme+'/32x32/apps/'
	def addtocache(lst):
		import urllib
		for app in lst:
			print(app)
			if app[1].split('.')[-1] == 'png':
				from PIL import Image
				img = Image.open(app[1])
				img = img.resize((32,32), Image.BILINEAR)
				img.save(basedir + 'cache/' + app[1].split('/')[-1])
				"""except:
					os.system('cp '+app[1]+' '+ basedir + 'cache/' + app[1].split('/')[-1])"""
			else:
				try:
					importpath = app[1] if app[1][0]=='/' else iconthemedir+app[1]+'.svg'
					exportpath = basedir + 'cache/' + (app[1] if app[1][0]!='/' else app[0]) + '.png'
					cairosvg.svg2png(url=importpath, write_to=exportpath)
				except:
					continue
	if new:
		addtocache(alist)
	else:
		newapps=[]
		for app in alist:
			try:
				exportpath = basedir + 'cache/' + (app[1] if app[1][0]!='/' else app[0]) + '.png'
			except:
				continue
			if not os.path.isfile(exportpath):
				newapps.append(app)
		addtocache(newapps)

def iconpath(iconname):
	try:
		return(basedir + 'cache/' + ((iconname+ '.png') if iconname[0]!='/' else (iconname.split('/')[-1])))
	except:
		return(iconname)



def colorconfig(widget):
	bgcolor = '#131313'
	fgcolor = '#E0E0E0'
	widget.config(bg = bgcolor)
	for wid in widget.winfo_children():
		wid.config(bg = bgcolor)
		if wid.winfo_class()=='Frame':
			colorconfig(wid)
		elif wid.winfo_class() == 'Button':
			wid.config(fg = fgcolor, highlightbackground=bgcolor, highlightcolor=fgcolor,\
					  activebackground = '#1D1D1D', activeforeground = fgcolor)
		elif wid.winfo_class() =='Entry':
			wid.config(fg = fgcolor,bg = '#1D1D1D', highlightbackground=bgcolor\
					   ,insertbackground=fgcolor, highlightcolor=bgcolor)
		else:
			wid.config(fg = fgcolor)

class menuwindow(tk.Tk):
	def __init__(self,alist):
		super().__init__()
		self.sig = signal.signal(signal.SIGUSR1, self.togglemenu)
		self.attributes('-type', 'splash')
		self.geometry('%dx%d+%d+%d' % (600, 400, 0, 20))
		self.bind("<FocusOut>", lambda *args: self.reset())
		
		
		self.applist= alist
		
		self.popup_activated=False
		
		self.popup = tk.Menu(self, tearoff=0, relief='flat')
		self.popup.add_command(label="Launch App")
		self.popup.add_command(label="Pin App")
		
		self.popup.bind("<FocusOut>", lambda *args: self.undo_popup())
		
		self.searchtext = tk.StringVar()
		self.searchtext.trace('w', self.updatesearch)
				
		self.searchbar = tk.Entry(self, width=100, textvariable = self.searchtext, relief='flat')
		self.searchbar.pack(side='top', pady = 12, padx=15)
		
		self.powermenu = tk.Frame(self)
		self.powermenu.pack(side='right')
		
		
		self.apppanel = tk.Frame(self)
		self.apppanel.pack(side='top',padx=5)
		
		self.searchresvisible = False
		
		self.searchresults = tk.Frame(self.apppanel)
		
		self.pinfilepath = basedir + 'pinedapps.cfg'
		
		self.reswidgets = []
		
		
		self.pinnedapps = tk.Frame(self.apppanel)
		self.pinnedapps.pack(side='top')

		
		self.pinapplist = []
		
		self.pinappwidgets=[]
		
		self.selectedapp=0
		self.searchbar.bind('<Return>', lambda *args:self.reswidgets[self.selectedapp][1]())
		self.searchbar.bind('<Up>', lambda *args:self.moveselectionup())
		self.searchbar.bind('<Down>', lambda *args:self.moveselectiondown())
		self.searchbar.focus()
		
		self.poweritems=(\
			('Shutdown', 'system-shutdown','lxqt-leave --shutdown'),
			('Reboot', 'system-reboot','lxqt-leave --reboot'),
			('Suspend', 'system-suspend','lxqt-leave --suspend'),
			('Lock Screen', 'system-lock-screen','lxqt-leave --lockscreen'),
			('Logout', 'system-log-out','lxqt-leave --logout'))
		
		
		if(not os.path.exists(self.pinfilepath)):
			os.system('touch "'+self.pinfilepath+'"')
		self.powericons = []
		for pwitm in self.poweritems:
			try:
				self.powericons.append(tk.PhotoImage(file = iconpath(pwitm[1])))
			except:
				continue
		
		self.powerbuttons = []
		
		for i in range(len(self.poweritems)):
			wid = tk.Button(self.powermenu,text = self.poweritems[i][0],compound='left',width=120,anchor="w", relief='flat',command = lambda item=self.poweritems[i][2]:os.system(item))
			self.powerbuttons.append(wid)
			wid.pack(side='top', pady=8, padx=5)
		self.updatepincache()
		colorconfig(self)
		self.togglemenu()
			
		
	def togglemenu(self ,signum=0, frm=0):
		print('Menu Toggled!')
		self.deiconify()
		self.wm_attributes("-topmost", 1)
		self.focus_force()
		self.wm_attributes("-topmost", 0)
		self.update()
		self.searchbar.focus()

	def moveselectionup(self):
		if self.searchresvisible:
			if self.selectedapp>0:
				self.removeselectedapp()
				self.selectedapp-=1;
				self.updateselectedapp()
	
	def createpinapp(self,application):
		photoimage = tk.PhotoImage(file=iconpath(application[1]))
		cmd = lambda item=application:os.system('nohup ' +' '.join([((arg) if arg[0] !='%' else '')\
			for arg in item[2].split(' ')]) + '&') or self.reset()
		wid=\
			tk.Button(self.pinnedapps,compound='top', image=photoimage,wraplength=100,\
			text = application[0], command= cmd, width = 100, height=70, relief='flat')
		self.pinappwidgets.append(wid)
		wid.grid(row = len(self.pinapplist)//3, column=len(self.pinapplist)%3)
		wid.bind("<Button-3>", lambda e,i=application, c=cmd:self.do_popup(e,i,c,True))
		self.pinapplist.append([application,cmd,photoimage])
						
	
	def newpinapp(self,application):
		if application not in self.pinapplist:
			self.createpinapp(application)
			with open(self.pinfilepath, "a") as pinappfile:
				pinappfile.write("|".join(application) + '\n')
	
	def removepinapp(self,application):
		for i in range(len(self.pinapplist)):
			if application[0] == self.pinapplist[i][0][0]:
				
				self.pinapplist.pop(i)
				with open(self.pinfilepath, "w") as pinappfile:
					for item in self.pinapplist:
						pinappfile.write("|".join(item[0]) + '\n')
				self.pinappwidgets[i].grid_forget()
				self.pinappwidgets[i].destroy()
				self.pinappwidgets.pop(i)
				
				for j in range(i,len(self.pinapplist)):
					self.pinappwidgets[j].grid(row = j//3, column=j%3)
				break
	
	def updatepincache(self):
		with open(self.pinfilepath, 'r') as pinappfile:
			apps = [app.split('|') for app in pinappfile.read().split('\n')]
		if len(apps)>0:
			apps.pop(len(apps)-1)
			for app in apps:
				self.createpinapp(app)
	
	def do_popup(self,event,application, command, pinapp=False):
		print(application[0])
		try:
			if pinapp:
				self.popup.entryconfig(0, command=command)
				self.popup.entryconfig(1,label="Unpin App", command=lambda a=application: self.removepinapp(a))
				self.popup_activated=True
				self.popup.tk_popup(event.x_root, event.y_root, 0)
			else:
				self.popup.entryconfig(0, command=command)
				self.popup.entryconfig(1,label="Pin App", command=lambda a=application: self.newpinapp(a))
				self.popup_activated=True
				self.popup.tk_popup(event.x_root, event.y_root, 0)
		
		finally:
			pass#self.popup.grab_release()
			
	def undo_popup(self):
		self.togglemenu()
		self.popup_activated=False
	
	def moveselectiondown(self):
		if self.searchresvisible:
			if len(self.reswidgets)>1 and self.selectedapp<(len(self.reswidgets)-1):
				self.removeselectedapp()
				self.selectedapp+=1;
				self.updateselectedapp()
	def removeselectedapp(self):
		self.reswidgets[self.selectedapp][0].configure(bg = '#131313')
		
	def updateselectedapp(self):
		self.reswidgets[self.selectedapp][0].configure(bg = '#1D1D1D')
	
	def updatesearch(self, *args):
		
		searchtxt = self.searchtext.get()
		for widget in self.reswidgets:
			widget[0].destroy()
		self.reswidgets=[]
		if searchtxt=='':
			if self.searchresvisible:
				self.searchresults.pack_forget()
				self.pinnedapps.pack()
				self.searchresvisible=False
				
		else:
			if not self.searchresvisible:
				self.pinnedapps.pack_forget()
				self.searchresults.pack()
				self.searchresvisible=True
			results=[]
			for app in self.applist:
				if searchtxt.lower() in app[0].lower():
					results.append(app)
			
			#print(results)
			for item in results:
				validimage=True
				try:
					photoimage = tk.PhotoImage(file=iconpath(item[1]))
				except:
					validimage=False
					
				cmd = lambda item=item:os.system('nohup ' +' '.join([((arg) if arg[0] !='%' else '')\
					for arg in item[2].split(' ')]) + '&') or self.reset()
				
				if validimage:
					widget = tk.Button(self.searchresults,compound='left',anchor='w',\
						text = item[0], command= cmd, width = 400, relief='flat', image=photoimage)
				else:
					widget = tk.Button(self.searchresults,compound='left',anchor='w',\
						text = item[0], command= cmd, width = 400, relief='flat')
				self.reswidgets.append([widget, cmd, photoimage])
				widget.bind("<Button-3>", lambda e,i=item, c=cmd:self.do_popup(e,i,c))
				widget.pack(side='top')
			print (len(results))
			if len(results)>0:
				self.selectedapp=0
				self.updateselectedapp()
		colorconfig(self.searchresults)
	
			
	def reset(self):
		if not self.popup_activated:
			self.iconify()
			self.searchtext.set('')
	
	def do_nothing(self):
		#https://stackoverflow.com/questions/9998274/tkinter-keyboard-interrupt-isnt-handled-until-tkinter-frame-is-raised
		self.after(200,self.do_nothing)
	
	


if __name__=='__main__':
	try:
		os.mkdir(basedir)
	except:
		pass
	
	pathlist = os.environ['XDG_DATA_DIRS'].split(':')
	applist = getapplist(pathlist)
	print(applist)
	try:
		os.mkdir(basedir+'cache')
		newcache=True
	except:
		newcache=False
	updateiconcache(applist,newcache)
	menu = menuwindow(applist)
	menu.after(500, menu.do_nothing())
	menu.mainloop()
