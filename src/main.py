import json
import time
import requests
import os
import re
import zipfile
from flask import Flask
from playwright.sync_api import sync_playwright

extensionId = 'ilehaonighjijnmpnagapkhpcdbhclfg'
extensionName = 'grass.zip'
unpackedExtensionName = 'extension'
CRX_URL = "https://clients2.google.com/service/update2/crx?response=redirect&prodversion=98.0.4758.102&acceptformat=crx2,crx3&x=id%3D~~~~%26uc"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36"

USER = os.environ['GRASS_USER']
PASSW = os.environ['GRASS_PASS']

if not USER or not PASSW:
    print('Please set GRASS_USER and GRASS_PASS env variables')
    exit()

app = Flask(__name__)

def download_extension(extension_id):
    url = CRX_URL.replace("~~~~", extension_id)
    headers = {"User-Agent": USER_AGENT}
    r = requests.get(url, stream=True, headers=headers)
    with open(extensionName, "wb") as fd:
        for chunk in r.iter_content(chunk_size=128):
            fd.write(chunk)

def fixup_extension_manifest(extension_path):
    manifest_file = os.path.join(extension_path, "manifest.json")
    with open(manifest_file, 'r') as file:
        data = json.load(file)

    data['manifest_version'] = 2

    with open(manifest_file, 'w') as file:
        json.dump(data, file, indent=4)


def setup_browser():
    with sync_playwright() as p:
        if os.path.exists(extensionName):
            print('Extension already exists, skip download...')
        else:
            print('Downloading extension...')
            download_extension(extensionId)
            print('Extension downloaded!')
        
        # unpack extension
        with zipfile.ZipFile(extensionName, 'r') as zip_ref:
            zip_ref.extractall(unpackedExtensionName)
        print('Extension unpacked!')
        
        # Launch a Chromium browser with the extension
        extension_path = os.path.join(os.getcwd(), unpackedExtensionName)
        fixup_extension_manifest(extension_path)
        context = p.chromium.launch_persistent_context(os.getcwd(), headless=False,
            bypass_csp=True,
            args=[
                '--headless=new',
                f'--disable-extensions-except={extension_path}',
                f'--load-extension={extension_path}',
        ])
        background = context.service_workers[0]
        if not background:
            background = context.wait_for_event("serviceworker")
        print('Browser launched!')
        page = context.new_page()

        # The URL of the extension's page may vary depending on the extension ID and its internal structure
        page.goto(f'chrome-extension://{extensionId}/index.html')

        # Log in to the extension
        page.get_by_placeholder('Username or Email').fill(USER)
        page.get_by_placeholder('Password').fill(PASSW)
        page.click('button[type="submit"]')
        print('Logged in! Waiting for connection...')
        time.sleep(2)

        # Wait for the network quality element to be visible
        print(page.content())
        page.get_by_text('Network quality').wait_for()
        print('Connected!')
        return page

page = setup_browser()

@app.route('/')
def get():
    # Retrieve the network quality and lifetime earnings
    # specific_text = 'Network quality'
    # network_quality = page.inner_text(f"text='{specific_text}'")
    # network_quality = re.findall(r'\d+', network_quality)[0]
    # lifetime_earnings = page.inner_text('//*[contains(text(), "Lifetime earnings")]//*[following-sibling::div]//child::p')

    # return {'network_quality': network_quality, 'lifetime_earnings': lifetime_earnings}
    return page.content()

app.run(host='0.0.0.0',port=80, debug=False)
