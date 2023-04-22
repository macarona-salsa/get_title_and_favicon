A python script to scrape the title and favicon of any website.

Tries to request page using the python requests module and parses through it
with beautifulsoup to find title (`<title>` element) and favicon (`<link>`
element with `rel="icon"`), then sends another request for the favicon.

If the script gets a `HTTP 403`, or fails to find the needed elements and
there's a `<script>` element on the page (a sign that the website relies on
dynamic content), it tries loading the resources again with a webdriver then
opreates on the source with beautifulsoup as normal.

Finally, it returns the title of the website as a string and the favicon as a
base64 encoded string. you can pass base64 encoded favicon to another function
to guess it's extension and save it to disk.

### Functions

- `get_title_and_favicon(url)` -> retrieves title and favicon (encoded in
base64) as a tuple

- `save_favicon(icon_encoded)` -> saves a base64 encoded favicon to disk

### Dependencies

- Requires firefox for loading dynamic websites. (using selenium and
geckodriver).
