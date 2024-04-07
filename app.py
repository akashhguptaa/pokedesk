import requests
import os
import time

database_id = os.environ.get('NOTION_DATABASE')
notion_api_key = os.environ.get('NOTION_API_KEY')

poke_array = []

def get_pokemon():
    #A start point of fetching the pokemon and an ending point of 1000, though there are 1026 regiistered pokemons in the poke_api
    start = 1
    end = 1000
    for i in range(start, end + 1):
        poke_response = requests.get(f"https://pokeapi.co/api/v2/pokemon/{i}")
        poke_data = poke_response.json()

        types_array = [{"name": type_data['type']['name']} for type_data in poke_data['types']]

        processed_name = " ".join([word.capitalize() for word in poke_data['species']['name'].split("-")])
        processed_name = processed_name.replace('Mr M', 'Mr. M').replace('Mime Jr', 'Mime Jr.').replace('Mr R', 'Mr. R') \
            .replace('mo O', 'mo-o').replace('Porygon Z', 'Porygon-Z').replace('Type Null', 'Type: Null') \
            .replace('Ho Oh', 'Ho-Oh').replace('Nidoran F', 'Nidoran♀').replace('Nidoran M', 'Nidoran♂') \
            .replace('Flabebe', 'Flabébé')

        #bulbapedia is pokemon website where there is a detailed data of pokemon available
        bulb_url = f"https://bulbapedia.bulbagarden.net/wiki/{processed_name.replace(' ', '_')}_Pokémon"

        #its the image of the pokemon that will be displayed on your database
        sprite = poke_data['sprites']['front_default'] or poke_data['sprites']['other']['official-artwork']['front_default']

        #Dictionary for all the data, that we are about to use in our notion database
        poke_data = {
            "name": processed_name,
            "number": poke_data['id'],
            "types": types_array,
            "height": poke_data['height'],
            "weight": poke_data['weight'],
            "hp": poke_data['stats'][0]['base_stat'],
            "attack": poke_data['stats'][1]['base_stat'],
            "defense": poke_data['stats'][2]['base_stat'],
            "special-attack": poke_data['stats'][3]['base_stat'],
            "special-defense": poke_data['stats'][4]['base_stat'],
            "speed": poke_data['stats'][5]['base_stat'],
            "sprite": sprite,
            "artwork": poke_data['sprites']['other']['official-artwork']['front_default'],
            "bulbURL": bulb_url
        }

        print(f"Fetched {poke_data['name']}.")
        poke_array.append(poke_data)

    #This is another piece of code, which will be shown in the child page of our notion data base where it will say unique things abut a pokemon, fetched from poke_api
    for pokemon in poke_array:
        flavor_response = requests.get(f"https://pokeapi.co/api/v2/pokemon-species/{pokemon['number']}")
        flavor_data = flavor_response.json()

        flavor_text = next(
            (entry['flavor_text'] for entry in flavor_data['flavor_text_entries'] if entry['language']['name'] == 'en'),
            "")
        category = next(
            (genus['genus'] for genus in flavor_data['genera'] if genus['language']['name'] == 'en'), "")
        generation = flavor_data['generation']['name'].split("-")[-1].upper()

        pokemon['flavor-text'] = flavor_text.replace("\n", " ")
        pokemon['category'] = category
        pokemon['generation'] = generation

        print(f"Fetched flavor info for {pokemon['name']}.")

    create_notion_page()

#While doijng multiple requests to the notion api, at once it seemed to get crasehd after a point of time for our huge database, so we used a function sleep that will create a gap of time in consecutive requests
def sleep(milliseconds):
    time.sleep(milliseconds / 1000)

def create_notion_page():
    for pokemon in poke_array:
        data = {
            "parent": {"database_id": database_id},
            "icon": {"type": "external", "external": {"url": pokemon['sprite']}},
            "cover": {"type": "external", "external": {"url": pokemon['artwork']}},
            "properties": {
                "Name": {"title": [{"text": {"content": pokemon['name']}}]},
                "Category": {"rich_text": [{"type": "text", "text": {"content": pokemon['category']}}]},
                "No": {"number": pokemon['number']},
                "Type": {"multi_select": pokemon['types']},
                "Generation": {"select": {"name": pokemon['generation']}},
                "Sprite": {"files": [{"type": "external", "name": "Pokemon Sprite", "external": {"url": pokemon['sprite']}}]},
                "Height": {"number": pokemon['height']},
                "Weight": {"number": pokemon['weight']},
                "HP": {"number": pokemon['hp']},
                "Attack": {"number": pokemon['attack']},
                "Defense": {"number": pokemon['defense']},
                "Sp. Attack": {"number": pokemon['special-attack']},
                "Sp. Defense": {"number": pokemon['special-defense']},
                "Speed": {"number": pokemon['speed']}
            },
            #child page is like ash's pokedesk, where if you will click on the a particular member in your database,it will show the details of it from the child page
            
            "children": [
                {"object": "block", "type": "quote", "quote": {"rich_text": [{"type": "text", "text": {"content": pokemon['flavor-text']}}]}},
                {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": ""}}]}},
                {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": "View This Pokémon's Entry on Bulbapedia:"}}]}},
                {"object": "block", "type": "bookmark", "bookmark": {"url": pokemon['bulbURL']}}
            ]
        }

        sleep(300)
        print(f"Sending {pokemon['name']} to Notion")

        response = requests.post(
            f"https://api.notion.com/v1/pages",
            headers={
                "Authorization": f"Bearer {notion_api_key}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28",
            },
            json=data
        )

        if response.status_code == 200:
            print("Success! ✨")
        else:
            print(f"Error: {response.status_code} {response.reason}")

    print("Operation complete.")

get_pokemon()
