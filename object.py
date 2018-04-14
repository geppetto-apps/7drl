import libtcodpy as libtcod
import math


class Object:
    # this is a generic object: the player, a monster, an item, the stairs...
    # it's always represented by a character on screen.
    def __init__(self, x, y, char, name, color, blocks=False, fighter=None, ai=None):
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.name = name
        self.fighter = fighter
        self.blocks = blocks
        if self.fighter:  # let the fighter component know who owns it
            self.fighter.owner = self

        self.ai = ai
        if self.ai:  # let the AI component know who owns it
            self.ai.owner = self

    def move_or_attack(self, dx, dy, map, objects):
        # the coordinates the player is moving to/attacking
        x = self.x + dx
        y = self.y + dy

        # try to find an attackable object there
        target = None
        for object in objects:
            if object.x == x and object.y == y and object.fighter is not None:
                target = object
                break

        # attack if target found, move otherwise
        if target is not None:
            self.fighter.attack(target)
        else:
            self.move(x, y, map, objects)

    def move(self, x, y, map, objects):
        for object in objects:
            if object.x == x and object.y == y and object.blocks:
                return

        if map.tile_at(x, y).blocked:
            return

        for object in objects:
            if object.blocks and object.x == x and object.y == y:
                return

        # move by the given amount
        self.x = x
        self.y = y

    def move_towards(self, target_x, target_y, map, objects):
        # vector from this object to the target, and distance
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.sqrt(dx ** 2 + dy ** 2)

        # normalize it to length 1 (preserving direction), then round it and
        # convert to integer so the movement is restricted to the map grid
        dx = int(round(dx / distance))
        dy = int(round(dy / distance))
        self.move(self.x + dx, self.y + dy, map, objects)

    def distance_to(self, other):
        # return the distance to another object
        dx = other.x - self.x
        dy = other.y - self.y
        return math.sqrt(dx ** 2 + dy ** 2)

    def draw(self, con, map):
        if libtcod.map_is_in_fov(map.fov_map, self.x, self.y):
            # set the color and then draw the character that represents this object at its position
            libtcod.console_set_default_foreground(con, self.color)
            libtcod.console_put_char(
                con, self.x, self.y, self.char, libtcod.BKGND_NONE)

    def clear(self, con):
        # erase the character that represents this object
        libtcod.console_put_char(con, self.x, self.y, ' ', libtcod.BKGND_NONE)
