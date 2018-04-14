import libtcodpy as libtcod


class Object:
    # this is a generic object: the player, a monster, an item, the stairs...
    # it's always represented by a character on screen.
    def __init__(self, x, y, char, name, color):
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.name = name

    def move_or_attack(self, dx, dy, map, objects):
        #the coordinates the player is moving to/attacking
        x = self.x + dx
        y = self.y + dy

        #try to find an attackable object there
        target = None
        for object in objects:
            if object.x == x and object.y == y:
                target = object
                break

        #attack if target found, move otherwise
        if target is not None:
            print 'The ' + target.name + ' laughs at your puny efforts to attack him!'
        else:
            self.move(dx, dy, map)

    def move(self, dx, dy, map):
        if not map.tile_at(self.x + dx, self.y + dy).blocked:
            # move by the given amount
            self.x += dx
            self.y += dy

    def draw(self, con, map):
        if libtcod.map_is_in_fov(map.fov_map, self.x, self.y):
            # set the color and then draw the character that represents this object at its position
            libtcod.console_set_default_foreground(con, self.color)
            libtcod.console_put_char(
                con, self.x, self.y, self.char, libtcod.BKGND_NONE)

    def clear(self, con):
        # erase the character that represents this object
        libtcod.console_put_char(con, self.x, self.y, ' ', libtcod.BKGND_NONE)
