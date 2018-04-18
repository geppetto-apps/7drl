import libtcodpy as libtcod
from object import Object
from map import Map
from components import Fighter, Item
from message import game_msgs, message
from constants import *
from dungeon_generator import DungeonGenerator
from envparse import env
import tiles
import dill

libtcod.console_set_custom_font(
    'sprites.png', libtcod.FONT_LAYOUT_ASCII_INROW)
libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT,
                          'python/libtcod tutorial', False)
con = libtcod.console_new(SCREEN_WIDTH, SCREEN_HEIGHT)
libtcod.sys_set_fps(LIMIT_FPS)

panel = libtcod.console_new(SCREEN_WIDTH, PANEL_HEIGHT)


def new_game():
    global player, inventory, game_msgs, game_state

    # create object representing the player
    fighter_component = Fighter(
        hp=30, defense=2, power=5, death_function=player_death)
    player = Object(0, 0, tiles.player_tile, 'player', libtcod.white,
                    blocks=True, fighter=fighter_component)

    # generate map (at this point it's not drawn to the screen)
    make_map()

    game_state = 'playing'

    # a warm welcoming message!
    message('Welcome stranger! Prepare to perish in the Tombs of the Ancient Kings.', libtcod.red)


def player_death(player):
    # the game ended!
    global game_state
    message('You died!', libtcod.dark_red)
    game_state = 'dead'

    # for added effect, transform the player into a corpse!
    player.char = tiles.tomb_tile


def make_map():
    global map

    # the list of objects with just the player

    generator = DungeonGenerator(env.int('SEED', default=None))
    map = Map(MAP_WIDTH, MAP_HEIGHT)
    map.objects.append(player)
    generator.generate(map, player)
    map.fov_recompute(player)
    # unexplored areas start black (which is the default background color)
    libtcod.console_clear(con)


def handle_keys():
    global player
    if key.vk == libtcod.KEY_ENTER and key.lalt:
        # Alt+Enter: toggle fullscreen
        libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())

    elif key.vk == libtcod.KEY_ESCAPE:
        return 'exit'  # exit game

    if game_state == 'playing':
        key_char = chr(key.c)
        # movement keys
        if key.vk == libtcod.KEY_UP or key_char == 'w':
            player.move_or_attack(0, -1, map)
            map.fov_recompute(player)

        elif key.vk == libtcod.KEY_DOWN or key_char == 's':
            player.move_or_attack(0, 1, map)
            map.fov_recompute(player)

        elif key.vk == libtcod.KEY_LEFT or key_char == 'a':
            player.move_or_attack(-1, 0, map)
            map.fov_recompute(player)

        elif key.vk == libtcod.KEY_RIGHT or key_char == 'd':
            player.move_or_attack(1, 0, map)
            map.fov_recompute(player)

        else:
            # test for other keys
            if key_char == 'g':
                # pick up an item
                for object in map.objects:  # look for an item in the player's tile
                    if object.x == player.x and object.y == player.y and object.item:
                        object.item.pick_up(map, player)
                        break

            # test for other keys
            if key_char == '<':
                # pick up an item
                for object in map.objects:  # look for an item in the player's tile
                    if object.x == player.x and object.y == player.y and object.ladder:
                        object.ladder.ascend(map)
                        break

            if key_char == 'i':
                # show the inventory; if an item is selected, use it
                chosen_item = inventory_menu(
                    'Press the key next to an item to use it, or any other to cancel.\n')
                if chosen_item is not None:
                    chosen_item.use(player)

            if key_char == 'd':
                # show the inventory; if an item is selected, drop it
                chosen_item = inventory_menu(
                    'Press the key next to an item to drop it, or any other to cancel.\n')
                if chosen_item is not None:
                    chosen_item.drop(player, map)

            return 'didnt-take-turn'


def menu(header, options, width):
    if len(options) > 26:
        raise ValueError('Cannot have a menu with more than 26 options.')
    # calculate total height for the header (after auto-wrap) and one line per option
    header_height = libtcod.console_get_height_rect(
        con, 0, 0, width, SCREEN_HEIGHT, header)
    if header == '':
        header_height = 0
    height = len(options) + header_height
    # create an off-screen console that represents the menu's window
    window = libtcod.console_new(width, height)

    # print the header, with auto-wrap
    libtcod.console_set_default_foreground(window, libtcod.white)
    libtcod.console_print_rect_ex(
        window, 0, 0, width, height, libtcod.BKGND_NONE, libtcod.LEFT, header)
    # print all the options
    y = header_height
    letter_index = ord('a')
    for option_text in options:
        text = '(' + chr(letter_index) + ') ' + option_text
        libtcod.console_print_ex(
            window, 0, y, libtcod.BKGND_NONE, libtcod.LEFT, text)
        y += 1
        letter_index += 1
    # blit the contents of "window" to the root console
    x = SCREEN_WIDTH/2 - width/2
    y = SCREEN_HEIGHT/2 - height/2
    libtcod.console_blit(window, 0, 0, width, height, 0, x, y, 1.0, 0.7)
    # present the root console to the player and wait for a key-press
    libtcod.console_flush()
    key = libtcod.console_wait_for_keypress(True)
    # (special case) Alt+Enter: toggle fullscreen
    if key.vk == libtcod.KEY_ENTER and key.lalt:
        libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())
    # convert the ASCII code to an index; if it corresponds to an option, return it
    index = key.c - ord('a')
    if index >= 0 and index < len(options):
        return index
    return None


