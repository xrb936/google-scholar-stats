from scholarly import scholarly
import json
import os
import time
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.json")
RESULTS_DIR = os.path.join(SCRIPT_DIR, "results")


def setup_proxy():
    proxy_url = os.environ.get("SOCKS5_PROXY")
    if not proxy_url:
        print("No SOCKS5_PROXY env var set, using direct connection.")
        return
    proxies = {"http": proxy_url, "https": proxy_url}
    nav = scholarly._Scholarly__nav
    nav._session1.proxies = proxies
    nav._session2.proxies = proxies
    print("SOCKS5 proxy configured.")


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def fetch_scholar(scholar_id, name=""):
    print(f"[{name or scholar_id}] Fetching Google Scholar profile...")
    author = scholarly.search_author_id(scholar_id)
    scholarly.fill(author, sections=["basics", "indices", "counts", "publications"])

    pubs = {}
    for p in author.get("publications", []):
        pub_id = p.get("author_pub_id", "")
        if pub_id:
            pubs[pub_id] = {
                "title": p.get("bib", {}).get("title", ""),
                "num_citations": p.get("num_citations", 0),
                "pub_year": p.get("bib", {}).get("pub_year", ""),
            }

    result = {
        "scholar_id": scholar_id,
        "name": author.get("name", name),
        "affiliation": author.get("affiliation", ""),
        "citedby": author.get("citedby", 0),
        "hindex": author.get("hindex", 0),
        "i10index": author.get("i10index", 0),
        "cites_per_year": author.get("cites_per_year", {}),
        "publications": pubs,
        "updated": datetime.now().isoformat(),
    }

    print(f"  Citations: {result['citedby']}, h-index: {result['hindex']}, "
          f"i10-index: {result['i10index']}, Papers: {len(pubs)}")
    return result


def main():
    setup_proxy()

    config = load_config()
    scholars = config.get("scholars", [])

    if not scholars:
        print("No scholars configured in config.json")
        return

    os.makedirs(RESULTS_DIR, exist_ok=True)

    for i, entry in enumerate(scholars):
        if i > 0:
            print("Waiting 5 minutes before next scholar...")
            time.sleep(300)

        scholar_id = entry["id"]
        name = entry.get("name", "")
        try:
            data = fetch_scholar(scholar_id, name)

            out_path = os.path.join(RESULTS_DIR, f"{scholar_id}.json")
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"  Saved to results/{scholar_id}.json")

        except Exception as e:
            print(f"  ERROR fetching {scholar_id}: {e}")

    print("Done.")


if __name__ == "__main__":
    main()
