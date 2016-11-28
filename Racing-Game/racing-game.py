import Constants
import math
import random
import operator
import pygame

class Texture:
    def __init__(self, filename):
        self.surface = pygame.image.load(filename).convert_alpha()

    def update(self):
        pass

class AnimatedTexture(Texture):
    def __init__(self, filename, numFrames, loop = False, speed = Constants.DEFAULT_ANIMATION_SPEED):
        self.currentFrame = 0
        self.speed = speed
        self.surfaces = []
        self.done = False
        self.loop = loop
        name, ext = os.path.splitext(filename)
        for i in range(numFrames):
            self.surfaces.append(pygame.image.load(name + "-" + str(i) + ext).convert_alpha())
        self.start()

    def start(self, frame = 0):
        self.currentFrame = frame
        self.surface = self.surfaces[self.currentFrame]
        self.startTime = time.time()

    def update(self):
        if self.done:
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

class Sprite:
    def __init__(self, engine, texture, pos, size, rotation=0):
        self.engine = engine
        self.x, self.y = pos
        self.w, self.h = size
        self.rotation = rotation
        self.texture = texture
        self.transform(size, rotation)

    def transform(self, size, rotation):
        self.w, self.h = size
        self.rotation = rotation
        self.displaySurf = pygame.transform.scale(self.texture.surface, (self.w, self.h))
        

    def changeRotation(self, rotation):
        self.rotation = rotation

    def update(self):
        pass

    def display(self, screen):
        #displaySurf = pygame.transform.scale(self.texture.surface, (self.w, self.h))
        #self.displaySurf = pygame.transform.rotozoom(self.texture.surface, self.rotation, 1)
        rect = self.displaySurf.get_rect()
        self.engine.gui.blitSurface(self.displaySurf, (self.x-(rect.width/2), self.y-(rect.height/2)) )
        
    def changePosition(self, newX, newY):
        self.x = newX
        self.y = newY

class CollisionSolver:
    INVERTED_BOX = 1
    BOX = 2
    
    @staticmethod
    def checkCollision(o1, o2):
        if not o1.solid or not o2.solid:
            return False

        # Check for sphere-sphere
        if o1.collisionType == CollisionSolver.BOX and o2.collisionType == CollisionSolver.BOX:
            return CollisionSolver.checkCollisionSphereSphere(o1, o2)
        elif o1.collisionType == CollisionSolver.BOX and o2.collisionType == CollisionSolver.INVERTED_BOX:
            return CollisionSolver.checkCollisionBoxInvertedBox(o1, o2)
        elif o1.collisionType == CollisionSolver.INVERTED_BOX and o2.collisionType == CollisionSolver.BOX:
            return CollisionSolver.checkCollision(o2, o1)
        



        # Check for others
        
        raise ValueError('CollisionSolver.areColliding got invalid parameters')
    
    @staticmethod
    def checkCollisionBoxBox(a, b):
        x1 = a.x - a.w/2
        y1 = a.y - a.h/2
        w1 = a.w
        h1 = a.h
        x2 = b.x - b.w/2
        y2 = b.x - b.h/2
        w2 = b.w
        h2 = b.h
        return (abs(x1 - x2) * 2 < (w1 + w2)) and (abs(y1 - y2) * 2 < (h1 + h2));

    @staticmethod
    def checkCollisionBoxInvertedBox(a, b):
        x1 = a.x - a.w/2
        y1 = a.y - a.h/2
        w1 = a.w
        h1 = a.h
        x2 = b.x - b.w/2
        y2 = b.x - b.h/2
        w2 = b.w
        h2 = b.h
        if x1 < x2 or (x1 + w1) > (x2 + w2):
            return True
        if y1 < y2 or (y1 + h1) > (y2 + h2):
            return True

        return False

