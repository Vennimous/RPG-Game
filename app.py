from flask import Flask, render_template, request, redirect, url_for, session
import random
import os
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this to a random string

# Store characters (in a real app, you'd use a database)
characters = []
current_dungeon = None
current_combat = None

# Your existing game constants
CLASS_BONUSES = {
    "Warrior": {"strength": 2, "constitution": 2, "base_hp": 12},
    "Rogue": {"dexterity": 2, "intelligence": 1, "base_hp": 8},
    "Mage": {"intelligence": 2, "wisdom": 1, "base_hp": 6},
    "Priest": {"wisdom": 2, "charisma": 1, "base_hp": 10}
}

RACE_BONUSES = {
    "Human": {"strength": 1, "dexterity": 1, "constitution": 1, "charisma": 1, "intelligence": 1},
    "Elf": {"dexterity": 2, "intelligence": 1, "wisdom": 1, "charisma": 1},
    "Dwarf": {"constitution": 2, "strength": 2, "wisdom": 1}
}

# Updated biomes with new enemies
BIOMES = {
    "Forest": {
        "description": "Dense woodland filled with ancient trees",
        "enemies": ["Wolf", "Giant Spider", "Dire Wolf", "Manticore", "Troll"]
    },
    "Cave": {
        "description": "Dark caverns echoing with unknown sounds",
        "enemies": ["Goblin", "Bugbear", "Ogre", "Basilisk", "Ettin", "Troll"]
    },
    "Crypt": {
        "description": "Ancient tomb filled with restless dead",
        "enemies": ["Skeleton", "Zombie", "Ghoul", "Minotaur Skeleton", "Ghost", "Vampire Spawn"]
    },
    "Mountain": {
        "description": "Rugged peaks with treacherous paths",
        "enemies": ["Wolf", "Gargoyle", "Manticore", "Air Elemental"]
    },
    "Swamp": {
        "description": "Murky wetlands filled with dangerous creatures",
        "enemies": ["Giant Spider", "Zombie", "Hell Hound", "Lamia"]
    },
    "Dungeon": {
        "description": "Ancient underground complex with many dangers",
        "enemies": ["Goblin", "Skeleton", "Cult Fanatic", "Gargoyle", "Doppelganger", "Ghost"]
    }
}

# Updated enemies with new higher CR enemies
ENEMIES = {
    # Existing enemies
    "Wolf": {"hp": 11, "ac": 13, "damage": "1d6", "cr": 0.5, "gold": 25},
    "Giant Spider": {"hp": 26, "ac": 14, "damage": "1d8", "cr": 1, "gold": 50},
    "Goblin": {"hp": 7, "ac": 15, "damage": "1d6", "cr": 0.25, "gold": 15},
    "Bugbear": {"hp": 27, "ac": 16, "damage": "2d8", "cr": 1, "gold": 50},
    "Skeleton": {"hp": 13, "ac": 13, "damage": "1d6", "cr": 0.25, "gold": 10},
    "Zombie": {"hp": 22, "ac": 8, "damage": "1d6", "cr": 0.25, "gold": 10},
    "Ghoul": {"hp": 22, "ac": 12, "damage": "1d6", "cr": 1, "gold": 50},
    "Dire Wolf": {"hp": 37, "ac": 14, "damage": "2d6", "cr": 1, "gold": 50},
    "Ogre": {"hp": 59, "ac": 11, "damage": "2d8", "cr": 2, "gold": 100},
    
    # New CR 2 enemies
    "Cult Fanatic": {"hp": 33, "ac": 13, "damage": "1d8+2", "cr": 2, "gold": 100},
    "Gargoyle": {"hp": 52, "ac": 15, "damage": "1d6+2", "cr": 2, "gold": 100},
    "Minotaur Skeleton": {"hp": 67, "ac": 12, "damage": "2d12+2", "cr": 2, "gold": 100},
    "Spined Devil": {"hp": 22, "ac": 13, "damage": "1d6+1", "cr": 2, "gold": 100},
    
    # New CR 3 enemies
    "Basilisk": {"hp": 52, "ac": 15, "damage": "2d6+3", "cr": 3, "gold": 200},
    "Doppelganger": {"hp": 52, "ac": 14, "damage": "1d6+2", "cr": 3, "gold": 200},
    "Hell Hound": {"hp": 45, "ac": 15, "damage": "1d8+3", "cr": 3, "gold": 200},
    "Manticore": {"hp": 68, "ac": 14, "damage": "2d6+3", "cr": 3, "gold": 200},
    
    # New CR 4 enemies
    "Ettin": {"hp": 85, "ac": 12, "damage": "2d8+5", "cr": 4, "gold": 300},
    "Ghost": {"hp": 45, "ac": 11, "damage": "3d6", "cr": 4, "gold": 300},
    "Lamia": {"hp": 97, "ac": 13, "damage": "2d6+2", "cr": 4, "gold": 300},
    
    # New CR 5 enemies
    "Air Elemental": {"hp": 90, "ac": 15, "damage": "2d8+5", "cr": 5, "gold": 400},
    "Troll": {"hp": 84, "ac": 15, "damage": "2d8+4", "cr": 5, "gold": 400},
    "Vampire Spawn": {"hp": 82, "ac": 15, "damage": "1d8+4", "cr": 5, "gold": 400}
}

# Spells with updated duration and AOE rules
SPELLS = {
    # Mage spells
    "Firebolt": {
        "type": "damage",
        "damage": "1d10",
        "targets": 1,
        "level": 1
    },
    "Magic Missile": {
        "type": "damage",
        "damage": "1d4+1",
        "targets": 1,
        "level": 1,
        "always_hits": True
    },
    "Mage Armor": {
        "type": "buff",
        "effect": {"ac_bonus": 3},
        "targets": 1,
        "level": 1,
        "duration": "dungeon"
    },
    "Burning Hands": {
        "type": "damage",
        "damage": "3d6",
        "targets": 3,
        "level": 1
    },
    "Fireball": {
        "type": "damage",
        "damage": "6d6",
        "targets": 3,
        "level": 3
    },
    
    # Priest spells
    "Lesser Heal": {
        "type": "healing",
        "healing": "1d8+2",
        "targets": 1,
        "level": 1
    },
    "Bless": {
        "type": "buff",
        "effect": {"attack_bonus": "1d4"},
        "targets": 3,
        "level": 1,
        "duration": "dungeon"
    },
    "Lesser Smite": {
        "type": "damage",
        "damage": "2d6",
        "targets": 1,
        "level": 1
    },
    "Mass Healing Word": {
        "type": "healing",
        "healing": "1d4+1",
        "targets": 3,
        "level": 3
    },
    "Revive": {
        "type": "revive",
        "targets": 1,
        "level": 3
    }
}

# Potions and items with updated duration rules
POTIONS = {
    "Healing Potion": {
        "type": "healing",
        "effect": "2d4+2 HP",
        "cost": 50
    },
    "Greater Healing Potion": {
        "type": "healing",
        "effect": "4d4+4 HP",
        "cost": 100
    },
    "Potion of Strength": {
        "type": "buff",
        "effect": {"strength_bonus": 2},
        "duration": "dungeon",
        "cost": 75
    },
    "Potion of Dexterity": {
        "type": "buff",
        "effect": {"initiative_bonus": 4}, # Changed from movement to initiative
        "duration": "dungeon",
        "cost": 75
    },
    "Potion of Protection": {
        "type": "buff",
        "effect": {"ac_bonus": 2},
        "duration": "dungeon",
        "cost": 100
    }
}

# Scrolls with updated duration and AOE rules
SCROLLS = {
    "Scroll of Fireball": {
        "type": "damage",
        "effect": "6d6 fire damage",
        "targets": 3,
        "cost": 150
    },
    "Scroll of Revive": {
        "type": "revive",
        "effect": "Revive fallen character",
        "targets": 1,
        "cost": 200
    },
    "Scroll of Protection": {
        "type": "buff",
        "effect": {"ac_bonus": 5},
        "duration": "dungeon",
        "targets": 1,
        "cost": 100
    },
    "Scroll of Haste": {
        "type": "buff",
        "effect": {"initiative_bonus": 5}, # Changed from movement to initiative
        "duration": "dungeon",
        "targets": 1,
        "cost": 150
    }
}

# Save/load functionality
def save_game():
    """Save the current game state to a file"""
    save_data = {
        'characters': characters,
        'current_dungeon': current_dungeon,
        'timestamp': datetime.now().isoformat()
    }
    
    save_dir = 'saves'
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    
    save_path = os.path.join(save_dir, 'savegame.json')
    with open(save_path, 'w') as f:
        json.dump(save_data, f)
    
    return True

