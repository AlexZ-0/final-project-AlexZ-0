import re, string, calendar, requests, time
from wikipedia import WikipediaPage
import wikipedia
from bs4 import BeautifulSoup
from match import match
from typing import List, Callable, Tuple, Any, Match, Optional


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


def search_wikipedia_titles(query: str, max_results: int = 10) -> List[str]:
    response = requests.get(
        "https://en.wikipedia.org/w/api.php",
        params={
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": max_results,
            "format": "json",
        },
        headers={"User-Agent": "intro-ai-class/1.0"}
    )
    response.raise_for_status()
    data = response.json()
    return [item["title"] for item in data.get("query", {}).get("search", [])]


def find_film_title(title: str) -> Optional[str]:
    if re.search(r"\(.*film.*\)$", title, re.IGNORECASE):
        return title

    candidates = search_wikipedia_titles(f"{title} film", max_results=10)
    for candidate in candidates:
        if re.search(r"\b(film|movie)\b", candidate, re.IGNORECASE):
            return candidate

    if candidates:
        return candidates[0]
    return None


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


def get_infobox_row_value(title: str, label_pattern: str, error_text: str) -> str:
    html = get_page_html(title)
    soup = BeautifulSoup(html, "html.parser")
    infobox = soup.find(class_="infobox")
    if not infobox:
        raise LookupError("Page has no infobox")

    for tr in infobox.find_all("tr"):
        th = tr.find("th")
        td = tr.find("td")
        if not th or not td:
            continue
        label = clean_text(" ".join(th.stripped_strings))
        if re.search(label_pattern, label, re.IGNORECASE):
            return clean_text(" ".join(td.stripped_strings))

    raise LookupError(error_text)


def get_polar_radius(planet_name: str) -> str:
    value = get_infobox_row_value(planet_name, r"^(?:Polar radius|Mean radius)$", "Page infobox has no polar radius information")
    pattern = r"([\d,.]+)\s*km"
    error_text = "Polar radius row has no km value"
    match = get_match(value, pattern, error_text)
    return match.group(1)


def get_birth_date(name: str) -> str:
    value = get_infobox_row_value(name, r"^Born$", "Page infobox has no birth information (at least none in xxxx-xx-xx format)")
    pattern = r"(\d{4}-\d{2}-\d{2})"
    error_text = "Birth row has no ISO date"
    match = get_match(value, pattern, error_text)
    return match.group(1)


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
    value = get_infobox_row_value(state, r"^Population$", "Page has no info on population")
    pattern = r"Total\s*([\d,]+)"
    error_text = "Page has no info on population total"
    match = get_match(value, pattern, error_text)
    return match.group(1)


def get_wars(gun: str) -> str:
    value = get_infobox_row_value(gun, r"^Wars$", "Page has no info on wars it was used in")
    return value


def get_official_language(country: str) -> str:
    value = get_infobox_row_value(
        country,
        r"^Official language(?:s)?(?: and national language(?:s)?)?$",
        "Page has no official language information"
    )
    return value


def get_total_area(country: str) -> str:
    html = get_page_html(country)
    soup = BeautifulSoup(html, "html.parser")
    infobox = soup.find(class_="infobox")
    if not infobox:
        raise LookupError("Page has no infobox")

    for tr in infobox.find_all("tr"):
        th = tr.find("th")
        td = tr.find("td")
        if not th or not td:
            continue
        label = clean_text(" ".join(th.stripped_strings))
        if re.search(r"^\W*Total$", label, re.IGNORECASE):
            value = clean_text(" ".join(td.stripped_strings))
            if re.search(r"\d[\d,]*\s*km\s*2", value, re.IGNORECASE):
                pattern = r"([\d,]+(?:\.\d+)?)\s*km\s*2"
                error_text = "Page area row has no km2 value"
                match = get_match(value, pattern, error_text)
                return match.group(1)

    raise LookupError("Page has no area information")


def get_president(country: str) -> str:
    value = get_infobox_row_value(country, r"^\W*President$", "Page has no president information")
    return value.strip()


def get_founded_date(company: str) -> str:
    value = get_infobox_row_value(company, r"^Founded$", "Page has no founding date information")
    pattern = r"(\d{4}-\d{2}-\d{2})"
    error_text = "Founding row has no ISO date"
    match = get_match(value, pattern, error_text)
    return match.group(1)


