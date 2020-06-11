# Retrives top 50 trends from twitter and tweets / tweets per minute for given keywords.
# To do: Sentiment analysis
# Store Twitter API Keys and Tokens in a file named config.py
# James S. Lucas - 20200611
import config
import tweepy
from sys import stdout, argv
import datetime
from operator import itemgetter

# twitter API keys:
API_KEY = config.API_KEY 
API_SECRET = config.API_SECRET 
ACCESS_TOKEN = config.ACCESS_TOKEN 
ACCESS_TOKEN_SECRET = config.ACCESS_TOKEN_SECRET

# tweepy auth for twitter
auth = tweepy.OAuthHandler(API_KEY, API_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
api = tweepy.API(auth)


# tweepy SteamListner Class
class MyStreamListener(tweepy.StreamListener):
    def __init__(self, tags):
        super(MyStreamListener, self).__init__()
        self.num_riot = 0
        self.start_time = datetime.datetime.now() 
        self.tags = tags
        self.dict_num_tweets = { i : 0 for i in self.tags}
        self.dict_tweet_rate = { i : 0 for i in self.tags}

    def on_status(self, status):
        #print(status.text)
        #positive_words = ['love', 'wonderful', 'best', 'great', 'superb', 'beautiful']
        #negative_words = ['bad', 'worst', 'stupid', 'waste', 'boring', '?', '!']
        elapsed_time = datetime.datetime.now() - self.start_time
        if elapsed_time.seconds > 1:
            message = ""
            tweet = status.text
            #words = tweet.split()
            for tag in self.tags:
                if tag.upper() in tweet.upper():
                    self.dict_num_tweets[tag] += 1
                self.dict_tweet_rate[tag] = round(self.dict_num_tweets[tag] / elapsed_time.seconds * 60)
            for tag in self.tags:
                message = message + tag + ": " + str(self.dict_num_tweets[tag]) + " / " + str(self.dict_tweet_rate[tag]) + " | "
            stdout.write("\r | " + message + "  ")

    # on_direct_message isn't working for some reason but not implemented in program so no worries
    def on_direct_message(self, status):
        print("Entered on_direct_message()")
        try:
            print(status.text)
            return True
        except BaseException as e:
            print("Failed on_direct_message()", str(e))    

    def on_error(self, status_code):
        # Status code 420 is too many connections in time period. 10 second rate limit increases exponentially for each 420 error
        if status_code == 420:
            print("Error 420, Twitter rate limit in effect")
            #returning False in on_data disconnects the stream
            return False


def get_trends():
    #WOEID = 1 # World
    #WOEID = 23424977 # USA
    #WOEID = 2347563 # CA (Not working)
    #WOEID = 2442047 # Los Angeles
    #WOEID = 2347591 # New York State (Not working)
    #WOEID = 2459115 # NYC
    #WOEID_dict = {'World': 1, 'USA': 23424977, 'CA': 2347563, 'LA': 2442047, 'New York State': 2347591, 'NYC': 2459115}
    #WOEID_dict = {'World': 1, 'NYC': 2459115, 'LA': 2442047, 'USA': 23424977}
    WOEID_dict = {'USA': 23424977}
    for k, v in WOEID_dict.items():
        data = api.trends_place(v, '#')
        trends = data[0]["trends"]
        # Remove trends with no Tweet volume data
        trends = filter(itemgetter("tweet_volume"), trends)
        # Alternatively, using 0 during sorting would work as well:
        # sorted(trends, key=lambda trend: trend["tweet_volume"] or 0, reverse=True)
        sorted_trends = sorted(trends, key=itemgetter("tweet_volume"), reverse=True)
        #top_10_trend_names = '\n'.join(trend['name'] for trend in sorted_trends[:10])
        #with open("trends.txt", 'w') as trends_file:
            #print(top_10_trend_names, file=trends_file)
        names = [trend['name'] for trend in sorted_trends]
        trends_names = ' | '.join(names)
        print(" ")
        print(k)
        print("| " + trends_names + " |")


def main(tags):
    try:
        get_trends()
        # Start the tweepy SteamListner as asynchronous thread.
        myStreamListener = MyStreamListener(tags)
        myStream = tweepy.Stream(auth=api.auth, listener=myStreamListener)
        print(" ")
        myStream.filter(track=tags)
    except KeyboardInterrupt:
        print(" ")
        print("End by Ctrl-C")
        myStream.disconnect()
        exit()


if __name__ == "__main__":
    tags =[]
    if len(argv) > 1:
        for i, arg in enumerate(argv):
            if i > 0:
                tags.append(arg)
    else:
        tags = ['floyd', 'protest', 'blm', 'covid', 'biden', 'trump', 'love']
    main(tags)