def load_game():
    """Load game state from file"""
    global characters, current_dungeon
    
    save_path = os.path.join('saves', 'savegame.json')
    if not os.path.exists(save_path):
        return False
    
    try:
        with open(save_path, 'r') as f:
            save_data = json.load(f)
        
        characters = save_data.get('characters', [])
        current_dungeon = save_data.get('current_dungeon', None)
        return True
    except Exception as e:
        print(f"Error loading game: {e}")
        return False

# Calculate XP for next level
def calculate_next_level_xp(current_level):
    """Calculate XP needed for next level"""
    # Simple formula: 100 * current_level^2
    return 100 * (current_level ** 2)

# Award XP after combat
def award_combat_xp(enemies):
    """Award XP after defeating enemies"""
    total_cr = sum(enemy['cr'] for enemy in enemies)
    
    # XP formula: 100 * CR
    total_xp = int(100 * total_cr)
    
    # Divide among characters
    xp_per_character = total_xp // len(characters)
    
    for character in characters:
        character['xp'] = character.get('xp', 0) + xp_per_character
    
    return total_xp

# Manage buffs when entering/exiting dungeons
def clear_dungeon_buffs():
    """Remove all dungeon-duration buffs from characters"""
    for character in characters:
        if 'buffs' in character:
            # Filter out dungeon-duration buffs
            character['buffs'] = [buff for buff in character['buffs'] if buff.get('duration') != 'dungeon']

# Generate quest rewards
def generate_quest_rewards(challenge_rating):
    """Generate bonus rewards for special quests"""
    # Magic items based on challenge rating
    possible_rewards = [
        {
            'type': 'weapon',
            'name': '+1 Longsword',
            'bonus': 1,
            'damage': '1d8+1',
            'value': 500
        },
        {
            'type': 'weapon',
            'name': '+1 Dagger',
            'bonus': 1,
            'damage': '1d4+1',
            'value': 300
        },
        {
            'type': 'armor',
            'name': '+1 Chain Shirt',
            'bonus': 1,
            'base_ac': 13,
            'value': 400
        },
        {
            'type': 'item',
            'name': 'Greater Healing Potion',
            'effect': '2d8+4 HP',
            'value': 200
        },
        {
            'type': 'item',
            'name': 'Scroll of Revive',
            'effect': 'Revive fallen character',
            'value': 300
        }
    ]
    
    # Select rewards based on challenge rating
    num_rewards = max(1, min(3, int(challenge_rating)))
    return random.sample(possible_rewards, num_rewards)

# Generate shop inventory
def generate_shop_inventory():
    """Generate shop inventory with various items"""
    inventory = {
        'weapons': [
            {'name': 'Longsword', 'damage': '1d8', 'cost': 25, 'type': 'one-handed'},
            {'name': 'Greatsword', 'damage': '2d6', 'cost': 50, 'type': 'two-handed'},
            {'name': 'Shortsword', 'damage': '1d6', 'cost': 15, 'type': 'one-handed'},
            {'name': 'Dagger', 'damage': '1d4', 'cost': 10, 'type': 'one-handed'},
            {'name': 'Rapier', 'damage': '1d8', 'cost': 25, 'type': 'one-handed'},
            {'name': 'Staff', 'damage': '1d6', 'cost': 5, 'type': 'two-handed'},
            {'name': 'Wand', 'damage': '1d4', 'cost': 20, 'type': 'one-handed'},
            {'name': 'Mace', 'damage': '1d6', 'cost': 15, 'type': 'one-handed'},
            {'name': 'Battleaxe', 'damage': '1d8', 'cost': 25, 'type': 'one-handed'},
            {'name': 'Warhammer', 'damage': '1d8', 'cost': 25, 'type': 'one-handed'},
            {'name': 'Shortbow', 'damage': '1d6', 'cost': 30, 'type': 'two-handed'},
            {'name': 'Longbow', 'damage': '1d8', 'cost': 50, 'type': 'two-handed'},
        ],
        'armor': [
            {'name': 'Robes', 'ac_bonus': 0, 'cost': 5},
            {'name': 'Leather', 'ac_bonus': 1, 'cost': 25},
            {'name': 'Chain Shirt', 'ac_bonus': 3, 'cost': 50},
            {'name': 'Breastplate', 'ac_bonus': 4, 'cost': 100},
            {'name': 'Half Plate', 'ac_bonus': 5, 'cost': 200},
        ],
        'shields': [
            {'name': 'Buckler', 'ac_bonus': 1, 'cost': 15},
            {'name': 'Shield', 'ac_bonus': 2, 'cost': 30},
        ],
        'potions': [
            {'name': 'Healing Potion', 'effect': '2d4+2 HP', 'cost': 50},
            {'name': 'Greater Healing Potion', 'effect': '4d4+4 HP', 'cost': 100},
            {'name': 'Potion of Strength', 'effect': '+2 STR (entire dungeon)', 'cost': 75},
            {'name': 'Potion of Dexterity', 'effect': '+4 Initiative (entire dungeon)', 'cost': 75},
            {'name': 'Potion of Protection', 'effect': '+2 AC (entire dungeon)', 'cost': 100},
        ],
        'scrolls': [
            {'name': 'Scroll of Fireball', 'effect': '6d6 fire damage to 3 targets', 'cost': 150},
            {'name': 'Scroll of Revive', 'effect': 'Revive fallen character', 'cost': 200},
            {'name': 'Scroll of Protection', 'effect': '+5 AC (entire dungeon)', 'cost': 100},
            {'name': 'Scroll of Haste', 'effect': '+5 Initiative (entire dungeon)', 'cost': 150},
        ],
        'magic_items': [
            {'name': '+1 Longsword', 'damage': '1d8+1', 'cost': 500, 'type': 'one-handed'},
            {'name': '+1 Dagger', 'damage': '1d4+1', 'cost': 300, 'type': 'one-handed'},
            {'name': '+1 Chain Shirt', 'ac_bonus': 4, 'cost': 400},
            {'name': 'Ring of Protection', 'effect': '+1 AC', 'cost': 350},
            {'name': 'Amulet of Health', 'effect': '+2 Constitution', 'cost': 450},
        ]
    }
    
    return inventory

def roll_dice(dice_str):
    """Roll dice based on string like '1d6' or '2d8'"""
    if 'd' not in dice_str:
        return int(dice_str)
    
    # Handle modifiers like "1d6+2"
    modifier = 0
    if '+' in dice_str:
        dice_part, mod_part = dice_str.split('+')
        dice_str = dice_part
        modifier = int(mod_part)
    
    num, sides = dice_str.split('d')
    num = int(num) if num else 1
    sides = int(sides)
    
    return sum(random.randint(1, sides) for _ in range(num)) + modifier

@app.route('/')
def home():
    # Check if a saved game exists
    save_exists = os.path.exists(os.path.join('saves', 'savegame.json'))
    return render_template('main_menu.html', save_exists=save_exists)

@app.route('/continue_game')
def continue_game():
    if load_game():
        return redirect(url_for('start_adventure'))
    else:
        return redirect(url_for('home'))

@app.route('/new_game')
def new_game():
    global characters, current_dungeon
    characters = []
    current_dungeon = None
    return redirect(url_for('create_party'))

@app.route('/create_party')
def create_party():
    try:
        # Define character classes with bonuses for display
        classes = {
            "Warrior": {
                "bonuses": {"strength": 2, "constitution": 2},
                "description": "Melee combat specialist with high HP"
            },
            "Rogue": {
                "bonuses": {"dexterity": 2, "intelligence": 1},
                "description": "Skilled at stealth and precision attacks"
            },
            "Mage": {
                "bonuses": {"intelligence": 2, "wisdom": 1},
                "description": "Arcane spellcaster with powerful offensive magic"
            },
            "Priest": {
                "bonuses": {"wisdom": 2, "charisma": 1},
                "description": "Divine spellcaster with healing and support spells"
            }
        }
        
        # Define races with bonuses for display
        races = {
            "Human": {
                "bonuses": {"strength": 1, "dexterity": 1, "constitution": 1, "intelligence": 1, "wisdom": 1, "charisma": 1},
                "description": "Versatile and adaptable"
            },
            "Elf": {
                "bonuses": {"dexterity": 2, "intelligence": 1, "wisdom": 1, "charisma": 1},
                "description": "Graceful and intelligent with keen senses"
            },
            "Dwarf": {
                "bonuses": {"constitution": 2, "strength": 2, "wisdom": 1},
                "description": "Sturdy and resilient miners and craftsmen"
            }
        }
        
        # Character portraits for each class
        portraits = {
            "Warrior": ["warrior_male_1.png", "warrior_female_1.png", "warrior_male_2.png"],
            "Rogue": ["rogue_male_1.png", "rogue_female_1.png", "rogue_male_2.png"],
            "Mage": ["mage_male_1.png", "mage_female_1.png", "mage_male_2.png"],
            "Priest": ["priest_male_1.png", "priest_female_1.png", "priest_male_2.png"]
        }
        
        return render_template('character_creation.html', 
                               classes=classes, 
                               races=races,
                               portraits=portraits)
    except Exception as e:
        return f"Error: {str(e)}"