def inventory_menu(header):
    inventory = player.inventory
    # show a menu with each item of the inventory as an option
    if len(inventory) == 0:
        options = ['Inventory is empty.']
    else:
        options = [item.name for item in inventory]

    index = menu(header, options, INVENTORY_WIDTH)
    # if an item was chosen, return it
    if index is None or len(inventory) == 0:
        return None
    return inventory[index].item


def render_all():
    map.draw(con)
    for object in map.objects:
        if object != player:
            object.draw(con, map)
    player.draw(con, map)
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
    curr_xp = player.fighter.next_xp(player.fighter.level() - 1)
    next_xp = player.fighter.next_xp(player.fighter.level())
    render_bar(1, 2, BAR_WIDTH, 'XP', player.fighter.xp, next_xp,
               libtcod.light_blue, libtcod.darker_blue, minimum=curr_xp)
    libtcod.console_print_ex(
        panel, 1, 3, libtcod.BKGND_NONE, libtcod.LEFT, player.display_name())

    # display names of objects under the mouse
    libtcod.console_set_default_foreground(panel, libtcod.light_gray)
    libtcod.console_print_ex(
        panel, 1, 0, libtcod.BKGND_NONE, libtcod.LEFT, get_names_under_mouse())

    # blit the contents of "panel" to the root console
    libtcod.console_blit(panel, 0, 0, SCREEN_WIDTH,
                         PANEL_HEIGHT, 0, 0, PANEL_Y)


def get_names_under_mouse():
    global mouse

    # return a string with the names of all objects under the mouse
    (x, y) = (mouse.cx, mouse.cy)
    # create a list with the names of all objects at the mouse's coordinates and in FOV
    names = [obj.display_name() for obj in map.objects
             if obj.x == x and obj.y == y and libtcod.map_is_in_fov(map.fov_map, obj.x, obj.y)]
    names = ', '.join(names)  # join the names, separated by commas
    return names.capitalize()


def render_bar(x, y, total_width, name, value, maximum, bar_color, back_color, minimum=0):
    # render a bar (HP, experience, etc). first calculate the width of the bar
    min = value - minimum
    max = maximum - minimum
    bar_width = int(float(min) / max * total_width)

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

# Give player some torches


def light_torch():
    map.torch_left = 100


def give_torch():
    item_component = Item(use_function=light_torch)
    item = Object(0, 0, 'i', 'A torch',
                  libtcod.red, item=item_component)
    player.inventory.append(item)


def play_game():
    global key, mouse

    player_action = None

    mouse = libtcod.Mouse()
    key = libtcod.Key()
    while not libtcod.console_is_window_closed():
        libtcod.console_set_default_foreground(con, libtcod.white)
        libtcod.sys_check_for_event(
            libtcod.EVENT_KEY_PRESS | libtcod.EVENT_MOUSE, key, mouse)
        render_all()
        libtcod.console_flush()

        # handle keys and exit game if needed
        for object in map.objects:
            object.clear(con)
        player_action = handle_keys()
        # let monsters take their turn
        if game_state == 'playing' and player_action != 'didnt-take-turn':
            for object in map.objects:
                if object != player and object.ai != None:
                    object.ai.take_turn(map, player)
            # deplete torch
            if map.torch_left > 0:
                map.torch_left -= 1
                if map.torch_left == 0:
                    message('Your torch burned out', libtcod.orange)
        if player_action == 'exit':
            # save_game()
            break


def save_game():
    global map
    file = open('savegame', 'wb')
    data = {}
    data['map'] = map
    data['player_index'] = map.objects.index(player)
    data['game_msgs'] = game_msgs
    data['game_state'] = game_state
    print data
    dill.dump(data, file)
    file.close()


def load_game():
    global map, player, game_msgs, game_state
    file = open('savegame', 'rb')
    data = dill.load(file)
    file.close()
    print data
    map = data['map']
    player = map.objects[data['player_index']]
    game_msgs = data['game_msgs']
    game_state = data['game_state']

    # Reset FOV after loading game
    map.fov_map = libtcod.map_new(map.w, map.h)
    map.set_fov()
    map.fov_recompute(player)


def main_menu():
    img = libtcod.image_load('menu_background1.png')

    while not libtcod.console_is_window_closed():  # show the game's title, and some credits!
        libtcod.console_clear(0)

        # show the background image, at twice the regular console resolution
        libtcod.image_blit_rect(
            img, 0, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, libtcod.BKGND_SET)

        libtcod.console_set_default_foreground(0, libtcod.dark_orange)
        libtcod.console_print_ex(0, SCREEN_WIDTH/2, SCREEN_HEIGHT/2-4, libtcod.BKGND_NONE, libtcod.CENTER,
                                 'Tower of the Brave')
        libtcod.console_set_default_foreground(0, libtcod.light_amber)
        libtcod.console_print_ex(0, SCREEN_WIDTH/2, SCREEN_HEIGHT-2, libtcod.BKGND_NONE, libtcod.CENTER,
                                 'By Quadragames')

        # show options and wait for the player's choice
        choice = menu(
            '', ['Play a new game', 'Continue last game', 'Quit'], 24)

        if choice == 0:  # new game
            new_game()
            play_game()
        elif choice == 1:  # load game
            load_game()
            play_game()
        elif choice == 2:  # quit
            break


main_menu()
