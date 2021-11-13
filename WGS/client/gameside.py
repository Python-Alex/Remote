import sys
import time
import pygame
import iapi
import listener
import gameinfo

gameinfo.listener = listener

connect = gameinfo.ConnectButton(10, 10, 100, 30)

while(True):

    pygame.display.set_caption('FPS: %d' % (gameinfo.clock.get_fps()))

    for event in pygame.event.get():
        if(event.type == pygame.QUIT):
            pygame.quit(); break


    gameinfo.clock.tick(300)
    pygame.display.update()
