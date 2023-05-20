import requests
import os
from multiprocessing.pool import ThreadPool
from tqdm import tqdm

album_dir = 'icloud-shared-album'

def download(urls, desc=''):
    result = ThreadPool(8).imap_unordered(download_media_item, urls)
    for _ in tqdm(result, unit=' media items', total=len(urls), desc=desc):
        pass

def download_media_item(url):
    r = requests.get(url)
    if r.status_code == 200:
        cd = r.headers['content-disposition']
        cd = cd[cd.find('filename="'):]
        filename = cd[10:cd.find('";')]
        open(album_dir + '/' + filename, 'wb').write(r.content)

print('iCloud Shared Album Downloader')
print('------------------------------------')
print('By: Nick Dawson (https://ndawson.me)')
print('------------------------------------')

# Get the URL of the shared album
print('Ex: https://www.icloud.com/sharedalbum/#abc01234567')
url = input("Enter the URL of the shared album: ")

# Parse the shared_album_id from the url string
shared_album_id = url[url.rfind('#')+1:]

# Make the api call to get the photos in the shared album
print('Getting list of photos...')
webstream_url = f'https://p69-sharedstreams.icloud.com/{shared_album_id}/sharedstreams/webstream'
webstream = requests.post(webstream_url, json={ "streamCtag": None })
webstream_json = webstream.json()

if webstream.status_code != 200:
    print(f'Error: Status code {webstream.status_code}')
    exit(1)

print(f'Downloading {len(webstream_json["photos"])} photos...')
print(f'Album: {webstream_json["streamName"]}')
print(f'User: {webstream_json["userFirstName"]} {webstream_json["userLastName"]}')

# Create a directory for the album
album_dir = webstream_json["streamName"]
if not os.path.exists(album_dir):
    os.makedirs(album_dir)

# Process photos data into usable format
photo_guids = []
photo_checksums = []
for photo in webstream_json["photos"]:
    max_derivative = max(photo["derivatives"].keys(), key=lambda x: int('0' + ''.join(filter(str.isdigit, x))))
    checksum_to_download = photo["derivatives"][max_derivative]["checksum"]

    photo_guids.append(photo["photoGuid"])
    photo_checksums.append(checksum_to_download)

# Get Web asset urls for each of the photo guids
print('Getting urls for each photo...')
webasseturls_url = f'https://p69-sharedstreams.icloud.com/{shared_album_id}/sharedstreams/webasseturls'
webasseturls = requests.post(webasseturls_url, json={ "photoGuids": photo_guids })
webasseturls_json = webasseturls.json()

if webasseturls.status_code != 200:
    print(f'Error: Status code {webasseturls.status_code}')
    exit(1)

# Process urls to get list of urls to download
urls_to_download = []
for item_checksum in webasseturls_json["items"]:
    item = webasseturls_json["items"][item_checksum]
    if item_checksum in photo_checksums:
        url_location = item["url_location"]
        photo_url = webasseturls_json["locations"][url_location]["scheme"] + '://' + url_location + item["url_path"]
        urls_to_download.append(photo_url)

download(urls_to_download, desc='Downloading photos')