@app.route('/create_character', methods=['POST'])
def create_character():
    name = request.form['name']
    char_class = request.form['char_class']
    race = request.form['race']
    portrait = request.form.get('portrait', '')
    
    # Create character dictionary
    character = {
        'name': name,
        'class': char_class,
        'race': race,
        'level': 1,
        'xp': 0,
        'portrait': portrait,
        'attributes': {
            'strength': 10,
            'dexterity': 10,
            'constitution': 10,
            'intelligence': 10,
            'wisdom': 10,
            'charisma': 10
        },
        'buffs': [] # Initialize buffs list
    }
    
    # Apply class bonuses
    if char_class in CLASS_BONUSES:
        for attr, bonus in CLASS_BONUSES[char_class].items():
            if attr in character['attributes']:
                character['attributes'][attr] += bonus
    
    # Apply race bonuses
    if race in RACE_BONUSES:
        for attr, bonus in RACE_BONUSES[race].items():
            if attr in character['attributes']:
                character['attributes'][attr] += bonus
    
    # Calculate HP
    base_hp = CLASS_BONUSES[char_class].get("base_hp", 8)
    con_modifier = (character['attributes']['constitution'] - 10) // 2
    character['hp'] = base_hp + con_modifier
    character['max_hp'] = character['hp']
    
    # Calculate base AC
    dex_modifier = (character['attributes']['dexterity'] - 10) // 2
    character['base_ac'] = 10 + dex_modifier
    
    # Initialize spell slots for spellcasters
    if char_class in ['Mage', 'Priest']:
        character['spell_slots'] = {
            'level_1': 2
        }
        character['current_spell_slots'] = {
            'level_1': 2
        }
    
    characters.append(character)
    
    # Redirect to equipment selection
    character_index = len(characters) - 1
    return redirect(url_for('choose_equipment', character_index=character_index))

@app.route('/choose_equipment/<int:character_index>')
def choose_equipment(character_index):
    if character_index >= len(characters):
        return redirect(url_for('view_party'))
    
    character = characters[character_index]
    
    # Define starting equipment based on class
    starting_equipment = {
        "Warrior": {
            "weapons": ["Longsword", "Battleaxe", "Warhammer", "Shortbow", "Greatsword"],
            "armor": ["Leather", "Chain Shirt"],
            "items": ["Shield", "Healing Potion"]
        },
        "Rogue": {
            "weapons": ["Shortsword", "Dagger", "Rapier", "Shortbow"],
            "armor": ["Leather"],
            "items": ["Buckler", "Healing Potion"]
        },
        "Mage": {
            "weapons": ["Staff", "Wand", "Dagger"],
            "armor": ["Robes"],
            "items": ["Healing Potion"]
        },
        "Priest": {
            "weapons": ["Mace", "Staff", "Warhammer"],
            "armor": ["Leather", "Chain Shirt"],
            "items": ["Shield", "Healing Potion"]
        }
    }
    
    # Get equipment options for this class
    equipment = starting_equipment.get(character['class'], {
        "weapons": ["Dagger"],
        "armor": ["Robes"],
        "items": ["Healing Potion"]
    })
    
    # Weapon properties (for display)
    weapon_properties = {
        "Longsword": {"damage": "1d8", "type": "one-handed", "description": "Versatile and reliable"},
        "Battleaxe": {"damage": "1d8", "type": "one-handed", "description": "Heavy chopping weapon"},
        "Warhammer": {"damage": "1d8", "type": "one-handed", "description": "Blunt force weapon"},
        "Shortbow": {"damage": "1d6", "type": "two-handed", "description": "Ranged weapon, effective up to 60 feet"},
        "Greatsword": {"damage": "2d6", "type": "two-handed", "description": "Large two-handed sword"},
        "Shortsword": {"damage": "1d6", "type": "one-handed", "description": "Fast, light weapon"},
        "Dagger": {"damage": "1d4", "type": "one-handed", "description": "Small, concealable blade"},
        "Rapier": {"damage": "1d8", "type": "one-handed", "description": "Elegant piercing weapon"},
        "Staff": {"damage": "1d6", "type": "two-handed", "description": "Simple wooden staff, good for spellcasting"},
        "Wand": {"damage": "1d4", "type": "one-handed", "description": "Focusing tool for spellcasters"},
        "Mace": {"damage": "1d6", "type": "one-handed", "description": "Blunt force weapon favored by clerics"}
    }
    
    # Armor properties (for display)
    armor_properties = {
        "Robes": {"ac_bonus": 0, "description": "Simple cloth garments with no protection"},
        "Leather": {"ac_bonus": 1, "description": "Hardened leather armor, light and flexible"},
        "Chain Shirt": {"ac_bonus": 3, "description": "Metal rings linked together, good protection"}
    }
    
    # Item properties (for display)
    item_properties = {
        "Shield": {"ac_bonus": 2, "description": "Wooden shield with metal reinforcement"},
        "Buckler": {"ac_bonus": 1, "description": "Small shield strapped to forearm"},
        "Healing Potion": {"effect": "2d4+2 HP", "description": "Restores health when consumed"}
    }
    
    return render_template('choose_equipment.html', 
                         character=character, 
                         equipment=equipment,
                         weapon_properties=weapon_properties,
                         armor_properties=armor_properties,
                         item_properties=item_properties,
                         character_index=character_index)

@app.route('/equip_character/<int:character_index>', methods=['POST'])
def equip_character(character_index):
    if character_index >= len(characters):
        return redirect(url_for('view_party'))
    
    character = characters[character_index]
    
    # Add equipment to character
    character['equipment'] = {
        'weapon': request.form['weapon'],
        'armor': request.form['armor'],
        'item': request.form['item']
    }
    
    # Calculate AC based on equipment
    base_ac = character['base_ac']
    
    # Armor bonus
    armor_bonuses = {
        "Robes": 0,
        "Leather": 1,
        "Chain Shirt": 3,
        "Breastplate": 4,
        "Half Plate": 5
    }
    armor_bonus = armor_bonuses.get(character['equipment']['armor'], 0)
    
    # Shield/item bonus
    shield_bonuses = {
        "Shield": 2,
        "Buckler": 1
    }
    shield_bonus = shield_bonuses.get(character['equipment']['item'], 0)
    
    character['ac'] = base_ac + armor_bonus + shield_bonus
    
    # Initialize inventory
    if 'inventory' not in character:
        character['inventory'] = []
    
    # Add shield to inventory if selected
    if character['equipment']['item'] in ["Shield", "Buckler"]:
        character['inventory'].append({
            'type': 'shield',
            'name': character['equipment']['item'],
            'ac_bonus': shield_bonus
        })
    
    # Add potions
    if character['equipment']['item'] == "Healing Potion":
        character['potions'] = 2
    else:
        character['potions'] = 1  # Everyone gets at least one
    
    # Initialize gold for the character
    character['gold'] = 50  # Starting gold
    
    # If this is a mage or priest, let them choose spells
    if character['class'] in ['Mage', 'Priest']:
        return redirect(url_for('choose_spells', character_index=character_index))
    else:
        return redirect(url_for('view_party'))

@app.route('/choose_spells/<int:character_index>')
def choose_spells(character_index):
    if character_index >= len(characters):
        return redirect(url_for('view_party'))
    
    character = characters[character_index]
    
    # Define starting spells based on class (showing updated spell details)
    if character['class'] == 'Mage':
        available_spells = [
            {"name": "Firebolt", "description": "A bolt of fire that deals 1d10 damage to a single target."},
            {"name": "Magic Missile", "description": "Always hits for 1d4+1 damage to a single target."},
            {"name": "Mage Armor", "description": "Increases AC by 3 for the entire dungeon."},
            {"name": "Burning Hands", "description": "Deals 3d6 fire damage to up to 3 targets."}
        ]
    elif character['class'] == 'Priest':
        available_spells = [
            {"name": "Lesser Heal", "description": "Heals a target for 1d8+2 HP."},
            {"name": "Bless", "description": "Grants a 1d4 attack bonus to up to 3 allies for the entire dungeon."},
            {"name": "Lesser Smite", "description": "Deals 2d6 holy damage to a single target."}
        ]
    else:
        available_spells = []
    
    # Number of spells they can choose
    num_spells = 2
    
    return render_template('choose_spells.html', 
                         character=character, 
                         spells=available_spells,
                         num_spells=num_spells,
                         character_index=character_index)

