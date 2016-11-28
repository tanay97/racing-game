import Constants
import math
import operator
import os
import pygame
import random
import time
from functools import *

class Texture:
    def __init__(self, filename):
        self.backupSurface = self.surface = pygame.image.load(filename).convert_alpha()

    def scaleTo(self, size):
        self.surface = pygame.transform.smoothscale(self.backupSurface, size)

    def update(self):
        pass
    
class AnimatedTexture(Texture):
    def __init__(self, filename, numFrames, loop, speed, start=0):
        self.currentFrame = start
        self.speed = speed
        self.surfaces = []
        self.backupSurfaces = []
        self.done = False
        self.loop = loop
        name, ext = os.path.splitext(filename)
        for i in range(numFrames):
            s = pygame.image.load(name + "-" + str(i) + ext).convert_alpha()
            self.backupSurfaces.append(s)
            self.surfaces.append(s)
        self.start(start)

    def scaleTo(self, size):
        for i in range(len(self.backupSurfaces)):
            self.surfaces[i] = pygame.transform.smoothscale(self.backupSurfaces[i], size)
        self.surface = self.surfaces[self.currentFrame]

    def start(self, frame = 0):
        self.currentFrame = frame
        self.surface = self.surfaces[self.currentFrame]
        self.startTime = time.time()

    def update(self):
        if self.done or self.speed == -1:
            return

        if (time.time() - self.startTime) >= self.speed:
            self.advanceFrame()
    
    def advanceFrame(self):
        self.currentFrame += 1
        if self.currentFrame == len(self.surfaces):
            if self.loop:
                self.currentFrame = 0
            else:
                self.done = True
                self.currentFrame -= 1
        self.surface = self.surfaces[self.currentFrame]    
    
class CollisionSolver:
    NONE = 0
    BOX = 1
    INVERTED_BOX = 2

    @staticmethod
    def checkCollision(o1, o2):
        if o1.collisionType == CollisionSolver.NONE or o2.collisionType == CollisionSolver.NONE:
            return
        
        # Check for sphere-sphere
        if o1.collisionType == CollisionSolver.BOX and o2.collisionType == CollisionSolver.BOX:
            return CollisionSolver.checkCollisionBoxBox(o1, o2)
        elif o1.collisionType == CollisionSolver.BOX and o2.collisionType == CollisionSolver.INVERTED_BOX:
            return CollisionSolver.checkCollisionBoxInvertedBox(o1, o2)
        elif o1.collisionType == CollisionSolver.INVERTED_BOX and o2.collisionType == CollisionSolver.BOX:
            return CollisionSolver.checkCollision(o2, o1)

        # Check for others
        
        raise ValueError('CollisionSolver.areColliding got invalid parameters')
    
    @staticmethod
    def checkCollisionBoxBox(a, b):
        x1 = a.x
        y1 = a.y
        w1 = a.w
        h1 = a.h
        x2 = b.x
        y2 = b.y
        w2 = b.w
        h2 = b.h
        return (abs(x1 - x2) * 2 < (w1 + w2)) and (abs(y1 - y2) * 2 < (h1 + h2))
    
    @staticmethod
    def checkCollisionBoxInvertedBox(a, b):
        x1 = a.x
        y1 = a.y
        w1 = a.w
        h1 = a.h
        x2 = b.x
        y2 = b.y
        w2 = b.w
        h2 = b.h
        if x1 < x2 or (x1 + w1) > (x2 + w2):
            return True
        if y1 < y2 or (y1 + h1) > (y2 + h2):
            return True
    
        return False    
        
    
class Sprite:
    def __init__(self, texture, pos, size):
        self.x, self.y = pos
        self.w, self.h = size
        self.texture = texture
        self.texture.scaleTo(size)
        self.size = size

    def update(self):
        pass

    def display(self, gui):
        gui.blitSurface(self.texture.surface, (self.x, self.y))

