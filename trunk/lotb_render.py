
		

class Game:
	def __init__(self,canvas,width,height,file):
		self.count = 0
		self.file = file
		self.canvas_width = width
		self.canvas_height = height
		self.main_map_top = (0,0)
		self.main_map_bottom =(round(width*7/8),height)  # 7/8th of the screen will be occupied by main map
		self.insect_map_top = (round(width*7/8),0)
		self.insect_map_bottom = (width,round(height*1/8))
		self.layout =""
		self.teams=[]
		self.canvas = canvas
		self.fileinput =[]

	def handle_rawText(self):
		#Transferring the contents of the file to a list, fileinput
		f = open(self.file,'r')
		for line in f.readlines(): self.fileinput.append(line)
		f.close()
			
			# Every turn has a number written in its 0th position except the first 5 lines
		while self.count!=5:
			raw_text = self.fileinput[self.count]
			if self.count ==0 and raw_text!="LOTB.DUMP.1": pass # Need to find out what nhas to be done 
			if self.count ==1: # The actual map
				#Here we expect the map
				self.layout = Layout(raw_text) #values to be replaced later.
			if self.count ==2: #Ammo and health positions
				self.layout.layout_change(raw_text)				
			if self.count ==3: #List of teams
				colour_pref = ['Red','Green','Blue','Yellow']
				count = -1
				for team in eval(raw_text):
					count +=1
					self.teams.append(Team(team,colour_pref[count]))
			if self.count ==4: #List of bots
				for bot_dict in eval(raw_text):
					bot = Bot(bot_dict['n'],bot_dict['t'])
					for team in self.teams: 
						if team.team_name == bot_dict['t']: team.bot_list.append(bot)
			self.count+=1 	
		self.render()
	def render(self):
		if self.count == 5:
			self.canvas.create_rectangle(0,0,self.canvas_width,self.canvas_height,fill='#000000')
			no_of_rows = len(self.layout.original_map)
			no_of_cols = len(self.layout.original_map[0])		

			self.draw_matrix(self.main_map_top,self.main_map_bottom,no_of_rows,no_of_cols)
			self.draw_matrix(self.insect_map_top,self.insect_map_bottom,no_of_rows,no_of_cols)
			self.canvas.pack()

			self.canvas.after(100,self.render)
			self.count+=1
		raw_text = self.fileinput[self.count]	

	def draw_matrix(self,top,bottom,no_of_rows,no_of_cols):
		# top,bottom are of the form (x,y) 
		#                  		   X(top)-----------
		#                                  -----------------
		#				   -----------------X(bottom)	
		print top
		print bottom
		delta = round((bottom[0]-top[0])/no_of_cols)
		x = top[0]
		y = top[1]
		x1 = top[0]
		y1 = bottom[1]		
		for i in range(0,no_of_cols):
			self.canvas.create_line(x,y,x1,y1,fill = '#ff0000')
			x1 = x1+delta
			x=x1
			self.canvas.create_line(x,y,x1,y1,fill = '#ff0000')
		delta = round((bottom[1]-top[1])/no_of_rows)
		x = top[0]
		y = top[1]		
		x1 = bottom[0]
		y1 = top[1]
		for i in range(0,no_of_rows):
			self.canvas.create_line(x,y,x1,y1,fill = '#ff0000')		
			y1 = y1+delta
			y = y1
			self.canvas.create_line(x,y,x1,y1,fill = '#ff0000')		


		#This takes care of rendering from the 5th line till the last

			
class Layout:
	def __init__(self,map): 
		# screen width and height to calculate main layout and insect map layout
		self.original_map = eval(map)
		self.present_map = eval(map)		
		self.mainx =0
		self.mainy =0
		self.cell_width =32 # The logic of filling this shall be changed later


	def layout_change(self,raw_text):
		msg = eval(raw_text)
		if type(msg)== dict: #We know its the health and ammo positions
			for key in msg:
				coord = key				
				if msg[key] == 'health': self.present_map[coord[0]-1][coord[1]-1] ='H'
				if msg[key] == 'ammo': self.present_map[coord[0]-1][coord[1]-1] ='A'




class Team:
	# The team contains the list of bots which belong to it
	def __init__(self,t_name,colour):
		self.team_name = t_name
		self.team_colour = colour
		self.bot_list = []

	def add_bot(self,bot): # the bot object created by Game Class is passed here to be appended to TeamClass
		self.bot_list.append(bot)


class Bot:
	def __init__(self,name,t_name): # these two variables passed by Game Class
		self.name = name
		self.team_name = t_name
		self.health = 0
		self.ammo = 0
		self.kills =0
		self.list_of_actions = [] # this will be a repository of all that the bot did in the game.

from Tkinter import *
import winsound
import os




#----The Canvas is created here and passed to Game class --------
root = Tk()
width = 800
height = 600
c = Canvas(root, width=width,height=height)

root.title("Lord of the Bots")
g = Game(c,width,height,'simlog.txt')
g.handle_rawText()
root.mainloop()

#----The width,height shall be replaced with "find_monitor_resolution()


