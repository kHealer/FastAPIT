from bs4 import BeautifulSoup
import requests
import os
from google.cloud import translate_v2 as translate

# Set up the translation client
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r'credentials.json'
translate_client = translate.Client()

# Set the target language
target_language = 'hi'

# Define a function to translate the text of a tag
def translate_tag(tag):
    if tag.string:
        if tag.name == 'img':
            # If the tag is an image tag, extract the image URL and append it to the translated content
            translated_text = f"{tag['alt']} ({tag['src']})"
        else:
            try:
                translated_text = translate_client.translate(tag.string, target_language=target_language)['translatedText']
            except Exception as e:
                if 'Text too long' in str(e):
                    # Split the text into smaller segments and translate each segment separately
                    original_text = tag.string
                    segment_length = 5000
                    segments = [original_text[i:i+segment_length] for i in range(0, len(original_text), segment_length)]
                    translated_segments = [translate_client.translate(segment, target_language=target_language)['translatedText'] for segment in segments]
                    translated_text = ''.join(translated_segments)
                else:
                    raise e
        tag.string.replace_with(translated_text)


# Define a function to translate a webpage
def translate_webpage(url):
    # Fetch the webpage content
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    html_content = response.text

    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')

    # Translate the webpage content using Google Cloud Translation API
    for tag in soup.find_all():
        translate_tag(tag)

    # Return the translated HTML content
    return soup.prettify()

# Translate the homepage of the website and save the translated content to a file
url = 'https://www.classcentral.com/'
translated_html_content = translate_webpage(url)
with open('index.html', 'w', encoding='utf-8') as f:
    f.write(translated_html_content)

# Find all the links on the homepage and translate their linked pages
homepage_links = []
homepage_response = requests.get(url)
homepage_soup = BeautifulSoup(homepage_response.text, 'html.parser')
for link in homepage_soup.find_all('a'):
    href = link.get('href')
    if href is not None and href.startswith('http'):
        homepage_links.append(href)

for link in homepage_links:
    if link.endswith('.css'):
        response = requests.get(link)
        filename = link.split('/')[-1]
        with open(filename, 'wb') as f:
            f.write(response.content)
    else:
        try:
            translated_html_content = translate_webpage(link)
            filename = link.replace('/', '_').replace(':', '') + '.html'
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(translated_html_content)
        except:
            pass
