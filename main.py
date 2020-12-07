import pygame
import random
import math

import sys
import os

from pygame.sdlmain_osx import InstallNSApplication
InstallNSApplication()

def resource_path(relative_path):
    try:
    # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)



class TitleScreen:
    def __init__(self, width, height):
        self.screen = pygame.display.set_mode([width, height])
        self.clock = pygame.time.Clock()


    def run(self):
        w,h = pygame.display.get_surface().get_size()
        button = pygame.Rect(0, 7*h//8, w, h//8)

        font = pygame.font.SysFont(None, 100)
        text_img = font.render('Start Game', True, (0, 0, 0))
        text_rect = text_img.get_rect()

        text_rect.center = button.center

        self.screen.fill((255, 255, 255))

        splash = pygame.transform.scale(pygame.image.load("splash.bmp"), (w, 7*h//8 - 30))
        self.screen.blit(splash, (0,0))

        pygame.draw.rect(self.screen, [0, 255, 0], button)  # draw button
        self.screen.blit(text_img, text_rect)

        done = False
        while not done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False

                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = event.pos  # gets mouse position

                    if button.collidepoint(mouse_pos):
                        done = True

            pygame.display.update()
            self.clock.tick(60)

        g = Game(*pygame.display.get_surface().get_size())
        g.run()




class Game:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode([width, height])
        self.bat = Bat(self, width // 2, height - 100)
        self.clock = pygame.time.Clock()

        self.moths = []
        self.echoes = []

        self.scoreboard = Scoreboard(self)

        # Blackout
        self.blackout = False
        self.blackout_time = 0

        # Redout
        self.redout = False
        self.redout_time = 0


    def run(self):
        running = True

        while running:
            while len(self.moths) < 4:
                mothConstuctor = moth_factory(self)
                self.moths.append(mothConstuctor(self))

            self.screen.fill((100, 100, 100))
            pygame.draw.circle(self.screen, (200,200,20), (self.width, 20), 300)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                   running = False

            pressed = pygame.key.get_pressed()

            keys = list(pressed[k] for k in [pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT, pygame.K_SPACE])
            actions = [self.bat.up, self.bat.down, self.bat.left, self.bat.right, self.bat.echo]

            for key, action in zip(keys, actions):
                if key:
                    action()


            self.scoreboard.draw()

            for echo in self.echoes:
                echo.draw()
                echo.update()

            self.bat.update()
            self.bat.draw()

            for moth in self.moths:
                moth.update()
                moth.draw()

            if self.blackout:
                cur_time = pygame.time.get_ticks()
                if not self.blackout_time:
                    self.blackout_time = cur_time
                if (cur_time - self.blackout_time) < 3000:
                    self.screen.fill((255,255,255))
                    self.bat.draw()
                else:
                    self.blackout = False
                    self.blackout_time = 0

            if self.redout:
                cur_time = pygame.time.get_ticks()
                if not self.redout_time:
                    self.redout_time = cur_time
                if (cur_time - self.redout_time) < 3000:
                    self.screen.fill((200,0,0))
                else:
                    self.redout = False
                    self.redout_time = 0

            pygame.display.flip()
            self.clock.tick(60)


        pygame.quit()



class Echo:
    def __init__(self, game, origin, delay=0):
        # Pos and size
        self.game = game
        self.x, self.y = origin

        self.radius = 0

        w,h = pygame.display.get_surface().get_size()

        corners = [(0,0), (0,h), (w,0), (w,h)]
        dists = [((self.x - x)**2 + (self.y-y)**2)**0.5 for x,y in corners]
        self.max_radius = max(dists)


        # Expansion speed control
        self.last_time = pygame.time.get_ticks()
        self.dist_per_tick = 1/100

        # Delay control
        self.spawn_time = pygame.time.get_ticks()
        self.delay = delay

        # Size and shape
        self.width = 8
        self.min_angle = math.pi/8
        self.max_angle = 7*math.pi/8


    def touching(self, x, y):
        dy, dx = (self.y-y), (self.x - x)
        dist = (dx**2 + dy**2)**0.5
        if (self.radius < dist) and (dist < (self.radius + self.width)):
            if (self.min_angle < math.atan2(dy, dx) and math.atan2(dy, dx) < self.max_angle ):
                return True
        return False




    def update(self):
        cur_time = pygame.time.get_ticks()
        if (cur_time - self.spawn_time) > self.delay:
            self.radius += (cur_time - self.last_time) * self.dist_per_tick

            if self.radius >= self.max_radius:
                self.game.echoes.remove(self)


    def draw(self):
        arc_rect = (self.x-self.radius, self.y-self.radius, self.radius*2, self.radius*2), #(x-radius,y-radius,radius*2,radius*2)
        pygame.draw.arc(self.game.screen,
                        (255, 0, 0),
                        arc_rect,
                        math.pi/8, 7*math.pi/8, self.width)



class Bat:

    def __init__(self, game, x, y):
        # Pos and size
        self.game = game
        self.x = x
        self.y = y

        self.width = 70
        self.height = 70

        # Movement config
        self.max_x, self.max_y = pygame.display.get_surface().get_size()
        self.move_speed = 5

        # Animation
        self.images = []
        for i in range(9):
            self.images.append(pygame.transform.scale(pygame.image.load(resource_path(f'bat/frame_{i}.bmp')), (self.width, self.height)))
        self.index = 0
        self.image = self.images[self.index]

        # Wing speed control
        self.last_frame_time = pygame.time.get_ticks()
        self.ticks_per_frame = 50

        # Echo spacing and timing
        self.echo_gap = 300
        self.last_echo_time = pygame.time.get_ticks()
        self.ticks_per_echo = 500


        self.startled = False
        self.count = 0
        self.startle_time = 0


    def update(self):
        cur_time = pygame.time.get_ticks()

        if (cur_time - self.last_frame_time > self.ticks_per_frame):
            self.last_frame_time = cur_time

            self.index = (self.index + 1) % len(self.images)
            self.image = self.images[self.index]

        for moth in self.game.moths:
            if moth.touching(self.x + self.width, self.y + self.height):
                if not (self.game.blackout or self.game.redout):
                    moth.die()

    def get_center(self):
        return (self.x + self.width/2, self.y + self.height/2)

    def draw(self):
        self.game.screen.blit(self.image, (self.x, self.y))

    def up(self):
        self.y -= (self.move_speed if self.y > 0 else -1)
    def down(self):
        self.y += (self.move_speed if self.y < self.max_y - self.height else -1)
    def left(self):
        self.x -= (self.move_speed if self.x > 0 else -1)
    def right(self):
        self.x += (self.move_speed if self.x < self.max_x  - self.width else -1)

    def echo(self):
        cur_time = pygame.time.get_ticks()

        if (cur_time - self.last_echo_time > self.ticks_per_echo):
            self.game.echoes.append(Echo(self.game, self.get_center(), delay = 0))
            self.game.echoes.append(Echo(self.game, self.get_center(), delay = self.echo_gap))
            self.game.echoes.append(Echo(self.game, self.get_center(), delay = self.echo_gap*1.5))

            self.last_echo_time = cur_time



class Scoreboard:
    def __init__(self, game):
        self.game = game

        self.scores = {
        "plain" : 0,
        "fast" : 0,
        "startle" : 0,
        "jam" : 0,
        }

        self.probs = {
        "plain" : .25,
        "fast" : .25,
        "startle" : .25,
        "jam" : .25,
        }

        self.images = {}

        for key in self.scores:
            self.images[key] = pygame.image.load(resource_path(f'moths/{key}/frame_01.bmp'))

    def addPoint(self, type):
        self.scores[type] += 1
        for key in self.probs:
            if key == type:
                self.probs[key] -= 0.03
            else:
                self.probs[key] += 0.01

    def draw(self):
        y = 20
        big_font = pygame.font.SysFont(None, 40)
        small_font = pygame.font.SysFont(None, 30)

        text_color = (255,255,255)

        title_img = small_font.render("EATEN  PROB", True, text_color)

        self.game.screen.blit(title_img, (80,5))
        for key in self.images:
            image = pygame.transform.scale(self.images[key], (50, 50))
            self.game.screen.blit(image, (20, y))

            text_img = big_font.render(str(self.scores[key]), True, text_color)
            self.game.screen.blit(text_img, (110, y+10))

            prob_img = big_font.render(f'{self.probs[key]:.2f}', True, text_color)
            self.game.screen.blit(prob_img, (160, y+10))


            y+=50



class Moth:
    def __init__(self, game):
        # Pos and size
        self.game = game

        self.x = random.randint(0, pygame.display.get_surface().get_size()[0] - self.width)
        self.y = random.randint(0, pygame.display.get_surface().get_size()[1]//2)


        # Movement config
        self.max_x, self.max_y = pygame.display.get_surface().get_size()


        self.index = 0
        self.image = self.images[self.index]

        # Wing speed control
        self.last_frame_time = pygame.time.get_ticks()
        self.ticks_per_frame = 50

        # show control
        self.show_time = -4000

        self.direction = random.choice([(1,1), (1,-1), (-1,1), (-1,-1)])


        self.showing = False
        self.dead = False
        self.dead_time = 0

    def power(self):
        return False

    def update(self):
        cur_time = pygame.time.get_ticks()
        if not self.dead:
            if  cur_time - self.last_frame_time > self.ticks_per_frame:
                self.last_frame_time = cur_time

                self.index = (self.index + 1) % len(self.images)
                self.image = self.images[self.index]

            dx, dy = self.direction
            self.x += self.move_speed * dx
            self.y += self.move_speed * dy

            if self.x >= self.max_x or self.x <= 0:
                self.direction = -dx, dy
                if self.x < 0:
                    self.x += 2
                else:
                    self.x -= 2

            if self.y >= self.max_y or self.y <= 0:
                self.direction = dx, -dy
                if self.y < 0:
                    self.y += 2
                else:
                    self.y -= 2


    def touching(self, x,y):
        return self.showing and (self.x < x and x < self.x + self.width) and (self.y < y and y < self.y + self.height)

    def die(self):
        if not self.dead:
            if not self.power():
                self.dead = True
                self.game.scoreboard.addPoint(self.type)

    def draw(self):
        cur_time = pygame.time.get_ticks()
        if self.dead:
            if not self.dead_time:
                self.dead_time = cur_time
            if cur_time - self.dead_time < 500:
                pygame.draw.circle(self.game.screen, (255,255,0), (self.x + self.width//2, self.y + self.height//2), 30)
            else:
                self.game.moths.remove(self)

        else:
            for echo in self.game.echoes:
                if echo.touching(self.x, self.y):
                    self.show_time = cur_time
            if cur_time - self.show_time < 1500:
                self.showing = True
                self.game.screen.blit(self.image, (self.x, self.y))
            else:
                self.showing = False


class PlainMoth(Moth):
    def __init__(self, game):
        self.type = 'plain'
        self.width = 70
        self.height = 70
        # Animation
        self.images = []
        for i in range(9):
            self.images.append(pygame.transform.scale(pygame.image.load(resource_path(f'moths/plain/frame_{i:02d}.bmp')), (self.width, self.height)))

        self.move_speed = 5

        # super
        super(PlainMoth, self).__init__(game)


class FastMoth(Moth):
    def __init__(self, game):
        self.type = 'fast'
        self.width = 70
        self.height = 70
        # Animation
        self.images = []
        for i in range(9):
            self.images.append(pygame.transform.scale(pygame.image.load(resource_path(f'moths/fast/frame_{i:02d}.bmp')), (self.width, self.height)))

        self.move_speed = 10

        # super
        super(FastMoth, self).__init__(game)


class StartleMoth(Moth):
    def __init__(self, game):
        self.type = 'startle'
        self.width = 70
        self.height = 70
        # Animation
        self.images = []
        for i in range(9):
            self.images.append(pygame.transform.scale(pygame.image.load(resource_path(f'moths/startle/frame_{i:02d}.bmp')), (self.width, self.height)))

        self.move_speed = 5

        # super
        super(StartleMoth, self).__init__(game)

    def power(self):
        activate = random.choice([0,0,1])
        if activate:
            self.game.redout = True
            return True
        return False


class JamMoth(Moth):
    def __init__(self, game):
        self.type = 'jam'
        self.width = 70
        self.height = 70
        # Animation
        self.images = []
        for i in range(9):
            self.images.append(pygame.transform.scale(pygame.image.load(resource_path(f'moths/jam/frame_{i:02d}.bmp')), (self.width, self.height)))

        self.move_speed = 5

        # super
        super(JamMoth, self).__init__(game)



    def power(self):
        activate = random.choice([0,0,1])
        if activate:
            self.game.blackout = True
            return True
        return False

def moth_factory(game):
    names = ["plain", "fast", "startle", "jam"]
    stackedProbs = [0]
    for n in names:
        stackedProbs.append(stackedProbs[-1] + game.scoreboard.probs[n])
    stackedProbs = stackedProbs[1:]

    seed = random.random()
    moths = [PlainMoth, FastMoth, StartleMoth, JamMoth]


    for p, m in zip(stackedProbs, moths):
        if seed < p:
            return m


if __name__ == '__main__':
    pygame.font.init()
    g = TitleScreen(1200, 800)
    g.run()
