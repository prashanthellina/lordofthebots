class Game:
	def __init__(self):
		self.count = 0
		self.layout =""
		self.teams=[]

	def handle_rawText(self,raw_text):
		# Every turn has a number written in its 0th position except the first 5 lines
		self.count+=1 			

		if self.count ==1 and raw_text!="LOTB.DUMP.1": return "GameOver" 
		if self.count ==2: # The actual map
			#Here we expect the map
			self.layout = Layout(raw_text,300,300) #values to be replaced later.
		if self.count ==3: #Ammo and health positions
			self.layout.layout_change(raw_text)

		if self.count ==4: #List of teams
			colour_pref = ['Red','Green','Blue','Yellow']
			count = -1
			for team in eval(raw_text):
				count +=1
				self.teams.append(Team(team,count))
		if self.count ==5: #List of bots
			for bot_dict in eval(raw_text):
				bot = Bot(bot_dict['n'],bot_dict['t'])
				for team in self.teams: 
					if team.team_name == bot_dict['t']: team.bot_list.append(bot)


			
	
	

			
class Layout:
	def __init__(self,map,width,height): 
		# screen width and height to calculate main layout and insect map layout
		self.original_map = eval(map)
		self.present_map = eval(map)		
		self.insx = round(width*(7/8)) # The insect map,insx n insy, will occupy 1/8th of the screen
		self.insy = round(height*(1/8))
		self.mainx =0
		self.mainy =0
		self.cell_width =32 # The logic of filling this shall be changed later
	def render(self,present_map):
		pass
		# Here the code goes for rendering the map on screen.
		# This automatically renders the insect map.

	def layout_change(self,raw_text):
		msg = eval(raw_text)
		if type(msg)== dict: #We know its the health and ammo positions
			for key in msg:
				coord = key
				if msg[key] == 'health': self.present_map[coord[0]-1][coord[1]-1] ='H'
				if msg[key] == 'ammo': self.present_map[coord[0]-1][coord[1]-1] ='A'
				self.render(self.present_map)



		self.render(self.present_map)
		# here the code goes for acting on a change in layout. 

class Team:
	# The team contains the list of bots which belong to it
	def __init__(self,t_name,colour):
		self.team_name = t_name
		self.team_color = colour
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
		print "Bot Created",self.name,"\nTeam:",self.team_name
		self.list_of_actions = [] # this will be a repository of all that the bot did in the game.

g = Game()
file = open('simlog.txt','r')
for line in file.readlines():
	g.handle_rawText(line)


