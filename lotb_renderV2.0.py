#!/usr/bin/env python
"""
$Id$
Lord of the bots simulation renderer
"""

import os
import optparse
from Tkinter import *

TEAM_COLORS = ['red','green','blue','yellow']

class LOTBRendererException(Exception):
    pass

class Game:
    def __init__(self, canvas, width, height, simlog_file):
        self.count = 0
        self.file = simlog_file
        self.canvas_width = width
        self.canvas_height = height
        self.main_map_top = (0,0)
        self.main_map_bottom =(round(width*7/8),height)  # 7/8th of the screen will be occupied by main map
        self.insect_map_top = (round(width*7/8),0)
        self.insect_map_bottom = (width,round(height*1/8))
	self.cell_width =32 # The logic of filling this shall be changed later
        self.layout = ""
        self.teams=[]
	self.no_of_cols = round((self.main_map_bottom[0]-self.main_map_top[0])/self.cell_width)
	self.no_of_rows = round((self.main_map_bottom[1]-self.main_map_top[0])/self.cell_width)
        self.canvas = canvas

        self.parse_header()
        self.render_layout()
        self.render()

    def load_teams(self, team_data):
        team_names = eval(team_data)
        
        for index, team_name in enumerate(team_names):
            team_color = TEAM_COLORS[index % len(TEAM_COLORS)]
            team_obj = Team(team_name, team_color)
            self.teams.append(team_obj)

    def load_bots(self, bots_data):
        bots_data = eval(bots_data)

        for bot_data in bots_data:
            bot_name = bot_data['n']
            bot_team = bot_data['t']
            bot = Bot(bot_name, bot_team)
            
            for team in self.teams: 
                if team.team_name == bot_team: team.bot_list.append(bot)

    def parse_header(self):
        f = self.file
            
        file_version = f.readline().strip()
        map_data = f.readline().strip()
        bonus = f.readline().strip()         # Ammo and health positions
        teams = f.readline().strip()
        bots = f.readline().strip()

        if file_version != 'LOTB.DUMP.1':
            print file_version
            raise LOTBRendererException('invalid file type')

        self.layout = Layout(map_data)
        self.layout.update(bonus)
	# Here i am setting the 	

        self.load_teams(teams)
        self.load_bots(bots)

    def render_layout(self):
        self.canvas.create_rectangle(0,0,self.canvas_width,self.canvas_height,fill='#000000')        
        no_of_rows = len(self.layout.original_map)
        no_of_cols = len(self.layout.original_map[0])        

        self.draw_matrix(self.main_map_top,self.main_map_bottom,no_of_rows,no_of_cols)
        self.draw_matrix(self.insect_map_top,self.insect_map_bottom,no_of_rows,no_of_cols)

        self.canvas.pack()

    def render_spawn(self, turn_count, action, action_data, line):
        bot_location = action_data['loc']
        bot_info = action_data['bot']
        bot_team, bot_name = bot_info
        bot = self.find_bot(bot_team, bot_name)
        bot.present_location = bot_location

        bot.list_of_actions.append(line)
        row, col = bot_location
        self.layout.present_map[row][col]= bot            

    def render_move(self, turn_count, action, action_data, line):
        w_from = action_data['f']
        w_to = action_data['t']
        bot_info = action_data['b']

        bot_team, bot_name = bot_info
        bot = self.find_bot(bot_team, bot_name)

        bot.present_location = w_to
        bot.list_of_actions.append(line)

        #Check whether a wall,health,ammo existed in the from position
        ret = 0
        if w_from in self.layout.health_positions: ret = "H"
        if w_from in self.layout.ammo_positions: ret = "A"
        if w_from in self.layout.wall_positions: ret = 1
        
        f_row, f_col = w_from
        t_row, t_col = w_to

        self.layout.present_map[f_row ][f_col ] = ret
        self.layout.present_map[t_row ][t_col ] = bot

    def render_fire(self, turn_count, action, action_data, line):
        w_from = action_data['f']
        w_to = action_data['t']
        bot_info = action_data['b']

        bot_team, bot_name = bot_info
        bot = self.find_bot(bot_team,bot_name)

        bot.present_location = w_to
        bot.list_of_actions.append(line)

        self.fire(self.main_map_top,self.main_map_bottom,w_from,w_to)
    
    def render_param(self,turn_count,action,action_data,line):
        bot_info = action_data['b']
        target = action_data['t']
        value = int(action_data['v'])
        bot = self.find_bot(bot_info[0],bot_info[1])
        if target =="ammo": bot.ammo=value
        if target =="health": bot.health=value
        if target =="kills": bot.kills = value
        if target =="deaths": bot.deaths=value
        self.canvas.create_rectangle(self.insect_map_top[0],self.insect_map_bottom[1],self.canvas_width,self.canvas_height,fill="#000000")
        self.update_score()
        

    def render(self):        
        line = self.file.readline()
        if not line: return 

        event = eval(line)
        
        # every action is of the form 
        # [0, 'spawn', {'loc': (4, 7), 'bot': ('prashanths_team', 'bot2')}]
        # [1, 'move', {'b': ('prashanths_team', 'bot1'), 't': (7, 1), 'f': (7, 2)}]
        # [1, 'fire', {'b': ('prashanths_team', 'bot1'), 't': (7, 0), 'f': (7, 1)}]
        # [2, 'bot_param', {'b': ('prashanths_team', 'bot1'), 't': 'ammo', 'v': 48}]

        turn_count, action, action_data = event

        if action == "spawn":
            self.render_spawn(turn_count, action, action_data, line)

        if action =="move":
            self.render_move(turn_count, action, action_data, line)

        if action =="fire":
            self.render_fire(turn_count, action, action_data, line)
        
        if action =="bot_param":
            self.render_param(turn_count, action, action_data, line)
            
	if action!="fire": # For fire action, the graphics is handled by render_fire(). 
            self.draw_matrix(self.main_map_top,
                         self.main_map_bottom,
                         len(self.layout.original_map),
                         len(self.layout.original_map[0]))

            self.draw_matrix(self.insect_map_top,
                         self.insect_map_bottom,
                         len(self.layout.original_map),
                         len(self.layout.original_map[0]))



        self.canvas.after(50,self.render)

    def fire(self,top, bottom, w_from, w_to):
        # draws a set of circles (fireball) from w_from to w_to
        deltax = round((bottom[0]-top[0])/len(self.layout.original_map[0]))
        deltay = round((bottom[1]-top[1])/len(self.layout.original_map))
        fromx = w_from[1]*deltax
        fromy = w_from[0]*deltay
        tox = w_to[1]*deltax
        toy = w_to[0]*deltay
        self.canvas.create_line(fromx+(deltax/2.0),fromy+(deltay/2.0),tox+(deltax/2.0),toy+(deltay/2.0),width=2,fill="#ffd700")
    def swap(self,a,b):
        return b,a

    def draw_fireball(self,x0, x1, y0, y1,incx,incy): # Bresenham's Algorithm  - presently not used in  the program
        steep = abs(y1 - y0) > abs(x1 - x0)        
        if steep:
            x0,y0 = self.swap(x0,y0)            
            x1,y1 = self.swap(x1,y1)
        if x0 > x1:
            x0,x1 = self.swap(x0,x1)
            y0,y1 = self.swap(y0,y1)
        deltax = x1 - x0
        deltay = abs(y1 - y0)
        error  = -deltax / 2.0
        y = y0
        ystep = -1
        if y0 < y1: ystep = 1
        for x in range(x0,x1):        
            
            if steep: 
                self.canvas.create_oval(y-(.05*incx),x-(.1*incy),y+(.1*incx),x+(.1*incy),fill="#ffd700") 
            else:     self.canvas.create_oval(x-(.05*incx),y-(.1*incy),x+(.1*incx),y+(.1*incy),fill="#ffd700")

