import sys
import json
import urllib.request
import urllib.parse
import os
import uuid
import time

SETTINGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Settings")
SETTINGS_FILE = os.path.join(SETTINGS_DIR, "settings.json")
RECENT_FILE = os.path.join(SETTINGS_DIR, "recent_games.json")
FAV_FILE = os.path.join(SETTINGS_DIR, "favorites.json")

def load_json(file_path):
    try:
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {} if file_path == SETTINGS_FILE else []

def save_json(file_path, data):
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    except Exception:
        pass

def add_recent_game(place_id, name):
    try:
        recents = load_json(RECENT_FILE)
        if not isinstance(recents, list):
            recents = []
        
        recents = [g for g in recents if str(g.get("id")) != str(place_id)]
        recents.insert(0, {
            "id": str(place_id),
            "name": name,
            "timestamp": time.time()
        })
        recents = recents[:10]
        save_json(RECENT_FILE, recents)
    except Exception:
        pass

def add_favorite_game(place_id, name):
    try:
        favs = load_json(FAV_FILE)
        if not isinstance(favs, list):
            favs = []
        
        # Avoid duplicates
        if not any(str(g.get("id")) == str(place_id) for g in favs):
            favs.append({
                "id": str(place_id),
                "name": name
            })
            save_json(FAV_FILE, favs)
            return True
    except Exception:
        pass
    return False

def open_url(url):
    try:
        os.system(f"start {url}")
    except Exception:
        pass

