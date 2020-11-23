#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import FlaskForm
from forms import *
from flask_migrate import Migrate
from sqlalchemy.sql import func
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')

# TODO: connect to a local postgresql database
app.config['SQLALCHEMY_DATABASE_URI']='postgresql://postgres:password@localhost:5432/Fyyurtest'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

#set up database instance
db = SQLAlchemy(app)

#setup migrate instance
migrate = Migrate(app,db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.
#**
#creating an association table to join artist and venue tables
show_artist = db.Table('show_artist',
    db.Column('artist_id', db.Integer, db.ForeignKey('artist.id'),primary_key=True),
    db.Column('venue_id', db.Integer, db.ForeignKey('venue.id'), primary_key=True),
    db.Column('start_time', db.DateTime, nullable=False))

#**

class Venue(db.Model):
    __tablename__ = 'venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))

    #**adding the missing fields in the venue table and the relationship - apply the flask db migrate and flask db upgrade to update the version of the database
    website = db.Column(db.String(500))
    genres = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(500))
    artists = db.relationship('Artist', secondary=show_artist,
        backref=db.backref('venues', lazy='joined'))

    #**
    # TODO: implement any missing fields, as a database migration using Flask-Migrate

class Artist(db.Model):
    __tablename__ = 'artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))

    #**adding the missing fields in the artist table and apply flask db migrate and flask db upgrade to update the versions with  a new version of the database
    website = db.Column(db.String(500))
    seeking_venue = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(500))
    #**

    # TODO: implement any missing fields, as a database migration using Flask-Migrate


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.

  #all the next steps for defining the list of cities and states 
  #with the venues inside it in a certain format as required in the front end
  #get venues grouped by city and state
  cities_states = db.session.query(Venue.city, Venue.state).group_by(Venue.city,Venue.state).all()
  
  #loop on the city and states and get the venues in them
  data = []
  for city_state in cities_states:
    venues_city_state = db.session.query(Venue.id,Venue.name).filter(Venue.city == city_state.city , Venue.state == city_state.state).all()
    
    #take each venues and get the upcoming_shows 
    venues_list = []
    for venue in venues_city_state:
        #get list of upcoming shows to each venue
        upcoming_shows = []
        upcomingshows_list = db.session.query(show_artist).filter(show_artist.c.venue_id == venue.id, show_artist.c.start_time > datetime.today()).all()
        venues_list.append({"id" : venue.id,
                       "name" : venue.name,
                       "num_upcoming_shows": len(upcomingshows_list)})
    data.append({"city" : city_state.city,
            "state" : city_state.state,
            "venues": venues_list
            })

  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"

  #get all the results of the search in venuesearch_list 
  venuesearch_list = Venue.query.filter(Venue.name.ilike('%{}%'.format(request.form.get('search_term',''))))
  result_objlist = []
  count = 0
  #loop on every object in the venues list returned from the query and prepare the needed list of objects with a specific format for the front end
  for resultobj in venuesearch_list:
    count += 1
    upcomingshows_list = db.session.query(show_artist).filter(show_artist.c.venue_id == resultobj.id, show_artist.c.start_time > datetime.today()).all()
    result_objlist.append({"id": resultobj.id,
                      "name": resultobj.name,
                      "num_upcoming_shows":len(upcomingshows_list)})
  response={
    "count": count,
    "data": result_objlist
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id

  #get the needed venue by venue_id
  selectedvenue = Venue.query.get(venue_id)
  #**
  #get list of past shows
  past_shows = []
  pastshows_list = db.session.query(show_artist).filter(show_artist.c.venue_id == venue_id, show_artist.c.start_time < datetime.today()).all()
  for show in pastshows_list:
    selected_artist = Artist.query.get(show.artist_id)
    past_shows.append({"artist_id": show.artist_id,
      "artist_name": selected_artist.name,
      "artist_image_link": selected_artist.image_link,
      "start_time": str(show.start_time)})

  #get list of upcoming shows
  upcoming_shows = []
  upcomingshows_list = db.session.query(show_artist).filter(show_artist.c.venue_id == venue_id, show_artist.c.start_time > datetime.today()).all()
  for show in upcomingshows_list:
    selected_artist = Artist.query.get(show.artist_id)
    upcoming_shows.append({"artist_id": show.artist_id,
      "artist_name": selected_artist.name,
      "artist_image_link": selected_artist.image_link,
      "start_time": str(show.start_time)})

  #customize data in the format needed for the front end
  data = {"id": selectedvenue.id,
    "name": selectedvenue.name,
    "genres": selectedvenue.genres.replace('{','').replace('}','').split(','),
    "address": selectedvenue.address,
    "city": selectedvenue.city,
    "state": selectedvenue.state,
    "phone": selectedvenue.phone,
    "website": selectedvenue.website,
    "facebook_link": selectedvenue.facebook_link,
    "seeking_talent": selectedvenue.seeking_talent,
    "seeking_description": selectedvenue.seeking_description,
    "image_link": selectedvenue.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows)
  }
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  form = VenueForm()
  try:
      #define the seeking talent Boolean field 
      seek_talent = False
      if form.seeking_talent.data == 'YES':
        seek_talent = True
      #assign the model attributes with the data entered by the user on the form
      venue = Venue(
            name = form.name.data,
            city = form.city.data,
            state = form.state.data,
            address = form.address.data,
            phone = form.phone.data,
            image_link = form.image_link.data,
            facebook_link = form.facebook_link.data,
            website = form.website.data,
            genres = form.genres.data,
            seeking_talent = seek_talent,
            seeking_description = form.seeking_description.data
      )
      db.session.add(venue)
      db.session.commit()
      # on successful db insert, flash success
      flash('Venue {} was successfully listed!'.format(form.name.data))
  except Exception as err:
      db.session.rollback()
      # TODO: on unsuccessful db insert, flash an error instead.
      flash('An error occurred. Venue could not be listed.')
  finally:
      db.session.close()
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  try:
    venue = Venue.query.get(venue_id)
    db.session.delete(venue)
    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()
  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  data =[]
  #get all the artists in the artist table
  artists = Artist.query.all()
  for artist in artists:
    data.append({"id": artist.id,
                 "name": artist.name})
  
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".

  #get all the results of the search in artistsearch_list 
  artistsearch_list = Artist.query.filter(Artist.name.ilike('%{}%'.format(request.form.get('search_term',''))))
  result_objlist = []
  count = 0
  #loop on every object in the artists list returned from the query and prepare the needed list of objects with a specific format for the front end
  for resultobj in artistsearch_list:
    count += 1
    upcomingshows_list = db.session.query(show_artist).filter(show_artist.c.artist_id == resultobj.id, show_artist.c.start_time > datetime.today()).all()
    result_objlist.append({"id": resultobj.id,
                      "name": resultobj.name,
                      "num_upcoming_shows":len(upcomingshows_list)})
  response={
    "count": count,
    "data": result_objlist
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def view_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id
  selectedartist = Artist.query.get(artist_id)

  #**
  #get list of past shows
  past_shows = []
  pastshows_list = db.session.query(show_artist).filter(show_artist.c.artist_id == artist_id, show_artist.c.start_time < datetime.today()).all()
  for show in pastshows_list:
    selected_venue = Venue.query.get(show.venue_id)
    past_shows.append({"venue_id": show.venue_id,
      "venue_name": selected_venue.name,
      "venue_image_link": selected_venue.image_link,
      "start_time": str(show.start_time)})

  #get list of upcoming shows
  upcoming_shows = []
  upcomingshows_list = db.session.query(show_artist).filter(show_artist.c.artist_id == artist_id, show_artist.c.start_time > datetime.today()).all()
  for show in upcomingshows_list:
    selected_venue = Venue.query.get(show.venue_id)
    upcoming_shows.append({"venue_id": show.venue_id,
      "venue_name": selected_venue.name,
      "venue_image_link": selected_venue.image_link,
      "start_time": str(show.start_time)})

  # define the data in the structure needed for the front end
  data = {"id": selectedartist.id,
    "name": selectedartist.name,
    "genres": selectedartist.genres.replace('{','').replace('}','').split(','),
    "city": selectedartist.city,
    "state": selectedartist.state,
    "phone": selectedartist.phone,
    "website": selectedartist.website,
    "facebook_link": selectedartist.facebook_link,
    "seeking_venue": selectedartist.seeking_venue,
    "seeking_description": selectedartist.seeking_description,
    "image_link": selectedartist.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows),
  }
  return render_template('pages/show_artist.html', artist=data)

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new artist record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  form = ArtistForm()
  try:
      #define the seeking talent Boolean field
      seek_venue = False
      if form.seeking_venue.data == 'YES':
        seek_venue = True
      #assign the attributes of the artist object with the data enetered by the user in the form
      artist = Artist(
            name = form.name.data,
            city = form.city.data,
            state = form.state.data,
            phone = form.phone.data,
            image_link = form.image_link.data,
            facebook_link = form.facebook_link.data,
            website = form.website.data,
            genres = request.form.getlist(form.genres.data),
            seeking_venue = seek_venue,
            seeking_description = form.seeking_description.data
      )
      db.session.add(artist)
      db.session.commit()
      # on successful db insert, flash success
      flash('Artist {} was successfully listed!'.format(form.name.data))
  except Exception as err:
      db.session.rollback()
      # TODO: on unsuccessful db insert, flash an error instead.
      flash('An error occurred. Artist {} could not be listed.'.format(form.name.data))
  finally:
      db.session.close()
  return render_template('pages/home.html')


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  #get the certain artist with artist_id
  artistobj = Artist.query.get(artist_id)

  # this step to avoid if there are no genres stored in the database 
  genres = ''
  if artistobj.genres == None :
    genres = ''
  else:
    genres =  list(artistobj.genres.replace('{','').replace('}','').split(','))
  artist = {
       "id": artistobj.id,
    "name": artistobj.name,
    "genres":genres,
    "city": artistobj.city,
    "state": artistobj.state,
    "phone": artistobj.phone,
    "website": artistobj.website,
    "facebook_link": artistobj.facebook_link,
    "seeking_venue": artistobj.seeking_venue,
    "seeking_description": artistobj.seeking_description,
    "image_link": artistobj.image_link
  }
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  form = ArtistForm()
  try:
    seek_venue = False
    if form.seeking_venue.data == "YES":
        seek_venue = True
    artist = Artist.query.get(artist_id)
    artist.name = form.name.data
    artist.genres = form.genres.data
    artist.city = form.city.data
    artist.state = form.state.data
    artist.phone = form.phone.data
    artist.website = form.website.data
    artist.facebook_link = form.facebook_link.data
    artist.seeking_venue = seek_venue
    artist.seeking_description = form.seeking_description.data
    artist.image_link = form.image_link.data
    db.session.commit()
    # on successful db insert, flash success
    flash('Artist {} was successfully updated!'.format(form.name.data))
  except Exception as err:
    db.session.rollback()
      # TODO: on unsuccessful db update, flash an error instead.
    flash('An error occurred. This Artist could not be updated.')
  finally:
    db.session.close()
  return redirect(url_for('view_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venueobj = Venue.query.get(venue_id)
  # this step to avoid if there are no genres stored in the database 
  genres = ''
  if venueobj.genres == None :
    genres = ''
  else:
    genres =  list(venueobj.genres.replace('{','').replace('}','').split(','))
  # TODO: populate form with values from venue with ID <venue_id>
  venue = {
    "id": venueobj.id ,
    "name": venueobj.name,
    "genres": genres,
    "address": venueobj.address,
    "city": venueobj.city,
    "state": venueobj.state,
    "phone": venueobj.phone,
    "website": venueobj.website,
    "facebook_link": venueobj.facebook_link,
    "seeking_talent": venueobj.seeking_talent,
    "seeking_description": venueobj.seeking_description,
    "image_link": venueobj.image_link
  }

  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  form = VenueForm()
  try:
    seek_talent = False
    if form.seeking_talent.data == "YES":
        seek_talent = True
    venue = Venue.query.get(venue_id)  
    venue.id = venue_id
    venue.name = form.name.data
    venue.genres = form.genres.data
    venue.address = form.address.data
    venue.city = form.city.data
    venue.state = form.state.data
    venue.phone = form.phone.data
    venue.website = form.website.data
    venue.facebook_link = form.facebook_link.data
    venue.seeking_talent = seek_talent
    venue.seeking_description = form.seeking_description.data
    venue.image_link = form.image_link.data
    db.session.commit()
    # on successful db insert, flash success
    flash('Venue {} was successfully updated!'.format(form.name.data))
  except Exception as err:
    db.session.rollback()
    # TODO: on unsuccessful db update, flash an error instead.
    flash('An error occurred. This Venue could not be updated.')
  finally:
    db.session.close()
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.

  #get all the shows in the show_artist table
  shows_list = db.session.query(show_artist).all()
  data = []
  #loop on every show and get the data for the artist and venue for this show
  for show in shows_list:
    selected_venue = Venue.query.get(show.venue_id)
    selected_artist = Artist.query.get(show.artist_id)
    data.append({"venue_id": selected_venue.id,
                "venue_name": selected_venue.name,
                "artist_id": selected_artist.id,
                "artist_name": selected_artist.name,
                "artist_image_link": selected_artist.image_link,
                "start_time": str(show.start_time)
    })
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  form = ShowForm()
  try:
    selected_artist = Artist.query.get(form.artist_id.data)
    selected_venue = Venue.query.get(form.venue_id.data)
    
    #insert record in the association table show_artist
    db.session.execute(show_artist.insert(),{"artist_id": form.artist_id.data, "venue_id": form.venue_id.data, "start_time": form.start_time.data})
    db.session.commit()
    # on successful db insert, flash success
    flash('Show for Artist {} in Venue {} was successfully listed!'.format(selected_artist.name,selected_venue.name))
  except Exception as err:
      db.session.rollback()
      # TODO: on unsuccessful db insert, flash an error instead.
      flash('An error occurred. This Show could not be listed.')
  finally:
      db.session.close()
  return render_template('pages/home.html')


#  Errors
#  ----------------------------------------------------------------

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
