# $ pip install google_images_download 

from google_images_download import google_images_download
def image_fetcher(artist_name):
    response = google_images_download.googleimagesdownload()
    # you can type anything for keywords
    arguments = {"keywords":artist_name,"limit":10,"no_numbering":True,"output_directory":"/var/www/FlaskApp/FlaskApp/static/downloads", "image_directory":artist_name}   
    paths = response.download(arguments)
    return
#image_fetcher("dali")

# a folder labbed downloads should appear on your desktop 