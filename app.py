"""
Mars Data Web Application

This Flask application manages the Mars data web scraper dashboard.
It handles routes for the main page and scraper activation, and
interfaces with MongoDB to store and retrieve Mars data.

Key functionalities:
- Serving the main dashboard page
- Triggering the Mars data scraping process
- Retrieving and displaying the latest Mars data
- Managing MongoDB connections and operations

Author: Freddrick Logan
"""

# Import necessary libraries
from flask import Flask, render_template, redirect, jsonify
from flask_pymongo import PyMongo
import scrape_mars  # Import the scraping script
import time
import logging
import os
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask application
app = Flask(__name__)

# Configure MongoDB connection
# Use environment variable for connection string if available, otherwise use default
app.config["MONGO_URI"] = os.environ.get("MONGO_URI", "mongodb://localhost:27017/mars_app")
mongo = PyMongo(app)

# Define the main route
@app.route("/")
def index():
    """
    Renders the main dashboard page with the latest Mars data.
    
    Retrieves the most recent Mars data from MongoDB and passes it to the template.
    If no data is available, an empty template is rendered.
    
    Returns:
        Rendered HTML template with Mars data
    """
    try:
        # Find the most recent Mars data from the 'mars' collection
        mars_data = mongo.db.mars.find_one()
        logger.info("Retrieved Mars data from MongoDB")
        
        # If the data includes a timestamp, convert it to a readable format
        if mars_data and 'last_updated' in mars_data:
            if isinstance(mars_data['last_updated'], (int, float)):
                mars_data['last_updated_formatted'] = datetime.fromtimestamp(
                    mars_data['last_updated']
                ).strftime('%Y-%m-%d %H:%M:%S')
        
        # Render the index template with the Mars data
        return render_template("index.html", mars=mars_data)
    
    except Exception as e:
        # Log any errors that occur during data retrieval
        logger.error(f"Error retrieving data from MongoDB: {e}")
        # Render the template with no data
        return render_template("index.html", mars=None)

# Define the scrape route
@app.route("/scrape")
def scrape():
    """
    Triggers the Mars data scraping process.
    
    Calls the scrape_all function from the scrape_mars module,
    updates the MongoDB record with the new data, and redirects
    back to the main page.
    
    Returns:
        Redirect to the main page after scraping is complete
    """
    try:
        # Initialize the Mars collection in MongoDB
        mars_collection = mongo.db.mars
        
        # Log the start of the scraping process
        logger.info("Starting Mars data scraping process")
        
        # Call the scrape_all function from scrape_mars.py
        mars_data = scrape_mars.scrape_all()
        
        # Add timestamp to the scraped data
        mars_data["last_updated"] = time.time()
        
        # Update the MongoDB record with the new data
        # If no record exists, one will be created
        mars_collection.update_one({}, {"$set": mars_data}, upsert=True)
        
        # Log successful scraping
        logger.info("Mars data scraping completed successfully")
        
        # Redirect back to the main page
        return redirect("/", code=302)
    
    except Exception as e:
        # Log any errors that occur during scraping
        logger.error(f"Error during Mars data scraping: {e}")
        return jsonify({"error": str(e)}), 500

# API route to get the latest Mars data in JSON format
@app.route("/api/mars-data")
def mars_data_api():
    """
    API endpoint to retrieve the latest Mars data in JSON format.
    
    Returns:
        JSON response containing Mars data or error message
    """
    try:
        # Find the most recent Mars data from the 'mars' collection
        mars_data = mongo.db.mars.find_one({}, {'_id': 0})  # Exclude MongoDB _id field
        
        # Return the data as JSON
        return jsonify(mars_data)
    
    except Exception as e:
        # Return error message if data retrieval fails
        logger.error(f"API error: {e}")
        return jsonify({"error": "Failed to retrieve Mars data"}), 500

# Run the application
if __name__ == "__main__":
    # Get port from environment variable or use default 5000
    port = int(os.environ.get("PORT", 5000))
    
    # Run the app with debugging enabled in development mode
    app.run(host='0.0.0.0', port=port, debug=os.environ.get("FLASK_ENV") == "development")