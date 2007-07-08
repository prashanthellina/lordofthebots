"""
Sample team file
"""
import random

team_name = "prashanths_team"
bots = ["bot1", "bot2"]

directions = ['north', 'east', 'west', 'south']

class Bot:
    def __init__(self):
        pass

    def perform(self, state):
        map = state.map
        teams = state.teams
        actions = []
        move_action = random.choice([True, False])
        fire_action = random.choice([True, False])
        move_direction = random.choice(directions)
        fire_direction = random.choice(directions)
        
        if move_action:
            actions.append('MOVE %s' % move_direction)

        if fire_action:
            actions.append('FIRE %s' % fire_direction)

        return actions

bot1 = Bot()
bot2 = Bot()