class Score(Sprite):
    def __init__(self):
        self.value = 0
        self.font = pygame.font.SysFont("monospace", 30)
        self.msgFont = pygame.font.SysFont("arial", 80)
        self.changeScore(0)
        self.timerStarted = False
        self.countdownLabel = self.msgFont.render("", 1,(255,0,0))
        self.displayplacement("")
        self.timerStopped = False
    
    def changeScore(self, change):
        # render text
        self.scoreLabel = self.font.render(str(self.value) + "(+" + str(change) + ")", 1, (255,255,255))
    
    def displayplacement(self,placement):
        self.placingLabel = self.font.render(str(placement),1,(255,255,0))
                                             
    def display(self, gui):

        gui.screen.blit(self.placingLabel,(gui.w - self.placingLabel.get_rect().width,gui.h-self.placingLabel.get_rect().height))
        #gui.screen.blit(self.scoreLabel, (0, 0))
        gui.screen.blit(self.countdownLabel,(gui.w/2 - self.countdownLabel.get_rect().width/2, gui.h/2 - self.countdownLabel.get_rect().height/2))
        if self.timerStarted:
            if not self.timerStopped:
                self.timeLabel = self.font.render(self.secondsToStr(time.time() - self.startTime), 1, (0, 0, 0))
            gui.screen.blit(self.timeLabel, (0, 0))
    def countDown(self, countdown):
        self.countdownLabel = self.msgFont.render(countdown, 1,(255,0,0))
        
    def stopTimer(self):
        self.timerStopped = True
    
    def add(self, v):
        self.value += v
        self.changeScore(v)
        
        
    def startTimer(self):
        self.startTime = time.time()
        self.timerStarted = True
        
    # From http://code.activestate.com/recipes/511486-secondstostr-hmmsssss-formatting-of-floating-point/
    def secondsToStr(self, t):
        rediv = lambda ll,b : list(divmod(ll[0],b)) + ll[1:]
        return "%d:%02d:%02d.%03d" % tuple(reduce(rediv,[[t*1000,],1000,60,60]))    

class GameObject(Sprite):
    def __init__(self, engine, texture, pos, size, collisionType, name):
        Sprite.__init__(self, texture, pos, size)
        
        self.dead = False
        self.engine = engine
        self.collisionType = collisionType
        self.name = name
    
    def update(self):
        self.texture.update()
        
    def explode(self, size):
        self.engine.objects.append(Explosion( self.engine, (self.x + self.w / 2 - size / 2, self.y + self.h / 2 - size / 2), (size, size) ) )
        self.dead = True
    
    def hit(self, other):
        pass    
    
class Explosion(GameObject):
    def __init__(self, engine, pos, size):
        GameObject.__init__(self, engine, AnimatedTexture("data/explode-alpha/explode-alpha.png", 30, False, .1), pos, size, CollisionSolver.BOX, "Explosion")
        if self.engine.camera.canSee((self.x,self.y),(self.w,self.h)) == True:
            self.engine.soundManager.getSound(Constants.EXPLOSION_SOUND).play()
            self.engine.soundManager.getSound(Constants.EXPLOSION_SOUND).fadeout(1500)
    def update(self):
        self.texture.update()
        if self.texture.done:
            self.dead = True

class Sensor(GameObject):
    def __init__(self, engine, pos, size):
        GameObject.__init__(self, engine, Texture("data/sensor.png"), pos, size, CollisionSolver.NONE, "Sensor")
    
    def update(self):
        pass
    
    def hasPassed(self, obj):
        return obj.y < self.y


class Start(GameObject):
    def __init__(self, engine, pos, size):
        GameObject.__init__(self, engine, Texture("data/start.png"), pos, size, CollisionSolver.NONE, "Start")

class Finish(GameObject):
    def __init__(self, engine, pos, size):
        GameObject.__init__(self, engine, Texture("data/finish.png"), pos, size, CollisionSolver.NONE, "Finish")
    


class Car(GameObject):
    def __init__(self, engine, texture, pos, a, v, vt, name):
        self.xv, self.yv = 0, 0
        self.acceleration = a
        self.maxSpeed = v
        self.turnSpeed = vt
        self.collisionDelay = .5
        self.lastCollisionTime = time.time() - self.collisionDelay
        GameObject.__init__(self, engine, texture, pos, Constants.CAR_SIZE, CollisionSolver.BOX, name) 
        
    def hit(self, other):
        pass
    
    def update(self):
        self.x += self.xv
        self.y += self.yv
        self.slow()
        self.act()
        
    def act(self):
        self.accelerate()
        
    def slow(self):
        if time.time() < self.lastCollisionTime + self.collisionDelay:
            self.yv *= Constants.FRICTION
        
    def accelerate(self):
        self.yv += self.acceleration
        if self.yv > self.maxSpeed:
            self.yv = self.maxSpeed
        elif self.yv < -self.maxSpeed:
            self.yv = -self.maxSpeed

