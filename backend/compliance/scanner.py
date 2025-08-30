"""Website compliance scanner"""
import aiohttp
from bs4 import BeautifulSoup

class ComplianceScanner:
    async def scan_website(self, url: str) -> dict:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                content = await response.text()
                soup = BeautifulSoup(content, 'html.parser')
                
        return {
            "url": url,
            "content": content,
            "forms": len(soup.find_all('form')),
            "images": len(soup.find_all('img')),
            "links": len(soup.find_all('a'))
        }
