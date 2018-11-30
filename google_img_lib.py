# $ pip install google_images_download 

from google_images_download import google_images_download
def image_fetcher(artist_name):
    response = google_images_download.googleimagesdownload()
    DOWNLOADS = "/var/www/FlaskApp/FlaskApp/downloads"
    # you can type anything for keywords
    arguments = {"keywords":artist_name,"limit":10,"print_urls":True, "no_directory": True}   
    paths = response.download(arguments)
    return paths

# a folder labbed downloads should appear on your desktop 
