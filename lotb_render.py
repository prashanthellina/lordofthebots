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
			if self.count ==0 and raw_text!="LOTB.DUMP.1": pass # Need to find out what has to be done 
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
			self.count+=1
			self.canvas.pack()
			self.canvas.after(100,self.render())	
		#Since when count =5, we only draw the game board

		raw_text = self.fileinput[self.count-1]	
		# The processing for the movements and other jingbang
		action = eval(raw_text)
		# every action is of the form 
		# [0, 'spawn', {'loc': (4, 7), 'bot': ('prashanths_team', 'bot2')}]
		# [1, 'move', {'b': ('prashanths_team', 'bot1'), 't': (7, 1), 'f': (7, 2)}]
		# [1, 'fire', {'b': ('prashanths_team', 'bot1'), 't': (7, 0), 'f': (7, 1)}]
		# [2, 'bot_param', {'b': ('prashanths_team', 'bot1'), 't': 'ammo', 'v': 48}]

		if action[1] =="spawn":			
			dict = action[2]
			bot_location = dict['loc']
			bot_info     = dict['bot']
			bot_team = bot_info[0]
			bot_name = bot_info[1]
			bot = self.find_bot(bot_team,bot_name)
			bot.present_location ==bot_location
			bot.list_of_actions.append(raw_text)
			self.layout.present_map[bot_location[0]-1][bot_location[1]-1]= bot			
			self.draw_matrix(self.main_map_top,self.main_map_bottom,len(self.layout.original_map),len(self.layout.original_map[0]))
			self.draw_matrix(self.insect_map_top,self.insect_map_bottom,len(self.layout.original_map),len(self.layout.original_map[0]))

		#If the action is MOVE
		#--------------------
		if action[1] =="move":
			dict = action[2]
			w_from = dict['f']
			w_to = dict['t']
			bot_info = dict['b']
			bot_team = bot_info[0]
			bot_name = bot_info[1]
			bot = self.find_bot(bot_team,bot_name)
			bot.present_location == w_to
			bot.list_of_actions.append(raw_text)			
			#Check whether a wall,health,ammo existed in the from position
			ret =0
			if w_from in self.layout.health_positions: ret = "H"
			if w_from in self.layout.ammo_positions: ret = "A"
			print w_from
			if w_from in self.layout.wall_positions: 
				ret = 1
				print w_from
				
			self.layout.present_map[w_from[0]-1][w_from[1]-1] = ret
			self.layout.present_map[w_to[0]-1][w_to[1]-1] =bot

			self.draw_matrix(self.main_map_top,self.main_map_bottom,len(self.layout.original_map),len(self.layout.original_map[0]))
			self.draw_matrix(self.insect_map_top,self.insect_map_bottom,len(self.layout.original_map),len(self.layout.original_map[0]))
		
		# if the action is FIRE
		if action[1] =="fire":
			dict = action[2]
			w_from = dict['f']
			w_to = dict['t']
			bot_info = dict['b']
			bot_team = bot_info[0]
			bot_name = bot_info[1]
			bot = self.find_bot(bot_team,bot_name)
			bot.present_location == w_to
			bot.list_of_actions.append(raw_text)

		self.count+=1		
		self.canvas.after(200,self.render)

	def fire(self,top,bottom,w_from,w_to):
		# THis has been separated from draw_matrix to preserve readability
		# It draws a set of circles (fireball) from w_from to w_to
		deltax = round((bottom[0]-top[0])/len(self.layout.original_map[0]))
		deltay = round((bottom[1]-top[1])/len(self.layout.original_map))
		fromx = w_from[0]*deltax
		fromy = w_from[1]*deltay
		tox = w_to[0]*deltax
		toy = w_to[1]*deltay


	def find_bot(self,bot_team,bot_name):
		#returns the Bot instance with the given parameters
			for team in self.teams:
				if team.team_name ==bot_team: break
			for bot in team.bot_list:
				if bot.name == bot_name:					
					break
			return bot	

	def draw_matrix(self,top,bottom,no_of_rows,no_of_cols):
		# top,bottom are of the form (x,y) 
		#                  		   X(top)-----------
		#                                  -----------------
		#				   -----------------X(bottom)			
		self.canvas.create_rectangle(top[0],top[1],bottom[0],bottom[1],fill='#000000')		
		deltax = round((bottom[0]-top[0])/no_of_cols)
		x = top[0]
		y = top[1]
		x1 = top[0]
		y1 = bottom[1]		
		for i in range(0,no_of_cols):
			self.canvas.create_line(x,y,x1,y1,fill = '#ff0000')
			x1 = x1+deltax
			x=x1
			self.canvas.create_line(x,y,x1,y1,fill = '#ff0000')
		deltay = round((bottom[1]-top[1])/no_of_rows)
		x = top[0]
		y = top[1]		
		x1 = bottom[0]
		y1 = top[1]
		for i in range(0,no_of_rows):
			self.canvas.create_line(x,y,x1,y1,fill = '#ff0000')		
			y1 = y1+deltay
			y = y1
			self.canvas.create_line(x,y,x1,y1,fill = '#ff0000')		
		#----------This part of the code places the pieces on the map as per the changes made
		x = top[0]
		y = top[1]
		y1 = y +deltay
		x1 = x
		x_increase = (10.0/100)*deltax
		y_increase = (10.0/100)*deltay
		for i in range(0,len(self.layout.present_map)):		
			y1 = y+deltay
			x1=x
			for k in range(0,len(self.layout.present_map[0])):
				x1 = x1+deltax
				if self.layout.present_map[i][k] ==1:	#Wall				
					self.canvas.create_rectangle(x+x_increase,y+y_increase,x1-x_increase,y1-y_increase,fill='#888888')
				if self.layout.present_map[i][k] =="H":	#Health pack		
					self.canvas.create_rectangle(x+x_increase,y+y_increase,x1-x_increase,y1-y_increase,fill='#ffffff')
					new_x = x+x_increase
					new_y = y+y_increase
					new_x1 = x1-x_increase
					new_y1 = y1-y_increase
					x_inc = (new_x1-new_x)/2
					y_inc = (new_y1-new_y)/2
					self.canvas.create_rectangle(new_x+x_inc-(x_increase/2.0),new_y,new_x+x_inc+(x_increase/2.0),new_y1,fill="#ff0000")
					self.canvas.create_rectangle(new_x,new_y+y_inc-(y_increase/2.0),new_x1,new_y1-y_inc+(y_increase/2.0),fill="#ff0000")

				if self.layout.present_map[i][k] == "A": # Ammo		
					delvalx = (10.0/100)*((x1-x)/2)
					newx = x+((x1-x)/2) - delvalx
					newx1 =  x+((x1-x)/2) + delvalx
					self.canvas.create_oval(newx,y+2,newx1,y1-2,fill="#ffd700")
					delvaly = (1.0/4)*(y1-y)
					newy = y+delvaly
					self.canvas.create_rectangle(newx,newy,newx1,y1-2,fill="#ffd700") 
				if isinstance(self.layout.present_map[i][k],type(self.teams[0].bot_list[0])): #Checking bot
					bot = self.layout.present_map[i][k]
					bot_team = bot.team_name  
					for team in self.teams:
						if team.team_name == bot_team: break

					bot_colour = team.team_colour  
					self.draw_bot(x,y,x+deltax,y+deltay,bot_colour)


				x = x1
			x = top[0]
			y = y1	
	def draw_bot(self,x,y,x1,y1,colour):
		#This section draws the bot within the the rectangle specified.
		#The bot is made to resemble an alien. Excuse me if it doesn't
		delx = (x1-x)*(1.0/4)
		dely = (y1-y)*(1.0/4)
		newx = x+delx
		newy = y + dely
		newx1 = x1-delx
		newy1 = y1-dely
		self.canvas.create_oval(newx,newy,newx1,newy1,fill=colour)
		self.canvas.create_line(newx+((newx1-newx)/2),newy+((newy1-newy)/2),x,y1,fill=colour,width=2)
		self.canvas.create_line(newx+((newx1-newx)/2),newy+((newy1-newy)/2),newx+((newx1-newx)/2),y1,fill=colour,width=2)
		self.canvas.create_line(newx+((newx1-newx)/2),newy+((newy1-newy)/2),x1,y1,fill=colour,width=2)
		self.canvas.create_line(newx+((newx1-newx)/2),newy+((newy1-newy)/2),newx+((newx1-newx)/2),y+((1.0/10)*(y1-y)),fill=colour,width=4)
		#Drawing the eye of the bot. The crucial stuff
		eyex = newx+((newx1-newx)*(1.0/5))
		eyey = newy+((newy1-newy)*(1.0/5))
		eyex1 = newx1-((newx1-newx)*(1.0/5))
		eyey1 = newy1-((newy1-newy)*(1.0/5))
		self.canvas.create_oval(eyex,eyey,eyex1,eyey1,fill="#ffffff")
		eyebx = eyex+((eyex1-eyex)*(1.0/5))
		eyeby = eyey+((eyey1-eyey)*(1.0/5))
		eyebx1 = eyex1-((eyex1-eyex)*(1.0/5))
		eyeby1 = eyey1-((eyey1-eyey)*(1.0/5))
		self.canvas.create_oval(eyebx,eyeby,eyebx1,eyeby1,fill="#000000")


			
