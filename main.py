import requests
import bs4
import pandas as pd
import streamlit as st
import altair as alt

# query = input("Enter a show name: ")

def get_show_from_completion_box(query):
    URL = "https://79frdp12pn-dsn.algolia.net/1/indexes/*/queries"
    ORIGIN = "https://www.rottentomatoes.com"
    REFERER = "https://www.rottentomatoes.com/"

    SHOW_URL_PREFIX = "https://www.rottentomatoes.com/tv/"

    query_params = {
        "x-algolia-agent": "Algolia for JavaScript (4.22.0); Browser (lite)",
        "x-algolia-api-key": "175588f6e5f8319b27702e4cc4013561",
        "x-algolia-application-id": "79FRDP12PN"
    }

    data = {
        "requests": [{
                "indexName": "content_rt",
                "query": query,
                # "params": "filters=isEmsSearchable%20%3D%201&hitsPerPage=5&analyticsTags=%5B%22header_search%22%5D&clickAnalytics=true"
            }
        ]
    }

    headers = {
        "content-type": "application/json",
        "origin": ORIGIN,
        "referer": REFERER
    }

    response = requests.post(URL, json=data, params=query_params, headers=headers)

    # get the first item under results.hits list
    show_item = response.json()["results"][0]["hits"][0]
    show_url = show_item["vanity"]
    show_title = show_item["title"]

    return show_title, show_url

def get_show_from_keyword(query):
    SEARCH_URL = 'https://www.rottentomatoes.com/search?search='
    # decode query to url format
    query = requests.utils.quote(query)
    response = requests.get(SEARCH_URL + query)
    page_html = response.text

    # get <search-page-result> item with type=tvSeries
    soup = bs4.BeautifulSoup(page_html, "html.parser")
    search_results = soup.find_all("search-page-result")
    show_item = None
    for result in search_results:
        if result["type"] == "tvSeries":
            show_item = result
            break
    
    # get first <search-page-media-row> item
    media_row = show_item.find("search-page-media-row")

    # get tomatometerscore attribute of <search-page-media-row>
    score = media_row["tomatometerscore"]
    if score == "":
        # get next <search-page-media-row> item
        media_row = media_row.find_next_sibling("search-page-media-row")
    
    # get second <a> tag under <search-page-media-row>
    show_item = media_row.find_all("a")[1]

    show_url = show_item["href"]
    show_title = show_item.text.strip()

    return show_title, show_url

def get_score_per_season(show_title, show_url):
    print(f"Seasons for {show_title}:")
    
    # trim any text before /tv/
    show_url = show_url[show_url.find("/tv/"):]
    
    # find potential slash after /tv/ and remove it and all text after it
    slash_index = show_url.find("/", 4)
    if slash_index != -1:
        show_url = show_url[:slash_index]
    
    show_url = f"https://www.rottentomatoes.com{show_url}"    
    
    # HTTP GET request to the show url
    response = requests.get(show_url)

    page_html = response.text

    # using beautiful soup, get first item of type <section> with id="seasons-list"
    soup = bs4.BeautifulSoup(page_html, "html.parser")
    seasons_list = soup.find("section", {"id": "seasons-list"})

    # get all <a> tags under seasons_list; get the <season-list-item> item under each <a> tag
    seasons = seasons_list.find_all("a")
    seasons = [season.find("season-list-item") for season in seasons]

    # for each item, list the attributes of the <season-list-item> tag, and store them in a dictionary
    seasons_info = []
    for season in seasons:
        season_info = {}
        for attr in season.attrs:
            season_info[attr] = season[attr]

        season_info["episodes"] = int(season["info"].split(",")[-1].strip().split(" ")[0])
        if season_info["episodes"] == 0:
            continue
            
        season_info["year"] = int(season["info"].split(",")[0].strip())

        seasons_info.append(season_info)

    # sort seasons by year, and print season names and value of the tomatometerscore attribute 
    seasons_info.sort(key=lambda season: season["year"])

    return seasons_info

