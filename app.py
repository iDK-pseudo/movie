from flask import Flask,render_template,g,request
import sqlite3
import requests
from random import randint
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime


app = Flask(__name__)

app.config.from_pyfile("app.cfg")

# SQLALCHEMY_DATABASE_URI='postgres+psycopg2://postgres:helloWORLD#@localhost:8000/moviedb'

db = SQLAlchemy(app)

username = "Guest"

class moviedb(db.Model):
	username = db.Column(db.String,unique = True,primary_key=True)
	name = db.Column(db.String,nullable = False)
	password = db.Column(db.String,nullable = False)
	email = db.Column(db.String,nullable = False)
	joining_date = db.Column(db.DateTime,nullable = False)

	def __repr__(self):
		return '<User %r>' % self.username


def connect_genre_db():
	sql= sqlite3.connect("genres.db")
	sql.row_factory = sqlite3.Row
	return sql

def get_genre_db():
	if not hasattr(g,'sqlite3'):
		g.sqlite_db=connect_genre_db()
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

	global username

	if(request.method == "POST"):
		result = request.form

		username = result['username']
		password = result['password']

		if(len(result)==2):
			res = moviedb.query.filter(moviedb.username == username).first()
			if(res is not None and res.password == password):
				return render_template("homepage.html",titles=titles,images=images,toast = "Welcome "+res.name+" !",username=username,logout=1)
			else:
				username = "Guest"
				return render_template("homepage.html",titles=titles,images=images,toast = "Entered username or password not found. Please try again !",username = username,logout = None)

		elif(len(result)==4):
			name = result['name']
			email = result['email']

			username_exists = moviedb.query.filter(moviedb.username.in_([username])).all()
			email_exists = moviedb.query.filter(moviedb.email.in_([email])).all()

			
			if(not(name and email and username and password)):
				username="Guest"
				return render_template("signup.html",toast = "Kindly fill all the fields !")

			elif(len(password)<8):
				username="Guest"
				return render_template("signup.html",toast = "The password cannot be less than 8 Characters !")

			elif(email_exists):
				username="Guest"
				return render_template("signup.html",toast = "Hmmm Seems like you have already registered. Please head to Home and Login")

			elif(username_exists):
				username="Guest"
				return render_template("signup.html",toast = "This username is already taken. Please try and pick another username.")
			
			else:
				element = moviedb(username = username,email=email,password=password,name=name,joining_date=datetime.today())
				db.session.add(element)
				db.session.commit()
				db.session.close()

				username="Guest"
				return render_template("homepage.html",titles=titles,images=images,toast="You may login now ! "+name,username = username,logout = None)

	else:
		if(username == "Guest"):
			return render_template('homepage.html',titles=titles,images=images,toast=None,username = username,logout = None)
		else:
			return render_template('homepage.html',titles=titles,images=images,toast=None,username = username,logout = 1)


# Discover/ Suprise Me

@app.route('/discover',methods=['GET','POST'])
def discover():
	return render_template('discover.html',username=username)


# Result Page of Discover

@app.route('/result/<genre>',methods=['GET','POST'])
def result(genre):
	db = get_genre_db()
	
	cur = db.execute("select id from genres where name = (?)",[genre])
	result = cur.fetchone()

	titles,images,year,overview = find_data(result['id'])
	ratings = extra_details(titles)

	return render_template('result.html',genre = genre.upper(),titles = titles,images= images,year = year,overview=overview,ratings = ratings,username = username)


# Result Page of Movie

@app.route('/result_page/<title>',methods=['GET','POST'])
def result_page(title):

	result = {}

	global username

	if(request.method == "POST"):
		result = request.form
		title = str(result['search'])

		if(title == ''):
			titles,images = movies_playing()

			if(username == "Guest"):
				return render_template('homepage.html',titles=titles,images=images,toast="Please try another name !",username = username,logout = None)
			else:
				return render_template('homepage.html',titles=titles,images=images,toast="Please try another name !",username = username,logout = 1)


	image,title,overview,released,writer,director,ratings,actors = find_movie_data(title)

	if(image == 0 and title == 0 and overview == 0):
		titles,images = movies_playing()

		if(username == "Guest"):
			return render_template('homepage.html',titles=titles,images=images,toast="Please try another name !",username = username,logout = None)
		else:
			return render_template('homepage.html',titles=titles,images=images,toast="Please try another name !",username = username,logout = 1)

	data = {'image':image,'title':title,'overview':overview,'released':released,'writer':writer,'director':director,'ratings':ratings,'actors':actors}
	return render_template('result_page.html',data = data,username=username)


@app.route('/signup',methods=['GET'])
def signup():
	return render_template("signup.html",toast = None)	

@app.route('/logout',methods=['GET'])
def logout():
	global username
	username= "Guest"
	titles,images = movies_playing()
	return render_template('homepage.html',titles=titles,images=images,toast="You have logged out !",username = username,logout = None)



# Functions used


# used by RESULT PAGE

def find_movie_data(title):
	url = "http://www.omdbapi.com/?i=tt3896198&apikey=5615edda&t="+title.replace(" ","+")
	api_key = "4b4170d57736cacfad0eaba78f8bed58"
	image_base_url = "https://image.tmdb.org/t/p/w500"
	

	res = requests.get(url,headers= {"Accept":"application/json"}).json()
	
	if('Error' in res.keys()):
		return 0,0,0,0,0,0,0,0

	id = res['imdbID']
	released = res['Released']
	writer = res['Writer']
	director = res['Director']
	ratings = res['Ratings']
	actors = res['Actors']

	url =  "https://api.themoviedb.org/3/find/{}?api_key={}&language=en-US&external_source=imdb_id".format(id,api_key)
	res = requests.get(url,headers= {"Accept":"application/json"}).json()

	if(len(res['movie_results']) == 0):
		return 0,0,0,0,0,0,0,0
	
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
		
		if('Ratings' in res.keys()):
			if(len(res['Ratings'])>0):
				ratings.append(res['Ratings'][0]['Value'])
			else:
				ratings.append("N/A")
		else:
			ratings.append("N/A")

	return ratings


# used by RESULT

def find_data(id):
	api_key = "4b4170d57736cacfad0eaba78f8bed58"
	for i in range(randint(1,15)):
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

	omdburl = "http://www.omdbapi.com/?i=tt3896198&apikey=5615edda&t="

	i=0
	no_of_results=15

	while(i<no_of_results):
		title = res['results'][i]['title'].replace(" ","+")

		url2 = omdburl+title

		omdbres = requests.get(url2,headers= {"Accept":"application/json"}).json()

		if('Error' not in omdbres):
			titles.append(res['results'][i]['title'])
			images.append(res['results'][i]['poster_path'])
			i+=1

		else:
			i+=1
			no_of_results+=1

	images = [image_base_url+i for i in images]

	return titles,images


if __name__ == '__main__': 
	username = "Guest"
	app.run(debug = True)