@app.route('/assign_spells/<int:character_index>', methods=['POST'])
def assign_spells(character_index):
    if character_index >= len(characters):
        return redirect(url_for('view_party'))
    
    character = characters[character_index]
    
    # Get selected spells
    selected_spells = request.form.getlist('spells')
    character['spells'] = selected_spells[:2]  # Limit to 2 spells
    
    return redirect(url_for('view_party'))

@app.route('/view_party')
def view_party():
    return render_template('party.html', characters=characters)

@app.route('/start_adventure')
def start_adventure():
    # Auto-save when returning to town
    save_game()
    return render_template('adventure.html', characters=characters)

@app.route('/enter_dungeon')
def enter_dungeon():
    global current_dungeon
    
    # Generate a random dungeon
    biome = random.choice(list(BIOMES.keys()))
    current_dungeon = {
        'biome': biome,
        'description': BIOMES[biome]['description'],
        'rooms': generate_dungeon_rooms(biome),
        'current_room': 0,
        'completed': False
    }
    
    return render_template('dungeon.html', 
                         dungeon=current_dungeon, 
                         characters=characters)

def generate_dungeon_rooms(biome):
    """Generate 3-5 rooms with enemies based on challenge rating"""
    rooms = []
    num_rooms = random.randint(3, 5)
    
    # Calculate party average level and adjust challenge rating
    avg_level = sum(char.get('level', 1) for char in characters) / len(characters)
    party_size_modifier = 0
    if len(characters) >= 5 and len(characters) <= 6:
        party_size_modifier = 1
    elif len(characters) >= 7:
        party_size_modifier = 2
    
    max_cr = avg_level + party_size_modifier
    
    for i in range(num_rooms):
        # Choose enemies that fit the challenge rating
        room_enemies = []
        total_cr = 0
        
        # Cap the challenge rating for the room
        room_max_cr = min(max_cr, 5)  # Cap at CR 5 for now
        
        # Keep adding enemies until we reach the target CR
        while total_cr < room_max_cr:
            # Filter enemies by CR
            valid_enemies = [name for name, data in ENEMIES.items() 
                           if data['cr'] <= room_max_cr - total_cr and 
                              name in BIOMES[biome]['enemies']]
            
            if not valid_enemies:
                break  # No more valid enemies to add
            
            enemy_name = random.choice(valid_enemies)
            enemy = ENEMIES[enemy_name].copy()
            enemy['name'] = enemy_name
            
            room_enemies.append(enemy)
            total_cr += enemy['cr']
            
            # Sometimes just one enemy is fine
            if total_cr > 0 and random.random() < 0.7:
                break
        
        room = {
            'number': i + 1,
            'description': f"Room {i + 1} of the {biome}",
            'enemies': room_enemies,
            'completed': False
        }
        rooms.append(room)
    
    return rooms

@app.route('/between_rooms')
def between_rooms():
    """Show the between rooms screen where players can use abilities and rest"""
    global current_dungeon
    
    if not current_dungeon:
        return redirect(url_for('start_adventure'))
    
    # You might want to add variables for short rests, etc.
    short_rests_remaining = 1  # Example value
    
    return render_template('between_rooms.html', 
                         characters=characters,
                         short_rests_remaining=short_rests_remaining)

@app.route('/use_ability_between_rooms/<int:character_index>/<string:ability_name>')
def use_ability_between_rooms(character_index, ability_name):
    """Handle using abilities between rooms"""
    if character_index >= len(characters):
        return redirect(url_for('between_rooms'))
    
    character = characters[character_index]
    target_index = request.args.get('target', type=int)
    
    if ability_name == "Lesser Heal" and target_index is not None and target_index < len(characters):
        # Handle healing spell
        target = characters[target_index]
        healing = roll_dice("1d8+2")
        target['hp'] = min(target['max_hp'], target['hp'] + healing)
        
        # Decrement spell slot
        if 'current_spell_slots' in character and 'level_1' in character['current_spell_slots']:
            character['current_spell_slots']['level_1'] -= 1
    
    return redirect(url_for('between_rooms'))

@app.route('/short_rest')
def short_rest():
    """Handle short rest mechanics"""
    global current_dungeon
    
    if not current_dungeon:
        return redirect(url_for('start_adventure'))
    
    # Heal characters
    for character in characters:
        # Heal 25% of max HP
        healing = character['max_hp'] // 4
        character['hp'] = min(character['max_hp'], character['hp'] + healing)
        
        # Restore some spell slots if character is a spellcaster
        if character['class'] in ['Mage', 'Priest'] and 'current_spell_slots' in character:
            for slot, value in character['current_spell_slots'].items():
                # Restore 1 spell slot of each level
                character['current_spell_slots'][slot] = min(
                    character['spell_slots'][slot], 
                    character['current_spell_slots'][slot] + 1
                )
    
    # Redirect back to between rooms
    return redirect(url_for('between_rooms'))

@app.route('/choose_dungeon')
def choose_dungeon():
    """Let players choose the challenge rating of their dungeon"""
    
    # Calculate the party's average level
    avg_level = sum(char.get('level', 1) for char in characters) / len(characters)
    
    # Available challenge ratings (up to party level + 2)
    available_cr = [0.5, 1, 2, 3, 4, 5]
    max_available_cr = min(5, int(avg_level) + 2)
    available_cr = [cr for cr in available_cr if cr <= max_available_cr]
    
    # Available biomes
    biomes = list(BIOMES.keys())
    
    return render_template('choose_dungeon.html',
                          available_cr=available_cr,
                          biomes=biomes,
                          characters=characters)

@app.route('/create_custom_dungeon', methods=['POST'])
def create_custom_dungeon():
    """Create a custom dungeon based on player choices"""
    global current_dungeon
    
    biome = request.form['biome']
    challenge_rating = float(request.form['challenge_rating'])
    
    if biome not in BIOMES:
        return redirect(url_for('choose_dungeon'))
    
    # Generate dungeon with specified challenge rating
    current_dungeon = {
        'biome': biome,
        'description': BIOMES[biome]['description'],
        'challenge_rating': challenge_rating,
        'rooms': generate_dungeon_rooms_with_cr(biome, challenge_rating),
        'current_room': 0,
        'completed': False
    }
    
    return render_template('dungeon.html', 
                         dungeon=current_dungeon, 
                         characters=characters)

def generate_dungeon_rooms_with_cr(biome, challenge_rating):
    """Generate 3-5 rooms with enemies based on specific challenge rating"""
    rooms = []
    num_rooms = random.randint(3, 5)
    
    for i in range(num_rooms):
        # Filter enemies by CR and biome
        valid_enemies = [name for name, data in ENEMIES.items() 
                        if data['cr'] <= challenge_rating and 
                           name in BIOMES[biome]['enemies']]
        
        if not valid_enemies:
            # Fallback to any enemies in this biome
            valid_enemies = BIOMES[biome]['enemies']
        
        # Create the room with multiple enemies
        room_enemies = []
        total_cr = 0
        remaining_cr = challenge_rating
        
        # Add enemies until we reach close to the target CR
        while total_cr < challenge_rating * 0.8 and remaining_cr > 0.25:
            # Select a random enemy that doesn't exceed remaining CR
            suitable_enemies = [name for name in valid_enemies if ENEMIES[name]['cr'] <= remaining_cr]
            
            if not suitable_enemies:
                break
                
            enemy_name = random.choice(suitable_enemies)
            enemy = ENEMIES[enemy_name].copy()
            enemy['name'] = enemy_name
            
            room_enemies.append(enemy)
            total_cr += enemy['cr']
            remaining_cr = challenge_rating - total_cr
            
            # Sometimes just one strong enemy is fine
            if random.random() < 0.3 and total_cr > 0:
                break
        
        room = {
            'number': i + 1,
            'description': f"Room {i + 1} of the {biome}",
            'enemies': room_enemies,
            'completed': False
        }
        rooms.append(room)
    
    return rooms

