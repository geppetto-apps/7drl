import libtcodpy as libtcod
from object import Object
from rect import Rect
from map import Map

SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50
LIMIT_FPS = 20

MAP_WIDTH = 80
MAP_HEIGHT = 45


libtcod.console_set_custom_font(
    'arial10x10.png', libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)
libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT,
                          'python/libtcod tutorial', False)
con = libtcod.console_new(SCREEN_WIDTH, SCREEN_HEIGHT)
libtcod.sys_set_fps(LIMIT_FPS)

player = Object(25, 23, '@', libtcod.white)
npc = Object(SCREEN_WIDTH/2 - 5, SCREEN_HEIGHT/2, '@', libtcod.yellow)
objects = [npc, player]

ROOM_MAX_SIZE = 10
ROOM_MIN_SIZE = 6
MAX_ROOMS = 30

def make_map():
    global map
    rooms = []
    num_rooms = 0
    map = Map(MAP_WIDTH, MAP_HEIGHT)

    for r in range(MAX_ROOMS):
        #random width and height
        w = libtcod.random_get_int(0, ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        h = libtcod.random_get_int(0, ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        #random position without going out of the boundaries of the map
        x = libtcod.random_get_int(0, 0, MAP_WIDTH - w - 1)
        y = libtcod.random_get_int(0, 0, MAP_HEIGHT - h - 1)

        #"Rect" class makes rectangles easier to work with
        new_room = Rect(x, y, w, h)

        #run through the other rooms and see if they intersect with this one
        failed = False
        for other_room in rooms:
            if new_room.intersect(other_room):
                failed = True
                break

        if not failed:
            #this means there are no intersections, so this room is valid

            #"paint" it to the map's tiles
            map.create_room(new_room)

            #center coordinates of new room, will be useful later
            (new_x, new_y) = new_room.center()

            if num_rooms == 0:
                #this is the first room, where the player starts at
                player.x = new_x
                player.y = new_y
            else:
                #all rooms after the first:
                #connect it to the previous room with a tunnel

                #center coordinates of previous room
                (prev_x, prev_y) = rooms[num_rooms-1].center()

                #draw a coin (random number that is either 0 or 1)
                if libtcod.random_get_int(0, 0, 1) == 1:
                    #first move horizontally, then vertically
                    map.create_h_tunnel(prev_x, new_x, prev_y)
                    map.create_v_tunnel(prev_y, new_y, new_x)
                else:
                    #first move vertically, then horizontally
                    map.create_v_tunnel(prev_y, new_y, prev_x)
                    map.create_h_tunnel(prev_x, new_x, new_y)

            #finally, append the new room to the list
            rooms.append(new_room)
            num_rooms += 1

    # # fill map with "unblocked" tiles
    # map = Map(MAP_WIDTH, MAP_HEIGHT)
    # room1 = Rect(20, 15, 10, 15)
    # room2 = Rect(50, 15, 10, 15)
    # map.create_room(room1)
    # map.create_room(room2)
    # map.create_h_tunnel(25, 55, 23)


def handle_keys():
    global player
    key = libtcod.console_wait_for_keypress(True)
    if key.vk == libtcod.KEY_ENTER and key.lalt:
        # Alt+Enter: toggle fullscreen
        libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())

    elif key.vk == libtcod.KEY_ESCAPE:
        return True  # exit game

    # movement keys
    if libtcod.console_is_key_pressed(libtcod.KEY_UP):
        player.move(0, -1, map)

    elif libtcod.console_is_key_pressed(libtcod.KEY_DOWN):
        player.move(0, 1, map)

    elif libtcod.console_is_key_pressed(libtcod.KEY_LEFT):
        player.move(-1, 0, map)

    elif libtcod.console_is_key_pressed(libtcod.KEY_RIGHT):
        player.move(1, 0, map)


def render_all():
    for object in objects:
        object.draw(con)
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
    exit = handle_keys()
    if exit:
        break
