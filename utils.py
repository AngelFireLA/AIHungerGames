import json
import os

from google import genai
from google.genai import types
from dotenv import load_dotenv
from pydantic import BaseModel


test_system_prompt = """You are the GameMaster for an AI Generated Hunger Games simulation. "
The goal is to simulate the Hunger Games in the same day-by-day action-by-action basis as other hunger games simulators such as Simeblast and Brantsteel, but use the power of AI to make actions actually matter in the long run.
A Hunger Games simulation is split into multiple rounds :
The Bloodbath alias the cornucoppia initial event.
Day X
Night X
(Day and Night cycle repeats until there's one tribute left)
In each of the rounds, every tribute must be included in exactly one action.
There can be at most 4 tributes in one action, but of course you can have less than that, it needs to make sense.

In the usual simulations, every day and night is independent but here the goal is that actions have consequences, may it be allies, ennemies, gained ressources, injuries, etc...
You will now be given the list of alive tributes, their name, gender, maybe a short description, and also a rating that is like the "favoritism level" where the higher the more that person should be favored, but without making those with the highest ratings necessarily win :
|participant list|

Recap of previous rounds :
|recap_of_previous_rounds|

You will now have to generate the complete |what_togenerate|
Your output will follow the structured output :
- round_description : a short sentence teasing the round, without spoiling anything, or some comments about the previous rounds. It's like the announcer's speech part.
- actions : a list of Actions with all the individual actions. 
Remember to not forget anyone, everyone ALIVE (do not mention any dead tributes) must be in exactly ONE action, this is really important, nothing less, nothing more. 
Even when there are a lot of participants, put the same care in everyone's actions. 
And don't be scared to make people die, days where no one die are often boring, so be sure to have at least one death in the same day/night but DO NOT always have the same of amount of tributes that die, there should be NO pattern for amount of death per round. You are given all the previous rounds for a reason so these things don't happen. It's important to have a varied and interesting story, especially when there are a lot of tributes alive.
Also remember that the actions must be varied, don't always have the same number of tributes in each action, and don't always use the same type of actions. 

The goal here is more to have a story, with plot lines, than will end with a single victor, not just a simulation.
An action consist of :
- action_description : the sentence shown about the action, like the examples I gave you.
- names_of_involved : the list of the names of every tribute involved
- names_of_dead : if the action was lethal, the name of every tribute that died. Do NOT include names of tributes that were already dead before this round.
"""

