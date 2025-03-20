#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mars Data Web Scraper

This script contains functions for scraping Mars data from various sources.
It uses Splinter and BeautifulSoup to extract news, images, facts, and
hemisphere data from different Mars-related websites.

Key functionalities:
- Scraping latest Mars news articles
- Retrieving the current featured Mars image
- Collecting Mars facts and data tables
- Gathering Mars hemisphere images and information
- Compiling all data into a structured dictionary

Author: Freddrick Logan
"""

# Import necessary libraries
from splinter import Browser
from bs4 import BeautifulSoup as bs
import pandas as pd
import time
import logging
import datetime
import requests
from webdriver_manager.chrome import ChromeDriverManager
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def init_browser():
    """
    Initialize and return a Splinter browser instance.
    
    Sets up a Chrome browser with appropriate options for web scraping.
    
    Returns:
        splinter.Browser: Configured browser instance
    """
    try:
        # Set up Splinter browser with ChromeDriverManager for Chrome WebDriver
        executable_path = {'executable_path': ChromeDriverManager().install()}
        
        # Configure browser options
        browser = Browser('chrome', **executable_path, headless=True)
        logger.info("Browser initialized successfully")
        return browser
    
    except Exception as e:
        logger.error(f"Error initializing browser: {e}")
        raise

def scrape_all():
    """
    Orchestrates the complete Mars data scraping process.
    
    Calls all individual scraping functions and combines the results
    into a single dictionary that can be stored in MongoDB.
    
    Returns:
        dict: Dictionary containing all scraped Mars data
    """
    try:
        # Initialize the browser
        browser = init_browser()
        
        # Create dictionary to store all Mars data
        mars_data = {}
        
        # Add each data category to the mars_data dictionary
        mars_data["news"] = scrape_mars_news(browser)
        mars_data["featured_image"] = scrape_featured_image(browser)
        mars_data["facts"] = scrape_mars_facts()
        mars_data["hemispheres"] = scrape_mars_hemispheres(browser)
        
        # Add metadata about the scraping process
        mars_data["last_scrape"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Close the browser session
        browser.quit()
        logger.info("Complete Mars data scraping successful")
        
        return mars_data
    
    except Exception as e:
        # Log any errors during the scraping process
        logger.error(f"Error during complete Mars scraping: {e}")
        
        # Make sure browser is closed even if scraping fails
        try:
            browser.quit()
        except:
            pass
        
        # Re-raise the exception to be handled by the caller
        raise

def scrape_mars_news(browser):
    """
    Scrape the latest news about Mars from NASA's Mars News website.
    
    Parameters:
        browser (splinter.Browser): Browser instance to use for scraping
    
    Returns:
        dict: Dictionary containing latest news title and paragraph text
    """
    try:
        # URL to scrape for Mars news
        news_url = 'https://redplanetscience.com/'
        browser.visit(news_url)
        
        # Allow time for dynamic content to load
        time.sleep(1)
        
        # Parse HTML with BeautifulSoup
        html = browser.html
        news_soup = bs(html, 'html.parser')
        
        # Find the latest news title and paragraph
        # First news item is the latest
        news_title = news_soup.find('div', class_='content_title').get_text()
        news_p = news_soup.find('div', class_='article_teaser_body').get_text()
        
        # Create a dictionary for the news data
        news_data = {
            "title": news_title,
            "paragraph": news_p
        }
        
        logger.info("Mars news scraping successful")
        return news_data
    
    except Exception as e:
        logger.error(f"Error scraping Mars news: {e}")
        
        # Return empty data if scraping fails
        return {
            "title": "Data not available",
            "paragraph": "Failed to retrieve the latest Mars news. Please try again later."
        }

def scrape_featured_image(browser):
    """
    Scrape the current featured Mars image from NASA's website.
    
    Parameters:
        browser (splinter.Browser): Browser instance to use for scraping
    
    Returns:
        str: URL of the featured Mars image
    """
    try:
        # URL to scrape for featured Mars image
        image_url = 'https://spaceimages-mars.com/'
        browser.visit(image_url)
        
        # Allow time for dynamic content to load
        time.sleep(1)
        
        # Click the 'FULL IMAGE' button to get the full-sized image
        browser.links.find_by_partial_text('FULL IMAGE').click()
        
        # Allow time for the full image to load
        time.sleep(1)
        
        # Parse HTML with BeautifulSoup
        html = browser.html
        img_soup = bs(html, 'html.parser')
        
        # Find the image URL
        img_url_rel = img_soup.find('img', class_='fancybox-image').get('src')
        
        # Build the absolute URL
        img_url = f"{image_url}{img_url_rel}"
        
        logger.info("Featured image scraping successful")
        return img_url
    
    except Exception as e:
        logger.error(f"Error scraping featured image: {e}")
        
        # Return a placeholder image URL if scraping fails
        return "https://via.placeholder.com/600x400?text=Mars+Image+Not+Available"

def scrape_mars_facts():
    """
    Scrape facts about Mars from the Mars facts website.
    
    Returns:
        str: HTML string containing a table of Mars facts
    """
    try:
        # URL to scrape for Mars facts
        facts_url = 'https://galaxyfacts-mars.com/'
        
        # Use pandas to read HTML tables from the page
        tables = pd.read_html(facts_url)
        
        # Get the first table which contains Mars facts
        # (compared to Earth)
        mars_facts_df = tables[0]
        
        # Rename columns for clarity
        mars_facts_df.columns = ['Description', 'Mars', 'Earth']
        
        # Set the description as the index for better display
        mars_facts_df.set_index('Description', inplace=True)
        
        # Convert the DataFrame to an HTML table string
        html_table = mars_facts_df.to_html(classes="table table-striped table-hover")
        
        # Clean up the table HTML
        html_table = html_table.replace('\n', '')
        
        logger.info("Mars facts scraping successful")
        return html_table
    
    except Exception as e:
        logger.error(f"Error scraping Mars facts: {e}")
        
        # Return a simple HTML message if scraping fails
        return "<table class='table'><tr><td>Mars facts currently unavailable</td></tr></table>"

def scrape_mars_hemispheres(browser):
    """
    Scrape images and titles for all four Mars hemispheres.
    
    Parameters:
        browser (splinter.Browser): Browser instance to use for scraping
    
    Returns:
        list: List of dictionaries containing hemisphere image URLs and titles
    """
    try:
        # URL to scrape for Mars hemisphere images
        hemispheres_url = 'https://marshemispheres.com/'
        browser.visit(hemispheres_url)
        
        # Allow time for dynamic content to load
        time.sleep(1)
        
        # Parse HTML with BeautifulSoup
        html = browser.html
        hemisphere_soup = bs(html, 'html.parser')
        
        # List to store hemisphere data
        hemisphere_image_urls = []
        
        # Find all hemisphere links
        links = hemisphere_soup.find_all('div', class_='description')
        
        # Loop through each hemisphere link
        for link in links:
            # Dictionary to store hemisphere data
            hemisphere = {}
            
            # Find the link to the hemisphere page
            href = link.find('a')['href']
            browser.visit(f"{hemispheres_url}{href}")
            
            # Allow time for the hemisphere page to load
            time.sleep(1)
            
            # Parse the hemisphere page
            hemisphere_html = browser.html
            hemisphere_soup = bs(hemisphere_html, 'html.parser')
            
            # Get the hemisphere title
            title = hemisphere_soup.find('h2', class_='title').text
            
            # Find the link to the full-resolution image
            downloads = hemisphere_soup.find('div', class_='downloads')
            img_url = f"{hemispheres_url}{downloads.find('a')['href']}"
            
            # Add data to the hemisphere dictionary
            hemisphere['title'] = title
            hemisphere['img_url'] = img_url
            
            # Add the hemisphere dictionary to the list
            hemisphere_image_urls.append(hemisphere)
            
            # Go back to the hemispheres page
            browser.back()
        
        logger.info("Mars hemispheres scraping successful")
        return hemisphere_image_urls
    
    except Exception as e:
        logger.error(f"Error scraping Mars hemispheres: {e}")
        
        # Return placeholder data if scraping fails
        placeholders = []
        for i, name in enumerate(['Cerberus', 'Schiaparelli', 'Syrtis Major', 'Valles Marineris']):
            placeholders.append({
                'title': f"{name} Hemisphere",
                'img_url': f"https://via.placeholder.com/600x400?text={name.replace(' ', '+')}+Hemisphere"
            })
        
        return placeholders

if __name__ == "__main__":
    # If run as a script, test the scraper
    print("Testing Mars data scraper...")
    data = scrape_all()
    print("Scraping completed!")
    print(f"Data retrieved for {len(data.keys())} categories")