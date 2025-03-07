from flask import Flask, render_template, redirect, url_for
from flask_pymongo import PyMongo
import scrape_mars

app = Flask(__name__)

# Use flask_pymongo to set up mongo connection
app.config["MONGO_URI"] = "mongodb://localhost:27017/mars_app"
mongo = PyMongo(app)

@app.route("/")
def index():
    # Find one record of data from the mongo database
    mars_data = mongo.db.mars.find_one()
    # Return template and data
    return render_template("index.html", mars=mars_data)

@app.route("/scrape")
def scrape():
    # Run the scrape function
    mars_data = scrape_mars.scrape_all()
    
    # Update the Mongo database using update and upsert=True
    mongo.db.mars.update_one({}, {"$set": mars_data}, upsert=True)
    
    # Redirect back to home page
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