def get_founders(company: str) -> str:
    value = get_infobox_row_value(company, r"^Founders$", "Page has no founder information")
    return value


def get_revenue(company: str) -> str:
    value = get_infobox_row_value(company, r"^Revenue$", "Page has no revenue information")
    pattern = r"US\$\s*([\d.,]+(?:\s*billion|\s*million)?)"
    error_text = "Revenue row has no dollars value"
    match = get_match(value, pattern, error_text)
    return match.group(1)


def get_net_income(company: str) -> str:
    value = get_infobox_row_value(company, r"^Net income$", "Page has no net income information")
    pattern = r"US\$\s*([\d.,]+(?:\s*billion|\s*million)?)"
    error_text = "Net income row has no dollars value"
    match = get_match(value, pattern, error_text)
    return match.group(1)


def get_number_of_employees(company: str) -> str:
    value = get_infobox_row_value(company, r"^Number of employees$", "Page has no employee count information")
    pattern = r"([\d,]+)"
    error_text = "Employees row has no numeric value"
    match = get_match(value, pattern, error_text)
    return match.group(1)


def get_headquarters(company: str) -> str:
    value = get_infobox_row_value(company, r"^Headquarters$", "Page has no headquarters information")
    return value


def get_died_date(name: str) -> str:
    value = get_infobox_row_value(name, r"^Died$", "Page has no death date information")
    pattern = r"(\d{4}-\d{2}-\d{2})"
    error_text = "Death row has no ISO date"
    match = get_match(value, pattern, error_text)
    return match.group(1)


def get_citizenship(name: str) -> str:
    value = get_infobox_row_value(name, r"^Citizenship$", "Page has no citizenship information")
    return value


def get_education(name: str) -> str:
    value = get_infobox_row_value(name, r"^Education$", "Page has no education information")
    return value


def get_known_for(name: str) -> str:
    value = get_infobox_row_value(name, r"^Known for$", "Page has no known-for information")
    return value


def get_capital(country: str) -> str:
    value = get_infobox_row_value(country, r"^Capital", "Page has no info on capital city")
    pattern = r"([A-Z][a-z]+(?: [A-Z][a-z]+)*)"
    error_text = "Capital row has no city value"
    match = get_match(value, pattern, error_text)
    return match.group(1)

def get_height(mountain: str) -> str:
    value = get_infobox_row_value(mountain, r"^(?:Elevation|Height)$", "Page has no info on mountain height")
    pattern = r"([\d.,]+)\s*m\s*\(([\d.,]+)\s*ft\)"
    error_text = "Height row has no metric value"
    match = get_match(value, pattern, error_text)
    return match.group(1)


def get_atmosphere_composition(celestial_body: str) -> str:
    infobox_text = clean_text(get_first_infobox_text(get_page_html(celestial_body)))
    pattern = r"Composition by volume\s*((?:\s*(?:\d[\d.]*%|Trace).*\n?)+)"
    error_text = "Page has no info on atmosphere composition"
    match = get_match(infobox_text, pattern, error_text)
    return match.group(1)


def get_director(movie: str) -> str:
    try:
        return get_infobox_row_value(movie, r"^Directed by$", "Page has no info on director")
    except LookupError:
        film_title = find_film_title(movie)
        if film_title and film_title.lower() != movie.lower():
            return get_infobox_row_value(film_title, r"^Directed by$", "Page has no info on director")
        raise


def get_length(river: str) -> str:
    value = get_infobox_row_value(river, r"^Length$", "Page has no info on river length")
    pattern = r"([\d,]+)\s*(?:km|mi)"
    error_text = "Length row has no km or mi value"
    match = get_match(value, pattern, error_text)
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

def capital(matches: List[str]) -> List[str]:
    return [get_capital(" ".join(matches))]

def official_language(matches: List[str]) -> List[str]:
    return [get_official_language(" ".join(matches))]

def total_area(matches: List[str]) -> List[str]:
    return [get_total_area(" ".join(matches))]

def president(matches: List[str]) -> List[str]:
    return [get_president(" ".join(matches))]

def founded_date(matches: List[str]) -> List[str]:
    return [get_founded_date(" ".join(matches))]