#            if steep:
#                self.canvas.create_oval(y-(.05*incx),x-(.1*incy),y+(.1*incx),x+(.1*incy),fill="#000000")
#            else:     self.canvas.create_oval(x-(.05*incx),y-(.1*incy),x+(.1*incx),y+(.1*incy),fill="#000000")
#            error = error + deltay
            if error > 0:
                y = y + ystep
                error = error - deltax




    def find_bot(self,bot_team, bot_name):
        #returns the Bot instance with the given parameters
            for team in self.teams:
                if team.team_name ==bot_team: break
            for bot in team.bot_list:
                if bot.name == bot_name:                    
                    break
            return bot    

    def draw_matrix(self,top,bottom,no_of_rows,no_of_cols):
        # top,bottom are of the form (x,y) 
        #                             X(top)-----------
        #                                  -----------------
        #                   -----------------X(bottom)            
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
                if self.layout.present_map[i][k] ==1:    #Wall                
                    self.canvas.create_rectangle(x+x_increase,y+y_increase,x1-x_increase,y1-y_increase,fill='#888888')
                if self.layout.present_map[i][k] =="H":    #Health pack        
                    self.canvas.create_rectangle(x+x_increase,y+y_increase,x1-x_increase,y1-y_increase,fill='#ffffff')
                    new_x = x+x_increase
                    new_y = y+y_increase
                    new_x1 = x1-x_increase
                    new_y1 = y1-y_increase
                    x_inc = (new_x1-new_x)/2
                    y_inc = (new_y1-new_y)/2
                    self.canvas.create_rectangle(new_x+x_inc-(x_increase/2.0),new_y,new_x+x_inc+(x_increase/2.0),new_y1,fill="#ff0000")
                    self.canvas.create_rectangle(new_x,new_y+y_inc-(y_increase/2.0),new_x1,new_y1-y_inc+(y_increase/2.0),fill="#ff0000")