class Layout:
	def __init__(self,map): 
		# screen width and height to calculate main layout and insect map layout
		self.original_map = eval(map)
		self.present_map = eval(map)		
		self.mainx =0
		self.mainy =0
		self.wall_positions = []
		self.cell_width =32 # The logic of filling this shall be changed later
		self.health_positions = []
		self.ammo_positions = []
		for row in range(0,len(self.present_map)):
			for cell in range(0,len(self.present_map[row])):				
				if self.present_map[row][cell] ==1: 					
					self.wall_positions.append((row+1,cell+1))
		


	def layout_change(self,raw_text):
		msg = eval(raw_text)
		if type(msg)== dict: #We know its the health and ammo positions
			for key in msg:
				coord = key				
				if msg[key] == 'health': 
					self.present_map[coord[0]-1][coord[1]-1] ='H'
					self.health_positions.append(coord)
				if msg[key] == 'ammo': 
					self.present_map[coord[0]-1][coord[1]-1] ='A'
					self.ammo_positions.append(coord)



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
		self.present_location =""
		self.ammo = 0
		self.kills =0
		self.list_of_actions = [] # this will be a repository of all that the bot did in the game.

from Tkinter import *
import winsound
import os




#----The Canvas is created here and passed to Game class --------
root = Tk()
width = 1024
height = 700
c = Canvas(root, width=width,height=height)

root.title("Lord of the Bots")
g = Game(c,width,height,'simlog.txt')
g.handle_rawText()
root.mainloop()

#----The width,height shall be replaced with "find_monitor_resolution()


