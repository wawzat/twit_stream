# Retrives top 50 trends from twitter and tweets / tweets per minute for given keywords.
# James S. Lucas - 20200607
import config
import tweepy
from sys import stdout, argv
import datetime

# twitter API keys (jayyman55_pi):
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
        elapsed_time = datetime.datetime.now() - self.start_time
        if elapsed_time.seconds > 1:
            tweet = status.text
            words = tweet.split()
            message = ""
            for tag in self.tags:
                if tag in words:
                    self.dict_num_tweets[tag] += 1
                self.dict_tweet_rate[tag] = round(self.dict_num_tweets[tag] / elapsed_time.seconds * 60)
            for tag in self.tags:
                message = message + tag + ": " + str(self.dict_num_tweets[tag]) + " / " + str(self.dict_tweet_rate[tag]) + " | "
            stdout.write("\r | " + message + "            ")

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
    #WOEID = 2347563 # CA
    WOEID = 2442047 # Los Angeles
    #WOEID = 2347591 # New York State
    #WOEID = 2459115 # NYC
    trends_list = api.trends_place(WOEID)
    trends_dict = trends_list[0]
    trends = trends_dict['trends']
    names = [trend['name'] for trend in trends]
    trends_names = ' | '.join(names)
    print(" ")
    print(trends_names)


def main(tags):
    try:
        get_trends()
        # Start the tweepy SteamListner as asynchronous thread.
        # Jayyman55: (784864349546393600), wawzat: (17898527)
        myStreamListener = MyStreamListener(tags)
        myStream = tweepy.Stream(auth=api.auth, listener=myStreamListener)
        print(" ")
        myStream.filter(track=tags)

    except KeyboardInterrupt:
        print(" ")
        print("End by Ctrl-C")

if __name__ == "__main__":
    tags =[]
    if len(argv) > 1:
        for i, arg in enumerate(argv):
            if i > 0:
                tags.append(arg)
    else:
        tags = ['floyd', 'protest', 'blm', 'covid', 'biden', 'trump', 'love']
    main(tags)