import requests
import base64
from tokens import imgur_id
from datetime import datetime
from os import remove
from PIL import Image, ImageFont, ImageDraw

def imgur_upload(filename):
    url = 'https://api.imgur.com/3/image'
    headers = {
        'Authorization': f'Client-ID {imgur_id}'
    }
    data = {}
    with open(filename, 'rb') as image_file:
        b64 = base64.b64encode(image_file.read())
        data = {
            'image': b64,
            'type': 'base64',
        }
    response = requests.post(url, headers=headers, data=data)
    remove(f'./{filename}')
    return response.json()['data']['link']

def ImageGen(url1, url2):
    size = 200

    img1 = Image.open(requests.get(url1, stream=True).raw).resize((size, size), Image.ANTIALIAS)
    img2 = Image.open(requests.get(url2, stream=True).raw).resize((size, size), Image.ANTIALIAS)

    foreground = Image.open("challenge_overlay.png").resize((int((size*2)*1.03), size), Image.ANTIALIAS)

    # Define Image Size
    img = Image.new('RGBA',(int((size*2)*1.03), size), (47,49,54))
    draw = ImageDraw.Draw(img)
    draw.text((0,0), "This is a test", (255,255,0))
    img.paste(img1,(0,0))
    img.paste(img2,(int((size * 1.06)),0))
    img.paste(foreground, (0, 0), foreground)
    filename=f"{str(datetime.now()).replace(':','-').replace('.','-').replace(' ','-')}.png"
    img.save(filename)
    return imgur_upload(filename)
    