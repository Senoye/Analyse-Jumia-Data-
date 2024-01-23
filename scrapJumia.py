from time import sleep
from urllib.request import urlopen, Request
from bs4 import BeautifulSoup as bs
from urllib.error import HTTPError
import csv
import uuid  # Import the uuid module for generating random IDs


category_names_urls = {
    # 'Informatique'  : 'ordinateurs-accessoires-informatique/',
    'TV & Hi' : 'electronique/',
    'Sports & Loisirs'  : 'sports-loisirs/',
    'Jardin et plein air'  : 'terrasse-jardin-exterieur/',
    'Téléphone & Tablette'  : 'telephone-tablette/',
    'Jouets et Jeux'  : 'jeux-et-jouets/',
    'Vêtements & Chaussures'  : 'fashion-mode/git ',
    'Maison, cuisine & bureau'  : 'maison-cuisine-jardin/',
    'Accessoire Auto Moto'  : 'automobile-outils/',
    'Beauté & Santé'  : 'beaute-hygiene-sante/',
    'Bébé & Jouets'  : 'bebe-puericulture/',
}

nb_article_par_page = 40
max_pages_to_scrape = 10

def scrape_page(category_name, soup):
    scraped_data = []  

    titles = soup.findAll("h3", {"class": "name"})
    prices = soup.findAll("div", {"class": "prc"})
    oldPrices = soup.findAll("div", {"class": "old"})
    discounts = soup.findAll("div", {"class": "bdg _dsct _sm"})
    marques = soup.findAll("div", {"class": "-pvxs"})
    rattings = soup.findAll("div", {"class": "rev"})

    for title, price, oldPrice, discount, marque, ratting in zip(titles, prices, oldPrices, discounts, marques, rattings):
        try:
            product_name = title.text.strip()
            product_price = ''.join(filter(str.isdigit, price.text.strip()))
            old_price = ''.join(filter(str.isdigit, oldPrice.text.strip()))
            discount_value = ''.join(filter(str.isdigit, discount.text.strip()))
            product_marque = marque.text.strip() if marque.text.strip() else "N/A"

            # Check if ratings exist before accessing
            ratting_text = ratting.text.split()[0]
            product_rating = float(ratting_text) if ratting else "N/A"

             # Generate a random numeric product ID using uuid
            product_id = str(int(uuid.uuid4().hex, 16))[:4]  # Adjust the length as needed

            # Calculate discounted percentage of the old price
            Dold_price = (float(old_price) - float(product_price)) / float(old_price) * 100

            # Check if Dold_price is negative or greater than 100
            if Dold_price < 0 or Dold_price > 100:
                Dold_price = 'N/A'
            else:
                Dold_price = round(Dold_price)

            print("Product ID =", product_id)
            print("name =", product_name)
            print("Price =", product_price)
            print("Old Price =", old_price)
            print("Discount =", discount_value)
            print("Marque = ", product_marque)
            print("Ratting = ", product_rating)
            print("Discounted Percentage Old Price = ", Dold_price)
            print("Category name = ", category_name)
            print()

            scraped_data.append([product_id, product_name, category_name, product_price, old_price ,Dold_price , discount_value, product_marque, product_rating])

        except AttributeError as e:
            print(f"Error: {e}")
            continue

    return scraped_data



# Function to get the number of results (Explication)
def get_total_results(soup):
    result_paragraph = soup.find("p", {"class": "-gy5 -phs"})
    if result_paragraph:
        result_text = result_paragraph.text.strip()
        result_number = ''.join(filter(str.isdigit, result_text))
        return int(result_number)
    return 0

def get_total_pages(soup):
    total_results = get_total_results(soup)
    return total_results // nb_article_par_page + (total_results % nb_article_par_page > 0)


## URL and headers
base_url = 'https://www.jumia.ma/'

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

search_query = 'pc'
csv_filename = '/home/youness/Desktop/data/jumia_scraping4.csv'

def get_page(url):
    print("getting page")
    sleep(1)
    request = Request(url, headers=headers)
    client = urlopen(request)
    html = client.read()
    return bs(html, 'html.parser')

def get_page_with_backoff(url, retries=5, backoff_factor=1.5):
    for attempt in range(retries):
        try:
            print(f"Attempt {attempt + 1} of {retries}")
            sleep(attempt * backoff_factor)
            request = Request(url, headers=headers)
            client = urlopen(request)
            html = client.read()
            return bs(html, 'html.parser')
        
        except HTTPError as e:
            if e.code == 429 and attempt < retries - 1:
                continue
            else:
                raise

for category_name, category_url in category_names_urls.items():
    print(f"Scraping data for {category_name} category...")
    print("-" * 80)
    # Make the request for the first page
    url = f'{base_url}{category_url}?q='+search_query
    soup = get_page(url)
    # Get the total number of pages
    total_pages = get_total_pages(soup) 
    total_pages = total_pages if total_pages < max_pages_to_scrape else max_pages_to_scrape

    # Scrape the first page
    data = scrape_page(category_name, soup)

    # Iterate over the remaining pages
    for page_num in range(2, total_pages + 1):
        url = f'{base_url}{category_url}?q='+search_query + f'&page={page_num}'  
        soup = get_page(url)
        # Scrape the current page
        data.extend(scrape_page(category_name, soup))

    # Save data to CSV
    with open(csv_filename, 'a', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile)

        # Write header if it's the first category
        if not csvfile.tell():
            csv_writer.writerow(['Product ID', 'Name', 'Category', 'Price (Dh)', 'Old Price (Dh)', 'Discount_old_price (%)', 'Discount (%)', 'Marque', 'Rating'])
        
        csv_writer.writerows(data)

    print(f"Data saved to {csv_filename}")
    print()

