# pylint: disable=missing-function-docstring,invalid-name
# pylint: disable=missing-class-docstring,missing-module-docstring
import os
import sys
import random
import uuid
import yaml
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.shortcuts import radiolist_dialog


class GameDB(dict):
    def __init__(self):
        dict.__init__(self)
        self.load()

    @staticmethod
    def data_filepath(filename):
        return os.path.join(os.path.dirname(__file__), filename)

    def load(self):
        with open(self.data_filepath('gamedata.yaml'), 'r') as fin:
            self.update(yaml.load(fin, Loader=yaml.SafeLoader))

    def save(self):
        with open(self.data_filepath('gamedata.yaml'), 'w') as fout:
            yaml.dump(dict(self), fout)


def get_free_family_name(db):
    family_names = db['family-names']
    random.shuffle(family_names)
    for name in family_names:
        match = False
        for player in db.get('players', []):
            if name == player['name']:
                match = True
                break
        if match:
            continue
        return name
    # return last-match (it is a duplicate)
    return family_names[-1]


def show_welcome(name, is_new):
    back = ''
    if not is_new:
        back = ' back'

    print(f"Welcome{back}, {name}!")


def select_advantage(db):
    attributes = db['attributes']
    advantage = radiolist_dialog(
        title=f'Family advantage',
        text='Select a family advantage',
        values=list(zip(attributes, attributes))
    ).run()
    if advantage is None:
        sys.exit(1)  # cancel
    return advantage


def select_province(db, player):
    all_provinces = db['provinces']
    province_name = radiolist_dialog(
        title=f"{player['name']} decides his fate",
        text='Select a province',
        values=list(zip(all_provinces.keys(), all_provinces.keys()))
    ).run()
    if province_name is None:
        sys.exit(1)  # cancel
    province = all_provinces[province_name]
    province['name'] = province_name
    return province


def create_player(db, name):
    player = {
        'name': name,
        'id': str(uuid.uuid4()),
        'ai': False,
        'age': random.randrange(18, 34),
        'level': 1,
        'location': 'home',
    }
    province = select_province(db, player)
    player['province'] = province['name']
    player = set_new_player_attributes(db, player, province)
    advantage = select_advantage(db)
    player[advantage] += 1
    return player


def set_new_player_attributes(db, player, province):
    # set province attribute values to player by random order
    some_attributes = db['attributes']
    random.shuffle(some_attributes)
    for idx, attr in enumerate(some_attributes):
        player[attr] = max(0.0, province.get(attr, 0.0) - idx)
    return player


def create_hatamoto(db, province):
    hatamoto = {
        'name': get_free_family_name(db),
        'id': str(uuid.uuid4()),
        'ai': True,
        'age': random.randrange(34, 68),
        'level': 2,
        'location': 'home',
    }
    hatamoto['province'] = province['name']
    hatamoto = set_new_player_attributes(db, hatamoto, province)
    hatamoto[random.choice(db['attributes'])] += 1
    return hatamoto


def create_ai_player(db, province):
    ai_player = {
        'name': get_free_family_name(db),
        'id': str(uuid.uuid4()),
        'ai': True,
        'age': random.randrange(18, 34),
        'level': 1,
        'location': 'home',
    }
    ai_player['province'] = province['name']
    ai_player = set_new_player_attributes(db, ai_player, province)
    ai_player[random.choice(db['attributes'])] += 1
    return ai_player


def join_province(db, player):
    # conditionally add player to province
    province = db['provinces'][player['province']]
    if player['id'] not in province.get('members', []):
        province['members'] = province.get('members', []) + [player['id']]
    return province


def ready_province(db, province):
    # Generate new Hatamoto
    if 'hatamoto' not in province:
        hatamoto = create_hatamoto(db, province)
        db['provinces'][province['name']]['hatamoto'] = hatamoto['id']

    # Create AI opponents
    while len(db['provinces'][province['name']]['members']) < 4:
        ai_player = create_ai_player(db, province)
        db['provinces'][province['name']]['members'].append(ai_player['id'])
        db['players'].append(ai_player)


def select_player(db):
    existing_players = db.get('players', [])
    all_names = [player['name'] for player in existing_players]
    name = ''
    while not name:
        name = prompt(
            "Your name?  ",
            completer=WordCompleter(all_names)
        ).strip()

    player = None
    for tgt_player in existing_players:
        if tgt_player['name'].lower() == name.lower():
            player = tgt_player
            name = player['name']

    show_welcome(name, is_new=player is None)

    if player is None:
        player = create_player(db, name)
        db['players'].append(player)

    return player


def main():
    db = GameDB()
    player = select_player(db)
    province = join_province(db, player)
    ready_province(db, province)
    db.save()


if __name__ == '__main__':
    main()
