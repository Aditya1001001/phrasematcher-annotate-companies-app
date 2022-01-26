import streamlit as st
from spacy import displacy
import spacy
from spacy.matcher import PhraseMatcher

import streamlit as st
import streamlit.components.v1 as components



st.set_page_config(
   page_title="Using PhraseMatcher To Label Data",
   page_icon="🛠",
   layout="wide",
   initial_sidebar_state="expanded",
   menu_items={
        "Get help": None,
        "Report a Bug": None,
        "About": None
            }
)

@st.experimental_singleton
def prepare_matcher():

    nlp = spacy.load("en_core_web_sm")

    matcher = PhraseMatcher(nlp.vocab)

    names, symbols = [], []

    with open("names.txt", "r") as f:
        names = f.readlines()

    with open("symbols.txt", "r") as f:
        symbols = f.readlines()

    patterns = [nlp.make_doc(name.strip()) for name in names]
    matcher.add("ORG", patterns)

    patterns = [nlp.make_doc(symbol.strip()) for symbol in symbols]
    matcher.add("TICKER", patterns)

    return nlp, matcher

nlp, matcher = prepare_matcher()

st.markdown("## Annotate Organization Names & Stock Tickers")

st.write("spaCy's PhraseMatcher class enables us to efficiently match large \
    lists of phrases. In this app, we use it to annotate organization names \
        and stock ticker symbols.")
st.write("To learn more about spaCy's PhraseMatcher, read our in-depth article \
    [here](https://newscatcherapi.com/blog/ultimate-guide-to-text-similarity-with-python).")


text = st.text_area("Enter the text you want to label", value="Microsoft (MSFT) \
    dipped 2.4% after announcing the software giant will buy video game company\
    Activision Blizzard (ATVI) in an all-cash transaction valued at $68.7\
    billion. Shares of Activision Blizzard surged 25.9%. \nThe shortened\
    trading week will feature quarterly reports from 35 companies in the \
    S&P 500, including Bank of America (BAC), UnitedHealth (UNH), and \
    Netflix (NFLX).",
    help = 'Text to label', placeholder = 'Enter the text you want to label', height = 200)

st.sidebar.markdown("### What Do You Want To Match For?")
match_org = st.sidebar.checkbox('Organization Names', value = True, help = "Do you want to match for organization names?")
match_ticker = st.sidebar.checkbox('Ticker Symbols', value = True, help = "Do you want to \
        match for organization ticker symbols?")

flag = st.sidebar.button('Annotate Text')

if flag:
    if len(text) == 0:
        st.markdown("### Please Enter Some Text To Match For 🤗")
    else:
        doc = nlp(text)
        matches = matcher(doc)
        plot_data = {
                    "text": doc.text,
                    "ents": [],
                    "title": None
                }

        if len(matches) == 0:
            st.markdown("### No Organization(s) Found 😥")
        else:
            # displacy options
            colors = {"ORG": "#F67DE3", "TICKER": "#7DF6D9"}
            options = {"colors": colors}

            
            with st.spinner("Labelling Text..."):
                matches_with_dup = {"ORG":{}, "TICKER": {}}
                for match_id, span_start, span_end in matches:

                    rule_id = nlp.vocab.strings[match_id]
                    text = doc[span_start: span_end].text
                    start_idx = doc.text.index(doc[span_start].text)
                    end_idx = start_idx + len(text)

                    if match_org and match_ticker:
                        matches_with_dup[rule_id][text] = {"start": start_idx, "end": end_idx, "label": rule_id}
                    elif match_org and not match_ticker:
                        if rule_id == "ORG":
                            matches_with_dup[rule_id][text] = {"start": start_idx, "end": end_idx, "label": rule_id}
                    elif not match_org and match_ticker:
                        if rule_id == "TICKER":
                            matches_with_dup[rule_id][text] = {"start": start_idx, "end": end_idx, "label": rule_id}

                # substring names/symbols will appear multiple times but the expanded 
                # longest versions of the names/symbols will appear only once    

                for ent_type in matches_with_dup.keys():
                    matches = matches_with_dup[ent_type]
                    keys = matches.keys()
                    counts = {text:0 for text in keys}
                    for text in keys:
                        for key in keys:
                            if text in key:
                                counts[text] += 1
                    for text, count in counts.items():
                        if count == 1:
                            plot_data['ents'].append(matches[text])
                
                plot_data['ents'] = sorted(plot_data['ents'], key=lambda ent: ent["start"]) 
            
                st.markdown("### Labeled Data")
                html = displacy.render(plot_data , style="ent", options=options, manual=True, page =True)
                components.html(html, height = 500, scrolling  = True)