class GameObject(Sprite):
    def __init__(self, engine, texture, pos, size, collisionType=CollisionSolver.BOX, rotation=0):
        Sprite.__init__(self, engine, texture, pos, size, rotation)
        self.dead = False
        self.solid = True
        self.engine = engine
        self.collisionType = collisionType
    

    def kill(self):
        self.dead = True

    def display(self, screen):
        if self.dead:
            return
        Sprite.display(self, screen)

    def explode(self):
        self.engine.addObject(Explosion(self.engine, (self.x, self.y)))

    def hit(self, other):
        pass

class Explosion(GameObject):
    def __init__(self, engine, pos, num = None):
        if num == None:
            num = random.randrange(len(Constants.EXPLOSION_IMAGE))
        self.num = num
        GameObject.__init__(self, engine, AnimatedTexture(EXPLOSION_IMAGE[num], Constants.EXPLOSION_NUMFRAMES[num], False), pos, Constants.EXPLOSION_SIZE[num], 0)
        self.solid = False
        self.engine.soundManager.getSound(Constants.EXPLOSION_SOUND[num]).play()

    def update(self):
        if self.dead:
            return
        self.texture.update()
        if self.texture.done:
            self.kill()

class Car(GameObject):
    def __init__(self, engine, pos, velocity, num = None):
        self.xv, self.yv = velocity
        self.rv = 0
        if num == None:
            num = random.randrange(len(Constants.CAR_IMAGE))
        self.acceleration = Constants.CAR_ACCELERATION[num]
        self.maxSpeed = Constants.CAR_MAX_SPEED[num]
        GameObject.__init__(self, engine, Texture(Constants.CAR_IMAGE[num]), pos, Constants.CAR_SIZE[num])

    def hit(self, other):
        pass

    def update(self):
        if self.dead:
            return
        self.control()
        self.changePosition(self.x + self.xv, self.y + self.yv)
        self.changeRotation(self.rotation + self.rv)
        if self.x -self.w/2 < 0:
            self.x = self.w/2
        elif self.x + self.w/2 > self.engine.gui.size[0]:
            self.x = self.engine.gui.size[0] - self.w/2

    def slow(self):
        self.yv *= Constants.FRICTION

    def accelerate(self):
        self.yv = max(self.maxSpeed, self.yv + self.acceleration)

    def control(self):
        pass

class AICar(Car):
    def __init__(self, engine, pos, velocity, num = None):
        if num == None:
            num = random.randrange(len(Constants.FIRST_AI_CAR, Constants.LAST_AI_CAR))
        Car.__init__(self, engine, pos, velocity, num)

    def control(self):
        self.accelerate()

class PlayerCar(Car):
    def __init__(self, engine, pos, velocity, num = None):
        if num == None:
            num = Constants.PLAYER_CAR
        Car.__init__(self, engine, pos, velocity, num)
        self.turnSpeed = Constants.TURNSPEED[num]
        
    def goLeft(self):
        self.xv =- self.turnSpeed

    def goRight(self):
        self.xv = self.turnSpeed

    def goStraight(self):
        self.xv = 0

    def control(self):
        self.accelerate()
        

class Lane(object):
    def __init__(self, left, right):
        self.left = left
        self.right = right
        self.center = (self.left + self.right) / 2

    def isInLane(self, obj):
        return obj.x - obj.w/2 >= self.left and obj.x + obj.w/2 <= self.right

