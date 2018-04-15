import libtcodpy as libtcod
from object import Object
from map import Map
from components import Fighter
from message import game_msgs, message
from constants import *
from dungeon_generator import DungeonGenerator
from envparse import env

game_state = 'playing'
player_action = None

libtcod.console_set_custom_font(
    'arial10x10.png', libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)
libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT,
                          'python/libtcod tutorial', False)
con = libtcod.console_new(SCREEN_WIDTH, SCREEN_HEIGHT)
libtcod.sys_set_fps(LIMIT_FPS)


def player_death(player):
    # the game ended!
    global game_state
    message('You died!', libtcod.dark_red)
    game_state = 'dead'

    # for added effect, transform the player into a corpse!
    player.char = '%'
    player.color = libtcod.dark_red


# create object representing the player
fighter_component = Fighter(
    hp=30, defense=2, power=5, death_function=player_death)
player = Object(0, 0, '@', 'player', libtcod.white,
                blocks=True, fighter=fighter_component)
objects = [player]


def make_map():
    global map

    generator = DungeonGenerator(env.int('SEED', default=None))
    map = Map(MAP_WIDTH, MAP_HEIGHT)
    generator.generate(map, objects)
    (x, y) = map.rooms[0].center()
    player.x = x
    player.y = y
    map.fov_recompute(player)


def handle_keys():
    global player
    if key.vk == libtcod.KEY_ENTER and key.lalt:
        # Alt+Enter: toggle fullscreen
        libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())

    elif key.vk == libtcod.KEY_ESCAPE:
        return 'exit'  # exit game

    if game_state == 'playing':
        # movement keys
        if key.vk == libtcod.KEY_UP:
            player.move_or_attack(0, -1, map, objects)
            map.fov_recompute(player)

        elif key.vk == libtcod.KEY_DOWN:
            player.move_or_attack(0, 1, map, objects)
            map.fov_recompute(player)

        elif key.vk == libtcod.KEY_LEFT:
            player.move_or_attack(-1, 0, map, objects)
            map.fov_recompute(player)

        elif key.vk == libtcod.KEY_RIGHT:
            player.move_or_attack(1, 0, map, objects)
            map.fov_recompute(player)

        else:
            return 'didnt-take-turn'


def render_all():
    for object in objects:
        if object != player:
            object.draw(con, map)
    player.draw(con, map)
    map.draw(con)
    # show the player's stats
    libtcod.console_set_default_foreground(con, libtcod.white)
    libtcod.console_print_ex(con, 1, SCREEN_HEIGHT - 2, libtcod.BKGND_NONE, libtcod.LEFT,
                             'HP: ' + str(player.fighter.hp) + '/' + str(player.fighter.max_hp) + '  ')
    libtcod.console_blit(con, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, 0)

    # prepare to render the GUI panel
    libtcod.console_set_default_background(panel, libtcod.black)
    libtcod.console_clear(panel)

    # print the game messages, one line at a time
    y = 1
    for (line, color) in game_msgs:
        libtcod.console_set_default_foreground(panel, color)
        libtcod.console_print_ex(
            panel, MSG_X, y, libtcod.BKGND_NONE, libtcod.LEFT, line)
        y += 1

    # show the player's stats
    render_bar(1, 1, BAR_WIDTH, 'HP', player.fighter.hp, player.fighter.max_hp,
               libtcod.light_red, libtcod.darker_red)

    # display names of objects under the mouse
    libtcod.console_set_default_foreground(panel, libtcod.light_gray)
    libtcod.console_print_ex(
        panel, 1, 0, libtcod.BKGND_NONE, libtcod.LEFT, get_names_under_mouse())

    # blit the contents of "panel" to the root console
    libtcod.console_blit(panel, 0, 0, SCREEN_WIDTH,
                         PANEL_HEIGHT, 0, 0, PANEL_Y)


panel = libtcod.console_new(SCREEN_WIDTH, PANEL_HEIGHT)

# a warm welcoming message!
message('Welcome stranger! Prepare to perish in the Tombs of the Ancient Kings.', libtcod.red)


make_map()

mouse = libtcod.Mouse()
key = libtcod.Key()


def get_names_under_mouse():
    global mouse

    # return a string with the names of all objects under the mouse
    (x, y) = (mouse.cx, mouse.cy)
    # create a list with the names of all objects at the mouse's coordinates and in FOV
    names = [obj.name for obj in objects
             if obj.x == x and obj.y == y and libtcod.map_is_in_fov(map.fov_map, obj.x, obj.y)]
    names = ', '.join(names)  # join the names, separated by commas
    return names.capitalize()


def render_bar(x, y, total_width, name, value, maximum, bar_color, back_color):
    # render a bar (HP, experience, etc). first calculate the width of the bar
    bar_width = int(float(value) / maximum * total_width)

    # render the background first
    libtcod.console_set_default_background(panel, back_color)
    libtcod.console_rect(panel, x, y, total_width, 1,
                         False, libtcod.BKGND_SCREEN)

    # now render the bar on top
    libtcod.console_set_default_background(panel, bar_color)
    if bar_width > 0:
        libtcod.console_rect(panel, x, y, bar_width, 1,
                             False, libtcod.BKGND_SCREEN)
    # finally, some centered text with the values
    libtcod.console_set_default_foreground(panel, libtcod.white)
    libtcod.console_print_ex(panel, x + total_width / 2, y, libtcod.BKGND_NONE, libtcod.CENTER,
                             name + ': ' + str(value) + '/' + str(maximum))


while not libtcod.console_is_window_closed():
    libtcod.console_set_default_foreground(con, libtcod.white)
    libtcod.sys_check_for_event(
        libtcod.EVENT_KEY_PRESS | libtcod.EVENT_MOUSE, key, mouse)
    render_all()
    libtcod.console_flush()

    # handle keys and exit game if needed
    for object in objects:
        object.clear(con)
    player_action = handle_keys()
    # let monsters take their turn
    if game_state == 'playing' and player_action != 'didnt-take-turn':
        for object in objects:
            if object != player and object.ai != None:
                object.ai.take_turn(map, player, objects)
    if player_action == 'exit':
        break
