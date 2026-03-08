import scrapy

class NotebookSpider(scrapy.Spider):
    name = "notebook"
    start_urls = ["https://lista.mercadolivre.com.br/informatica/portateis-acessorios/notebooks/novo/"]

    def parse(self, response):
        products = response.css('div.ui-search-result__wrapper')
        for product in products:
            title = product.css('h2.poly-component__title::text').get() or product.css('a.poly-component__title::text').get() or product.css('h2.ui-search-item__title::text').get()
            
            # The user asked to extract the brand, and it is no longer available in the component class
            # We can extract it from the product title using common notebook brands
            brands = ['dell', 'hp', 'lenovo', 'acer', 'apple', 'asus', 'samsung', 'positivo', 'vaio', 'multilaser', 'lg', 'compaq', 'galaxy book', 'ultra', 'atfly', 'macbook', 'legion', 'toshiba', 'rog', 'msi', 'gigabyte']
            
            brand = None
            if title:
                title_lower = title.lower()
                for b in brands:
                    if b in title_lower:
                        brand = b.capitalize() if b != 'hp' else 'HP'
                        if brand == 'Galaxy book':
                            brand = 'Samsung'
                        if brand == 'Macbook':
                            brand = 'Apple'
                        if brand == 'Legion':
                            brand = 'Lenovo'
                        if brand == 'Rog':
                            brand = 'Asus'
                        break

            prices = product.css('span.andes-money-amount__fraction::text').getall()
            
            yield {
                'brand': brand,
                'name': title,
                'seller': product.css('span.poly-component__seller::text').get(),
                'reviews_rating_number': product.css('span.poly-phrase-label::text').get(),
                'sales_bucket': product.css('span.poly-phrase-label::text').getall()[-1] if product.css('span.poly-phrase-label::text').getall() else None,
                'old_money': prices[0] if len(prices) > 0 else None,
                'new_money': prices[1] if len(prices) > 1 else None,
                'url': product.css('a.poly-component__title::attr(href)').get() or product.css('a.ui-search-link::attr(href)').get()
            }
            
        # Find out if the next page button is active
        has_next = response.css('li.andes-pagination__button--next:not(.andes-pagination__button--disabled)').get() is not None
        
        if has_next:
            base_url = response.meta.get('base_url', response.url.split('_Desde_')[0])
            current_page = response.meta.get('current_page', 1)
            next_page_num = current_page + 1
            offset = (next_page_num - 1) * 50 + 1
            next_url = f"{base_url}_Desde_{offset}_NoIndex_True"
            yield scrapy.Request(url=next_url, callback=self.parse, meta={'current_page': next_page_num, 'base_url': base_url})