class Road(GameObject):
    def __init__(self, engine, pos, size, numLanes):
        self.engine = engine
        self.collisionType = CollisionSolver.INVERTED_BOX
        self.x, self.y = pos
        self.w, self.h = size
        self.dead = False
        self.solid = True
        self.numLanes = numLanes
        self.engine = engine
        self.initLanes()
        self.s1 = Sprite(self.engine, Texture(Constants.BACKGROUND_TEXTURE), (self.engine.gui.size[0]/2, 0), self.engine.gui.size)
        self.s2 = Sprite(self.engine, Texture(Constants.BACKGROUND_TEXTURE), (self.engine.gui.size[0]/2, -self.engine.gui.size[1]), self.engine.gui.size)

    def initLanes(self):
        laneSize = self.w / self.numLanes
        self.lanes = []
        for i in range(self.numLanes):
            self.lanes.append(Lane(i * laneSize, i * laneSize + laneSize))

    def update(self):
        yDiff = self.s1.y + self.s1.h/2 - self.engine.camera.pos[1]
        if yDiff >= 2 * self.engine.gui.size[1]:
            self.s1.y -= self.engine.gui.size[1] * 2
            self.s1, self.s2 = self.s2, self.s1

    def hit(self, other):
        other.slow()
        

    def display(self, screen):
        self.s1.display(screen)
        self.s2.display(screen)


class GUI:
    def __init__(self, engine):
        pygame.init()
        self.engine = engine
        self.size = Constants.WINDOW_SIZE
        self.title = Constants.WINDOW_TITLE
        self.icon = Constants.WINDOW_ICON
        self.screen = pygame.display.set_mode( self.size )
        self.setCaption(self.title, self.icon)
        self.background = pygame.Surface(self.screen.get_size())
        self.background = self.background.convert()
        self.background.fill((0, 0, 0))

    def cleanup(self):
        pass

    def setCaption(self, title, icon):
        pygame.display.set_caption(title, icon)

    def beginDraw(self):
        self.screen.blit(self.background, (0, 0) )

    def endDraw(self):
        pygame.display.flip()

    def blitSurface(self, surface, pos):
        self.screen.blit(surface, self.engine.camera.applyOffset(pos))

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

class Camera(object):
    def __init__(self, follow, size):
        self.follow = follow
        self.size = size
        self.pos = (0, 0)

    def applyOffset(self, pos):
        return tuple(map(operator.sub, pos, self.pos))

    def update(self):
        self.pos = (self.pos[0], self.follow.y - 3/4*self.size[1])

class Game:

    def __init__(self):
        self.init()
        self.loop()
        self.quit()

    def init(self):
        pygame.init()
        self.soundManager = SoundManager()
        self.gui = GUI(self)
        self.objects = []
        self.playerCar = PlayerCar(self, (self.gui.size[0] // 2, self.gui.size[1] // 2), (0, 0), 0)
        self.camera = Camera(self.playerCar, self.gui.size)
        #pos = (140, 0)
        pos = (self.gui.size[0] // 2, self.gui.size[1] // 2)
        size = (360, 100000000000000000000)
        self.addObject(Road(self, pos, size, 3))
        self.addObject(self.playerCar)
        

    def quit(self):
        self.soundManager.quit()
        pygame.quit()

    def processPlayer(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_a] == keys[pygame.K_d]:
            self.playerCar.goStraight()
        elif keys[pygame.K_a]:
            self.playerCar.goLeft()
        elif keys[pygame.K_d]:
            self.playerCar.goRight()

    def doPhysics(self):
        for i in range(len(self.objects)):
            for j in range(i + 1, len(self.objects)):
                if CollisionSolver.checkCollision(self.objects[i], self.objects[j]):
                    self.objects[i].hit(self.objects[j])
                    self.objects[j].hit(self.objects[i])

    def loop(self):
        done = False
        clock = pygame.time.Clock()
        while not done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    done = True
            
            self.processPlayer()
            self.doPhysics()
            self.camera.update()
            self.updateAllObjects()
            self.removeDead()
            self.draw()
            clock.tick(60)

    def addObject(self, object):
        self.objects.append(object)

    def updateAllObjects(self):
        for o in self.objects:
            o.update()
    
    def draw(self):
        self.gui.beginDraw()
        for o in self.objects:
            o.display(self.gui.screen)
        self.gui.endDraw()

    def removeDead(self):
        for o in list(self.objects):
            if o.dead:
                self.objects.remove(o)

Game()
