import libtcodpy as libtcod
from components import Fighter, BasicMonster, Item, ConfusedMonster, Ladder
from rect import Rect
from message import message
from object import Object
from sounds import play_sound
import tiles
import random

ROOM_MAX_SIZE = 14
ROOM_MIN_SIZE = 8
MAX_ROOMS = 20

MAX_ROOM_MONSTERS = 5
MAX_ROOM_ITEMS = 3

HEAL_AMOUNT = 8

LIGHTNING_DAMAGE = 20
LIGHTNING_RANGE = 5


def cast_heal(player):
    # heal the player
    if player.fighter.hp == player.fighter.max_hp:
        message('You are already at full health.', libtcod.red)
        play_sound('wrong.wav')
        return 'cancelled'

    message('Your wounds start to feel better!', libtcod.light_violet)
    play_sound('Heal.wav')
    player.fighter.heal(HEAL_AMOUNT)

def closest_monster(player, max_range):
    # find closest enemy, up to a maximum range, and in the player's FOV
    closest_enemy = None
    # start with (slightly more than) maximum range
    closest_dist = max_range + 1

    map = player.map
    for object in map._objects:
        if object.fighter and not object == player and libtcod.map_is_in_fov(map.fov_map, object.x, object.y):
            # calculate distance between this object and the player
            dist = player.distance_to(object)
            if dist < closest_dist:  # it's closer, so remember it
                closest_enemy = object
                closest_dist = dist
    return closest_enemy

def cast_lightning(player):
    # find closest enemy (inside a maximum range) and damage it
    monster = closest_monster(player, LIGHTNING_RANGE)
    if monster is None:  # no enemy found within maximum range
        message('No enemy is close enough to strike.', libtcod.red)
        return 'cancelled'

    # zap it!
    play_sound('Spellexplosion.wav')
    message('A lighting bolt strikes the ' + monster.name + ' with a loud thunder! The damage is '
            + str(LIGHTNING_DAMAGE) + ' hit points.', libtcod.light_blue)
    monster.fighter.take_damage(LIGHTNING_DAMAGE, player.fighter)

def cast_confuse(player):
    # find closest enemy in-range and confuse it
    monster = closest_monster(player, ConfusedMonster.CONFUSE_RANGE)
    if monster is None:  # no enemy found within maximum range
        message('No enemy is close enough to confuse.', libtcod.red)
        return 'cancelled'
    # replace the monster's AI with a "confused" one; after some turns it will restore the old AI
    old_ai = monster.ai
    monster.ai = ConfusedMonster(old_ai)
    monster.ai.owner = monster  # tell the new component who owns it
    message('The eyes of the ' + monster.name +
            ' look vacant, as he starts to stumble around!', libtcod.light_green)
    play_sound('Confuse.wav')

def monster_death(monster):
    # transform it into a nasty corpse! it doesn't block, can't be
    # attacked and doesn't move
    message(monster.name.capitalize() + ' is dead!', libtcod.green)
    monster.chars = [tiles.tomb_tile]
    play_sound('Monsterkill.wav')
    monster.color = libtcod.white
    monster.blocks = False
    monster.fighter = None
    monster.ai = None
    if monster.name == 'orc':
        # 25 % chance of dropping potion
        if libtcod.random_get_int(0, 0, 100) > 75:
            message(monster.name.capitalize() +
                    ' dropped healing potion!', libtcod.light_amber)
            item = place_potion(cast_heal, monster.x, monster.y)
            monster.map.add_object(item)
    monster.name = 'remains of ' + monster.name
    monster.map.send_to_back(monster)

def place_potion(cast_heal, x, y):
    item_component = Item(use_function=cast_heal)
    return Object(x, y, tiles.healingpotion_tile, 'healing potion',
                    libtcod.white, item=item_component)

def place_bolt(cast_fn, x, y):
    item_component = Item(use_function=cast_fn)
    return Object(x, y, tiles.scroll_tile, 'scroll of lightning bolt',
                    libtcod.white, item=item_component)

def place_chest(open_fn, x, y):
    item_component = Item(use_function=open_fn)
    return Object(x, y, tiles.chest_tile, 'chest',
                    libtcod.white, item=item_component)

class MonsterGenerator:
    @staticmethod
    def orc(x, y, player, distance, monster_death):
        fighter_component = Fighter(
            xp=(int(distance)+player.fighter.xp), power_base=2, xp_gain=10, striked_char=tiles.striked_orc_tile, death_function=monster_death)
        ai_component = BasicMonster()

        return Object(x, y, tiles.orc_tile, 'orc', libtcod.white,
                            blocks=True, fighter=fighter_component, ai=ai_component)

    @staticmethod
    def skeleton(x, y, player, distance, monster_death):
        fighter_component = Fighter(
            xp=(int(distance)+player.fighter.xp), power_base=4, defense_base=1, xp_gain=20, death_function=monster_death)
        ai_component = BasicMonster()

        return Object(x, y, tiles.skeleton_tile, 'skeleton', libtcod.white,
                            blocks=True, fighter=fighter_component, ai=ai_component)

    @staticmethod
    def wizard(x, y, player, distance, monster_death):
        fighter_component = Fighter(
            xp=(int(distance)+player.fighter.xp), power_base=2, defense_base=0, xp_gain=30, death_function=monster_death)
        ai_component = BasicMonster(atk_range=6)

        return Object(x, y, tiles.wizard_tile, 'wizard', libtcod.white,
                            blocks=True, fighter=fighter_component, ai=ai_component)

