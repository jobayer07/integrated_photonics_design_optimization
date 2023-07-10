from __future__ import division
import numpy
import matplotlib.cm as cm
import matplotlib.pyplot as plt
import sys, os
import numpy as np
#importlibutil

import random
import math

micron=1e-6

sys.path.append("/opt/lumerical/v212/api/python")
import lumapi
base_file = "base_rotator.fsp"
        
#--- COST FUNCTION ------------------------------------------------------------+

# function we are attempting to optimize (minimize)
def func1(x):
    if os.path.exists(base_file):
        with lumapi.FDTD(filename=base_file, hide='TRUE') as fdtd:
            xmax=x[0]*micron
            ymin_bot=x[1]*micron
            w_bot=x[2]*micron
            
            ymin_top=-x[3]*micron
            ymax_top=x[3]*micron
            
            print('xmax:', x[0], ', ymin_bot:', x[1], ', w_bot:', x[2], ', ymin_top:', -x[3])
            fdtd.switchtolayout()
            
            fdtd.select("Bottom")
            Vbot=fdtd.get("vertices")
            Vbot[0, 0]=xmax
            Vbot[0, 1]=ymin_bot
            Vbot[1, 0]=xmax
            Vbot[1, 1]=ymin_bot+w_bot
            fdtd.set("vertices", Vbot)
            
            fdtd.select("Top")
            Vtop=fdtd.get("vertices")
            Vtop[0, 0]=xmax
            Vtop[0, 1]=ymin_top
            Vtop[1, 0]=xmax
            Vtop[1, 1]=ymax_top
            fdtd.set("vertices", Vtop)
            
            fdtd.select("FDTD")
            fdtd.set("x max", xmax-0.5e-6)
            
            fdtd.save()
            fdtd.run()
            
            bot_monitor=fdtd.getresult("monitor_bottom", "E")
            E_abs=abs(bot_monitor["E"])
            P=E_abs**2
            
            i1,i2,i3,i4,i5=np.shape(P)
            
            line_pow=P[i1-5, :, 0, 0, 1] #P[xindex, yindex all, 0, 0, Y polarization]
            p_target=np.max(line_pow)
            print('P_TE:', p_target)
    else:
        print("base file doesn't exist...")
    return -p_target

#--- MAIN ---------------------------------------------------------------------+

class Particle:
    def __init__(self,x0):
        self.position_i=[]          # particle position
        self.velocity_i=[]          # particle velocity
        self.pos_best_i=[]          # best position individual
        self.err_best_i=-1          # best error individual
        self.err_i=-1               # error individual

        for i in range(0,num_dimensions):
            self.velocity_i.append(random.uniform(-1,1)) #up to 4 decimal place
            self.position_i.append(x0[i])

    # evaluate current fitness
    def evaluate(self,costFunc):
        self.err_i=costFunc(self.position_i)

        # check to see if the current position is an individual best
        if self.err_i < self.err_best_i or self.err_best_i==-1:
            self.pos_best_i=self.position_i
            self.err_best_i=self.err_i

    # update new particle velocity
    def update_velocity(self,pos_best_g):
        w=0.5       # constant inertia weight (how much to weigh the previous velocity)
        c1=1        # cognative constant
        c2=2        # social constant

        for i in range(0,num_dimensions):
            r1=random.random()
            r2=random.random()

            vel_cognitive=c1*r1*(self.pos_best_i[i]-self.position_i[i])
            vel_social=c2*r2*(pos_best_g[i]-self.position_i[i])
            self.velocity_i[i]=w*self.velocity_i[i]+vel_cognitive+vel_social

    # update the particle position based off new velocity updates
    def update_position(self,bounds):
        for i in range(0,num_dimensions):
            self.position_i[i]=self.position_i[i]+self.velocity_i[i]

            # adjust maximum position if necessary
            if self.position_i[i]>bounds[i][1]:
                self.position_i[i]=bounds[i][1]

            # adjust minimum position if neseccary
            if self.position_i[i] < bounds[i][0]:
                self.position_i[i]=bounds[i][0]
                
class PSO():
    def __init__(self,costFunc,x0,bounds,num_particles,maxiter):
        global num_dimensions

        num_dimensions=len(x0)
        err_best_g=-1                   # best error for group
        pos_best_g=[]                   # best position for group

        # establish the swarm
        swarm=[]
        for i in range(0,num_particles):
            swarm.append(Particle(x0))

        # begin optimization loop
        i=0
        while i < maxiter:
            #print i,err_best_g
            # cycle through particles in swarm and evaluate fitness
            for j in range(0,num_particles):
                print ('Swarm=', i, ', Particle=', j)
                swarm[j].evaluate(costFunc)

                # determine if current particle is the best (globally)
                if swarm[j].err_i < err_best_g or err_best_g == -1:
                    pos_best_g=list(swarm[j].position_i)
                    err_best_g=float(swarm[j].err_i)

            # cycle through swarm and update velocities and position
            for j in range(0,num_particles):
                swarm[j].update_velocity(pos_best_g)
                swarm[j].update_position(bounds)
            i+=1

        # print final results
        print ('FINAL:')
        print (pos_best_g)
        print (err_best_g)
        

#--- RUN ----------------------------------------------------------------------+
initial=[50, 0.65, 0.45, 0.525]               # initial starting location [x1,x2...]
bounds=[(48, 53), (0.6, 0.75), (0.4, 0.5), (0.5,0.6)]  # input bounds [(x1_min,x1_max),(x2_min,x2_max)...]
PSO(func1,initial,bounds,num_particles=20,maxiter=10)

