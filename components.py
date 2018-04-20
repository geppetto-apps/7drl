import libtcodpy as libtcod
from message import message
from sounds import play_sound


class Fighter:
    # combat-related properties and methods (monster, player, NPC).
    def __init__(self, xp=0, xp_gain=50, hp_base=30, power_base=3,defense_base=0, death_function=None):
        self.owner = None
        self.xp = xp
        self.xp_gain = xp_gain
        self.hp_base = hp_base
        self.power_base = power_base
        self.defense_base = defense_base

        self.set_stats_from_level()
        self.death_function = death_function
        self.hp = self.max_hp

    def take_damage(self, damage, attacker):
        # apply damage if possible
        if damage > 0:
            self.hp -= damage
            play_sound('hurt.wav')
        # check for death. if there's a death function, call it
        if self.hp <= 0:
            attacker.grant_xp(self.xp_gain)
            function = self.death_function
            if function is not None:
                function(self.owner)

    def attack(self, target):
        if target.fighter is None:
            return

        # a simple formula for attack damage
        damage = libtcod.random_get_int(0, 0, self.power) - libtcod.random_get_int(0, 0, target.fighter.defense)

        if damage > 0:
            # make the target take some damage
            message(self.owner.name.capitalize() + ' attacks ' + target.name +
                    ' for ' + str(damage) + ' hit points.')
            target.fighter.take_damage(damage, self)
        else:
            play_sound('miss.wav')
            message(self.owner.name.capitalize() + ' attacks ' + target.name +
                    ' but it has no effect!')

    def heal(self, amount):
        # heal by the given amount, without going over the maximum
        self.hp += amount
        if self.hp > self.max_hp:
            self.hp = self.max_hp

    def grant_xp(self, amount):
        level = self.level()
        self.xp += amount
        if self.level() > level:
            self.set_stats_from_level()
            message('You leveled up!', libtcod.green)
            self.hp = self.max_hp
            play_sound('Levelup.wav')

    def level(self):
        xp = 0
        delta = 100
        level = 0
        while xp <= self.xp:
            level += + 1
            xp += delta
            delta *= 1.1
        return level

    def next_xp(self, level):
        xp = 0
        delta = 100
        i = 0
        while i < level:
            i += + 1
            xp += delta
            delta *= 1.1
        return int(xp)

    def set_stats_from_level(self):
        level = self.level()
        self.max_hp = self.hp_base + (level - 1) * 10
        self.defense = self.defense_base + level - 1
        self.power = self.power_base + level


class BasicMonster:
    class IdleState:
        def __init__(self, ai):
            self.ai = ai

        def take_turn(self, map, player):
            monster = self.ai.owner
            if libtcod.map_is_in_fov(map.fov_map, monster.x, monster.y):
                message('A monster has caught your attention!')
                self.ai.state = BasicMonster.AggroState(self.ai)
                return
            dx = 0
            dy = 0
            if libtcod.random_get_int(0, 0, 1) == 1:
                dx = libtcod.random_get_int(0, -1, 1)
            else:
                dy = libtcod.random_get_int(0, -1, 1)
            self.ai.owner.move_by(dx, dy, map)

    class AggroState:
        def __init__(self, ai):
            self.ai = ai

        # AI for a basic monster.
        def take_turn(self, map, player):
            # a basic monster takes its turn. If you can see it, it can see you
            monster = self.ai.owner
            if not libtcod.map_is_in_fov(map.fov_map, monster.x, monster.y):
                self.ai.state = BasicMonster.IdleState(self.ai)
                return

            # move towards player if far away
            if monster.distance_to(player) >= 2:
                monster.move_astar(player, map)

            # close enough, attack! (if the player is still alive.)
            elif player.fighter.hp > 0:
                monster.fighter.attack(player)

    def __init__(self):
        self.owner = None
        self.state = BasicMonster.IdleState(self)

    def take_turn(self, map, player):
        self.state.take_turn(map, player)


class ConfusedMonster:
    CONFUSE_RANGE = 5
    CONFUSE_NUM_TURNS = 10

    # AI for a temporarily confused monster (reverts to previous AI after a while).
    def __init__(self, old_ai, num_turns=CONFUSE_NUM_TURNS):
        self.owner = None
        self.old_ai = old_ai
        self.num_turns = num_turns

    def take_turn(self, map, player):
        if self.num_turns > 0:  # still confused...
            # move in a random direction, and decrease the number of turns confused
            dx = libtcod.random_get_int(0, -1, 1)
            dy = libtcod.random_get_int(0, -1, 1)
            self.owner.move_by(dx, dy, map)
            self.num_turns -= 1
        # restore the previous AI (this one will be deleted because it's not referenced anymore)
        else:
            self.owner.ai = self.old_ai
            message('The ' + self.owner.name +
                    ' is no longer confused!', libtcod.red)


class Item:
    def __init__(self, use_function=None):
        self.owner = None
        self.use_function = use_function

    # an item that can be picked up and used.
    def pick_up(self, map, player):
        # add to the player's inventory and remove from the map
        if len(player.inventory) >= 26:
            message('Your inventory is full, cannot pick up ' +
                    self.owner.name + '.', libtcod.red)
            play_sound('wrong.wav')
        else:
            player.inventory.append(self.owner)
            map.objects.remove(self.owner)
            message('You picked up a ' + self.owner.name + '!', libtcod.green)

    def use(self, player):
        # just call the "use_function" if it is defined
        if self.use_function is None:
            message('The ' + self.owner.name + ' cannot be used.')
        else:
            if self.use_function() != 'cancelled':
                # destroy after use, unless it was cancelled for some reason
                player.inventory.remove(self.owner)

    def drop(self, player, map):
        # add to the map and remove from the player's inventory. also, place it at the player's coordinates
        map.objects.append(self.owner)
        player.inventory.remove(self.owner)
        self.owner.x = player.x
        self.owner.y = player.y
        message('You dropped a ' + self.owner.name + '.', libtcod.yellow)

class Ladder:
    def __init__(self, use_function):
        self.owner = None
        self.use_function = use_function

    # an item that can be picked up and used.
    def ascend(self, objects):
        self.use_function()