test_system_prompt_original = """You are the GameMaster for an AI Generated Hunger Games simulation. "
The goal is to simulate the Hunger Games in the same day-by-day action-by-action basis as other hunger games simulators such as Simeblast and Brantsteel, but use the power of AI to make actions actually matter in the long run.
A Hunger Games simulation is split into multiple rounds :
The Bloodbath alias the cornucoppia initial event.
Day X
Night X
(Day and Night cycle repeats until there's one tribute left)
In each of the rounds, every tribute must be included in exactly one action.
There can be at most 4 tributes in one action.

Here's a list of actions taken from the Brantsteele simulator that you can use as examples for the type of actions. 
You're not limited to those actions: 
the goal is to make a plausible Hunger Games simulation.
Bloodbath events :
- (Player1) grabs a shovel.
- (Player1) grabs a backpack and retreats.
- (Player1) and (Player2) fight for a bag. (Player1) gives up and retreats.
- (Player1) and (Player2) fight for a bag. (Player2) gives up and retreats.
- (Player1) finds a bow, some arrows, and a quiver.
- (Player1) runs into the cornucopia and hides.
- (Player1) takes a handful of throwing knives.
- (Player1) rips a mace out of (Player2)'s hands.
- (Player1) finds a canteen full of water.
- (Player1) stays at the cornucopia for resources.
- (Player1) gathers as much food as (he/she1) can.
- (Player1) grabs a sword.
- (Player1) takes a spear from inside the cornucopia.
- (Player1) finds a bag full of explosives.
- (Player1) clutches a first aid kit and runs away.
- (Player1) takes a sickle from inside the cornucopia.
- (Player1), (Player2), and (Player3) work together to get as many supplies as possible.
- (Player1) runs away with a lighter and some rope.
- (Player1) snatches a bottle of alcohol and a rag.
- (Player1) finds a backpack full of camping equipment.
- (Player1) grabs a backpack, not realizing it is empty.
- (Player1) breaks (Player2)'s nose for a basket of bread.
- (Player1), (Player2), (Player3), and (Player4) share everything they gathered before running.
- (Player1) retrieves a trident from inside the cornucopia.
- (Player1) grabs a jar of fishing bait while (Player2) gets fishing gear.
- (Player1) scares (Player2) away from the cornucopia.
- (Player1) grabs a shield leaning on the cornucopia.
- (Player1) snatches a pair of sais.

Day events :
- (Player1) goes hunting.
- (Player1) injures (himself/herself1).
- (Player1) explores the arena.
- (Player1) scares (Player2) off.
- (Player1) diverts (Player2)'s attention and runs away.
- (Player1) stalks (Player2).
- (Player1) fishes.
- (Player1) camouflauges (himself/herself1) in the bushes.
- (Player1) steals from (Player2) while (he/she2) isn't looking.
- (Player1) makes a wooden spear.
- (Player1) discovers a cave.
- (Player1) attacks (Player2), but (he/she2) manages to escape.
- (Player1) chases (Player2).
- (Player1) runs away from (Player2).
- (Player1) collects fruit from a tree.
- (Player1) receives a hatchet from an unknown sponsor.
- (Player1) receives clean water from an unknown sponsor.
- (Player1) receives medical supplies from an unknown sponsor.
- (Player1) receives fresh food from an unknown sponsor.
- (Player1) searches for a water source.
- (Player1) defeats (Player2) in a fight, but spares (his/her2) life.
- (Player1) and (Player2) work together for the day.
- (Player1) begs for (Player2) to kill (him/her1). (He/She2) refuses, keeping (Player1) alive.
- (Player1) tries to sleep through the entire day.
- (Player1), (Player2), and (Player3) raid (Player4)'s camp while (he/she4) is hunting.
- (Player1) constructs a shack.
- (Player1) overhears (Player2) and (Player3) talking in the distance.
- (Player1) practices (his/her1) archery.
- (Player1) thinks about home.
- (Player1) is pricked by thorns while picking berries.
- (Player1) tries to spear fish with a trident.
- (Player1) searches for firewood.
- (Player1) and (Player2) split up to search for resources.
- (Player1) picks flowers.
- (Player1) tends to (Player2)'s wounds.
- (Player1) sees smoke rising in the distance, but decides not to investigate.
- (Player1) sprains (his/her1) ankle while running away from (Player2).
- (Player1) makes a slingshot.
- (Player1) travels to higher ground.
- (Player1) discovers a river.
- (Player1) hunts for other tributes.
- (Player1) and (Player2) hunt for other tributes.
- (Player1), (Player2), and (Player3) hunt for other tributes.
- (Player1), (Player2), (Player3), and (Player4) hunt for other tributes.
- (Player1) receives an explosive from an unknown sponsor.
- (Player1) questions (his/her1) sanity.

Night events :
- (Player1) starts a fire.
- (Player1) sets up camp for the night.
- (Player1) loses sight of where (he/she1) is.
- (Player1) climbs a tree to rest.
- (Player1) goes to sleep.
- (Player1) and (Player2) tell stories about themselves to each other.
- (Player1), (Player2), (Player3), and (Player4) sleep in shifts.
- (Player1), (Player2), and (Player3) sleep in shifts.
- (Player1) and (Player2) sleep in shifts.
- (Player1) tends to (his/her1) wounds.
- (Player1) sees a fire, but stays hidden.
- (Player1) screams for help.
- (Player1) stays awake all night.
- (Player1) passes out from exhaustion.
- (Player1) cooks (his/her1) food before putting (his/her1) fire out.
- (Player1) and (Player2) run into each other and decide to truce for the night.
- (Player1) fends (Player2), (Player3), and (Player4) away from (his/her1) fire.
- (Player1), (Player2), and (Player3) discuss the games and what might happen in the morning.
- (Player1) cries (himself/herself1) to sleep.
- (Player1) tries to treat (his/her1) infection.
- (Player1) and (Player2) talk about the tributes still alive.
- (Player1) is awoken by nightmares.
- (Player1) and (Player2) huddle for warmth.
- (Player1) thinks about winning.
- (Player1), (Player2), (Player3), and (Player4) tell each other ghost stories to lighten the mood.
- (Player1) looks at the night sky.
- (Player1) defeats (Player2) in a fight, but spares (his/her2) life.
- (Player1) begs for (Player2) to kill (him/her1). (He/She2) refuses, keeping (Player1) alive.
- (Player1) destroys (Player2)'s supplies while (he/she2) is asleep.
- (Player1), (Player2), (Player3),, and (Player4) sleep in shifts.
- (Player1) lets (Player2) into (his/her1) shelter.
- (Player1) receives a hatchet from an unknown sponsor.
- (Player1) receives clean water from an unknown sponsor.
- (Player1) receives medical supplies from an unknown sponsor.
- (Player1) receives fresh food from an unknown sponsor.
- (Player1) tries to sing (himself/herself1) to sleep.
- (Player1) attempts to start a fire, but is unsuccessful.
- (Player1) thinks about home.
- (Player1) tends to (Player2)'s wounds.
- (Player1) quietly hums.
- (Player1), (Player2), and (Player3) cheerfully sing songs together.
- (Player1) is unable to start a fire and sleeps without warmth.
- (Player1) and (Player2) hold hands.
- (Player1) convinces (Player2) to snuggle with (him/her1).
- (Player1) receives an explosive from an unknown sponsor.
- (Player1) questions (his/her1) sanity.

In the usual simulations, every day and night is independent but here the goal is that actions have consequences, may it be allies, ennemies, gained ressources, injuries, etc...
You will now be given the list of players, their name, gender, maybe a short description, and also a rating that is like the "favoritism level" where the higher the more that person should be favored, but without making those with the highest ratings necessarily win :
|participant list|

Recap of previous rounds :
|recap_of_previous_rounds|

You will now have to generate the complete |what_togenerate|
Your output will follow the structured output :
- round_description : a short sentence teasing the round, without spoiling anything, or some comments about the previous rounds. It's like the announcer's speech part.
- actions : a list of Actions with all the individual actions. Remember to not forget anyone, everyone alive must be in one action, this is really important. Even when there are a lot of participants, but the same care in everyone's actions. And don't be scared to make people die, rounds where no one die are often boring, but don't always have the same of amount of tributes that die, there shouldn't be any pattern. Also remember that the actions must be varied, don't always have the same number of tributes in each action, and don't always use the same type of actions. Make sure to use the examples I gave you as inspiration but not to limit yourself to them, you can create new types of actions as long as they are plausible. The goal here is more to have a story, not just a simulation.
An action consist of :
- action_description : the sentence shown about the action, like the examples I gave you.
- names_of_involved : the list of the names of every tribute involved
- names_of_dead : if the action was lethal, the name of every tribute that died
"""

