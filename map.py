import libtcodpy as libtcod
from rect import Rect
from object import Object
from components import Fighter, BasicMonster
from message import message

color_dark_wall = libtcod.Color(0, 0, 100)
color_dark_ground = libtcod.Color(50, 50, 150)
color_dark_wall = libtcod.Color(0, 0, 100)
color_medium_wall = libtcod.Color(65, 55, 75)
color_light_wall = libtcod.Color(130, 110, 50)
color_dark_ground = libtcod.Color(50, 50, 150)
color_medium_ground = libtcod.Color(125, 115, 100)
color_light_ground = libtcod.Color(200, 180, 50)

TORCH_RADIUS = 10
FOV_ALGO = 0  # default FOV algorithm
FOV_LIGHT_WALLS = True


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
        self.torch_left = 0
        self.tiles = [[Tile(True)
                       for _ in range(self.h)]
                      for _ in range(self.w)]

    def create_room(self, room):
        # go through the tiles in the rectangle and make them passable
        for x in range(room.x1 + 1, room.x2):
            for y in range(room.y1 + 1, room.y2):
                self.tiles[x][y].blocked = False
                self.tiles[x][y].block_sight = False
        self.tiles[room.x1 + 1][room.y1 + 1].blocked = True
        self.tiles[room.x1 + 1][room.y1 + 1].block_sight = True
        self.tiles[room.x1 + 1][room.y2 - 1].blocked = True
        self.tiles[room.x1 + 1][room.y2 - 1].block_sight = True
        self.tiles[room.x2 - 1][room.y1 + 1].blocked = True
        self.tiles[room.x2 - 1][room.y1 + 1].block_sight = True
        self.tiles[room.x2 - 1][room.y2 - 1].blocked = True
        self.tiles[room.x2 - 1][room.y2 - 1].block_sight = True

    def create_h_tunnel(self, x1, x2, y):
        for x in range(min(x1, x2), max(x1, x2) + 1):
            self.tiles[x][y].blocked = False
            self.tiles[x][y].block_sight = False

    def create_v_tunnel(self, y1, y2, x):
        # vertical tunnel
        for y in range(min(y1, y2), max(y1, y2) + 1):
            self.tiles[x][y].blocked = False
            self.tiles[x][y].block_sight = False

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
                        color = color_light_wall
                        if self.torch_left == 0:
                            color = color_dark_wall
                        elif self.torch_left < 50:
                            color = color_medium_wall
                        libtcod.console_set_char_background(
                            con, x, y, color, libtcod.BKGND_SET)
                    else:
                        color = color_light_ground
                        if self.torch_left == 0:
                            color = color_dark_ground
                        elif self.torch_left < 50:
                            color = color_medium_ground
                        libtcod.console_set_char_background(
                            con, x, y, color, libtcod.BKGND_SET)
                    # since it's visible, explore it
                    self.tiles[x][y].explored = True
