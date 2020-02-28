from tools import  *
from objects import *
from routines import *


#This file is for strategy

class ExampleBot(GoslingAgent):
    def run(agent):
        if len(agent.stack) < 1:
            if agent.kickoff_flag:
                agent.push(kickoff)
            else:
                agent.push(atba())
        