@app.route('/start_combat/<int:room_index>')
def start_combat(room_index):
    global current_combat, current_dungeon
    
    if not current_dungeon or room_index >= len(current_dungeon['rooms']):
        return redirect(url_for('start_adventure'))
    
    room = current_dungeon['rooms'][room_index]
    
    # Set up initiative order
    initiative_order = []
    
    # Add all characters to initiative order
    for i, character in enumerate(characters):
        # Roll initiative (d20 + dex modifier + initiative bonuses from buffs)
        dex_mod = (character['attributes']['dexterity'] - 10) // 2
        
        # Calculate initiative bonus from buffs
        initiative_bonus = 0
        if 'buffs' in character:
            for buff in character['buffs']:
                if 'initiative_bonus' in buff.get('effect', {}):
                    initiative_bonus += buff['effect']['initiative_bonus']
        
        initiative_roll = random.randint(1, 20) + dex_mod + initiative_bonus
        initiative_order.append({
            'type': 'character',
            'index': i,
            'initiative': initiative_roll,
            'acted': False
        })
    
    # Add all enemies to initiative order
    for i, enemy in enumerate(room['enemies']):
        # Default dexterity = 10
        enemy_dex = enemy.get('dexterity', 10)
        enemy_initiative = random.randint(1, 20) + (enemy_dex - 10) // 2
        initiative_order.append({
            'type': 'enemy',
            'enemy_index': i,
            'initiative': enemy_initiative,
            'acted': False
        })
    
    # Sort by initiative (highest first)
    initiative_order.sort(key=lambda x: x['initiative'], reverse=True)
    
    current_combat = {
        'enemies': room['enemies'],
        'room_index': room_index,
        'round': 1,
        'initiative_order': initiative_order,
        'current_actor_index': 0,
        'log': []
    }
    
    return render_template('combat.html', 
                         combat=current_combat, 
                         characters=characters)

@app.route('/combat_action')
def combat_action():
    global current_combat, current_dungeon
    
    if not current_combat:
        return redirect(url_for('start_adventure'))
    
    # Get current actor
    current_actor = current_combat['initiative_order'][current_combat['current_actor_index']]
    
    # Show action selection screen
    if current_actor['type'] == 'character':
        character_index = current_actor['index']
        character = characters[character_index]
        
        # Check if character can act (not at 0 HP)
        if character['hp'] <= 0:
            # Skip this character's turn
            current_combat['log'].append(f"{character['name']} is unconscious and cannot act.")
            
            # Mark actor as having acted
            current_actor['acted'] = True
            
            # Move to next actor
            next_actor()
            
            # Check if we need to start a new round
            if all(actor['acted'] for actor in current_combat['initiative_order']):
                start_new_round()
            
            # Redirect based on next actor
            if current_combat['initiative_order'][current_combat['current_actor_index']]['type'] == 'character':
                return redirect(url_for('combat_action'))
            else:
                return handle_enemy_turn()
        
        # Add the index to the character data
        character_data = character.copy()
        character_data['index'] = character_index
        
        # Get available attacks
        attacks = []
        if 'equipment' in character and 'weapon' in character['equipment']:
            weapon = character['equipment']['weapon']
            
            # For each enemy, create an attack option
            for i, enemy in enumerate(current_combat['enemies']):
                if enemy['hp'] > 0:  # Only target living enemies
                    attacks.append({
                        'name': weapon,
                        'type': 'weapon',
                        'hit_chance': calculate_hit_chance(character, enemy),
                        'damage': get_weapon_damage(character, weapon),
                        'target_index': i,
                        'target_name': enemy['name']
                    })
        
        # Get available spells
        spells = []
        if 'spells' in character:
            for spell_name in character['spells']:
                spell = SPELLS.get(spell_name)
                if not spell:
                    continue
                
                # Check if character has required spell slots
                spell_level = spell.get('level', 1)
                slot_name = f"level_{spell_level}"
                
                if character['current_spell_slots'].get(slot_name, 0) <= 0:
                    continue  # No spell slots remaining
                
                if spell['type'] == 'damage':
                    # For damage spells, create an option for each enemy
                    # For AOE spells, we'll handle multiple targets in the route
                    for i, enemy in enumerate(current_combat['enemies']):
                        if enemy['hp'] > 0:  # Only target living enemies
                            spells.append({
                                'name': spell_name,
                                'type': 'spell',
                                'hit_chance': 100 if spell.get('always_hits') else calculate_spell_hit_chance(character, enemy, spell_name),
                                'damage': spell['damage'],
                                'targets': spell['targets'],
                                'target_index': i,
                                'target_name': enemy['name'],
                                'level': spell_level
                            })
                
                elif spell['type'] == 'healing':
                    # For healing spells, create an option for each character
                    for i, target in enumerate(characters):
                        if target['hp'] < target['max_hp']:  # Only include if healing is needed
                            spells.append({
                                'name': spell_name,
                                'type': 'spell',
                                'hit_chance': 100,
                                'healing': spell['healing'],
                                'targets': spell['targets'],
                                'target_index': i,
                                'target_name': target['name'],
                                'level': spell_level
                            })
                
                elif spell['type'] == 'buff':
                    # For buff spells, create options based on targets
                    for i, target in enumerate(characters):
                        if target['hp'] > 0:  # Only buff living characters
                            spells.append({
                                'name': spell_name,
                                'type': 'spell',
                                'hit_chance': 100,
                                'effect': spell['effect'],
                                'duration': spell.get('duration'),
                                'targets': spell['targets'],
                                'target_index': i,
                                'target_name': target['name'],
                                'level': spell_level
                            })
                
                elif spell['type'] == 'revive':
                    # For revive spells, create an option for each defeated character
                    for i, target in enumerate(characters):
                        if target['hp'] <= 0:  # Only include defeated characters
                            spells.append({
                                'name': spell_name,
                                'type': 'spell',
                                'hit_chance': 100,
                                'target_index': i,
                                'target_name': target['name'],
                                'level': spell_level
                            })
        
        # Check if character has potions
        has_potions = character.get('potions', 0) > 0
        
        return render_template('combat_action.html',
                             character=character_data,
                             attacks=attacks,
                             spells=spells,
                             has_potions=has_potions,
                             combat=current_combat,
                             enemies=current_combat['enemies'])
    else:
        # Enemy's turn - handle automatically
        return handle_enemy_turn()

def calculate_hit_chance(character, enemy):
    """Calculate hit chance percentage"""
    # Base 65% chance
    base_chance = 65
    
    # Add attribute modifier
    if character['equipment']['weapon'] in ['Shortbow', 'Dagger', 'Rapier']:
        # Dex-based weapons
        attr_mod = (character['attributes']['dexterity'] - 10) // 2
    else:
        # Str-based weapons
        attr_mod = (character['attributes']['strength'] - 10) // 2
    
    # Apply any attack bonuses from buffs
    attack_bonus = 0
    if 'buffs' in character:
        for buff in character['buffs']:
            if 'attack_bonus' in buff.get('effect', {}):
                # If attack bonus is a dice string, roll it
                bonus = buff['effect']['attack_bonus']
                if isinstance(bonus, str) and 'd' in bonus:
                    attack_bonus += roll_dice(bonus)
                else:
                    attack_bonus += bonus
    
    # Hit formula: base_chance + (attr_mod * 5) + attack_bonus - (enemy_ac - 10) * 5
    hit_chance = base_chance + (attr_mod * 5) + attack_bonus - (enemy['ac'] - 10) * 5
    
    # Clamp between 5% and 95%
    return max(5, min(95, hit_chance))

def calculate_spell_hit_chance(character, enemy, spell_name):
    """Calculate spell hit chance percentage"""
    # Determine which attribute to use
    if character['class'] == 'Mage':
        attr_mod = (character['attributes']['intelligence'] - 10) // 2
    else:  # Priest
        attr_mod = (character['attributes']['wisdom'] - 10) // 2
    
    # Base 70% chance for spells
    base_chance = 70
    hit_chance = base_chance + (attr_mod * 5)
    
    # Some spells always hit
    spell = SPELLS.get(spell_name, {})
    if spell.get('always_hits', False):
        return 100
    
    # Clamp between 5% and 95%
    return max(5, min(95, hit_chance))

def get_weapon_damage(character, weapon):
    """Get damage dice for weapon with character modifiers"""
    weapon_damage = {
        "Longsword": "1d8",
        "Battleaxe": "1d8",
        "Warhammer": "1d8",
        "Shortbow": "1d6",
        "Shortsword": "1d6",
        "Dagger": "1d4",
        "Rapier": "1d8",
        "Staff": "1d6",
        "Wand": "1d4",
        "Mace": "1d6",
        "Greatsword": "2d6"
    }
    
    # Check for magic weapons that add a bonus
    if weapon.startswith('+'):
        for item in character.get('inventory', []):
            if item.get('name') == weapon and 'bonus' in item:
                bonus = item['bonus']
                base_weapon = weapon[2:]  # Remove the "+X " prefix
                base_damage = weapon_damage.get(base_weapon, "1d4")
                return f"{base_damage}+{bonus}"
    
    return weapon_damage.get(weapon, "1d4")

