import mutagen
import glob
import unicodedata

audio_file_mask = '*.mp3'
image_filename_pattern = '{album_artist}-{date}-{album}'
output_pattern = """
{album_artist} – [{date}] {album}
{image_filename}

<strong><a href="{download_url}">Download</a></strong>
<a href="{release_page}">Release page</a>
<a href="http://freemusi.cc/?q=release+IS+{release}">Play on freemusi.cc</a>"""

# find audio files
audio_files = glob.glob(audio_file_mask) 

# read meta data from first file
metadata = mutagen.File(audio_files[0])
if metadata.has_key('ALBUM_ARTIST'):
    raise NotImplementedError
else:
    album_artist = metadata.get('TPE1').text[0]
date = metadata.get('TDRC').text[0]
album = metadata.get('TALB').text[0]
source_webpage_url = metadata.get('WOAS').url
release =  ', '.join(metadata.get('TXXX:RELEASE').text)

image_filename = image_filename_pattern.format(album_artist=album_artist, date=date,album=album)
image_filename = unicodedata.normalize('NFKD', image_filename.decode('UTF-8')).encode('ascii', 'ignore').replace(' ','-').replace('.','-').lower() 

print output_pattern.format(
        album_artist=album_artist, 
        date=date, 
        album=album, 
        image_filename=image_filename,
        download_url=source_webpage_url.replace('/details/','/compress/'), 
        release_page=source_webpage_url, 
        release=release)