class DungeonGenerator:
    def __init__(self, seed=None):
        self.seed = seed or libtcod.random_get_int(0, 0, 65555)
        print "Seed: " + str(self.seed)
        self.random = libtcod.random_new_from_seed(self.seed)
        random.seed(self.seed)

    def generate(self, map, player, start_x=None, start_y=None):
        room_tries = 0
        while map.num_rooms < MAX_ROOMS and room_tries < MAX_ROOMS * 10:
            if self.generate_room(map, start_x, start_y):
                start_x = None
                start_y = None
            room_tries += 1
        for x in range(0, map.w):
            for y in range(0, map.h):
                tile = map.tiles[x][y]
                if tile != None and tile.tunnel:
                    tile.blocked = False
                    tile.block_sight = False
        # sort rooms
        first_room = map.rooms[0]
        (x, y) = first_room.center()
        player.x = x
        player.y = y

        def sort_fn(room):
            (x, y) = room.center()
            return player.astar_distance_to(map, x, y)

        map.rooms.sort(key=sort_fn)

        # get the 3 last rooms
        last_rooms = map.rooms[-3:]
        random.shuffle(last_rooms)

        # put the ladder in one of the last rooms
        exit_room = last_rooms.pop()
        x = self.random_int(exit_room.x1 + 2, exit_room.x2 - 2)
        y = self.random_int(exit_room.y1 + 2, exit_room.y2 - 2)

        # create a ladder
        def ascend():
            print("ascending!")
        ladder_component = Ladder(ascend)
        ladder = Object(x, y, tiles.stairsdown_tile, 'stairs', libtcod.white, ladder=ladder_component)
        map.add_object(ladder)

        def open_fn(player):
            print('opening chest')

        # place chests
        for room in last_rooms:
            (x, y) = room.center()
            # map.add_object(place_chest(open_fn, x, y))

        for i in range(1, map.num_rooms):
            # add some contents to this room, such as monsters
            room = map.rooms[i]
            self.place_objects(map, room, player)
            # grant some xp for discovering rooms
            (x, y) = room.center()
            map.tiles[x][y].xp_gain = 20
        map.set_fov()

    def generate_room(self, map, start_x, start_y):
        # random width and height
        w = libtcod.random_get_int(
            self.random, ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        h = libtcod.random_get_int(
            self.random, ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        # random position without going out of the boundaries of the map
        if start_x != None and start_y != None:
            x = start_x - w / 2
            y = start_y - h / 2
        else:
            x = self.random_int(0, map.w - w - 1)
            y = self.random_int(0, map.h - h - 1)

        # "Rect" class makes rectangles easier to work with
        new_room = Rect(x, y, w, h)

        # run through the other rooms and see if they intersect with this one
        for other_room in map.rooms:
            if new_room.intersect(other_room):
                return False

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
        return True

    def place_objects(self, map, room, player):
        # choose random number of monsters
        num_monsters = libtcod.random_get_int(
            self.random, 0, MAX_ROOM_MONSTERS)

        for _ in range(num_monsters):
            # choose random spot for this monster
            x = self.random_int(room.x1 + 1, room.x2 - 1)
            y = self.random_int(room.y1 + 1, room.y2 - 1)

            # only place it if the tile is not blocked
            if not map.tile_at(x, y).blocked:
                distance = player.astar_distance_to(map, x, y)
                dice = self.random_int(0, 50) + (map.floor - 1) * 10
                if dice < 40:
                    # create an orc
                    monster = MonsterGenerator.orc(x, y, player, distance, monster_death)
                elif dice < 50:
                    # create a skeleton
                    monster = MonsterGenerator.skeleton(x, y, player, distance, monster_death)
                else:
                    monster = MonsterGenerator.wizard(x, y, player, distance, monster_death)

                map.add_object(monster)

        # choose random number of items
        num_items = self.random_int(0, MAX_ROOM_ITEMS)

        for _ in range(num_items):
            # choose random spot for this item
            x = self.random_int(room.x1+1, room.x2-1)
            y = self.random_int(room.y1+1, room.y2-1)

            # only place it if the tile is not blocked
            if not map.tile_at(x, y).blocked:
                item = None
                if self.chance(50):
                    # create a healing potion (70 % chance)
                    item = place_potion(cast_heal, x, y)
                elif self.chance(50):
                    # create a lightning bolt scroll (30% chance)
                    item = place_bolt(cast_lightning, x, y)
                else:
                    # create a confuse scroll (15% chance)
                    item_component = Item(use_function=cast_confuse)
                    item = Object(x, y, tiles.scroll_tile, 'scroll of confusion',
                                  libtcod.orange, item=item_component)
                map.add_object(item)

    def random_int(self, min, max):
        return libtcod.random_get_int(self.random, min, max)

    def chance(self, percent):
        dice = self.random_int(0, 100)
        return dice < percent
