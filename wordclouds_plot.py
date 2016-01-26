import ujson as json
import timeit, math, re, string, HTMLParser
from collections import defaultdict
from ark_twokenize import tokenizeRawTweetText
from NER_tagger import parse_raw_message_emoji
from count_keywords import build_stopsets
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import plotly.plotly as py
from plotly.graph_objs import *

p = re.compile(r'^#*[a-z]+[\'-/]*[a-z]*$', re.UNICODE)
pLink = re.compile(r'https*:\S+\.\w+', re.IGNORECASE)
pMention = re.compile(r'@[A-Za-z0-9_]+\b')
pNewLine = re.compile(r'[\r\n]+')
pRetweet = re.compile(r'\brt\b', re.IGNORECASE)
punctuation = {0x2018:0x27, 0x2019:0x27, 0x201C:0x22, 0x201D:0x22}
h = HTMLParser.HTMLParser()

def count_tweets_each_month(data_dir, fileName, MONTHS, stopset):

    month_dict = defaultdict(list)
    messages_dict = {}
    monthly_words_count = dict()

    for line in open(data_dir + fileName, "r"):
        tweet = json.loads(line.decode('utf-8'))

        if 'lang' in tweet:                
            language = tweet['lang']

            # Only process and analyze tweets written in English
            if language == 'en':
                
                msg_id = tweet['id']

                timestamp = tweet['created_at'].split()
                day = timestamp[0].strip(",")
                date = timestamp[1]
                month = timestamp[2]
                year = timestamp[3]
                two_digit_month = '%02d' % int(MONTHS.index(month)+1)

                month_dict[year + two_digit_month].append(msg_id)

                message = tweet['text']
                if "\n" in message:
                    new_message = message.replace("\n", " ")
                else:
                    new_message = message

                # customized function to parse messages with emoji and emoticons
                new_message = parse_raw_message_emoji(new_message)

                # ArkTweetNLP tokenizer
                tokens = tokenizeRawTweetText(new_message)

                new_tokens = []
                for word in tokens:
                    normalized_word = get_normalized_word(word.strip("\n"))
                    new_tokens.append(normalized_word)

                try:
                    monthly_words_count[year + two_digit_month] += len(new_tokens)
                except KeyError:
                    monthly_words_count[year + two_digit_month] = len(new_tokens)

                stopwords_removed_tokens = []
                for item in new_tokens:

                    # item = item.strip(string.punctuation).lower()
                    # if not(re.compile(r'^#*[a-z]+[\'-/]*[a-z]*$', re.UNICODE).match(item)):
                    #     return None
                    # print item, type(item)

                    if (item not in stopset) and (item is not None):
                        stopwords_removed_tokens.append(item)
                messages_dict[msg_id] = stopwords_removed_tokens

    print "Numbers of tweets in each month:"
    for k, v in sorted(month_dict.items(), key=lambda t: t[0]):
        print k, len(v)

    print "Numbers of normalized words in each month:"
    for k, v in sorted(monthly_words_count.items(), key=lambda t: t[0]):
        print k, v

    return month_dict, messages_dict, monthly_words_count

def get_normalized_word(word):
    """
    Returns normalized word or None, if it doesn't have a normalized representation.
    """
    if pLink.match(word):
        return '[http://LINK]'
    if pMention.match(word):
        return '[@SOMEONE]'
    if type(word) is unicode:
        word = word.translate(punctuation)
    if len(word) < 1:
        return None
    if word[0] == '#':
        word = word.strip('.,*;-:"\'`?!)(#').lower()
    else:
        word = word.strip(string.punctuation).lower()
    # if not(p.match(word)):
    #     return None

    return word

