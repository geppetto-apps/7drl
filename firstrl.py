import libtcodpy as libtcod
from object import Object
from map import Map
from components import Fighter

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


def player_death(player):
    # the game ended!
    global game_state
    print 'You died!'
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

    map = Map(MAP_WIDTH, MAP_HEIGHT)
    map.generate(objects)
    (x, y) = map.rooms[0].center()
    player.x = x
    player.y = y
    map.fov_recompute(player)


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
            player.move_or_attack(0, -1, map, objects)
            map.fov_recompute(player)

        elif libtcod.console_is_key_pressed(libtcod.KEY_DOWN):
            player.move_or_attack(0, 1, map, objects)
            map.fov_recompute(player)

        elif libtcod.console_is_key_pressed(libtcod.KEY_LEFT):
            player.move_or_attack(-1, 0, map, objects)
            map.fov_recompute(player)

        elif libtcod.console_is_key_pressed(libtcod.KEY_RIGHT):
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


make_map()
while not libtcod.console_is_window_closed():
    libtcod.console_set_default_foreground(con, libtcod.white)
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