class AICar(Car):
    def __init__(self, engine, pos):
        texture = AnimatedTexture(Constants.AI_CAR_IMAGE, Constants.NUM_AI_CARS, loop=False, speed=-1, start=random.randrange(Constants.NUM_AI_CARS))
        a = Constants.AI_CAR_ACCELERATION
        v = Constants.AI_CAR_SPEED
        vt = Constants.AI_CAR_TURNSPEED
        self.moving = False
        self.lanes = []
        
        Car.__init__(self, engine, texture, pos, a, v, vt, "AICar")
        
        for lane in engine.road.lanes:
            if lane.isObjectIn(self):
                self.lanes.append(lane)      
        
    def act(self):
        self.accelerate()
        if self.moving:
            self.moveToClearLane()
        else:
            self.chooseLane()
    
    def moveToClearLane(self):
        if self.xv == 0 or not self.moving:
            return
        
        if self.xv > 0 and self.x >= self.xTarget:
            self.x = self.xTarget
            self.xv = 0
            self.moving = False
            del self.lanes[0]
        elif self.xv < 0 and self.x <= self.xTarget:
            self.x = self.xTarget
            self.xv = 0
            self.moving = False
            del self.lanes[0]
            
    def chooseLane(self):
        currentLane = self.engine.road.getLaneObjectIsIn(self)
        lanes = [currentLane] + self.engine.road.getAdjacentLanes(currentLane)
        dists = []
        for i in range(len(lanes)):
            lane = lanes[i]
            dists.append(300)
            for o in self.engine.objects + self.engine.normalCars:
                if o is self:
                    continue
               
                
                dist = self.y - o.y
                if dist < -self.w * 2:
                    continue
                if o.name == "AICar" and dist < self.w:
                    #print ("Found AICar")
                    if lane in o.lanes:
                        #print ("Already reserved lane")
                        dists[i] = -1
                        break
                    else:
                        #print ("Lane is free")
                        pass
                        
                if not lane.isObjectIn(o):
                    continue                
                if dist < dists[i]:
                    dists[i] = dist
        
        target = lanes[dists.index(max(dists))]
        self.lanes.append(target)
                
        self.xTarget = target.center - self.w/2
        self.xv = math.copysign(self.turnSpeed, self.xTarget - self.x)
        self.moving = True
        
    def hit(self, other):
        if other.name == "NormalCar":
            self.lastCollisionTime = time.time()
        

class NormalCar(Car):
    def __init__(self, engine, pos,turnlane):
        texture = AnimatedTexture(Constants.NORMAL_CAR_IMAGE, Constants.NUM_NORMAL_CARS, loop=False, speed=-1, start=random.randrange(Constants.NUM_NORMAL_CARS))
        a = Constants.NORMAL_CAR_ACCELERATION
        v = Constants.NORMAL_CAR_SPEED
        vt = Constants.NORMAL_CAR_TURNSPEED
        self.turnlane = turnlane
        self.moving = False
        #print ("Constructor: " + str(self.turnlane))
        Car.__init__(self, engine, texture, pos, a, v, vt, "NormalCar")
        
    def hit(self, other):
        if other.name == "PlayerCar" or other.name == "AICar":
            self.explode(300)            
            
    def act(self):
        self.accelerate()
        if self.y > -self.engine.camera.yOffset + self.engine.camera.h + Constants.CAR_SIZE[1]:
            self.dead = True
        self.moveToLane()

    def moveNormalCar(self):
        if self.turnlane == None:
            return
        if self.moving or self.turnlane.isObjectIn(self):
            return
        self.engine.soundManager.getSound(Constants.TIRE_SKID).play()
        self.engine.soundManager.getSound(Constants.TIRE_SKID).fadeout(500)
        self.xv = math.copysign(Constants.NORMAL_CAR_TURNSPEED,self.turnlane.x - self.x)
        #print("xv: " + str(self.xv))
        self.moving = True
        self.xTarget=self.turnlane.center - self.w/2
        #print("xTarget: " + str(self.xTarget))

    def moveToLane(self):
        if self.xv == 0 or not self.moving:
            return
        #print ("moving")
        if self.xv > 0 and self.x >= self.xTarget:
            self.x = self.xTarget
            self.xv = 0
            self.moving = False

        elif self.xv < 0 and self.x <= self.xTarget:
            self.x = self.xTarget
            self.xv = 0
            self.moving = False
    

