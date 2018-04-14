import libtcodpy as libtcod
from object import Object
from map import Map

SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50
LIMIT_FPS = 20

MAP_WIDTH = 80
MAP_HEIGHT = 45

game_state = 'playing'
player_action = None

libtcod.console_set_custom_font(
    'arial10x10.png', libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)
libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT,
                          'python/libtcod tutorial', False)
con = libtcod.console_new(SCREEN_WIDTH, SCREEN_HEIGHT)
libtcod.sys_set_fps(LIMIT_FPS)

player = Object(25, 23, '@', libtcod.white)
npc = Object(SCREEN_WIDTH/2 - 5, SCREEN_HEIGHT/2, '@', libtcod.yellow)
objects = [npc, player]


def make_map():
    global map

    map = Map(MAP_WIDTH, MAP_HEIGHT)
    map.generate(objects)
    (x, y) = map.rooms[0].center()
    player.x = x
    player.y = y
    map.fov_recompute(player)
    (x, y) = map.rooms[1].center()
    npc.x = x
    npc.y = y


def handle_keys():
    global player
    key = libtcod.console_wait_for_keypress(True)
    if key.vk == libtcod.KEY_ENTER and key.lalt:
        # Alt+Enter: toggle fullscreen
        libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())

    elif key.vk == libtcod.KEY_ESCAPE:
        return 'exit'  # exit game

    if game_state == 'playing':
        # movement keys
        if libtcod.console_is_key_pressed(libtcod.KEY_UP):
            player.move(0, -1, map)
            map.fov_recompute(player)

        elif libtcod.console_is_key_pressed(libtcod.KEY_DOWN):
            player.move(0, 1, map)
            map.fov_recompute(player)

        elif libtcod.console_is_key_pressed(libtcod.KEY_LEFT):
            player.move(-1, 0, map)
            map.fov_recompute(player)

        elif libtcod.console_is_key_pressed(libtcod.KEY_RIGHT):
            player.move(1, 0, map)
            map.fov_recompute(player)

        else:
            return 'didnt-take-turn'


def render_all():
    for object in objects:
        object.draw(con, map)
    map.draw(con)
    libtcod.console_blit(con, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, 0)


make_map()
while not libtcod.console_is_window_closed():
    libtcod.console_set_default_foreground(con, libtcod.white)
    render_all()
    libtcod.console_flush()

    # handle keys and exit game if needed
    for object in objects:
        object.clear(con)
    player_action = handle_keys()
    #let monsters take their turn
    if game_state == 'playing' and player_action != 'didnt-take-turn':
        for object in objects:
            if object != player:
                print 'The ' + object.char + ' growls!'
    if player_action == 'exit':
        break
