# Retrives top 50 trends from twitter and tweets / tweets per minute for given keywords.
# Performs rudimentary sentiment scoring
# Store Twitter API Keys and Tokens in a file named config.py
# To do: for - in searches are matching partial words (i.e., lie in believe)
# James S. Lucas - 20200616
import config
import tweepy
from sys import stdout, argv
import datetime
from operator import itemgetter
import argparse
import csv

# twitter API keys:
API_KEY = config.API_KEY 
API_SECRET = config.API_SECRET 
ACCESS_TOKEN = config.ACCESS_TOKEN 
ACCESS_TOKEN_SECRET = config.ACCESS_TOKEN_SECRET

# tweepy auth for twitter
auth = tweepy.OAuthHandler(API_KEY, API_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
api = tweepy.API(auth)


def get_arguments():
    parser = argparse.ArgumentParser(
    description='get current trends and stats for given topics from Twitter.',
    prog='twit_stream',
    usage='%(prog)s [-l <locations>] [-k <keywords>] [-c]',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    g=parser.add_argument_group(title='arguments',
          description='''   -l, --locations <trend location(s)>     optional.  enter trend locations.
   -k, --keywords <keywords>               optional.  enter keywords to search in stream.
   -c, --csv                               optional.  save tweets and score to csv file tweets.csv         ''')
    g.add_argument('-l', '--locations',
                    type=str,
                    default=['USA'],
                    nargs = '*',
                    choices = [
                        'World', 'NYC', 'LA', 'USA'
                        ],
                    metavar='',
                    dest='locations',
                    help=argparse.SUPPRESS)
    g.add_argument('-k', '--keywords',
                    type=str,
                    default=['biden', 'trump', 'dnc', 'rnc'],
                    nargs = '*',
                    metavar='',
                    dest='keywords',
                    help=argparse.SUPPRESS)
    g.add_argument('-c', '--csv', action='store_true',
                    dest='csv',
                    help=argparse.SUPPRESS)
    args = parser.parse_args()
    return(args)


# tweepy SteamListner Class
class MyStreamListener(tweepy.StreamListener):
    def __init__(self, tags, args):
        super(MyStreamListener, self).__init__()
        self.start_time = datetime.datetime.now() 
        self.tags = tags
        self.args = args
        self.dict_num_tweets = { i : 0 for i in self.tags}
        self.dict_tweet_rate = { i : 0 for i in self.tags}
        self.dict_sentiment = { i : 0 for i in self.tags}

    def on_status(self, status):
        #print(status.text)
        csv_output_file = r"D:\Users\James\OneDrive\Documents\Raspberry Pi-Matrix5\JSL Python Code\Twitter\tweets.csv"
        row = []
        tweet_score = 0
        positive_words = [
            'amazing', 'beautiful', 'begin', 'best', 'better', 'celebrate', 'celebrating', 'creative', 'fabulous',
            'fight', 'great', 'happy', 'incredible', 'leader', 'pleased', 'positive', 'potential', 'ready',
            'superb', 'support biden', 'support trump', 'voting', 'win', 'wonderful', 'trump2020', 'biden2020'
            ]
        negative_words = [
            'against', 'afraid', 'anyone voting', 'bad', 'bs', 'cheat', 'cheeto', 'creepy', 'crying', 'deny', 'detest', 'despite',
            'devisive', 'embarrass', 'evil', 'fail', 'fake', 'feeble', 'fraud', 'garbage', 'hell', 'homophobe', 'hoax', 'idiot',
            'leftist', 'liar', 'lying', 'loser', 'losing', 'misinformation', 'not', 'outrage', 'orange', 'painful', 'pedophile',
            'racism', 'racist', 'rapist', 'rid', 'stupid', 'sleepy', 'sucks',
            'upset', 'useless', 'waste', 'weak', 'wing', 'worst'
            ]
        elapsed_time = datetime.datetime.now() - self.start_time
        if elapsed_time.seconds > 1:
            message = ""
            try:
                tweet = status.extended_tweet["full_text"]
            except AttributeError:
                tweet = status.text
            #words = tweet.split()
            for tag in self.tags:
                if not tweet.startswith('RT'):
                    if tag.upper() in tweet.upper():
                        self.dict_num_tweets[tag] += 1
                        for pos_word in positive_words:
                            if pos_word.upper() in tweet.upper():
                                self.dict_sentiment[tag] += 1
                                tweet_score += 1
                                break
                        for neg_word in negative_words:
                            if neg_word.upper() in tweet.upper():
                                self.dict_sentiment[tag] -= 1
                                tweet_score -= 1
                                break
                        if self.args.csv:
                            with open(csv_output_file, 'a', encoding='utf_8_sig', newline='') as f_output:
                                csv_output = csv.writer(f_output)
                                row.append(tag)
                                if tweet_score > 0:
                                    word = pos_word
                                elif tweet_score < 0:
                                    word = neg_word
                                else:
                                    word = " "
                                row.append(word)
                                row.append(tweet_score)
                                row.append(status.author.screen_name)
                                row.append(status.source)
                                row.append(tweet)
                                csv_output.writerow(row)
                                row = []
                                tweet_score = 0
                self.dict_tweet_rate[tag] = round(self.dict_num_tweets[tag] / elapsed_time.seconds * 60)
            for tag in self.tags:
                if self.dict_num_tweets[tag] != 0:
                    sentiment_pct = round(self.dict_sentiment[tag] / self.dict_num_tweets[tag], 2)
                else:
                    sentiment_pct = 0
                message = (
                    message + tag + ": " + str(self.dict_num_tweets[tag])
                    + " / " + str(sentiment_pct)
                    + " / " + str(self.dict_tweet_rate[tag])
                    + " | "
                   )
            stdout.write("\r | " + message + "  ")

    def on_error(self, status_code):
        # Status code 420 is too many connections in time period. 10 second rate limit increases exponentially for each 420 error
        if status_code == 420:
            print("Error 420, Twitter rate limit in effect")
            #returning False in on_data disconnects the stream
            return False


def get_trends(args):
    WOEID_dict = {'World': 1, 'NYC': 2459115, 'LA': 2442047, 'USA': 23424977}
    locations = args.locations
    for location in locations:
        data = api.trends_place(WOEID_dict.get(location), '#')
        trends = data[0]["trends"]
        # Remove trends with no Tweet volume data
        trends = filter(itemgetter("tweet_volume"), trends)
        sorted_trends = sorted(trends, key=itemgetter("tweet_volume"), reverse=True)
        names = [trend['name'] for trend in sorted_trends]
        trends_names = ' | '.join(names)
        print(" ")
        print(location)
        print("| " + trends_names + " |")


def main():
    try:
        args = get_arguments()
        tags = args.keywords
        get_trends(args)
        # Start the tweepy SteamListner as asynchronous thread.
        myStreamListener = MyStreamListener(tags, args)
        myStream = tweepy.Stream(auth=api.auth, listener=myStreamListener, tweet_mode='extended')
        print(" ")
        myStream.filter(track=tags)
    except KeyboardInterrupt:
        print(" ")
        print("End by Ctrl-C")
        myStream.disconnect()
        exit()


if __name__ == "__main__":
    main()