def categorize_show_improved(seasons_list):
    # Extracting scores and number of episodes from each season's data
    scores = [int(season['tomatometerscore']) for season in seasons_list]
    episodes = [season['episodes'] for season in seasons_list]

    # Defining thresholds and criteria
    high_score_threshold = 80
    significant_drop = 15

    # Function to find a significant drop in score
    def significant_drop_occurs(scores):
        for i in range(1, len(scores)):
            if scores[i] < scores[i - 1] - significant_drop and scores[i] < high_score_threshold:
                return True, i  # Returns True and the season where the drop occurs
        return False, None

    # Function to check for recovery after the drop
    def recovery_after_drop(scores, drop_season):
        for score in scores[drop_season:]:
            if score >= high_score_threshold:
                return True
        return False

    drop_occurs, drop_season = significant_drop_occurs(scores)

    # Categorization Logic
    if drop_occurs:
        if recovery_after_drop(scores, drop_season):
            return f"Drop in quality but recovers after Season {drop_season}"
        else:
            return f"Stop watching after Season {drop_season}"
    else:
        # If no significant drop, analyze based on overall quality
        if all(score >= high_score_threshold for score in scores):
            return "Consistently High Quality"
        elif all(score < high_score_threshold for score in scores):
            return "Consistently Low Quality"
        else:
            return "Varied Quality"

def main():
    # Create a streamlit page with a search box to enter a show name
    # When the user presses Enter in the search box, get the show name from the search box
    # Use the show name to get the show url
    # Use the show url to get the seasons info
    # Display the seasons info in a table

    st.title("Rotten Tomatoes TV Show Ratings")

    query = st.text_input("Enter a show name:")
    if query == "":
        return
    
    tv_show = get_show_from_keyword(query)
    if tv_show is None:
        st.write("No show found")
        return
    
    st.write(f"Link to show page:")
    st.link_button(tv_show[0], f"https://www.rottentomatoes.com{tv_show[1]}")

    st.write(f"Seasons for {tv_show[0]}:")
    seasons_info = get_score_per_season(*tv_show)
    
    # Write scores per season to a table
    df = pd.DataFrame(seasons_info)
    df = df[["seasontitle", "year", "episodes", "tomatometerscore"]]
    df.columns = ["Season", "Year", "Number of Episodes", "Score"]
    st.table(df)

    # if not all scores are numbers, return
    if not all(df["Score"].str.isnumeric()):
        st.write("Incomplete Score Data")
        return

    # turn score to integer
    df["Score"] = df["Score"].astype(int)

    # show the scores as an altair graph. The Y-axis should be sorted by its integer value, not by its string value
    chart = alt.Chart(df).mark_line().encode(
        x="Season",
        y=alt.Y("Score", sort="-x")
    )

    # add a red dotted threshold line at 80
    threshold = alt.Chart(pd.DataFrame({"threshold": [80]})).mark_rule(color="red", strokeDash=[5, 5]).encode(
        y="threshold"
    )

    # draw the chart
    st.altair_chart(chart + threshold, use_container_width=True)
    
    st.header("Recommendation")
    recommendation = categorize_show_improved(seasons_info)
    st.write(recommendation)





def main_debug():
    tv_show = get_show_from_keyword("rick and morty")
    seasons_info = get_score_per_season(*tv_show)

def get_list_of_shows(page_number):
    SHOWS_URL = "https://www.rottentomatoes.com/browse/tv_series_browse/sort:popular?page="
    response = requests.get(SHOWS_URL + page_number)
    page_html = response.text
    soup = bs4.BeautifulSoup(page_html, "html.parser")

    # get all <a> where href starts with "/tv/"
    show_items = soup.find_all("a", href=lambda href: href and href.startswith("/tv/"))

    # get the href attribute of each <a> tag, and get the title from the text of the first span inside the <a> tag
    shows = []
    for show in show_items:
        show_url = show["href"]
        show_title = show.find("span").text.strip()

        if "Season " in show_title:
            continue

        print(show_title)
        shows.append((show_title, show_url))

    return shows

def main2():
    shows = get_list_of_shows("5")
    # tv_show = get_show_from_keyword(query)

    for tv_show in shows:
        seasons_info = get_score_per_season(*tv_show)
        if seasons_info is None:
            continue

        # save all seasons infor to a csv file, with row per show, and columns per season
        f = open("shows.csv", "a")
        f.write(tv_show[0])
        for season in seasons_info:
            f.write(f",{season['tomatometerscore']}")
        f.write("\n")
        f.close()


if __name__ == '__main__':
    main()
