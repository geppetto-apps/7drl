import libtcodpy as libtcod


class Fighter:
    # combat-related properties and methods (monster, player, NPC).
    def __init__(self, hp, defense, power, death_function=None):
        self.owner = None
        self.max_hp = hp
        self.hp = hp
        self.defense = defense
        self.power = power
        self.death_function = death_function

    def take_damage(self, damage):
        # apply damage if possible
        if damage > 0:
            self.hp -= damage
        # check for death. if there's a death function, call it
        if self.hp <= 0:
            function = self.death_function
            if function is not None:
                function(self.owner)

    def attack(self, target):
        if target.fighter is None:
            return

        # a simple formula for attack damage
        damage = self.power - target.fighter.defense

        if damage > 0:
            # make the target take some damage
            print self.owner.name.capitalize() + ' attacks ' + target.name + \
                ' for ' + str(damage) + ' hit points.'
            target.fighter.take_damage(damage)
        else:
            print self.owner.name.capitalize() + ' attacks ' + target.name + \
                ' but it has no effect!'


class BasicMonster:
    def __init__(self):
        self.owner = None

    # AI for a basic monster.
    def take_turn(self, map, player, objects):
        # a basic monster takes its turn. If you can see it, it can see you
        monster = self.owner
        if libtcod.map_is_in_fov(map.fov_map, monster.x, monster.y):

            # move towards player if far away
            if monster.distance_to(player) >= 2:
                monster.move_towards(player.x, player.y, map, objects)

            # close enough, attack! (if the player is still alive.)
            elif player.fighter.hp > 0:
                monster.fighter.attack(player)
