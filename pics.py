import shutil
import re
from tqdm import tqdm
from urllib.parse import urlparse
from os.path import basename
import os.path
import requests
import requests_cache
from lxml import html
from xml.etree.ElementTree import tostring

min_w = 4096
min_h = 2160
big_urls = []
dl_size = 0
dl_location="pics"
def get_image(url):
    global dl_size
    # print(dl_size)
    url = "https://en.wikipedia.org" + url
    image_page = requests.get(url)
    image_tree = html.fromstring(image_page.content)
    search = image_tree.xpath("//span[@class=\"fileInfo\"]")
    if len(search) > 0:
        info_span = search[0]
    else:
        return
    info_text = info_span.text
    img_size = info_text[info_text.find("(") + 1 : info_text.find("pixels")]
    size_split = img_size.split("×")
    try:
        img_size = [int(i.replace(",","")) for i in size_split]
    except:
        return
    if img_size[0] >= min_w and img_size[1] >= min_h:
        orig_url = "http:" + image_tree.xpath("//a[@class='internal']/@href")[0]
        big_urls.append(orig_url)
        file_size = re.search(r"file size:\s*(.*)\s*MIME", info_text).groups()[0].split()
        # import pdb; pdb.set_trace()
        if file_size and len(file_size) == 2:
            num_units = float(file_size[0].replace(",",""))
            if file_size[1].lower().startswith("mb"):
                dl_size += num_units * 1000000
            else:
                dl_size += num_units * 1000

def get_images_for_month(url):
    url = "https://en.wikipedia.org" + url
    month_page = requests.get(url)
    month_tree = html.fromstring(month_page.content)
    image_urls = [u for u in month_tree.xpath('//a/@href') if "File:" in u and not u.endswith(".svg")]
    for iurl in image_urls:
        get_image(iurl)


def dl(url, pbar):
    pbar.set_description("Downloading file %s" % url)
    url_parts = urlparse(url)
    file_name = basename(url_parts.path)
    if len(file_name) > 180:
        dot_loc = file_name.rfind(".")
        file_name = file_name[:180] + file_name[dot_loc:]
    file_path = dl_location + "/" + file_name
    if not os.path.isfile(file_path):
        r = requests.get(url, stream=True)
        if r.status_code == 200:
            with open(file_path, 'wb') as f:
                r.raw.decode_content = True
                shutil.copyfileobj(r.raw, f)
    pbar.update(1)

requests_cache.install_cache("wikicache")

archive_header_url = "https://en.wikipedia.org/wiki/Template:POTDArchiveHeader"

r = requests.get(archive_header_url)

tree = html.fromstring(r.content)
center = tree.xpath("//center//div[@class = \"hlist\"]//table")[0]
sc = tostring(center, "utf-8", method="xml")
month_urls = [url for url in center.xpath('//a/@href') if "Picture_of_the_day/" in url and not "redlink" in url]
print(month_urls)
for month_url in month_urls:
    get_images_for_month(month_url)

# done grabbing pages, time to disable the cache
requests_cache.uninstall_cache()
print(len(big_urls))
print(dl_size)
pbar = tqdm(total=len(big_urls))
for img_url in big_urls:
    dl(img_url, pbar)

pbar.close()