@app.route('/perform_attack/<string:attack_type>/<string:attack_name>')
def perform_attack(attack_type, attack_name):
    global current_combat, current_dungeon
    
    if not current_combat:
        return redirect(url_for('start_adventure'))
    
    # Get target index from query parameter
    target_index = request.args.get('target', type=int)
    if target_index is None:
        return redirect(url_for('combat_action'))
    
    # Get current actor
    current_actor_index = current_combat['current_actor_index']
    current_actor = current_combat['initiative_order'][current_actor_index]
    
    if current_actor['type'] != 'character':
        return redirect(url_for('combat_action'))
    
    character = characters[current_actor['index']]
    
    # Handle different attack types
    if attack_type == 'weapon':
        # Single target weapon attack
        if target_index >= len(current_combat['enemies']):
            return redirect(url_for('combat_action'))
        
        enemy = current_combat['enemies'][target_index]
        
        # Roll to hit
        hit_chance = calculate_hit_chance(character, enemy)
        roll = random.randint(1, 100)
        hit = roll <= hit_chance
        
        if hit:
            # Roll damage
            damage = roll_dice(get_weapon_damage(character, attack_name))
            enemy['hp'] -= damage
            
            # Log the action
            current_combat['log'].append(f"{character['name']} hits {enemy['name']} with {attack_name} for {damage} damage!")
        else:
            # Log the miss
            current_combat['log'].append(f"{character['name']} misses {enemy['name']} with {attack_name}!")
    
    elif attack_type == 'spell':
        # Get spell details
        spell = SPELLS.get(attack_name)
        if not spell:
            return redirect(url_for('combat_action'))
        
        # Check if character has required spell slots
        spell_level = spell.get('level', 1)
        slot_name = f"level_{spell_level}"
        
        if character['current_spell_slots'].get(slot_name, 0) <= 0:
            current_combat['log'].append(f"{character['name']} doesn't have enough {slot_name.replace('_', ' ')} spell slots!")
            return redirect(url_for('combat_action'))
        
        # Use spell slot
        character['current_spell_slots'][slot_name] -= 1
        
        # Handle different spell types
        if spell['type'] == 'damage':
            # Get primary target
            if target_index >= len(current_combat['enemies']):
                return redirect(url_for('combat_action'))
            
            primary_target = current_combat['enemies'][target_index]
            
            # Determine how many targets to hit (AOE spells can hit multiple)
            num_targets = min(spell['targets'], len(current_combat['enemies']))
            
            # Start with the primary target
            targets = [primary_target]
            
            # Add additional targets for AOE spells
            if num_targets > 1:
                # Get other living enemies besides the primary target
                other_enemies = [e for i, e in enumerate(current_combat['enemies']) 
                               if e['hp'] > 0 and i != target_index]
                
                # Add up to the spell's target limit
                targets.extend(other_enemies[:num_targets-1])
            
            # Process each target
            for enemy in targets:
                # Roll to hit unless the spell always hits
                if spell.get('always_hits', False):
                    hit = True
                else:
                    hit_chance = calculate_spell_hit_chance(character, enemy, attack_name)
                    roll = random.randint(1, 100)
                    hit = roll <= hit_chance
                
                if hit:
                    # Roll damage
                    damage = roll_dice(spell['damage'])
                    enemy['hp'] -= damage
                    
                    # Log the action
                    current_combat['log'].append(f"{character['name']} hits {enemy['name']} with {attack_name} for {damage} damage!")
                else:
                    # Log the miss
                    current_combat['log'].append(f"{character['name']} misses {enemy['name']} with {attack_name}!")
        
        elif spell['type'] == 'healing':
            # Get primary target
            if target_index >= len(characters):
                return redirect(url_for('combat_action'))
            
            primary_target = characters[target_index]
            
            # Determine how many targets to heal (AOE spells can heal multiple)
            num_targets = min(spell['targets'], len(characters))
            
            # Start with the primary target
            targets = [primary_target]
            
            # Add additional targets for AOE spells
            if num_targets > 1:
                # Prioritize characters with lowest HP percentage
                other_characters = [(i, c) for i, c in enumerate(characters) 
                                   if i != target_index and c['hp'] > 0 and c['hp'] < c['max_hp']]
                
                # Sort by HP percentage
                other_characters.sort(key=lambda x: x[1]['hp'] / x[1]['max_hp'])
                
                # Add up to the spell's target limit
                targets.extend([c for _, c in other_characters[:num_targets-1]])
            
            # Process each target
            for target in targets:
                # Roll healing
                healing = roll_dice(spell['healing'])
                old_hp = target['hp']
                target['hp'] = min(target['max_hp'], target['hp'] + healing)
                actual_healing = target['hp'] - old_hp
                
                # Log the action
                current_combat['log'].append(f"{character['name']} heals {target['name']} for {actual_healing} HP with {attack_name}!")
        
        elif spell['type'] == 'buff':
            # Get primary target
            if target_index >= len(characters):
                return redirect(url_for('combat_action'))
            
            primary_target = characters[target_index]
            
            # Determine how many targets to buff
            num_targets = min(spell['targets'], len(characters))
            
            # Start with the primary target
            targets = [primary_target]
            
            # Add additional targets for multi-target buffs
            if num_targets > 1:
                # Get other living characters besides the primary target
                other_characters = [c for i, c in enumerate(characters) 
                                   if c['hp'] > 0 and i != target_index]
                
                # Add up to the spell's target limit
                targets.extend(other_characters[:num_targets-1])
            
            # Process each target
            for target in targets:
                # Initialize buffs list if it doesn't exist
                if 'buffs' not in target:
                    target['buffs'] = []
                
                # Add the buff
                target['buffs'].append({
                    'name': attack_name,
                    'effect': spell['effect'],
                    'duration': spell.get('duration', 'combat')
                })
                
                # Log the action
                current_combat['log'].append(f"{character['name']} casts {attack_name} on {target['name']}!")
        
        elif spell['type'] == 'revive':
            # Get target
            if target_index >= len(characters):
                return redirect(url_for('combat_action'))
            
            target = characters[target_index]
            
            # Can only revive defeated characters
            if target['hp'] > 0:
                current_combat['log'].append(f"{target['name']} is already conscious!")
                return redirect(url_for('combat_action'))
            
            # Revive with 1 HP
            target['hp'] = 1
            
            # Log the action
            current_combat['log'].append(f"{character['name']} revives {target['name']} with {attack_name}!")
    
    # Mark actor as having acted
    current_actor['acted'] = True
    
    # Move to next actor
    next_actor()
    
    # Check if all enemies are defeated
    if all(enemy['hp'] <= 0 for enemy in current_combat['enemies']):
        room_index = current_combat['room_index']
        current_dungeon['rooms'][room_index]['completed'] = True
        
        # Calculate gold and XP rewards
        total_gold = sum(enemy['gold'] for enemy in current_combat['enemies'])
        total_xp = award_combat_xp(current_combat['enemies'])
        
        # Divide gold among characters
        gold_per_character = total_gold // len(characters)
        for char in characters:
            char['gold'] = char.get('gold', 0) + gold_per_character
        
        return render_template('victory.html', 
                             enemies=current_combat['enemies'], 
                             characters=characters,
                             room_index=room_index,
                             total_gold=total_gold,
                             total_xp=total_xp)
    
    # Check if we need to start a new round
    if all(actor['acted'] for actor in current_combat['initiative_order']):
        start_new_round()
    
    # Redirect based on next actor
    if current_combat['initiative_order'][current_combat['current_actor_index']]['type'] == 'character':
        return redirect(url_for('combat_action'))
    else:
        return handle_enemy_turn()

