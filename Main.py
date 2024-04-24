from urllib.parse import urlparse, parse_qs
from xml.etree import ElementTree
import http.server
import socketserver
import requests
import json
import os

class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        url = urlparse(self.path)
        if self.path == '/info':
            response = {
                "version": VERSION,
                "service": "currency",
                "author": "Michail.Kharitonov"
            }
            self.send_OK(response)
        elif url.path == '/info/currency':
            query_params = parse_qs(url.query)
            date = query_params.get('date', [''])[0]
            currency = query_params.get('currency', [''])[0]
            response = ""
            if date == "":
                response = requests.get('https://www.cbr.ru/scripts/XML_daily.asp')
            else:
                response = requests.get('https://www.cbr.ru/scripts/XML_daily.asp?date_req=' + date)

            tree = ElementTree.fromstring(response.content)

            for valute in tree.findall('Valute'):
                if valute.find('CharCode').text == currency:
                    response = {
                        "data": {
                            currency: float(valute.find('Value').text.replace(',','.'))
                        },
                        "service": "currency"
                    }
                    self.send_OK(response)
                    break
            else:
                self.send_not_found_request()
        else:
            self.send_not_found_request()

    def send_not_found_request(sender):
        sender.send_response(404)
        sender.send_header('Content-type', 'application/json')
        sender.end_headers()
        response = {
            "error": {
                "code": 404
                },
            "service": "currency"
        }
        sender.wfile.write(bytes(json.dumps(response), 'utf8'))

    def send_OK(self, content):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(bytes(json.dumps(content), 'utf8'))

VERSION = os.getenv('APP_VERSION')
PORT = int(os.getenv('APP_PORT'))

Handler = MyHttpRequestHandler

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print("serving at port", PORT)
    httpd.serve_forever()