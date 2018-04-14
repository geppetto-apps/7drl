import libtcodpy as libtcod
from rect import Rect
from object import Object

color_dark_wall = libtcod.Color(0, 0, 100)
color_dark_ground = libtcod.Color(50, 50, 150)
color_dark_wall = libtcod.Color(0, 0, 100)
color_light_wall = libtcod.Color(130, 110, 50)
color_dark_ground = libtcod.Color(50, 50, 150)
color_light_ground = libtcod.Color(200, 180, 50)


ROOM_MAX_SIZE = 10
ROOM_MIN_SIZE = 6
MAX_ROOMS = 30

FOV_ALGO = 0  # default FOV algorithm
FOV_LIGHT_WALLS = True
TORCH_RADIUS = 10

MAX_ROOM_MONSTERS = 10


class Tile:
    # a tile of the map and its properties
    def __init__(self, blocked, block_sight=None):
        self.blocked = blocked

        # by default, if a tile is blocked, it also blocks sight
        if block_sight is None:
            block_sight = blocked
        self.block_sight = block_sight
        self.explored = False


class Map:
    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.rooms = []
        self.num_rooms = 0
        self.fov_map = libtcod.map_new(self.w, self.h)
        self.tiles = [[Tile(True)
                       for y in range(self.h)]
                      for x in range(self.w)]

    def create_room(self, room):
        # go through the tiles in the rectangle and make them passable
        for x in range(room.x1 + 1, room.x2):
            for y in range(room.y1 + 1, room.y2):
                self.tiles[x][y].blocked = False
                self.tiles[x][y].block_sight = False

    def create_h_tunnel(self, x1, x2, y):
        for x in range(min(x1, x2), max(x1, x2) + 1):
            self.tiles[x][y].blocked = False
            self.tiles[x][y].block_sight = False

    def create_v_tunnel(self, y1, y2, x):
        # vertical tunnel
        for y in range(min(y1, y2), max(y1, y2) + 1):
            self.tiles[x][y].blocked = False
            self.tiles[x][y].block_sight = False

    def generate(self, objects):
        for r in range(MAX_ROOMS):
            # random width and height
            w = libtcod.random_get_int(0, ROOM_MIN_SIZE, ROOM_MAX_SIZE)
            h = libtcod.random_get_int(0, ROOM_MIN_SIZE, ROOM_MAX_SIZE)
            # random position without going out of the boundaries of the map
            x = libtcod.random_get_int(0, 0, self.w - w - 1)
            y = libtcod.random_get_int(0, 0, self.h - h - 1)

            # "Rect" class makes rectangles easier to work with
            new_room = Rect(x, y, w, h)

            # run through the other rooms and see if they intersect with this one
            failed = False
            for other_room in self.rooms:
                if new_room.intersect(other_room):
                    failed = True
                    break

            if not failed:
                # this means there are no intersections, so this room is valid

                # "paint" it to the map's tiles
                self.create_room(new_room)

                # center coordinates of new room, will be useful later
                (new_x, new_y) = new_room.center()

                if self.num_rooms != 0:
                    # all rooms after the first:
                    # connect it to the previous room with a tunnel

                    # center coordinates of previous room
                    (prev_x, prev_y) = self.rooms[self.num_rooms-1].center()

                    # draw a coin (random number that is either 0 or 1)
                    if libtcod.random_get_int(0, 0, 1) == 1:
                        # first move horizontally, then vertically
                        self.create_h_tunnel(prev_x, new_x, prev_y)
                        self.create_v_tunnel(prev_y, new_y, new_x)
                    else:
                        # first move vertically, then horizontally
                        self.create_v_tunnel(prev_y, new_y, prev_x)
                        self.create_h_tunnel(prev_x, new_x, new_y)

                # finally, append the new room to the list
                self.rooms.append(new_room)
                self.num_rooms += 1
                # add some contents to this room, such as monsters
                self.place_objects(new_room, objects)
        self.set_fov()

    def place_objects(self, room, objects):
        # choose random number of monsters
        num_monsters = libtcod.random_get_int(0, 0, MAX_ROOM_MONSTERS)

        for i in range(num_monsters):
            # choose random spot for this monster
            x = libtcod.random_get_int(0, room.x1 + 1, room.x2 - 1)
            y = libtcod.random_get_int(0, room.y1 + 1, room.y2 - 1)

            # 80% chance of getting an orc
            if libtcod.random_get_int(0, 0, 100) < 80:
                # create an orc
                monster = Object(x, y, 'o', 'Orc', libtcod.desaturated_green)
            else:
                # create a troll
                monster = Object(x, y, 'T', 'Troll', libtcod.darker_green)

            objects.append(monster)

    def set_fov(self):
        for y in range(self.h):
            for x in range(self.w):
                libtcod.map_set_properties(
                    self.fov_map, x, y, not self.tiles[x][y].block_sight, not self.tiles[x][y].blocked)

    def fov_recompute(self, player):
        libtcod.map_compute_fov(
            self.fov_map, player.x, player.y, TORCH_RADIUS, FOV_LIGHT_WALLS, FOV_ALGO)

    def tile_at(self, x, y):
        return self.tiles[x][y]

    def draw(self, con):
        for y in range(self.h):
            for x in range(self.w):
                visible = libtcod.map_is_in_fov(self.fov_map, x, y)
                wall = self.tiles[x][y].block_sight
                if not visible:
                    # if it's not visible right now, the player can only see it if it's explored
                    if self.tiles[x][y].explored:
                        # it's out of the player's FOV
                        if wall:
                            libtcod.console_set_char_background(
                                con, x, y, color_dark_wall, libtcod.BKGND_SET)
                        else:
                            libtcod.console_set_char_background(
                                con, x, y, color_dark_ground, libtcod.BKGND_SET)
                else:
                    # it's visible
                    if wall:
                        libtcod.console_set_char_background(
                            con, x, y, color_light_wall, libtcod.BKGND_SET)
                    else:
                        libtcod.console_set_char_background(
                            con, x, y, color_light_ground, libtcod.BKGND_SET)
                    # since it's visible, explore it
                    self.tiles[x][y].explored = True
