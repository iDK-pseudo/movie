from flask import Flask,render_template,g,request
import sqlite3
import requests
from random import randint

app = Flask(__name__)

def connect_db():
	sql= sqlite3.connect("genres.db")
	sql.row_factory = sqlite3.Row
	return sql

def get_db():
	if not hasattr(g,'sqlite3'):
		g.sqlite_db=connect_db()
	return g.sqlite_db

@app.teardown_appcontext
def close_db(error):
	if hasattr(g,'sqlite_db'):
		g.sqlite_db.close()



#Routes used -



# HOMEPAGE
@app.route('/',methods=['GET','POST'])
def main():
	titles,images = movies_playing()
	return render_template('homepage.html',titles=titles,images=images)



# Discover/ Suprise Me

@app.route('/discover',methods=['GET','POST'])
def discover():
	return render_template('discover.html')


# Result Page of Discover

@app.route('/result/<genre>',methods=['GET','POST'])
def result(genre):
	db = get_db()
	
	cur = db.execute("select id from genres where name = (?)",[genre])
	result = cur.fetchone()

	titles,images,year,overview = find_data(result['id'])
	ratings = extra_details(titles)

	return render_template('result.html',genre = genre.upper(),titles = titles,images= images,year = year,overview=overview,ratings = ratings)



# Result Page of Movie

@app.route('/result_page/<title>',methods=['GET','POST'])
def result_page(title):

	result = {}

	if(request.method == "POST"):
		result = request.form
		title = str(result['search'])

	rating = extra_details([title])
	image,title,overview,released,writer,director,ratings,actors = find_movie_data(title)

	data = {'image':image,'title':title,'overview':overview,'released':released,'writer':writer,'director':director,'ratings':ratings,'actors':actors}
	return render_template('result_page.html',data = data)





# Functions used


# used by RESULT PAGE

def find_movie_data(title):
	url = "http://www.omdbapi.com/?i=tt3896198&apikey=5615edda&t="+title.replace(" ","+")
	api_key = "4b4170d57736cacfad0eaba78f8bed58"
	image_base_url = "https://image.tmdb.org/t/p/w500"
	

	res = requests.get(url,headers= {"Accept":"application/json"}).json()
	id = res['imdbID']
	released = res['Released']
	writer = res['Writer']
	director = res['Director']
	ratings = res['Ratings']
	actors = res['Actors']

	url =  "https://api.themoviedb.org/3/find/{}?api_key={}&language=en-US&external_source=imdb_id".format(id,api_key)
	res = requests.get(url,headers= {"Accept":"application/json"}).json()
	
	image = image_base_url+res['movie_results'][0]['poster_path']
	overview = res['movie_results'][0]['overview']
	title = res['movie_results'][0]['title']

	return image,title,overview,released,writer,director,ratings,actors


# used by RESULT, RESULT PAGE

def extra_details(titles):
	url = "http://www.omdbapi.com/?i=tt3896198&apikey=5615edda&t="
	new_titles = list()
	ratings = list()
	
	for t in titles:
		new_title = t.replace(" ","+")
		new_titles.append(new_title)

	for t in new_titles:
		res = requests.get(url+t,headers= {"Accept":"application/json"}).json()
		
		if(res['Ratings']):
			ratings.append(res['Ratings'][0]['Value'])
		else:
			ratings.append("N/A")

	return ratings


# used by RESULT

def find_data(id):
	api_key = "4b4170d57736cacfad0eaba78f8bed58"
	for i in range(randint(5,10)):
		year = randint(1999,2020)

	url = "https://api.themoviedb.org/3/discover/movie?api_key={}&with_genres={}&sort_by=popularity.desc&year={}".format(api_key,id,year)

	image_base_url = "https://image.tmdb.org/t/p/w500"
	res = requests.get(url,headers = {"Accept":"application/json"}).json()

	titles = list()
	images = list()
	year = list()
	overview = list()

	for i in range(5):
		titles.append(res['results'][i]['title'])
		images.append(res['results'][i]['poster_path'])
		year.append(res['results'][i]['release_date'][:4:])
		overview.append(res['results'][i]['overview'])

	images = [image_base_url+i for i in images]

	return titles,images,year,overview


# used by HOMEPAGE

def movies_playing():
	api_key = "4b4170d57736cacfad0eaba78f8bed58"
	url = "https://api.themoviedb.org/3/trending/movie/week?api_key={}".format(api_key)

	image_base_url = "https://image.tmdb.org/t/p/w500"
	res = requests.get(url,headers = {"Accept":"application/json"}).json()

	titles = list()
	images = list()

	for i in range(15):
		# if(len(res['results'][i]['title'])>30):
		# 	titles.append(res['results'][i]['title'][:25:]+"...")
		# else:
		titles.append(res['results'][i]['title'])
		images.append(res['results'][i]['poster_path'])
		

	images = [image_base_url+i for i in images]

	return titles,images


if __name__ == '__main__':
	app.run(debug = True)