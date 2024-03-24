import requests
from Utils import log, parse_text_for_tg_markdown
import urllib.parse
from telebot import types
from uuid import uuid4

GITHUB_API = "https://api.github.com"
REPO_SEARCH_ENDPOINT = GITHUB_API + "/search/repositories"
REPO_RELEASE_ENDPOINT = GITHUB_API + "/repos"


# these dictonaries are needed later to edit message
message_dict = {}
full_name_dict = {}
buttons_dict = {}


# get repos for the input
def search_repos(query):
    encoded_query = urllib.parse.quote(query)
    url = f"{REPO_SEARCH_ENDPOINT}?q={encoded_query}"
    try:
        response = requests.get(url)
        if response.ok:
            data = response.json()
            if data["total_count"] > 0:
                log(f"Found {data['total_count']} repos for \"{query}\"")
                return data["items"][:50]
            else:
                log(f"Not 200. {response}")
    except requests.RequestException as e:
        log(f"Error fetching repos: {e}")
    return None


def get_release_details(repo):
    url = f"{REPO_RELEASE_ENDPOINT}/{repo}/releases"
    try:
        response = requests.get(url)
        if response.ok:
            data = response.json()
            return data
        else:
            log(f"Not 200. {response.text()}")
    except requests.RequestException as e:
            log(f"Error fetching releases: {e}")
    return None


def get_buttons(query, repo):
    buttons = types.InlineKeyboardMarkup(row_width=3)
    btn_retry = types.InlineKeyboardButton(
        "Search again", switch_inline_query_current_chat=query
    )
    btn_repo = types.InlineKeyboardButton("View Repo", url=repo)
    buttons.row(btn_retry, btn_repo)
    return buttons


def prepare_inline_results(query, items):
    results = []
    for item in items:
        id = str(uuid4())
        full_name = item["full_name"]
        repo_description = item["description"]
        language = item["language"]
        stars = item["stargazers_count"]
        thumbnail = item["owner"]["avatar_url"]
        fork_count = item["forks_count"]
        description = f"💻 {language}"
        if stars > 0:
            description += f" | ⭐️ {stars}"
        if fork_count > 0:
            description += f" | 🍴 {fork_count}"
        inline_message = f"{description}\n{repo_description}"
        text_message = (
            f"<b>{full_name}</b>\n\n<i>{repo_description}</i>\n\n{description}"
        )
        repo_url = item["html_url"]
        buttons = get_buttons(query=query, repo=repo_url)
        buttons_dict[id] = buttons
        message_dict[id] = text_message
        full_name_dict[id] = full_name
        results.append(
            types.InlineQueryResultArticle(
                id=id,
                title=full_name,
                thumbnail_url=thumbnail,
                description=inline_message,
                input_message_content=types.InputTextMessageContent(
                    message_text=text_message, parse_mode="html"
                ),
                reply_markup=buttons,
            )
        )
    return results


def get_inline_data(query):
    repos = search_repos(query)
    if repos is None:
        results = []
    else:
        results = prepare_inline_results(query, repos)
    return results


def get_latest_release_details(full_name):
    data = get_release_details(full_name)
    if data is not None and len(data) > 0:
        item = data[0]
        tag = item["tag_name"]
        name = item["name"]
        time = item["published_at"]
        downloads =  sum(asset['download_count'] for asset in item["assets"])
        message = parse_text_for_tg_markdown(item["body"])
        url = item["html_url"]
        release_details = f"\n<b>Latest Release</b>\n\n{name}\nversion: {tag}\nDownloads: {downloads}\nTime: {time}\n\n<i>{message}</i>"
        return release_details, url
    else:
        return None, None


def get_message_url_and_buttons_for(id):
    message = message_dict.get(id)
    full_name = full_name_dict.get(id)
    buttons = buttons_dict.get(id, types.InlineKeyboardMarkup(row_width=2))
    release_info, url = get_latest_release_details(full_name)
    btn_release = types.InlineKeyboardButton("Goto Download Page", url=url)
    buttons.row(btn_release)
    updated_text = (str(message) + "\n\n" + str(release_info))[:4095]
    return updated_text, buttons