def handle_enemy_turn():
    """Process the enemy's turn"""
    global current_combat
    
    if not current_combat:
        return redirect(url_for('start_adventure'))
    
    # Get the enemy that's acting
    current_actor = current_combat['initiative_order'][current_combat['current_actor_index']]
    enemy_index = current_actor.get('enemy_index', 0)
    
    if enemy_index >= len(current_combat['enemies']):
        # Invalid enemy index, move to next actor
        current_actor['acted'] = True
        next_actor()
        return redirect(url_for('combat_action'))
    
    enemy = current_combat['enemies'][enemy_index]
    
    # Check if enemy is already defeated
    if enemy['hp'] <= 0:
        # Skip this enemy's turn
        current_combat['log'].append(f"{enemy['name']} is defeated and cannot act.")
        current_actor['acted'] = True
        next_actor()
        
        # Check if we need to start a new round
        if all(actor['acted'] for actor in current_combat['initiative_order']):
            start_new_round()
        
        # Redirect based on next actor
        if current_combat['initiative_order'][current_combat['current_actor_index']]['type'] == 'character':
            return redirect(url_for('combat_action'))
        else:
            return handle_enemy_turn()
    
    # Select a random living character to attack
    living_characters = [i for i, char in enumerate(characters) if char['hp'] > 0]
    if not living_characters:
        # All characters are defeated
        return render_template('game_over.html')
    
    target_index = random.choice(living_characters)
    target = characters[target_index]
    
    # Roll to hit
    attack_roll = random.randint(1, 20)
    
    # Calculate AC including buffs
    target_ac = target['ac']
    if 'buffs' in target:
        for buff in target['buffs']:
            if 'ac_bonus' in buff.get('effect', {}):
                target_ac += buff['effect']['ac_bonus']
    
    hit = attack_roll >= target_ac
    
    damage = 0
    if hit:
        # Roll damage
        damage = roll_dice(enemy['damage'])
        target['hp'] -= damage
        # Check if character is defeated
        if target['hp'] <= 0:
            target['hp'] = 0
    
    # Log the action
    if hit:
        current_combat['log'].append(f"{enemy['name']} hits {target['name']} for {damage} damage!")
    else:
        current_combat['log'].append(f"{enemy['name']} misses {target['name']}!")
    
    # Mark enemy as having acted
    current_actor['acted'] = True
    
    # Move to next actor
    next_actor()
    
    # Check if we need to start a new round
    if all(actor['acted'] for actor in current_combat['initiative_order']):
        start_new_round()
    
    # Check if all characters are defeated
    if all(char['hp'] <= 0 for char in characters):
        return render_template('game_over.html')
    
    # Continue combat
    return redirect(url_for('combat_action'))

def next_actor():
    """Move to the next actor in initiative order"""
    global current_combat
    
    current_combat['current_actor_index'] = (current_combat['current_actor_index'] + 1) % len(current_combat['initiative_order'])

def start_new_round():
    """Start a new combat round"""
    global current_combat
    
    current_combat['round'] += 1
    for actor in current_combat['initiative_order']:
        actor['acted'] = False
    
    current_combat['log'].append(f"=== Round {current_combat['round']} ===")
    
    # Process buffs with combat duration at the start of each round
    for character in characters:
        if 'buffs' in character:
            # Remove expired combat-duration buffs
            character['buffs'] = [buff for buff in character['buffs'] if buff.get('duration') != 'combat']

@app.route('/use_potion/<int:character_index>')
def use_potion(character_index):
    """Use a healing potion"""
    global current_combat
    
    if not current_combat:
        return redirect(url_for('start_adventure'))
    
    character = characters[character_index]
    
    # Check if character has potions
    potions = character.get('potions', 0)
    if potions <= 0:
        current_combat['log'].append(f"{character['name']} has no potions!")
        return redirect(url_for('combat_action'))
    
    # Use potion
    healing = roll_dice("2d4+2")
    character['hp'] = min(character['max_hp'], character['hp'] + healing)
    character['potions'] = potions - 1
    
    current_combat['log'].append(f"{character['name']} drinks a potion and heals {healing} HP!")
    
    # Mark actor as having acted
    current_actor = current_combat['initiative_order'][current_combat['current_actor_index']]
    current_actor['acted'] = True
    
    # Move to next actor
    next_actor()
    
    # Check if we need to start a new round
    if all(actor['acted'] for actor in current_combat['initiative_order']):
        start_new_round()
    
    # Continue combat
    return redirect(url_for('combat_action'))

@app.route('/next_room')
def next_room():
    global current_dungeon
    
    if not current_dungeon:
        return redirect(url_for('start_adventure'))
    
    current_dungeon['current_room'] += 1
    
    if current_dungeon['current_room'] >= len(current_dungeon['rooms']):
        # Dungeon completed!
        return render_template('dungeon_complete.html', 
                             dungeon=current_dungeon, 
                             characters=characters)
    
    return render_template('dungeon.html', 
                         dungeon=current_dungeon, 
                         characters=characters)

@app.route('/exit_dungeon')
def exit_dungeon():
    """Exit the current dungeon and return to town"""
    global current_dungeon
    
    # Clear dungeon-duration buffs when leaving
    clear_dungeon_buffs()
    
    current_dungeon = None
    return redirect(url_for('start_adventure'))

@app.route('/visit_inn')
def visit_inn():
    """Visit the inn for rest and quests"""
    return render_template('inn.html', characters=characters)

@app.route('/rest_at_inn')
def rest_at_inn():
    """Rest at the inn to fully heal all characters"""
    # Calculate total cost (50 gold)
    rest_cost = 50
    
    # Check if party has enough gold
    total_gold = sum(char.get('gold', 0) for char in characters)
    
    if total_gold < rest_cost:
        # Not enough gold
        return render_template('inn.html', 
                              characters=characters,
                              error=f"Your party needs {rest_cost} gold to rest at the inn.")
    
    # Distribute the cost among characters
    cost_per_character = rest_cost // len(characters)
    remainder = rest_cost % len(characters)
    
    for i, character in enumerate(characters):
        # Add remainder to first character
        char_cost = cost_per_character + (remainder if i == 0 else 0)
        
        if character.get('gold', 0) >= char_cost:
            character['gold'] -= char_cost
        else:
            # Character doesn't have enough, take what they have
            remainder = char_cost - character.get('gold', 0)
            character['gold'] = 0
            
            # Distribute remainder to next character
            if i < len(characters) - 1:
                characters[i+1]['gold'] = characters[i+1].get('gold', 0) - remainder
    
    # Heal all characters
    for character in characters:
        character['hp'] = character['max_hp']
        
        # Reset spell slots if character is a spellcaster
        if character['class'] in ['Mage', 'Priest'] and 'spell_slots' in character:
            for slot in character['current_spell_slots']:
                character['current_spell_slots'][slot] = character['spell_slots'][slot]
    
    return redirect(url_for('start_adventure'))

@app.route('/get_quest')
def get_quest():
    """Get a special quest with bonus rewards"""
    global current_dungeon
    
    # Generate a more challenging dungeon with better rewards
    biome = random.choice(list(BIOMES.keys()))
    
    # Calculate party average level for challenge rating
    avg_level = sum(char.get('level', 1) for char in characters) / len(characters)
    quest_cr = min(5, avg_level + 1)  # Slightly more challenging
    
    current_dungeon = {
        'biome': biome,
        'description': f"Special Quest: {BIOMES[biome]['description']}",
        'rooms': generate_dungeon_rooms_with_cr(biome, quest_cr),
        'current_room': 0,
        'completed': False,
        'is_quest': True,
        'bonus_rewards': generate_quest_rewards(quest_cr)
    }
    
    return render_template('dungeon.html', 
                         dungeon=current_dungeon, 
                         characters=characters)

@app.route('/visit_shop')
def visit_shop():
    """Visit the shop to buy items"""
    # Get character index from query parameter
    character_index = request.args.get('character_index', type=int)
    
    # Validate character index
    if character_index is not None and (character_index < 0 or character_index >= len(characters)):
        character_index = None
    
    # Get error message from query parameter
    error = request.args.get('error')
    
    # Generate shop inventory
    shop_inventory = generate_shop_inventory()
    
    return render_template('shop.html', 
                         characters=characters, 
                         inventory=shop_inventory,
                         selected_character_index=character_index,
                         error=error)