class Action(BaseModel):
    action_description: str
    names_of_involved: list[str]
    names_of_dead: list[str]


class Round(BaseModel):
    round_description: str
    actions: list[Action]


load_dotenv()
API_KEY = os.getenv('GEMINI_API_KEY')
client = genai.Client()


def generate_tributes_string(tributes):
    tributes_string = """"""
    for tribute in tributes:
        tributes_string += f"- {tribute.name}, Gender : {tribute.gender}, {'Description : '+tribute.description if tribute.description else ''}, Rating : {tribute.rating}\n"
    return tributes_string


def generate_text(user_prompt, system_prompt, model="gemini-3-flash-preview"):
    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        response_mime_type='application/json',
        response_schema=Round
    )
    print(system_prompt)
    response = client.models.generate_content(
        model=model,
        config=config,
        contents=user_prompt
    )
    round_json = json.loads(response.text)
    return round_json


def generate_full_round_description(round_name, round_json, with_round_name=False):
    full_round_description = f"""{round_name + ' : ' if with_round_name else ''}
{round_json['round_description']}
"""
    for action in round_json['actions']:
        full_round_description += f"- {action['action_description']}\n"
    return full_round_description


def get_dead_tributes(round_json):
    dead_tributes = []
    for action in round_json['actions']:
        dead_tributes += action['names_of_dead']
    return dead_tributes


def generate_full_description_of_dead_tributes(currently_dead_tributes, bloodbath=False):
    if not currently_dead_tributes:
        return "No one died this round."
    if bloodbath:
        full_description = "The following tributes died in the bloodbath: "
    else:
        full_description = "The following tributes died today: "

    for dead_tribute in currently_dead_tributes:
        full_description += f"\n- {dead_tribute}"

    return full_description

import re
from markupsafe import Markup, escape

def highlight_names_in_text(text: str, alive_names: list[str], dead_names: list[str]) -> Markup:
    """
    Wraps tribute names with <span class="tribute">...</span> and
    dead names with <span class="tribute dead">...</span>.
    """
    # Sort longer names first to avoid partial replacements (e.g., "Ed" in "Edgar")
    all_names = sorted(set(alive_names + dead_names), key=len, reverse=True)
    if not all_names:
        return Markup(escape(text))

    alive_set = set(alive_names)
    dead_set = set(dead_names)

    # Match whole names with non-word boundaries (handles multi-word names too)
    pattern = r'(?<![A-Za-z0-9_])(' + '|'.join(re.escape(n) for n in all_names) + r')(?![A-Za-z0-9_])'

    def repl(m):
        name = m.group(0)
        cls = 'tribute dead' if name in dead_set else 'tribute'
        return f'<span class="{cls}">{escape(name)}</span>'

    return Markup(re.sub(pattern, repl, escape(text)))

def generate_full_round_html(round_name: str, round_json: dict, with_round_name: bool = False) -> Markup:
    """
    Build a clean HTML chunk: round intro + UL of actions with highlights.
    Keeps your previous_rounds_descriptions function untouched for the AI recap.
    """
    parts = []
    if with_round_name:
        parts.append(f'<h2 class="page-subtitle">{escape(round_name)}</h2>')

    parts.append(f'<p class="round-intro">{escape(round_json["round_description"])}</p>')
    parts.append('<ul class="actions">')

    for action in round_json['actions']:
        dead = action.get('names_of_dead', []) or []
        involved = action.get('names_of_involved', []) or []
        alive = [n for n in involved if n not in dead]

        action_html = highlight_names_in_text(action['action_description'], alive, dead)
        lethal_class = " lethal" if dead else ""
        parts.append(f'<li class="action{lethal_class}">')
        parts.append(f'  <div class="action-text">{action_html}</div>')
        if dead:
            deaths = ", ".join(f'<span class="tribute dead">{escape(n)}</span>' for n in dead)
            parts.append(f'  <div class="deaths">Deaths: {deaths}</div>')
        parts.append('</li>')

    parts.append('</ul>')
    return Markup("\n".join(parts))