def founders(matches: List[str]) -> List[str]:
    return [get_founders(" ".join(matches))]

def revenue(matches: List[str]) -> List[str]:
    return [get_revenue(" ".join(matches))]

def net_income(matches: List[str]) -> List[str]:
    return [get_net_income(" ".join(matches))]

def number_of_employees(matches: List[str]) -> List[str]:
    return [get_number_of_employees(" ".join(matches))]

def headquarters(matches: List[str]) -> List[str]:
    return [get_headquarters(" ".join(matches))]

def died_date(matches: List[str]) -> List[str]:
    return [get_died_date(" ".join(matches))]

def citizenship(matches: List[str]) -> List[str]:
    return [get_citizenship(" ".join(matches))]

def education(matches: List[str]) -> List[str]:
    return [get_education(" ".join(matches))]

def known_for(matches: List[str]) -> List[str]:
    return [get_known_for(" ".join(matches))]

def height(matches: List[str]) -> List[str]:
    return [get_height(" ".join(matches))]

def atmosphere_composition(matches: List[str]) -> List[str]:
    return [get_atmosphere_composition(" ".join(matches))]

def director(matches: List[str]) -> List[str]:
    return [get_director(" ".join(matches))]

def length(matches: List[str]) -> List[str]:
    return [get_length(" ".join(matches))]


def bye_action(dummy: List[str]) -> None:
    raise KeyboardInterrupt

pa_list: List[Tuple[List[str], Callable[[List[str]], List[Any]]]] = [
    ("when was % born".split(), birth_date),
    ("what is the official language of %".split(), official_language),
    ("what is the total area of %".split(), total_area),
    ("who is the president of %".split(), president),
    ("what is the population of %".split(), population),
    ("when was % founded".split(), founded_date),
    ("who founded %".split(), founders),
    ("what is the revenue of %".split(), revenue),
    ("what is the net income of %".split(), net_income),
    ("how many employees does % have".split(), number_of_employees),
    ("where are the headquarters of %".split(), headquarters),
    ("what is the polar radius of %".split(), polar_radius),
    ("infobox %".split(), show_infobox),
    ("conservation status %".split(), endangered),
    ("what are the symptoms of %".split(), symptoms),
    ("where was % used".split(), wars),
    ("what is the capital of %".split(), capital),
    ("how tall is %".split(), height),
    ("what is the atmosphere composition of %".split(), atmosphere_composition),
    ("who directed %".split(), director),
    ("where did % study".split(), education),
    ("where did % study".split(), education),
    ("what is the length of %".split(), length),

    (["bye"], bye_action),
]

query_templates: List[str] = [
    "what is the capital of ...",
    "what is the official language of ...",
    "what is the total area of ...",
    "who is the president of ...",
    "what is the population of ...",
    "when was ... born",
    "when was ... founded",
    "who founded ...",
    "who directed ...",
    "what is the revenue of ...",
    "what is the net income of ...",
    "how many employees does ... have",
    "where are the headquarters of ...",
    "how tall is ...",
    "what is the length of ...",
    "what are the symptoms of ...",
    "where was ... used",
    "conservation status ...",
    "infobox ...",
    "what is the polar radius of ...",
    "what is the atmosphere composition of ...",
    "when did ... die",
    "where did ... study",
]


def search_pa_list(src: List[str]) -> List[str]:
    for pat, act in pa_list:
        mat = match(pat, src)
        if mat is not None:
            try:
                answer = act(mat)
                return answer if answer else ["No answers"]
            except LookupError:
                return ["Infobox could not be found"]
            except AttributeError:
                return ["Infobox has no related information"]
            except Exception:
                return ["An unexpected error occurred while reading the infobox"]
    return ["I don't understand"]


def get_page_infobox(title: str) -> str:
    html = get_page_html(title)
    return clean_text(get_first_infobox_text(html))


def query_response(src: List[str]) -> Tuple[List[str], Optional[str]]:
    answers = search_pa_list(src)
    title = None
    for pat, act in pa_list:
        mat = match(pat, src)
        if mat is not None:
            if pat != ["bye"]:
                title = " ".join(mat).strip() if mat else None
            break
    return answers, title


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


if __name__ == "__main__":
    query_loop()