def search_games(query_text):
    if not query_text or len(query_text.strip()) < 1:
        return [
            {
                "Title": "play <game name>",
                "SubTitle": "Search and launch any Roblox game instantly (e.g. play bedwars)",
                "IcoPath": "icons/icon.png"
            },
            {
                "Title": "-f (or favorites)",
                "SubTitle": "View and launch your pinned favorite games",
                "IcoPath": "icons/icon.png"
            },
            {
                "Title": "pin <game name>",
                "SubTitle": "Search and pin a game to your permanent favorites list",
                "IcoPath": "icons/icon.png"
            },
            {
                "Title": "recent",
                "SubTitle": "View and quickly relaunch your recently played games",
                "IcoPath": "icons/icon.png"
            },
            {
                "Title": "user <username>",
                "SubTitle": "Look up a Roblox user profile and jump straight to their page",
                "IcoPath": "icons/icon.png"
            },
            {
                "Title": "setcookie <your_.roblosecurity_cookie>",
                "SubTitle": "Save your account session cookie locally",
                "IcoPath": "icons/icon.png"
            },
            {
                "Title": "privacy",
                "SubTitle": "Open Roblox account privacy & visibility settings in your browser",
                "IcoPath": "icons/icon.png",
                "JsonRPCAction": {
                    "method": "open_privacy",
                    "parameters": [],
                    "dontHideAfterAction": False
                }
            }
        ]

    clean_query = query_text.strip()

    # Handle Favorites Command (-f or favorites)
    if clean_query.lower() in ["-f", "favorites"]:
        favs = load_json(FAV_FILE)
        if not favs:
            return [{
                "Title": "No Favorite Games Pinned",
                "SubTitle": "Use 'pin <game name>' to add games to your favorites",
                "IcoPath": "icons/icon.png"
            }]
        
        results = []
        for item in favs:
            gid = str(item.get("id"))
            gname = item.get("name", f"Place ID: {gid}")
            results.append({
                "Title": f"⭐ {gname}",
                "SubTitle": f"Launch Favorite | Place ID: {gid}",
                "IcoPath": "icons/icon.png",
                "JsonRPCAction": {
                    "method": "launch_game",
                    "parameters": [gid, gname],
                    "dontHideAfterAction": False
                }
            })
        return results

    # Handle Recent Games Command
    if clean_query.lower() == "recent":
        recents = load_json(RECENT_FILE)
        if not recents:
            return [{
                "Title": "No Recent Games",
                "SubTitle": "Games you launch will automatically show up here",
                "IcoPath": "icons/icon.png"
            }]
        
        results = []
        for item in recents:
            gid = str(item.get("id"))
            gname = item.get("name", f"Place ID: {gid}")
            results.append({
                "Title": gname,
                "SubTitle": f"Relaunch Place ID: {gid}",
                "IcoPath": "icons/icon.png",
                "JsonRPCAction": {
                    "method": "launch_game",
                    "parameters": [gid, gname],
                    "dontHideAfterAction": False
                }
            })
        return results

    # Handle Set Cookie Command
    if clean_query.lower().startswith("setcookie "):
        new_cookie = clean_query[10:].strip()
        if (new_cookie.startswith('"') and new_cookie.endswith('"')) or (new_cookie.startswith("'") and new_cookie.endswith("'")):
            new_cookie = new_cookie[1:-1]
        settings = load_json(SETTINGS_FILE)
        settings["roblox_cookie"] = new_cookie
        save_json(SETTINGS_FILE, settings)
        return [{
            "Title": "Cookie Saved Successfully",
            "SubTitle": "Your .ROBLOSECURITY token has been updated in settings.json",
            "IcoPath": "icons/icon.png"
        }]

    # Handle Privacy Shortcut Command
    if clean_query.lower() == "privacy" or clean_query.lower() == "rbx privacy":
        return [{
            "Title": "Open Privacy Settings",
            "SubTitle": "Press Enter to open your account visibility settings page",
            "IcoPath": "icons/icon.png",
            "JsonRPCAction": {
                "method": "open_privacy",
                "parameters": [],
                "dontHideAfterAction": False
            }
        }]

    # Handle User Lookup Command
    if clean_query.lower().startswith("user "):
        username = clean_query[5:].strip()
        if not username:
            return [{
                "Title": "Invalid Username",
                "SubTitle": "Please specify a username (e.g. user Builderman)",
                "IcoPath": "icons/icon.png"
            }]
        
        try:
            payload = json.dumps({"usernames": [username], "excludeBannedUsers": True}).encode("utf-8")
            req = urllib.request.Request(
                "https://users.roblox.com/v1/usernames/users",
                data=payload,
                headers={"User-Agent": "Mozilla/5.0", "Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                users_data = data.get("data", [])
                if not users_data:
                    return [{
                        "Title": f"User '{username}' Not Found",
                        "SubTitle": "Check spelling or try a different username",
                        "IcoPath": "icons/icon.png"
                    }]
                
                user_info = users_data[0]
                user_id = user_info.get("id")
                display_name = user_info.get("displayName")
                name = user_info.get("name")
                profile_url = f"https://www.roblox.com/users/{user_id}/profile"

                desc = "Open profile in browser"
                try:
                    detail_req = urllib.request.Request(
                        f"https://users.roblox.com/v1/users/{user_id}",
                        headers={"User-Agent": "Mozilla/5.0"}
                    )
                    with urllib.request.urlopen(detail_req, timeout=2) as d_resp:
                        detail_data = json.loads(d_resp.read().decode("utf-8"))
                        bio = detail_data.get("description", "").replace("\n", " ")
                        if bio:
                            desc = f"Bio: {bio[:70]}..." if len(bio) > 70 else f"Bio: {bio}"
                except Exception:
                    pass

                return [{
                    "Title": f"{display_name} (@{name})",
                    "SubTitle": f"{desc} | ID: {user_id}",
                    "IcoPath": "icons/icon.png",
                    "JsonRPCAction": {
                        "method": "open_url",
                        "parameters": [profile_url],
                        "dontHideAfterAction": False
                    }
                }]
        except Exception as e:
            return [{
                "Title": "Error Looking Up User",
                "SubTitle": str(e),
                "IcoPath": "icons/icon.png"
            }]

    # Determine mode: Play vs Pin
    is_pin_mode = False
    if clean_query.lower().startswith("pin "):
        is_pin_mode = True
        clean_query = clean_query[4:].strip()
    elif clean_query.lower().startswith("play "):
        clean_query = clean_query[5:].strip()
    else:
        return [
            {
                "Title": "Invalid Command Format",
                "SubTitle": "Use 'play [game]', 'pin [game]', '-f', 'recent', 'user [name]', or clear input for menu",
                "IcoPath": "icons/icon.png"
            },
            {
                "Title": "Open Privacy Settings",
                "SubTitle": "Press Enter to open account privacy settings",
                "IcoPath": "icons/icon.png",
                "JsonRPCAction": {
                    "method": "open_privacy",
                    "parameters": [],
                    "dontHideAfterAction": False
                }
            }
        ]

    if not clean_query:
        return []

    # 1. Direct Place ID Support
    if clean_query.isdigit():
        action_name = "pin_game" if is_pin_mode else "launch_game"
        title_prefix = f"Pin Place ID: {clean_query}" if is_pin_mode else f"Launch Place ID: {clean_query}"
        sub_text = "Press Enter to save to favorites" if is_pin_mode else "Press Enter to launch this specific place"
        return [{
            "Title": title_prefix,
            "SubTitle": sub_text,
            "IcoPath": "icons/icon.png",
            "JsonRPCAction": {
                "method": action_name,
                "parameters": [clean_query, f"Place ID: {clean_query}"],
                "dontHideAfterAction": False
            }
        }]

    results = []
    seen_ids = set()

    # 2. Try Roblox's autocomplete API
    try:
        encoded_query = urllib.parse.quote(clean_query)
        auto_url = f"https://apis.roblox.com/games-autocomplete/v1/get-suggestion/{encoded_query}"
        req = urllib.request.Request(auto_url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            for item in data.get("suggestions", []) or data.get("games", []):
                gid = str(item.get("placeId") or item.get("universeId") or item.get("id", ""))
                gname = item.get("name") or item.get("query")
                if gid and gname and gid not in seen_ids:
                    seen_ids.add(gid)
                    action_name = "pin_game" if is_pin_mode else "launch_game"
                    title_text = f"⭐ Pin: {gname}" if is_pin_mode else gname
                    results.append({
                        "Title": title_text,
                        "SubTitle": f"Place ID: {gid}",
                        "IcoPath": "icons/icon.png",
                        "JsonRPCAction": {
                            "method": action_name,
                            "parameters": [gid, gname],
                            "dontHideAfterAction": False
                        }
                    })
    except Exception:
        pass

    # 3. Try Roblox's Omni-Search API
    if len(results) < 5:
        try:
            session_id = str(uuid.uuid4())
            omni_url = f"https://apis.roblox.com/search-api/omni-search?searchQuery={urllib.parse.quote(clean_query)}&sessionId={session_id}&pageType=all"
            req = urllib.request.Request(omni_url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json", "Referer": "https://www.roblox.com/"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                search_data = json.loads(resp.read().decode('utf-8'))
                for group in search_data.get("searchResults", []):
                    for content in group.get("contents", []):
                        gid = str(content.get("rootPlaceId") or content.get("placeId") or content.get("universeId", ""))
                        name = content.get("name") or content.get("title")
                        if gid and name and gid not in seen_ids:
                            seen_ids.add(gid)
                            player_count = content.get("playerCount") or content.get("playing")
                            sub = f"Active Players: {player_count:,} | ID: {gid}" if isinstance(player_count, int) else f"ID: {gid}"
                            action_name = "pin_game" if is_pin_mode else "launch_game"
                            title_text = f"⭐ Pin: {name}" if is_pin_mode else name
                            results.append({
                                "Title": title_text,
                                "SubTitle": sub,
                                "IcoPath": "icons/icon.png",
                                "JsonRPCAction": {
                                    "method": action_name,
                                    "parameters": [gid, name],
                                    "dontHideAfterAction": False
                                }
                            })
        except Exception:
            pass

    # 4. Fallback to Rolimons public game dataset index
    if len(results) < 3:
        try:
            roli_url = "https://api.rolimons.com/games/v1/gamelist"
            req = urllib.request.Request(roli_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=4) as resp:
                roli_data = json.loads(resp.read().decode('utf-8'))
                games_dict = roli_data.get("games", {})
                query_lower = clean_query.lower()
                matches = []
                for place_id, details in games_dict.items():
                    if isinstance(details, list) and len(details) > 0:
                        name = details[0]
                        players = details[1] if len(details) > 1 else 0
                        if query_lower in name.lower():
                            matches.append((players, str(place_id), name))
                matches.sort(key=lambda x: x[0], reverse=True)
                for players, place_id, name in matches:
                    if place_id not in seen_ids:
                        seen_ids.add(place_id)
                        action_name = "pin_game" if is_pin_mode else "launch_game"
                        title_text = f"⭐ Pin: {name}" if is_pin_mode else name
                        results.append({
                            "Title": title_text,
                            "SubTitle": f"Active Players: {players:,} | Place ID: {place_id}",
                            "IcoPath": "icons/icon.png",
                            "JsonRPCAction": {
                                "method": action_name,
                                "parameters": [place_id, name],
                                "dontHideAfterAction": False
                            }
                        })
                        if len(results) >= 15:
                            break
        except Exception:
            pass

    # 5. Web Search Fallback
    if not results and not is_pin_mode:
        results.append({
            "Title": f"Search '{clean_query}' on Roblox.com",
            "SubTitle": "Open official website discovery page",
            "IcoPath": "icons/icon.png",
            "JsonRPCAction": {
                "method": "open_web_search",
                "parameters": [clean_query],
                "dontHideAfterAction": False
            }
        })

    return results

def launch_game(place_id, game_name="Roblox Game"):
    try:
        resolved_id = place_id
        if len(place_id) > 0:
            try:
                url = f"https://apis.roblox.com/universes/v1/places/{place_id}/universe"
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=2) as resp:
                    data = json.loads(resp.read().decode('utf-8'))
                    if "universeId" in data:
                        uni_id = data["universeId"]
                        uni_url = f"https://games.roblox.com/v1/games?universeIds={uni_id}"
                        with urllib.request.urlopen(urllib.request.Request(uni_url, headers={"User-Agent": "Mozilla/5.0"}), timeout=2) as u_resp:
                            u_data = json.loads(u_resp.read().decode('utf-8'))
                            if "data" in u_data and len(u_data["data"]) > 0:
                                root_id = u_data["data"][0].get("rootPlaceId")
                                if root_id:
                                    resolved_id = str(root_id)
            except Exception:
                pass

        add_recent_game(resolved_id, game_name)
        os.system(f"start roblox://placeId={resolved_id}")
    except Exception:
        pass

def pin_game(place_id, game_name="Roblox Game"):
    try:
        resolved_id = place_id
        if len(place_id) > 0:
            try:
                url = f"https://apis.roblox.com/universes/v1/places/{place_id}/universe"
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=2) as resp:
                    data = json.loads(resp.read().decode('utf-8'))
                    if "universeId" in data:
                        uni_id = data["universeId"]
                        uni_url = f"https://games.roblox.com/v1/games?universeIds={uni_id}"
                        with urllib.request.urlopen(urllib.request.Request(uni_url, headers={"User-Agent": "Mozilla/5.0"}), timeout=2) as u_resp:
                            u_data = json.loads(u_resp.read().decode('utf-8'))
                            if "data" in u_data and len(u_data["data"]) > 0:
                                root_id = u_data["data"][0].get("rootPlaceId")
                                if root_id:
                                    resolved_id = str(root_id)
            except Exception:
                pass

        add_favorite_game(resolved_id, game_name)
    except Exception:
        pass

def open_web_search(query):
    try:
        encoded = urllib.parse.quote(query)
        os.system(f"start https://www.roblox.com/discover?Keyword={encoded}")
    except Exception:
        pass

def open_privacy_page():
    open_url("https://www.roblox.com/my/account#!/privacy/VisibilityAndPrivateServers/Visibility")

def main():
    try:
        line = sys.stdin.readline() if sys.stdin else None
        query_text = ""
        
        if line and line.strip():
            try:
                request = json.loads(line.strip())
                method = request.get("method")
                params = request.get("parameters", [])

                if method == "launch_game":
                    if params:
                        gid = params[0]
                        gname = params[1] if len(params) > 1 else "Roblox Game"
                        launch_game(gid, gname)
                    print(json.dumps({"result": []}))
                    sys.stdout.flush()
                    return

                if method == "pin_game":
                    if params:
                        gid = params[0]
                        gname = params[1] if len(params) > 1 else "Roblox Game"
                        pin_game(gid, gname)
                    print(json.dumps({"result": []}))
                    sys.stdout.flush()
                    return

                if method == "open_web_search":
                    if params:
                        open_web_search(params[0])
                    print(json.dumps({"result": []}))
                    sys.stdout.flush()
                    return

                if method == "open_privacy":
                    open_privacy_page()
                    print(json.dumps({"result": []}))
                    sys.stdout.flush()
                    return

                if method == "open_url":
                    if params:
                        open_url(params[0])
                    print(json.dumps({"result": []}))
                    sys.stdout.flush()
                    return

                if isinstance(params, list) and len(params) > 0:
                    query_text = str(params[0])
                else:
                    query_text = str(request)
            except Exception:
                query_text = line.strip()
        else:
            query_text = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""

        if query_text.startswith("{"):
            try:
                parsed = json.loads(query_text)
                method = parsed.get("method")
                params = parsed.get("parameters", [])
                if method == "launch_game" and params:
                    gid = params[0]
                    gname = params[1] if len(params) > 1 else "Roblox Game"
                    launch_game(gid, gname)
                    print(json.dumps({"result": []}))
                    sys.stdout.flush()
                    return
                if method == "pin_game" and params:
                    gid = params[0]
                    gname = params[1] if len(params) > 1 else "Roblox Game"
                    pin_game(gid, gname)
                    print(json.dumps({"result": []}))
                    sys.stdout.flush()
                    return
                if method == "open_web_search" and params:
                    open_web_search(params[0])
                    print(json.dumps({"result": []}))
                    sys.stdout.flush()
                    return
                if method == "open_privacy":
                    open_privacy_page()
                    print(json.dumps({"result": []}))
                    sys.stdout.flush()
                    return
                if method == "open_url" and params:
                    open_url(params[0])
                    print(json.dumps({"result": []}))
                    sys.stdout.flush()
                    return
                query_text = str(params[0]) if params else ""
            except Exception:
                pass

        results = search_games(query_text)
        print(json.dumps({"result": results}))
        sys.stdout.flush()

    except Exception as e:
        error_result = {
            "result": [{
                "Title": "Error processing request",
                "SubTitle": str(e),
                "IcoPath": "icons/icon.png"
            }]
        }
        print(json.dumps(error_result))
        sys.stdout.flush()

if __name__ == "__main__":
    main()