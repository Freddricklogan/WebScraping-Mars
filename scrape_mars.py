import pandas as pd
from bs4 import BeautifulSoup
from splinter import Browser
from webdriver_manager.chrome import ChromeDriverManager
import datetime as dt

def scrape_all():
    # Initiate headless driver for deployment
    executable_path = {'executable_path': ChromeDriverManager().install()}
    browser = Browser('chrome', **executable_path, headless=True)
    
    # Set news title and paragraph variables
    news_title, news_paragraph = mars_news(browser)
    
    # Run all scraping functions and store in dictionary
    data = {
        "news_title": news_title,
        "news_paragraph": news_paragraph,
        "featured_image": featured_image(browser),
        "facts": mars_facts(),
        "hemispheres": hemispheres(browser),
        "last_modified": dt.datetime.now()
    }
    
    # Stop webdriver and return data
    browser.quit()
    return data

def mars_news(browser):
    # In a production environment, we would visit the actual site
    # For demo purposes, we'll simulate results
    
    # Example news title and paragraph
    news_title = "NASA's Perseverance Rover Successfully Cores Its First Rock"
    news_paragraph = "The core, about 6 centimeters in length, is now enclosed in an airtight titanium sample tube, making it available for retrieval in the future."
    
    return news_title, news_paragraph

def featured_image(browser):
    # For demo purposes, return a sample image URL
    return "https://spaceimages-mars.com/image/featured/mars1.jpg"

def mars_facts():
    # For demo, create a simple dataframe with Mars facts
    df = pd.DataFrame({
        'Description': ['Diameter', 'Mass', 'Moons', 'Distance from Sun', 'Length of Year', 'Temperature'],
        'Mars': ['6,779 km', '6.39 × 10^23 kg', '2', '227,943,824 km', '687 Earth days', '-87 to -5 °C']
    })
    
    # Convert dataframe to HTML table string
    return df.to_html(index=False, classes="table table-striped")

def hemispheres(browser):
    # For demo, return sample hemisphere data
    hemisphere_image_urls = [
        {"title": "Cerberus Hemisphere", "img_url": "https://marshemispheres.com/images/cerberus_enhanced.jpg"},
        {"title": "Schiaparelli Hemisphere", "img_url": "https://marshemispheres.com/images/schiaparelli_enhanced.jpg"},
        {"title": "Syrtis Major Hemisphere", "img_url": "https://marshemispheres.com/images/syrtis_major_enhanced.jpg"},
        {"title": "Valles Marineris Hemisphere", "img_url": "https://marshemispheres.com/images/valles_marineris_enhanced.jpg"}
    ]
    
    return hemisphere_image_urls

if __name__ == "__main__":
    # If running as script, print scraped data
    print(scrape_all())
