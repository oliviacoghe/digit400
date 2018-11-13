# $ pip install google_images_download 

from google_images_download import google_images_download

response = google_images_download.googleimagesdownload()

# you can type anything for keywords
arguments = {"keywords":"van gogh, monet, dali","limit":10,"print_urls":True}   
paths = response.download(arguments)
print(paths)

# a folder labbed downloads should appear on your desktop 
# the path for this file on my machine is /Users/Coghe/Desktop/