class PlayerCar(Car):
    def __init__(self, engine, pos):
        texture = Texture(Constants.PLAYER_CAR_IMAGE)
        a = Constants.PLAYER_CAR_ACCELERATION
        v = Constants.PLAYER_CAR_SPEED
        vt = Constants.PLAYER_CAR_TURNSPEED
        Car.__init__(self, engine, texture, pos, a, v, vt, "PlayerCar")
        self.engine.soundManager.getSound(Constants.ENGINE_SOUND).play(-1)
    
    def hit(self, other):
        if other.name == "Road" or other.name == "NormalCar":
            self.lastCollisionTime = time.time()
        if other.name == "AICar":
            # Try self.x
            self.x -= self.xv
            if CollisionSolver.checkCollision(self, other):
                self.x += self.xv
                self.y -= self.yv
                if CollisionSolver.checkCollision(self, other):
                    self.y += self.yv
                    other.x -= other.xv
                    if CollisionSolver.checkCollision(self, other):
                        other.x += other.xv
                        other.y -= other.yv
                        if CollisionSolver.checkCollision(self, other):
                            other.y += other.yv
        pass
    
    def goLeft(self):
        self.xv =- self.turnSpeed
    
    def goRight(self):
        self.xv = self.turnSpeed
    
    def goStraight(self):
        self.xv = 0
        
        
class Lane(object):
    def  __init__(self, pos, size):
        self.x = pos
        self.w = size
        self.center = self.x + self.w / 2
        
    def isObjectIn(self, obj):
        return obj.x + obj.w >= self.x and obj.x <= self.x + self.w

class Road(GameObject):
    def __init__(self, engine, length, numLanes):
        self.w = 360
        self.h = length
        self.x = engine.gui.w/2 - self.w/2
        self.y = -self.h
        self.lanes = []
        laneSize = self.w / numLanes
        for i in range(numLanes):
            self.lanes.append(Lane(i*laneSize + self.x, laneSize))
        self.collisionType = CollisionSolver.INVERTED_BOX
        self.dead = False
        self.engine = engine
        self.name = "Road"
        self.s1 = Sprite(Texture(Constants.BACKGROUND_TEXTURE), (0, 0), (self.engine.gui.w, self.engine.gui.h) )
        self.s2 = Sprite(Texture(Constants.BACKGROUND_TEXTURE), (0, -self.engine.gui.h), (self.engine.gui.w, self.engine.gui.h) )
        
    def update(self):
        self.s1.update()
        self.s2.update()
        
        yDiff = self.s1.y + self.s1.h + self.engine.camera.yOffset
        if yDiff >= 2 * self.engine.gui.h:
            self.s1.y -= self.engine.gui.h * 2
            self.s1, self.s2 = self.s2, self.s1     
        
    def display(self, gui):
        self.s1.display(gui)
        self.s2.display(gui)
        
    def getAdjacentLanes(self, lane):
        re = []
        index = self.lanes.index(lane)
        if index > 0:
            re.append(self.lanes[index - 1])
        if index < len(self.lanes) - 1:
            re.append(self.lanes[index + 1])
        return re
    
    def getLaneObjectIsIn(self, obj):
        for lane in self.lanes:
            if lane.isObjectIn(obj):
                return lane
        return None



class Camera(object):
    def __init__(self, follow, size):
        self.follow = follow
        self.w, self.h = size
        self.xOffset, self.yOffset = (0, 0)
        self.collisionType = CollisionSolver.BOX

    def applyOffset(self, pos):
        return (pos[0] + self.xOffset, pos[1] + self.yOffset)

    def update(self):
        #self.xOffset = -self.follow.x - self.follow.w/2 + self.w / 2
        self.yOffset = -self.follow.y  + self.h - self.follow.h
        
    def canSee(self, pos, size):
        y1 = pos[1]
        h1 = size[1]
        y2 = -self.yOffset
        h2 = self.h
        return y1 < y2 + h2 and h1 + y1 > y2
            
            
class SoundManager:
    def __init__(self):
        pygame.mixer.pre_init()
        pygame.mixer.init()
        self.sounds = dict()
    
    def getSound(self, filename):
        if not filename in self.sounds.keys():
            self.sounds[filename] = pygame.mixer.Sound(filename)
        return self.sounds[filename]

    def quit(self):
        pygame.mixer.quit()
        
