from flask import Flask,request,render_template,redirect
from io import BytesIO
from flask import send_file, make_response
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import tweepy,twitter_credentials
from tweepy import OAuthHandler,Stream
from clean_data import clean_text
from textblob import TextBlob


import matplotlib.pyplot as plt
plt.style.use('ggplot')

app = Flask('__name__')

auth = OAuthHandler(twitter_credentials.ckey,twitter_credentials.csecret)
auth.set_access_token(twitter_credentials.atoken,twitter_credentials.asecret)

api = tweepy.API(auth)

#----------------------- Trending Topics --------------#
@app.route('/')
def home(): 
    tweets =[]
    trends_result = api.trends_place(1)
    for trend in trends_result[0]["trends"][:7]:
        trend = trend['name']
        hash = trend.startswith('#')
        if hash:
            tweets.append(trend)
        else:
            with_hash = '#'+trend
            tweets.append(with_hash)
        
    return render_template('index.html',tweets=tweets)
   
@app.route('/profile',methods=['POST'])
def profile():
    data ={}
    e=''
    home()
    try:
        if request.method == "POST":
            # Profile data
            text = request.form['profile']
            user = api.get_user(text)
            data['name'] = user.name
            data['twitter_profile']='@'+user.screen_name
            data['location'] =user.location
            data['description'] = user.description
            data['followers'] = user.followers_count
            data['following'] = user.friends_count
            data['profile_created'] = user.created_at
            
            #Tweet data
            tweets = user.status
            data['recent_tweet'] = tweets.text
            data['tweet_created'] = tweets.created_at
            data['retweet'] = tweets.retweet_count
            data['favorited'] = tweets.favorite_count

    except:
        e = "Sorry! I can't found this user. Please Enter Properly.."
    print(type(data))
    return render_template('index.html',data=data,
                                        name = data['name'],
                                        twitter_profile = data['twitter_profile'],
                                        location = data['location'],
                                        descripption = data['description'],
                                        followers = data['followers'],
                                        following = data['following'],
                                        profile_created = data['profile_created'],
                                        recent_tweet = data['recent_tweet'],
                                        tweet_created = data['tweet_created'],
                                        retweet_count = data['retweet'],
                                        favorite_count = data['favorited'], 
                                        e=e)
  #------------------ Twitter Sentiment Analysis --------------------#

@app.route('/sentiment',methods=['POST'])

def sentiment():

    if request.method == "POST":
        search_term = request.form['search_term']
        count = int(request.form['count'])
        tweets = tweepy.Cursor(api.search,q=search_term).items(count)

        positive =0
        negative =0
        neutral = 0
        polarity =0

        def percentage(part,whole):
            return 100*float(part)/float(whole)


        for data in tweets:
            tweet = data.text
            tweet = clean_text(tweet)

            analysis = TextBlob(tweet)
            polarity +=analysis.sentiment.polarity

            if analysis.sentiment.polarity ==0.00:
                neutral +=1
            elif analysis.sentiment.polarity >0.00:
                positive +=1
            elif analysis.sentiment.polarity <0.00:
                negative +=1

        positivity  = percentage(positive,count)
        negativity  = percentage(negative,count)
        neutrality  = percentage(neutral,count)
        reaction = polarity/count

        positive = format(positivity,'.2f')
        negative = format(negativity,'.2f')
        neutral = format(neutrality,'.2f')

        labels =['Positive['+str(positivity)+'%]','Negative['+str(negativity)+'%]','Neutral['+str(neutrality)+'%]']
            
        sizes = [positivity,negativity,neutrality]
        colors =['green','red','orange']
        fig,ax = plt.subplots()
        ax.pie(sizes,colors=colors,labels=labels,autopct='%1.1f%%', startangle=90, pctdistance=0.85,)
        inner_circle = plt.Circle((0,0),0.70,fc='white')

        fig = plt.gcf()
        fig.gca().add_artist(inner_circle)
        ax.axis('equal') 
        plt.title('People reaction on '+"'"+search_term.capitalize()+"'"+' by analyzing '+str(count)+' Tweets') 
        #ax.set_title("Course Attendance\n",fontsize=24)
        plt.tight_layout()
        canvas = FigureCanvas(fig)
        img = BytesIO()
        fig.savefig(img)
        img.seek(0)
        return send_file(img, mimetype='image/png')

    

if __name__ == '__main__':
    app.run(debug=False)
