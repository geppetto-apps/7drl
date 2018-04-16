import libtcodpy as libtcod
from components import Fighter, BasicMonster, Item
from rect import Rect
from message import message
from object import Object

ROOM_MAX_SIZE = 10
ROOM_MIN_SIZE = 6
MAX_ROOMS = 30

MAX_ROOM_MONSTERS = 5
MAX_ROOM_ITEMS = 2

HEAL_AMOUNT = 4

LIGHTNING_DAMAGE = 20
LIGHTNING_RANGE = 5


class DungeonGenerator:
    def __init__(self, seed=None):
        self.seed = seed or libtcod.random_get_int(0, 0, 65555)
        print "Seed: " + str(self.seed)
        self.random = libtcod.random_new_from_seed(self.seed)

    def generate(self, map, objects, player):
        for r in range(MAX_ROOMS):
            # random width and height
            w = libtcod.random_get_int(
                self.random, ROOM_MIN_SIZE, ROOM_MAX_SIZE)
            h = libtcod.random_get_int(
                self.random, ROOM_MIN_SIZE, ROOM_MAX_SIZE)
            # random position without going out of the boundaries of the map
            x = self.random_int(0, map.w - w - 1)
            y = self.random_int(0, map.h - h - 1)

            # "Rect" class makes rectangles easier to work with
            new_room = Rect(x, y, w, h)

            # run through the other rooms and see if they intersect with this one
            failed = False
            for other_room in map.rooms:
                if new_room.intersect(other_room):
                    failed = True
                    break

            if not failed:
                # this means there are no intersections, so this room is valid

                # "paint" it to the map's tiles
                map.create_room(new_room)

                # center coordinates of new room, will be useful later
                (new_x, new_y) = new_room.center()

                if map.num_rooms != 0:
                    # all rooms after the first:
                    # connect it to the previous room with a tunnel

                    # center coordinates of previous room
                    (prev_x, prev_y) = map.rooms[map.num_rooms-1].center()

                    # draw a coin (random number that is either 0 or 1)
                    if self.random_int(0, 1) == 1:
                        # first move horizontally, then vertically
                        map.create_h_tunnel(prev_x, new_x, prev_y)
                        map.create_v_tunnel(prev_y, new_y, new_x)
                    else:
                        # first move vertically, then horizontally
                        map.create_v_tunnel(prev_y, new_y, prev_x)
                        map.create_h_tunnel(prev_x, new_x, new_y)

                # finally, append the new room to the list
                map.rooms.append(new_room)
                map.num_rooms += 1
                # add some contents to this room, such as monsters
                self.place_objects(map, new_room, objects, player)
        map.set_fov()

    def place_objects(self, map, room, objects, player):
        def cast_heal():
            # heal the player
            if player.fighter.hp == player.fighter.max_hp:
                message('You are already at full health.', libtcod.red)
                return 'cancelled'

            message('Your wounds start to feel better!', libtcod.light_violet)
            player.fighter.heal(HEAL_AMOUNT)

        def closest_monster(max_range):
            # find closest enemy, up to a maximum range, and in the player's FOV
            closest_enemy = None
            # start with (slightly more than) maximum range
            closest_dist = max_range + 1

            for object in objects:
                if object.fighter and not object == player and libtcod.map_is_in_fov(map.fov_map, object.x, object.y):
                    # calculate distance between this object and the player
                    dist = player.distance_to(object)
                    if dist < closest_dist:  # it's closer, so remember it
                        closest_enemy = object
                        closest_dist = dist
            return closest_enemy

        def cast_lightning():
            # find closest enemy (inside a maximum range) and damage it
            monster = closest_monster(LIGHTNING_RANGE)
            if monster is None:  # no enemy found within maximum range
                message('No enemy is close enough to strike.', libtcod.red)
                return 'cancelled'

            # zap it!
            message('A lighting bolt strikes the ' + monster.name + ' with a loud thunder! The damage is '
                    + str(LIGHTNING_DAMAGE) + ' hit points.', libtcod.light_blue)
            monster.fighter.take_damage(LIGHTNING_DAMAGE)

        def monster_death(monster):
            # transform it into a nasty corpse! it doesn't block, can't be
            # attacked and doesn't move
            message(monster.name.capitalize() + ' is dead!', libtcod.green)
            monster.char = '%'
            monster.color = libtcod.dark_red
            monster.blocks = False
            monster.fighter = None
            monster.ai = None
            if monster.name == 'orc':
                # 50 % chance of dropping potion
                if self.chance(50):
                    message(monster.name.capitalize() +
                            ' dropped healing potion!', libtcod.light_amber)
                    item = self.place_potion(cast_heal, monster.x, monster.y)
                    objects.append(item)
            monster.name = 'remains of ' + monster.name
            monster.send_to_back(objects)

        # choose random number of monsters
        num_monsters = libtcod.random_get_int(
            self.random, 0, MAX_ROOM_MONSTERS)

        for _ in range(num_monsters):
            # choose random spot for this monster
            x = self.random_int(room.x1 + 1, room.x2 - 1)
            y = self.random_int(room.y1 + 1, room.y2 - 1)

            # only place it if the tile is not blocked
            if not map.tile_at(x, y).blocked:
                if self.chance(80):
                    # create an orc
                    fighter_component = Fighter(
                        hp=10, defense=0, power=3, death_function=monster_death)
                    ai_component = BasicMonster()

                    monster = Object(x, y, 'o', 'orc', libtcod.desaturated_green,
                                     blocks=True, fighter=fighter_component, ai=ai_component)
                else:
                    # create a troll
                    fighter_component = Fighter(
                        hp=16, defense=1, power=4, death_function=monster_death)
                    ai_component = BasicMonster()

                    monster = Object(x, y, 'T', 'troll', libtcod.darker_green,
                                     blocks=True, fighter=fighter_component, ai=ai_component)

                objects.append(monster)

        # choose random number of items
        num_items = self.random_int(0, MAX_ROOM_ITEMS)

        for i in range(num_items):
            # choose random spot for this item
            x = self.random_int(room.x1+1, room.x2-1)
            y = self.random_int(room.y1+1, room.y2-1)

            # only place it if the tile is not blocked
            if not map.tile_at(x, y).blocked:
                if self.chance(70):
                    # create a healing potion (70 % chance)
                    item = self.place_potion(cast_heal, x, y)
                    objects.append(item)
                    # items appear below other objects
                    item.send_to_back(objects)
                else:
                    # create a lightning bolt scroll (30% chance)
                    item = self.place_bolt(cast_lightning, x, y)
                    objects.append(item)
                    # items appear below other objects
                    item.send_to_back(objects)

    def place_potion(self, cast_heal, x, y):
        item_component = Item(use_function=cast_heal)
        return Object(x, y, '!', 'healing potion',
                      libtcod.violet, item=item_component)

    def place_bolt(self, cast_fn, x, y):
        item_component = Item(use_function=cast_fn)
        return Object(x, y, '#', 'scroll of lightning bolt',
                      libtcod.light_yellow, item=item_component)

    def random_int(self, min, max):
        return libtcod.random_get_int(self.random, min, max)

    def chance(self, percent):
        dice = self.random_int(0, 100)
        return dice < 70