#                    self.canvas.create_line(new_x+x_inc,new_y+(y1-y)/2.0)

                if self.layout.present_map[i][k] == "A": # Ammo        
                    delvalx = (10.0/100)*((x1-x)/2)
                    newx = x+((x1-x)/2) - delvalx
                    newx1 =  x+((x1-x)/2) + delvalx
                    delvaly = (1.0/4)*(y1-y)
                    newy = y+delvaly
                    self.canvas.create_oval(newx,y+2,newx1,newy+(2*delvaly),fill="#ffd700")
                    self.canvas.create_rectangle(newx,newy,newx1,newy+(2*delvaly),fill="#ffd700") 
                if isinstance(self.layout.present_map[i][k],type(self.teams[0].bot_list[0])): #Checking bot
                    bot = self.layout.present_map[i][k]
                    bot_team = bot.team_name  
                    for team in self.teams:
                        if team.team_name == bot_team: break

                    bot_colour = team.team_colour  
                    self.draw_bot(x,y,x+deltax,y+deltay,bot_colour)
                    #----Printing the name of bot on its top. ----#
                    font = "10 italic bold"
  #          	    if deltax<30: font = "2 italic bold"  #For the insect map
                    if deltax>30: self.canvas.create_text(x+(.2*deltax),y+(.2*deltay),fill="#0000ff",text=bot.name)             
                    #---------------------------------------------#
                
                    
                x = x1
            x = top[0]
            y = y1
            

    def update_score(self):
        #Updating the score below the insect map
        x = self.insect_map_top[0]+((self.insect_map_bottom[0]-self.insect_map_top[0])/2.0) + 15
        y = self.insect_map_bottom[1] +(.1*self.canvas_height)
        font = "Times 10 italic bold"

        self.canvas.create_text(x,y,fill="#ffffff",text="------------\nSTATUS\n------------\n H     A   K",font=font)
        y  =y+ 40
        x = self.insect_map_top[0]+((self.insect_map_bottom[0]-self.insect_map_top[0])/2.0) - 5 
        for team in self.teams:
                for bot in team.bot_list:
                        text = bot.name+"     "+str(bot.health)+"      "+str(bot.ammo)+"      "+str(bot.kills)
                        self.canvas.create_text(x,y,text=text,font=font,fill="#ffffff")
                        y=y+15



                    
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
        self.health_positions = []
        self.ammo_positions = []
        for row in range(0,len(self.present_map)):
            for cell in range(0,len(self.present_map[row])):                
                if self.present_map[row][cell] ==1:                     
                    self.wall_positions.append((row,cell))

    def update(self, bonus_data):
        msg = eval(bonus_data)
        if type(msg)== dict: #We know its the health and ammo positions
            for key in msg:
                coord = key                
                print coord
                if msg[key] == 'health': 
                    self.present_map[coord[0]][coord[1]] ='H'
                    self.health_positions.append(coord)
                if msg[key] == 'ammo': 
                    self.present_map[coord[0]][coord[1]] ='A'
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
        self.deaths = 0
        self.list_of_actions = [] # this will be a repository of all that the bot did in the game.

def main(options):

    simlog_file = sys.stdin
    if options.simulation_log:
        simlog_file = file(options.simulation_log)

    root = Tk()
    root.title("Lord of the Bots")

    width = 1024
    height = 700
    c = Canvas(root, width=width,height=height)

    g = Game(c, width, height, simlog_file)

    root.mainloop()

if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option('-s', '--simulation-log', metavar='FILE', help='input simulation log')
    (options, args) = parser.parse_args()

    main(options)
