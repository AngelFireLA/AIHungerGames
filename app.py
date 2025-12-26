import flask
from flask import Flask, session, render_template, request, redirect, url_for, jsonify
from flask_session import Session
from copy import deepcopy


from utils import generate_text, test_system_prompt, generate_tributes_string, generate_full_round_description, \
    generate_full_description_of_dead_tributes, get_dead_tributes, generate_full_round_html
from tribute import Tribute

 # basic flask app setup
app = Flask(__name__)
app.config['SECRET_KEY'] = 'nggyu'
app.config["SESSION_TYPE"] = "filesystem"  # or "redis", "sqlalchemy", etc.
Session(app)

rounds = ["Bloodbath", "Day 1", "Night 1", "Day 2", "Night 2", "Day 3", "Night 3", "Day 4", "Night 4", "Day 5", "Night 5", "Day 6", "Night 6", "Day 7", "Night 7", "Day 8", "Night 8", "Day 9", "Night 9", "Day 10", "Night 10", "Day 11", "Night 11", "Day 12", "Night 12", "Day 13", "Night 13"]

test_tributes = [
    Tribute("A", "male", None, 0),
    Tribute("B", "male", None, 0),
    Tribute("C", "femboy", None, 0),
    Tribute("D", "male", None, 0),
    Tribute("E", "male", None, 0),
    Tribute("F", "female", None, 0),
    Tribute("G", "male", None, 0),
    Tribute("H", "male", None, 0),
    Tribute("I", "male", None, 0),
    Tribute("J", "male", None, 0),
]

# Keep an immutable copy of the starting lineup for resets and final page
initial_tributes_state = deepcopy(test_tributes)
initial_tribute_names = [t.name for t in initial_tributes_state]

@app.route("/")
def index():
    global test_tributes
    test_tributes = deepcopy(initial_tributes_state)
    session["previous_rounds_descriptions"] = ""
    session["dead_tributes_since_last_checkpoint"] = []
    session["last_round_name"] = None
    session["showed_dead_list"] = False
    return render_template("index.html", rounds=rounds)

@app.route("/get_next_round", methods=["GET"])
def get_next_round():
    # If the game is effectively over, go to winner page
    if len(test_tributes) <= 1:
        return redirect(url_for("winner_page"))

    if not session.get("previous_rounds_descriptions"):
        session["previous_rounds_descriptions"] = ""
    if not session.get("dead_tributes_since_last_checkpoint"):
        session["dead_tributes_since_last_checkpoint"] = []
    if not session.get("last_round_name"):
        session["last_round_name"] = None
    if not session.get("showed_dead_list"):
        session["showed_dead_list"] = False

    if session["last_round_name"] is None:
        next_round = "Bloodbath"
    else:
        try:
            current_index = rounds.index(session["last_round_name"])
            next_round = rounds[current_index + 1]
        except (ValueError, IndexError):
            return jsonify({"error": "No more rounds available."}), 400

    return redirect(url_for("get_round", round_name=next_round))

@app.route("/winner", methods=["GET"])
def winner_page():
    alive_names = [t.name for t in test_tributes]
    winner_name = alive_names[0] if len(alive_names) == 1 else None
    fallen = [n for n in initial_tribute_names if n not in alive_names]
    recap = session.get("previous_rounds_descriptions", "")

    return render_template(
        "winner.html",
        winner=winner_name,
        fallen=fallen,
        recap=recap
    )

@app.route("/get_round/<string:round_name>", methods=["GET"])
def get_round(round_name):
    if not session["previous_rounds_descriptions"]:
        session["previous_rounds_descriptions"] = ""
    if not session["dead_tributes_since_last_checkpoint"]:
        session["dead_tributes_since_last_checkpoint"] = []
    if not session["last_round_name"]:
        session["last_round_name"] = None
    if not session["showed_dead_list"]:
        session["showed_dead_list"] = False
    previous_round_name = session["last_round_name"]
    if previous_round_name and not session["showed_dead_list"]:
        if previous_round_name == "Bloodbath":
            dead_list_description = generate_full_description_of_dead_tributes(session["dead_tributes_since_last_checkpoint"], bloodbath=True)
            session["dead_tributes_since_last_checkpoint"] = []
            session["showed_dead_list"] = True
            return render_template("round.html", round_name=round_name, round_description=dead_list_description, is_dead_list=True, previous_round_name=previous_round_name)
        elif "Night" in previous_round_name:
            dead_list_description = generate_full_description_of_dead_tributes(session["dead_tributes_since_last_checkpoint"])
            session["dead_tributes_since_last_checkpoint"] = []
            session["showed_dead_list"] = True
            return render_template("round.html", round_name=round_name, round_description=dead_list_description, is_dead_list=True, previous_round_name=previous_round_name)

    system_prompt = test_system_prompt.replace("|participant list|", generate_tributes_string(test_tributes))

    if session["previous_rounds_descriptions"]:
        system_prompt = system_prompt.replace("|recap_of_previous_rounds|", session["previous_rounds_descriptions"])
    else:
        system_prompt = system_prompt.replace("|recap_of_previous_rounds|", "No previous rounds.")

    system_prompt = system_prompt.replace("|what_togenerate|", round_name)

    round_json = generate_text("Proceed", system_prompt)

    tributes_dead_this_round = get_dead_tributes(round_json)
    session["dead_tributes_since_last_checkpoint"] += tributes_dead_this_round
    session["previous_rounds_descriptions"] += f"\n {generate_full_round_description(round_name, round_json, with_round_name=True)}"
    session["previous_rounds_descriptions"] += f"\n List of dead people this round :\n{', '.join(tributes_dead_this_round) if tributes_dead_this_round else 'No one died'}.\n"
    for dead_tribute in session["dead_tributes_since_last_checkpoint"]:
        for tribute in test_tributes[:]:
            if tribute.name == dead_tribute:
                test_tributes.remove(tribute)
                break
    session["last_round_name"] = round_name
    session["showed_dead_list"] = False
    print(session["previous_rounds_descriptions"], previous_round_name, session["dead_tributes_since_last_checkpoint"], session["showed_dead_list"])
    return render_template(
        "round.html",
        round_name=round_name,
        round_description=generate_full_round_html(round_name, round_json),  # HTML for UI
        is_dead_list=False,
        previous_round_name=previous_round_name
    )

if __name__ == "__main__":
    app.run(debug=True)


