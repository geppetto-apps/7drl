import libtcodpy as libtcod
from components import Fighter, BasicMonster
from rect import Rect
from message import message
from object import Object

ROOM_MAX_SIZE = 10
ROOM_MIN_SIZE = 6
MAX_ROOMS = 30

MAX_ROOM_MONSTERS = 5


class DungeonGenerator:
    def __init__(self, seed=None):
        self.seed = seed or libtcod.random_get_int(0, 0, 65555)
        self.random = libtcod.random_new_from_seed(self.seed)

    def generate(self, map, objects):
        for r in range(MAX_ROOMS):
            # random width and height
            w = libtcod.random_get_int(
                self.random, ROOM_MIN_SIZE, ROOM_MAX_SIZE)
            h = libtcod.random_get_int(
                self.random, ROOM_MIN_SIZE, ROOM_MAX_SIZE)
            # random position without going out of the boundaries of the map
            x = libtcod.random_get_int(self.random, 0, map.w - w - 1)
            y = libtcod.random_get_int(self.random, 0, map.h - h - 1)

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
                    if libtcod.random_get_int(self.random, 0, 1) == 1:
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
                self.place_objects(map, new_room, objects)
        map.set_fov()

    def place_objects(self, map, room, objects):
        def monster_death(monster):
            # transform it into a nasty corpse! it doesn't block, can't be
            # attacked and doesn't move
            message(monster.name.capitalize() + ' is dead!', libtcod.green)
            monster.char = '%'
            monster.color = libtcod.dark_red
            monster.blocks = False
            monster.fighter = None
            monster.ai = None
            monster.name = 'remains of ' + monster.name
            monster.send_to_back(objects)

        # choose random number of monsters
        num_monsters = libtcod.random_get_int(
            self.random, 0, MAX_ROOM_MONSTERS)

        for _ in range(num_monsters):
            # choose random spot for this monster
            x = libtcod.random_get_int(self.random, room.x1 + 1, room.x2 - 1)
            y = libtcod.random_get_int(self.random, room.y1 + 1, room.y2 - 1)

            # 80% chance of getting an orc
            # 80% chance of getting an orc
            if libtcod.random_get_int(self.random, 0, 100) < 80:
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
