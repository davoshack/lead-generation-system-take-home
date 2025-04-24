# Camber Lead-gen Engineering Take Home
### Lead Generation System Take-Home Exam


## Info Candidate:
#### Name: Juan David Hernández Giraldo
#### Email: jdhernandez@azzertai.com
#### Linkedin: https://www.linkedin.com/in/juandhernandez/
#### Github: https://github.com/davoshack
#### Personal site: https://www.davoscode.com/

## Installation
```bash
pip install -r requirements.txt
```
## To execute the scraper
```bash
python main.py
```

## To export the data
```bash
python export_data.py
```

## Final Google Sheet
[Link to Final Google Sheet](https://docs.google.com/spreadsheets/d/16SKR11n_t0J1TfTO-eg8pG9lmBJfHR2wkVyRZy-a8uo/edit?usp=sharing)

## Resume Aproach

As a software engineer, my approach when designing and building any software solution is the following:

First, focus on:
- good coding practices
- performance
- maintainability
- Scalability
- Resource efficiency

Second, a software design mindset: Design and build simple solutions that are easy to maintain or extend in the future.

I try to respond to some questions that help me define what I need to build the solution:

- What is the software application or feature?
- What problem does the software solve?
- How is it going to work?
- What technical details do I need to know?
- Are there particular algorithms or libraries that are important?
- What will be the overall design? 
- What are the steps, and how much time does each step take?
- Etc...,

My approach to resolving any technical challenge follows the same patterns: Focus on performance, readability, and good software design principles.

For this particular challenge, I identified some key points:

- A scraper could be a bottleneck if the data to scrape is huge and the process isn't managed properly.

- Two different tasks to implement: 1) a crawling process to get all the URLs available in the HTML content, and 2) a scraping process to recollect and store the information requested.

- Export and import the data scraped.

- The data enrichment process using Clay SaaS.

To avoid performance issues and timeouts when crawling and scraping, ***I implemented asynchronous and parallel data processes in the Python scripts.***

Also, I stored the scraped data in a LiteSQL database and then exported it to a CSV file. 

That CSV file was imported into Clay to perform the data enrichment.

In this assessment, I faced two problems:

1) The company's information in the web page directory to scrape is loading dynamically, which means that only the first 16 companies' information was possible to extract.

For scraping dynamically loaded content, it is need to apply other approaches, like implementing the Selenium library or accessing API Endpoints that are enabled in the site.


2) The data categorization by company size and location.
When creating the formulas and testing, I got inconsistent results.
 I need to investigate more about how to create these formulas in the Clay Platform.