@app.route('/buy_item/<string:item_type>/<string:item_name>/<int:character_index>')
def buy_item(item_type, item_name, character_index):
    """Purchase an item from the shop"""
    if character_index >= len(characters):
        return redirect(url_for('visit_shop'))
    
    character = characters[character_index]
    
    # Generate shop inventory to check price
    shop_inventory = generate_shop_inventory()
    
    # Find the item and its cost
    item = None
    if item_type in shop_inventory:
        for shop_item in shop_inventory[item_type]:
            if shop_item['name'] == item_name:
                item = shop_item
                break
    
    if not item:
        return redirect(url_for('visit_shop'))
    
    # Check if character has enough gold
    if character.get('gold', 0) < item['cost']:
        # Not enough gold
        return redirect(url_for('visit_shop', 
                              character_index=character_index,
                              error=f"{character['name']} doesn't have enough gold!"))
    
    # Purchase the item
    character['gold'] -= item['cost']
    
    # Add the item to character's inventory
    if 'inventory' not in character:
        character['inventory'] = []
    
    # Handle different item types
    if item_type == 'potions':
        # Add to potion count
        character['potions'] = character.get('potions', 0) + 1
        
        # Also add to inventory for reference
        character['inventory'].append(item.copy())
    elif item_type == 'weapons':
        # Add to inventory and equip if desired
        character['inventory'].append(item.copy())
        
        # Optionally equip the weapon
        character['equipment']['weapon'] = item['name']
    elif item_type == 'armor':
        # Add to inventory and equip if desired
        character['inventory'].append(item.copy())
        
        # Optionally equip the armor and update AC
        old_armor = character['equipment']['armor']
        character['equipment']['armor'] = item['name']
        
        # Recalculate AC
        old_armor_bonus = {
            "Robes": 0,
            "Leather": 1,
            "Chain Shirt": 3,
            "Breastplate": 4,
            "Half Plate": 5
        }.get(old_armor, 0)
        
        character['ac'] = character['ac'] - old_armor_bonus + item['ac_bonus']
    elif item_type == 'shields':
        # Add to inventory and equip if desired
        character['inventory'].append(item.copy())
        
        # Optionally equip the shield and update AC
        old_shield = character['equipment'].get('item')
        character['equipment']['item'] = item['name']
        
        # Recalculate AC if changing shields
        old_shield_bonus = {
            "Shield": 2,
            "Buckler": 1
        }.get(old_shield, 0)
        
        character['ac'] = character['ac'] - old_shield_bonus + item['ac_bonus']
    elif item_type == 'scrolls':
        # Add to inventory for later use
        character['inventory'].append(item.copy())
    elif item_type == 'magic_items':
        # Add to inventory and apply effects if needed
        character['inventory'].append(item.copy())
        
        # Some magic items might be equipped
        if 'type' in item and item['type'] == 'one-handed':
            # It's a weapon, can be equipped
            character['equipment']['weapon'] = item['name']
    
    return redirect(url_for('visit_shop', character_index=character_index))

@app.route('/view_character/<int:character_index>')
def view_character(character_index):
    """View detailed character information"""
    if character_index >= len(characters):
        return redirect(url_for('start_adventure'))
    
    character = characters[character_index]
    
    # Calculate XP needed for next level
    current_level = character.get('level', 1)
    next_level_xp = calculate_next_level_xp(current_level)
    current_xp = character.get('xp', 0)
    
    # Check if character can level up
    can_level_up = current_xp >= next_level_xp
    
    return render_template('character_detail.html', 
                         character=character, 
                         character_index=character_index,
                         next_level_xp=next_level_xp,
                         can_level_up=can_level_up)

@app.route('/level_up/<int:character_index>')
def level_up(character_index):
    """Level up a character"""
    if character_index >= len(characters):
        return redirect(url_for('start_adventure'))
    
    character = characters[character_index]
    current_level = character.get('level', 1)
    current_xp = character.get('xp', 0)
    
    # Calculate XP needed for next level
    next_level_xp = calculate_next_level_xp(current_level)
    
    # Check if character has enough XP
    if current_xp < next_level_xp:
        return redirect(url_for('view_character', character_index=character_index))
    
    # Level up the character
    character['level'] = current_level + 1
    
    # Increase max HP
    class_hp_gain = {
        'Warrior': 10,
        'Rogue': 8,
        'Mage': 6,
        'Priest': 8
    }
    
    hp_gain = class_hp_gain.get(character['class'], 8)
    con_modifier = (character['attributes']['constitution'] - 10) // 2
    character['max_hp'] += hp_gain + con_modifier
    character['hp'] = character['max_hp']  # Heal to full on level up
    
    # Add spell slots for spellcasters
    if character['class'] in ['Mage', 'Priest']:
        # Every odd level, gain a 2nd level spell slot
        if (current_level + 1) % 2 == 1 and current_level + 1 >= 3:
            if 'level_2' not in character['spell_slots']:
                character['spell_slots']['level_2'] = 1
                character['current_spell_slots']['level_2'] = 1
            else:
                character['spell_slots']['level_2'] += 1
                character['current_spell_slots']['level_2'] += 1
        
        # Otherwise, gain a 1st level spell slot
        else:
            character['spell_slots']['level_1'] += 1
            character['current_spell_slots']['level_1'] += 1
        
        # At level 5, gain access to 3rd level spells
        if current_level + 1 == 5:
            character['spell_slots']['level_3'] = 1
            character['current_spell_slots']['level_3'] = 1
            
            # Add a new spell
            if character['class'] == 'Mage':
                if 'Fireball' not in character['spells']:
                    character['spells'].append('Fireball')
            elif character['class'] == 'Priest':
                if 'Mass Healing Word' not in character['spells']:
                    character['spells'].append('Mass Healing Word')
    
    return redirect(url_for('view_character', character_index=character_index))

@app.route('/use_scroll/<int:character_index>/<int:item_index>')
def use_scroll(character_index, item_index):
    """Use a scroll from inventory"""
    if character_index >= len(characters):
        return redirect(url_for('start_adventure'))
    
    character = characters[character_index]
    
    if 'inventory' not in character or item_index >= len(character['inventory']):
        return redirect(url_for('view_character', character_index=character_index))
    
    item = character['inventory'][item_index]
    
    # Check if it's actually a scroll
    if 'name' not in item or not item['name'].startswith('Scroll of'):
        return redirect(url_for('view_character', character_index=character_index))
    
    # Handle different scroll types
    scroll_name = item['name']
    
    if scroll_name == 'Scroll of Fireball':
        # Used in combat, should save for combat
        # Just show a message for now
        return render_template('character_detail.html',
                            character=character,
                            character_index=character_index,
                            message=f"This scroll can only be used in combat.")
    
    elif scroll_name == 'Scroll of Revive':
        # Can revive a fallen character
        # Show a list of fallen characters to choose from
        fallen_characters = [(i, char) for i, char in enumerate(characters) if char['hp'] <= 0]
        
        if not fallen_characters:
            return render_template('character_detail.html',
                                character=character,
                                character_index=character_index,
                                message=f"There are no fallen characters to revive.")
        
        return render_template('use_scroll.html',
                            scroll=item,
                            character=character,
                            character_index=character_index,
                            targets=fallen_characters)
    
    elif scroll_name == 'Scroll of Protection':
        # Apply buff to character
        if 'buffs' not in character:
            character['buffs'] = []
        
        character['buffs'].append({
            'name': 'Protection',
            'effect': {'ac_bonus': 5},
            'duration': 'dungeon'
        })
        
        # Remove scroll from inventory
        character['inventory'].pop(item_index)
        
        return render_template('character_detail.html',
                            character=character,
                            character_index=character_index,
                            message=f"You used {scroll_name}. +5 AC buff will apply in your next dungeon.")
    
    elif scroll_name == 'Scroll of Haste':
        # Apply buff to character
        if 'buffs' not in character:
            character['buffs'] = []
        
        character['buffs'].append({
            'name': 'Haste',
            'effect': {'initiative_bonus': 5},
            'duration': 'dungeon'
        })
        
        # Remove scroll from inventory
        character['inventory'].pop(item_index)
        
        return render_template('character_detail.html',
                            character=character,
                            character_index=character_index,
                            message=f"You used {scroll_name}. +5 Initiative buff will apply in your next dungeon.")
    
    # Default case
    return redirect(url_for('view_character', character_index=character_index))

@app.route('/use_scroll_target/<int:character_index>/<int:item_index>/<int:target_index>')
def use_scroll_target(character_index, item_index, target_index):
    """Use a scroll on a specific target"""
    if character_index >= len(characters) or target_index >= len(characters):
        return redirect(url_for('start_adventure'))
    
    character = characters[character_index]
    target = characters[target_index]
    
    if 'inventory' not in character or item_index >= len(character['inventory']):
        return redirect(url_for('view_character', character_index=character_index))
    
    item = character['inventory'][item_index]
    
    # Check if it's actually a scroll
    if 'name' not in item or not item['name'].startswith('Scroll of'):
        return redirect(url_for('view_character', character_index=character_index))
    
    # Handle the scroll effect
    scroll_name = item['name']
    
    if scroll_name == 'Scroll of Revive':
        # Revive the target character
        if target['hp'] <= 0:
            target['hp'] = target['max_hp'] // 2  # Revive with half HP
            
            # Remove scroll from inventory
            character['inventory'].pop(item_index)
            
            return render_template('character_detail.html',
                                character=character,
                                character_index=character_index,
                                message=f"You used {scroll_name} to revive {target['name']}.")
    
    # Default case
    return redirect(url_for('view_character', character_index=character_index))

@app.route('/debug')
def debug():
    import os
    template_dir = os.path.join(app.root_path, 'templates')
    files = os.listdir(template_dir) if os.path.exists(template_dir) else []
    return f"Template directory: {template_dir}<br>Files: {files}"

@app.route('/test')
def test():
    return render_template('test.html')

if __name__ == '__main__':
    app.run(debug=True)