class GUI:
    def __init__(self, engine, size, title, icon):
        pygame.init()
        pygame.font.init()
        self.engine = engine
        self.w, self.h = size
        self.title = title
        self.icon = icon
        self.screen = pygame.display.set_mode( (self.w, self.h) )
        self.setCaption(self.title, self.icon)
        self.background = pygame.Surface(self.screen.get_size())
        self.background = self.background.convert()
        self.background.fill((0, 0, 0))

    def cleanup(self):
        pygame.font.quit()
        pass

    def setCaption(self, title, icon):
        pygame.display.set_caption(title, icon)

    def beginDraw(self):
        self.screen.blit(self.background, (0, 0) )

    def endDraw(self):
        pygame.display.flip()

    def blitSurface(self, surface, pos):
        if self.engine.camera.canSee(pos, surface.get_rect().size):
            self.screen.blit(surface, self.engine.camera.applyOffset(pos))
        
class Controller:
    def __init__(self, engine):
        self.engine = engine
        # Initialize cars
        self.cars = self.engine.aiCars
        random.shuffle(self.cars)
        # The cars at the start will move slower
        self.accelerations = []
        self.finalPositions = []
        self.passed = []
        for i in range(len(self.cars)):
            self.accelerations.append(Constants.PLAYER_CAR_SPEED * i * .1)
            self.finalPositions.append((i + 1) * .2 * -self.engine.road.h)
            self.passed.append(False)
        
        #self.accelerations.sort()
        for i in range(len(self.cars)):
            self.cars[i].yv = -self.accelerations[i]
            self.cars[i].maxSpeed = 10000000
        
    def setInitialSpeeds(self):
        for i in range(len(self.cars)):
            if not self.passed[i] and self.cars[i].y + self.cars[i].h < -self.engine.camera.yOffset - self.engine.camera.h:
                # This code only excecutes once (for each car). It sets the speed of the car once it has left the screen initially        if not self.passed[i] and self.cars[i].y < -self.engine.camera.yOffset - self.engine.camera.h:
                self.passed[i] = True
                # Calculate the time it takes the player car to pass this car
                dp = self.finalPositions[i] - self.engine.playerCar.y
                t = dp / self.engine.playerCar.maxSpeed
            
                # Calculate the velocity this car has to go to meet there
                dai = (self.finalPositions[i] - self.cars[i].y)
                v = dai / t
                # Set this car's velocity to v
                self.cars[i].yv = -v
                self.cars[i].maxSpeed = v        
        
    def update(self):
        self.setInitialSpeeds()
        self.correctCars()
        
            

    def findNormalCar(self):
        i = 0
        mindistance = 10000000
        while i < len(self.engine.normalCars):
            car = self.engine.normalCars[i]
            currentdistance = abs(car.y - self.engine.playerCar.y)
            if currentdistance < mindistance and car.turnlane != None and currentdistance > 150:
                mindistance = currentdistance
                carin = i
            i += 1
        self.engine.normalCars[carin].moveNormalCar()
        #print (self.engine.normalCars[carin])
            
    def correctCars(self):
        for i in range(len(self.cars)):
            if not self.passed[i]:
                continue
            if self.finalPositions[i] > self.cars[i].y:
                self.cars[i].maxSpeed = Constants.PLAYER_CAR_SPEED - 3
            elif self.cars[i].y > self.engine.playerCar.y:
                self.cars[i].maxSpeed = Constants.PLAYER_CAR_SPEED - 3
            else:
                # Calculate the ideal v
                dp = self.finalPositions[i] - self.engine.playerCar.y
                t = dp / self.engine.playerCar.maxSpeed
                dai = (self.finalPositions[i] - self.cars[i].y)
                v = dai / t
                # nudge the ai car's speed a little towards it, applying a lower cap
                dv = min(math.copysign(1, v - self.cars[i].maxSpeed), v - self.cars[i].maxSpeed)
                self.cars[i].maxSpeed = max((Constants.PLAYER_CAR_SPEED ), self.cars[i].maxSpeed + dv) # The speed will never go lower than 10
        
