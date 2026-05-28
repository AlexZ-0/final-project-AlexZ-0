import re, string, calendar, requests, time
from wikipedia import WikipediaPage
import wikipedia
from bs4 import BeautifulSoup
from match import match
from typing import List, Callable, Tuple, Any, Match
import random


def get_page_html(title: str) -> str:
    for attempt in range(5):
        response = requests.get(
            "https://en.wikipedia.org/w/api.php",
            params={
                "action": "parse",
                "page": title,
                "prop": "text",
                "format": "json",
                "redirects": True,
            },
            headers={"User-Agent": "intro-ai-class/1.0"}
        )
        if response.status_code == 429:
            wait = int(response.headers.get("Retry-After", 5))
            print(f"Rate limited — waiting {wait}s before retrying '{title}'...")
            time.sleep(wait)
            continue
        if response.status_code == 200 and response.text.strip():
            data = response.json()
            if "error" not in data:
                time.sleep(2)
                return data["parse"]["text"]["*"]
    raise ConnectionError(f"Could not retrieve Wikipedia page for '{title}' after 5 attempts")


def get_first_infobox_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    results = soup.find_all(class_="infobox")

    if not results:
        raise LookupError("Page has no infobox")
    return results[0].text


def clean_text(text: str) -> str:
    only_ascii = "".join([char if char in string.printable else " " for char in text])
    no_dup_spaces = re.sub(" +", " ", only_ascii)
    no_dup_newlines = re.sub("\n+", "\n", no_dup_spaces)
    return no_dup_newlines


def get_match(
    text: str,
    pattern: str,
    error_text: str = "Page doesn't appear to have the property you're expecting",
) -> Match:
    p = re.compile(pattern, re.DOTALL | re.IGNORECASE)
    match = p.search(text)

    if not match:
        raise AttributeError(error_text)
    return match


def get_polar_radius(planet_name: str) -> str:
    infobox_text = clean_text(get_first_infobox_text(get_page_html(planet_name)))
    pattern = r"(?:Polar radius|Mean radius)(?:[^\d]*)(?P<radius>[\d,.]+)(?:.*?)km"
    error_text = "Page infobox has no polar radius information"
    match = get_match(infobox_text, pattern, error_text)
    return match.group("radius")


def get_birth_date(name: str) -> str:
    infobox_text = clean_text(get_first_infobox_text(get_page_html(name)))
    pattern = r"(?:Born\D*)(?P<birth>\d{4}-\d{2}-\d{2})"
    error_text = "Page infobox has no birth information (at least none in xxxx-xx-xx format)"
    match = get_match(infobox_text, pattern, error_text)
    return match.group("birth")


def show_infobox(matches: List[str]) -> List[str]:
    title = " ".join(matches)
    html = get_page_html(title)
    info = get_first_infobox_text(html)
    return [clean_text(info)]


def get_endangered(name: str) -> str:
    infobox_text = clean_text(get_first_infobox_text(get_page_html(name)))
    pattern = r"Conservation status\s*(.+?)\n"
    error_text = "Page has no info on endangered status"
    match = get_match(infobox_text, pattern, error_text)
    return match.group(1)


def get_symptoms(sickness: str) -> str:
    infobox_text = clean_text(get_first_infobox_text(get_page_html(sickness)))
    pattern = r"Symptoms\s*(.*?)Complications"
    error_text = "Page has no info on symptoms"
    match = get_match(infobox_text, pattern, error_text)
    return match.group(1)


def get_population(state: str) -> str:
    infobox_text = clean_text(get_first_infobox_text(get_page_html(state)))
    pattern = r"Population.*?Total\s*([\d,]+)"
    error_text = "Page has no info on population"
    match = get_match(infobox_text, pattern, error_text)
    return match.group(1)


def get_wars(gun: str) -> str:
    infobox_text = clean_text(get_first_infobox_text(get_page_html(gun)))
    pattern = r"Wars\s*(.*?)\n"
    error_text = "Page has no info on wars it was used in"
    match = get_match(infobox_text, pattern, error_text)
    return match.group(1)