def plot_keyword_wordcloud_each_month(messages_dict, month_dict, word, img_dir):

    month_tokens_dict = {}

    for k, v in month_dict.items():

        month = k
        message_ids = v

        month_tokens_dict[month] = []

        for msg_id in message_ids:
            stopwords_removed_tokens = messages_dict[msg_id]

            month_tokens_dict[month] += stopwords_removed_tokens

    for k, v in month_tokens_dict.items():

        title = word.replace(" ", "_") + "_" + k
        print title

        text = ' '.join(v)
        text = text.replace("xa0", "")

        if " " in word:
            text = ' '.join([i for i in text.split() if i not in word.split(" ")])
        else:
            text = ' '.join([i for i in text.split() if i not in [word]])

        plot_word_cloud(text, title, img_dir)

def always_black(word=None, font_size=None, position=None,
                 orientation=None, font_path=None, random_state=None):
    """
        Always return black color for font
    """
    return "black"

def plot_word_cloud(text, title, img_dir):

    wordcloud = WordCloud(color_func=always_black, background_color='white').generate(text)
    # Open a plot of the generated image.
    plt.imshow(wordcloud)
    plt.axis("off")
    plt.title('word cloud for ' + title + ' tweets')
    plt.savefig(img_dir + title + '.png')

def plot_word_produced_tweets(monthly_words_count, word):

    month_array = []
    count_array = []
    for k, v in sorted(monthly_words_count.items(), key=lambda t: t[0]):        
        month_array.append(k[:4] + '_' + k[4:])
        count_array.append(v)

    trace = Scatter(
        x = month_array,
        y = count_array,
        mode = 'lines',
        name = 'lines'
    )
    data = [trace]
    layout = Layout(
        title = 'The number of words per one month sample period that ' + word + ' produced',
        width = 1500,
        xaxis = XAxis(
            title = 'each month'
        ),
        yaxis = YAxis(
            title = 'numbers of normalized words'
        )
    )
    fig = Figure(
        data = data,
        layout = layout
    )
    plot_url = py.plot(fig, filename = word + '_produced_words_counts.png')

def main():
    # mark the beginning time of process
    start = timeit.default_timer()

    EVENT = 'Mon, 11 Aug 2014'
    MONTHS = [u'Jan', u'Feb', u'Mar', u'Apr', u'May', u'Jun', u'Jul', u'Aug', u'Sep', u'Oct', u'Nov', u'Dec']

    keywords = ['suicide', 'depression', 'seek help', 'suicide lifeline', 'crisis hotline', 'Parkinson\'s disease', 'Robin Williams']

    stopset = build_stopsets()

    data_dir = "/Users/tl8313/Documents/study_robinwilliams/extracted/"

    suicide_json = "suicide.json"
    depression_json = "depression.json"
    seekhelp_json = "seek_help.json"
    suicidelifeline_json = "suicide_lifeline.json"
    crisishotline_json = "crisis_hotline.json"
    parkinsons_json = "parkinsons.json"
    robinwilliams_json = "robin_williams.json"

    json_files = [suicide_json, depression_json, seekhelp_json, suicidelifeline_json, crisishotline_json, parkinsons_json, robinwilliams_json]

    img_dir = "/Users/tl8313/Documents/study_robinwilliams/figures/"

    suicidelifeline_month_dict, suicidelifeline_messages, suicidelifeline_monthly_words_count = count_tweets_each_month(data_dir, suicidelifeline_json, MONTHS, stopset)

    # plot_keyword_wordcloud_each_month(suicidelifeline_messages, suicidelifeline_month_dict, keywords[3].lower(), img_dir)

    for word_file in zip(keywords, json_files):
        word = word_file[0].lower()
        jsonfile = word_file[1]
        print word, jsonfile

        month_dict, messages, monthly_words_count = count_tweets_each_month(data_dir, jsonfile, MONTHS, stopset)
        plot_word_produced_tweets(monthly_words_count, word)
        # plot_keyword_wordcloud_each_month(messages, month_dict, word, img_dir)

    ##### mark the ending time of process #####
    end = timeit.default_timer()
    seconds = math.ceil(end - start)
    # Convert Secs Into Human Readable Time String (HH:MM:SS)
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    print "This process took %d:%02d:%02d" % (h, m, s)
    
if __name__ == '__main__':
    main()