class Game:

    def __init__(self):
        self.init()
        self.loop()
        self.quit()

    def init(self):

        self.gui = GUI(self, Constants.WINDOW_SIZE, "Racing Game", "")
        self.soundManager = SoundManager()
        self.reset()
        self.score
        self.first = True

    def reset(self):
        print ("Resetting")
        self.objects = []
        self.road = Road(self, 100000, 5)
        self.objects.append(self.road)
        self.objects.append(Start(self, (self.road.x, -250), (self.road.w, 250) ) )
        self.objects.append(Finish(self, (self.road.x, -self.road.h -250), (self.road.w, 250) ) )        
        self.aiCars = []
        self.normalCars = []
        self.score = Score()
        self.scorelist = []
        self.placeSensors()
        self.fps = 60
        for i in range(5):
            if i == 2:
                self.playerCar = PlayerCar( self, (self.road.lanes[i].center - Constants.CAR_SIZE[0] / 2, -Constants.CAR_SIZE[1]))
                car = self.playerCar
            else:
                car = AICar(self, (self.road.lanes[i].center - Constants.CAR_SIZE[0] / 2, -Constants.CAR_SIZE[1]) ) 
                self.aiCars.append(car)
            self.objects.append(car)
        self.camera = Camera(self.playerCar, Constants.WINDOW_SIZE )
        self.lastChallenge = time.time()
        self.placeCars()
        self.controller = Controller(self)
        self.initStateMachine()        

    def initStateMachine(self):
        self.STATE_WAITING = 0
        self.STATE_COUNTDOWN = 1
        self.STATE_PLAYING = 2
        self.state = self.STATE_WAITING
        
    def quit(self):
        self.soundManager.quit()
        pygame.quit()

    def doWaitingLogic(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.done = True
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    done = True
                elif event.key == pygame.K_SPACE:
                    self.starttime = time.time()
                    if not self.first:
                        self.reset()
                    self.state = self.STATE_COUNTDOWN
        self.camera.update()
        self.drawObjects()

    def doCountdownLogic(self):
        if time.time() - self.starttime >= 3:
            self.countdown = "Go!!"
            self.state = self.STATE_PLAYING
            self.score.startTimer()
            
            self.starttime = time.time()

        elif time.time() - self.starttime >= 2:
            self.countdown = "1"
        elif time.time() - self.starttime >= 1:
            self.countdown = "2"
        elif time.time() - self.starttime >= 0:
            self.countdown = "3"
        
        self.score.countDown(self.countdown)
        self.camera.update()
        self.drawObjects()


    def doPlayingLogic(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.done = True
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.done = True
        if time.time() - self.starttime >= 1:
            self.score.countDown("")
        self.getPlacement()
        self.addChallenge()
        self.doPhysics()
        self.update()
        self.removeDead()
        self.drawObjects()
        

    def loop(self):
        self.done = False
        clock = pygame.time.Clock()
        
        while not self.done:
            
            if self.state == self.STATE_WAITING:
                self.doWaitingLogic()
            elif self.state == self.STATE_COUNTDOWN:
                self.doCountdownLogic()
            elif self.state == self.STATE_PLAYING:
                self.doPlayingLogic()
                
            clock.tick(self.fps)

    def update(self):
        self.controller.update()
        self.camera.update()
        for o in self.objects + self.normalCars:
            o.update()
        self.processPlayer()
        self.doScoring()
        
    def drawObjects(self):
        self.gui.beginDraw()
        for o in self.objects + self.normalCars + [self.score]:
            o.display(self.gui)
        self.gui.endDraw()
        
    def removeDead(self):
        for o in list(self.objects):
            if o.dead:
                self.objects.remove(o)
        for c in list(self.normalCars):
            if c.dead:
                self.normalCars.remove(c)     
                
    def doPhysics(self):
        for i in range(len(self.objects)):
            for j in range(i + 1, len(self.objects)):
                if CollisionSolver.checkCollision(self.objects[i], self.objects[j]):
                    self.objects[i].hit(self.objects[j])
                    self.objects[j].hit(self.objects[i])
            for car in self.normalCars:
                if self.camera.canSee((car.x,car.y),(car.w,car.h)):
                    if CollisionSolver.checkCollision(self.objects[i], car):
                        self.objects[i].hit(car)
                        car.hit(self.objects[i])
        
                        
    def processPlayer(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] == keys[pygame.K_RIGHT]:
            self.playerCar.goStraight()
        elif keys[pygame.K_LEFT]:
            self.playerCar.goLeft()
        elif keys[pygame.K_RIGHT]:
            self.playerCar.goRight()
        #if keys[pygame.K_SPACE]:
            #self.controller.findNormalCar()
        if self.playerCar.y < -self.road.h - self.playerCar.h:
            self.state = self.STATE_WAITING
            self.first = False
            self.score.stopTimer()
            
    def getMinDistance(self, lane1, lane2):
        vx = Constants.PLAYER_CAR_TURNSPEED
        dx = abs(lane1.center - lane2.center)
        #print("x distance: "+ str(dx))
        t = dx / vx
        vy = abs(Constants.NORMAL_CAR_SPEED - Constants.PLAYER_CAR_SPEED)
        dy = vy * t
        #print (dy)
        #if dy <= 100 and dy>0:
        dy += 2*Constants.CAR_SIZE[1]

        #print ("y distance"+ str(dy))
        return dy 
        
    def placeCars(self):
        yPos = -1000
        blankLane = self.road.lanes[0]
        currentLane = self.road.lanes[0]

        end = -self.road.h * Constants.NORMAL_CAR_SPEED / Constants.PLAYER_CAR_SPEED
        while yPos > end:
            pathLane = random.choice(self.road.lanes)
            blankLane = pathLane
            while pathLane == blankLane:
               blankLane = random.choice(self.road.lanes)
            yMin = self.getMinDistance(pathLane,currentLane)
            ySpace = 50 #self.getRandomLaneSpacing()
            yPos -= yMin + ySpace 
            possibleLanes = list(self.road.lanes)
            possibleLanes.remove(pathLane)
            for i in range(random.randrange(len(possibleLanes))):
                lane = random.choice(possibleLanes)
                possibleLanes.remove(lane)
                if i == 0:
                    adjacent = self.road.getAdjacentLanes(lane)
                    choices = [item for item in adjacent if item in possibleLanes]
                    if len(choices)> 0:
                        turnlane = random.choice(choices)
                        possibleLanes.remove(turnlane)
                    else:
                        turnlane = None
                else:
                    turnlane = None            
                self.addNormalCar(lane, yPos,turnlane)
        for car in self.normalCars:
                
            currentLane = pathLane 
    def placeSensors(self):
        self.sensors = []
        yPos = 0
        self.perfectSensorTimeScore = 5
        while yPos < self.road.h:
            yPos += 1000
            self.sensors.append(Sensor(self, (0, -yPos), (self.gui.w, 10) ) )
        totalTime = self.road.h / Constants.PLAYER_CAR_SPEED / 60
        print ("Total Time: " + str(totalTime) )
        self.perfectSensorTime = totalTime / len(self.sensors)
        self.lastSensorTime = -1
               
    
    def addChallenge(self):
        if len(self.scorelist) < 5:
            return
        average = sum(self.scorelist)/len(self.scorelist)
        if average >= Constants.DIFFICULTY:
            self.controller.findNormalCar()
            self.playerCar.maxSpeed = Constants.PLAYER_CAR_SPEED + (average - Constants.DIFFICULTY)*5
        else:
            self.playerCar.maxSpeed = Constants.PLAYER_CAR_SPEED
        
    def addNormalCar(self,lane,yPos,turnlane):
        xPos = lane.center
        c = NormalCar(self, (xPos - Constants.CAR_SIZE[0] / 2, yPos - Constants.CAR_SIZE[1] / 2),turnlane)
        self.normalCars.append(c)
        #self.addObject(c)

    def getPlacement(self):
        self.placement = 1
        for car in self.aiCars:
            if car.y < self.playerCar.y:
                self.placement += 1
        if self.placement == 1:
            self.score.displayplacement(str(self.placement)+ "st")
        elif self.placement == 2:
            self.score.displayplacement(str(self.placement)+ "nd")
        elif self.placement == 3:
            self.score.displayplacement(str(self.placement)+ "rd")
        else:
            self.score.displayplacement(str(self.placement)+ "th")
                
    def doScoring(self):
        if len(self.sensors) == 0:
            return
        if self.sensors[0].hasPassed(self.playerCar):
            del self.sensors[0]
            if self.lastSensorTime != -1:
                #print ("Time: " + str(time.time() - self.lastSensorTime) )
                #print ("Perfect Time: " + str(self.perfectSensorTime))
                score = round(self.perfectSensorTimeScore * self.perfectSensorTime / (time.time() - self.lastSensorTime),3)
                if score >= 5:
                    score = 5
                self.score.add(score)
                self.scorelist.append(score)
                if len(self.scorelist) > 5:
                    del self.scorelist[0]
    
            self.addChallenge()
            self.lastSensorTime = time.time()
    

Game()