def play_hangman(dummy: List[str]) -> List[str]:
    places = [
        "California", "Texas", "Florida", "New York",
        "Chicago", "Houston", "Phoenix", "Philadelphia",
        "San Antonio", "San Diego", "Dalla", "Moscow"
    ]

    secret = random.choice(places).lower()
    display = ["_" if c.isalpha() else c for c in secret]
    guessed = set()
    lives = 6

    print("\n🎮 Starting Hangman! Guess the U.S. state or city.")
    print("I’ll also give you a clue once you get close.\n")

    while lives > 0 and "_" in display:
        print("Word:", " ".join(display))
        print(f"Lives left: {lives}")
        print(f"Guessed letters: {', '.join(sorted(guessed))}\n")

        guess = input("Guess a letter: ").lower().strip()

        if not guess.isalpha() or len(guess) != 1:
            print("Please guess a single letter.\n")
            continue

        if guess in guessed:
            print("You already guessed that.\n")
            continue

        guessed.add(guess)

        if guess in secret:
            print("Correct!\n")
            for i, c in enumerate(secret):
                if c == guess:
                    display[i] = c
        else:
            print("Wrong!\n")
            lives -= 1

        if display.count("_") <= len(secret) // 2:
            try:
                clue = get_population(secret.title())
                print(f" Clue: Its population is around {clue}.\n")
            except:
                pass

    if "_" not in display:
        print(f"You win! The word was: {secret.title()}")
    else:
        print(f"Out of lives! The word was: {secret.title()}")

    return ["Game over"]

def get_capital(country: str) -> str:
    infobox_text = clean_text(get_first_infobox_text(get_page_html(country)))
    pattern = r"#Regex"
    error_text = "Page has no info on capital city"
    match = get_match(infobox_text, pattern, error_text)
    return match.group(1)


def get_height(mountain: str) -> str:
    infobox_text = clean_text(get_first_infobox_text(get_page_html(mountain)))
    pattern = r"#Regex"
    error_text = "Page has no info on mountain height"
    match = get_match(infobox_text, pattern, error_text)
    return match.group(1)


def get_discovery_year(element: str) -> str:
    infobox_text = clean_text(get_first_infobox_text(get_page_html(element)))
    pattern = r"#Regex"
    error_text = "Page has no info on discovery year"
    match = get_match(infobox_text, pattern, error_text)
    return match.group(1)


def get_director(movie: str) -> str:
    infobox_text = clean_text(get_first_infobox_text(get_page_html(movie)))
    pattern = r"#Regex"
    error_text = "Page has no info on director"
    match = get_match(infobox_text, pattern, error_text)
    return match.group(1)


def get_length(river: str) -> str:
    infobox_text = clean_text(get_first_infobox_text(get_page_html(river)))
    pattern = r"#Regex"
    error_text = "Page has no info on river length"
    match = get_match(infobox_text, pattern, error_text)
    return match.group(1)


def birth_date(matches: List[str]) -> List[str]:
    return [get_birth_date(" ".join(matches))]

def endangered(matches: List[str]) -> List[str]:
    return [get_endangered(" ".join(matches))]

def wars(matches: List[str]) -> List[str]:
    return [get_wars(" ".join(matches))]

def symptoms(matches: List[str]) -> List[str]:
    return [get_symptoms(" ".join(matches))]

def population(matches: List[str]) -> List[str]:
    return [get_population(" ".join(matches))]

def polar_radius(matches: List[str]) -> List[str]:
    return [get_polar_radius(matches[0])]

# NEW action wrappers
def capital(matches: List[str]) -> List[str]:
    return [get_capital(" ".join(matches))]

def height(matches: List[str]) -> List[str]:
    return [get_height(" ".join(matches))]

def discovery_year(matches: List[str]) -> List[str]:
    return [get_discovery_year(" ".join(matches))]

def director(matches: List[str]) -> List[str]:
    return [get_director(" ".join(matches))]

def length(matches: List[str]) -> List[str]:
    return [get_length(" ".join(matches))]


def bye_action(dummy: List[str]) -> None:
    raise KeyboardInterrupt

pa_list: List[Tuple[List[str], Callable[[List[str]], List[Any]]]] = [
    ("when was % born".split(), birth_date),
    ("what is the polar radius of %".split(), polar_radius),
    ("infobox %".split(), show_infobox),
    ("conservation status %".split(), endangered),
    ("what are the symptoms of %".split(), symptoms),
    ("what is the population of %".split(), population),
    ("play hangman".split(), play_hangman),
    ("where was % used".split(), wars),
    ("what is the capital of %".split(), capital),
    ("how tall is %".split(), height),
    ("when was % discovered".split(), discovery_year),
    ("who directed %".split(), director),
    ("what is the length of %".split(), length),

    (["bye"], bye_action),
]


def search_pa_list(src: List[str]) -> List[str]:
    for pat, act in pa_list:
        mat = match(pat, src)
        if mat is not None:
            answer = act(mat)
            return answer if answer else ["No answers"]
    return ["I don't understand"]


def query_loop() -> None:
    print("Welcome to the wikipedia chatbot!\n")
    while True:
        try:
            print()
            query = input("Your query? ").replace("?", "").lower().split()
            answers = search_pa_list(query)
            for ans in answers:
                print(ans)

        except (KeyboardInterrupt, EOFError):
            break

    print("\nSo long!\n")


query_loop()
