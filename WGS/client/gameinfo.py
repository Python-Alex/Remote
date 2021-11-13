import iapi
import types
import pygame
import dispatcher

pygame.init()

listener = object # unset for now

display = types.new_class('display')
display.source_object = pygame.display.set_mode((800, 600))

clock = pygame.time.Clock()

fonts = [pygame.font.Font(pygame.font.get_default_font(), size) for size in range(0, 64, 2)]

class LoginButton(pygame.Rect):

    def __init__(self, x, y, w, h):
        pygame.Rect.__init__(self, x, y, w, h)
        self.left = x
        self.top = y
        self.width = w
        self.height = h

        self.sizeof_login = fonts[8].size('Login')
        

class ConnectButton(pygame.Rect):

    def __init__(self, x, y, w, h):
        pygame.Rect.__init__(self, x, y, w, h)
        self.left = x
        self.top = y
        self.width = w
        self.height = h

        self.sizeof_connect = fonts[8].size('Connect')

    def draw(self):
        pygame.draw.rect(display.source_object, (255,255,255), self, width=1)
        r_object = fonts[8].render('Connect', True, (255,255,255))
        display.source_object.blit(r_object, (self.centerx - (self.sizeof_connect[0] // 2), self.centery - (self.sizeof_connect[1] // 2)))

    def check_click(self, pos: tuple):
        if(self.collidepoint(pos)):
            iapi.WrappedFunctions.register_connection(listener.Client)
