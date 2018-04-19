import libtcodpy as libtcod
import math


class Object:
    # this is a generic object: the player, a monster, an item, the stairs...
    # it's always represented by a character on screen.
    def __init__(self, x, y, char, name, color, blocks=False, fighter=None, ai=None, item=None, ladder=None):
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.name = name
        self.fighter = fighter
        self.blocks = blocks
        self.inventory = []
        if self.fighter:  # let the fighter component know who owns it
            self.fighter.owner = self

        self.ai = ai
        if self.ai:  # let the AI component know who owns it
            self.ai.owner = self
        self.item = item
        if self.item:  # let the Item component know who owns it
            self.item.owner = self
        self.ladder = ladder
        if self.ladder:# let the Ladder component know who owns it
            self.ladder.owner = self

    def move_or_attack(self, dx, dy, map):
        # the coordinates the player is moving to/attacking
        x = self.x + dx
        y = self.y + dy

        # try to find an attackable object there
        target = None
        for object in map.objects:
            if object.x == x and object.y == y and object.fighter is not None:
                target = object
                break

        # attack if target found, move otherwise
        if target is not None:
            self.fighter.attack(target)
        else:
            self.move(x, y, map)

    def move_by(self, dx, dy, map):
        self.move(self.x + dx, self.y + dy, map)

    def move(self, x, y, map):
        for object in map.objects:
            if object.x == x and object.y == y and object.blocks:
                return

        if map.tile_at(x, y).blocked:
            return

        for object in map.objects:
            if object.blocks and object.x == x and object.y == y:
                return

        # move by the given amount
        self.x = x
        self.y = y

    def move_towards(self, target_x, target_y, map):
        # vector from this object to the target, and distance
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.sqrt(dx ** 2 + dy ** 2)

        # normalize it to length 1 (preserving direction), then round it and
        # convert to integer so the movement is restricted to the map grid
        dx = int(round(dx / distance))
        dy = int(round(dy / distance))
        self.move(self.x + dx, self.y + dy, map)

    def move_astar(self, target, map):
        my_path = self.astar_path(map, target.x, target.y, target)

        #Check if the path exists, and in this case, also the path is shorter than 25 tiles
        #The path size matters if you want the monster to use alternative longer paths (for example through other rooms) if for example the player is in a corridor
        #It makes sense to keep path size relatively low to keep the monsters from running around the map if there's an alternative path really far away
        if not libtcod.path_is_empty(my_path) and libtcod.path_size(my_path) < 25:
            #Find the next coordinates in the computed full path
            x, y = libtcod.path_walk(my_path, True)
            if x or y:
                #Set self's coordinates to the next path tile
                self.x = x
                self.y = y
        else:
            #Keep the old move function as a backup so that if there are no paths (for example another monster blocks a corridor)
            #it will still try to move towards the player (closer to the corridor opening)
            self.move_towards(target.x, target.y, map)

        #Delete the path to free memory
        libtcod.path_delete(my_path)

    def astar_path(self, map, x, y, target=None):
        #Create a FOV map that has the dimensions of the map
        fov = libtcod.map_new(map.w, map.h)

        #Scan the current map each turn and set all the walls as unwalkable
        for y1 in range(map.h):
            for x1 in range(map.w):
                libtcod.map_set_properties(fov, x1, y1, not map.tiles[x1][y1].block_sight, not map.tiles[x1][y1].blocked)

        #Scan all the objects to see if there are objects that must be navigated around
        #Check also that the object isn't self or the target (so that the start and the end points are free)
        #The AI class handles the situation if self is next to the target so it will not use this A* function anyway
        for obj in map.objects:
            if obj.blocks and obj != self and obj != target:
                #Set the tile as a wall so it must be navigated around
                libtcod.map_set_properties(fov, obj.x, obj.y, True, False)

        #Allocate a A* path
        #The 1.41 is the normal diagonal cost of moving, it can be set as 0.0 if diagonal moves are prohibited
        return libtcod.path_new_using_map(fov, 1.41)

    def distance_to(self, x, y=None):
        if y == None:
            other = x
            x = other.x
            y = other.y
        # return the distance to another object
        dx = x - self.x
        dy = y - self.y
        return math.sqrt(dx ** 2 + dy ** 2)

    def astar_distance_to(self, map, x, y=None):
        if y == None:
            other = x
            x = other.x
            y = other.y
        # return the distance to another object
        my_path = self.astar_path(map, x, y)
        #Compute the path between self's coordinates and the target's coordinates
        libtcod.path_compute(my_path, self.x, self.y, x, y)
        return libtcod.path_size(my_path)

    def display_name(self):
        if self.fighter == None:
            return self.name
        return self.name + " (lvl " + str(self.fighter.level()) + ")"

    def draw(self, con, map):
        if libtcod.map_is_in_fov(map.fov_map, self.x, self.y):
            # set the color and then draw the character that represents this object at its position
            libtcod.console_set_default_foreground(con, self.color)
            libtcod.console_put_char(
                con, self.x, self.y, self.char, libtcod.BKGND_NONE)

    def clear(self, con):
        # erase the character that represents this object
        libtcod.console_put_char(con, self.x, self.y, ' ', libtcod.BKGND_NONE)

    def send_to_back(self, objects):
        # make this object be drawn first, so all others appear above it if they're in the same tile.
        objects.remove(self)
        objects.insert(0, self)
