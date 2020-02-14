import requests, gzip

response = requests.get(
    'http://localhost:8000/tes.html',
    headers={'Accept-Encoding': 'gzip'},
)

# View the new `text-matches` array which provides information
# about your search term within the results

print response.headers
print response.encoding
#print len(gzip.zlib.compress(response.content), 16+zlib.MAX_WBITS)
