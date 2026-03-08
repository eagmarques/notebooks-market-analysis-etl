"""
notebook.py — Scrapy Spider
Collects raw notebook listings from Mercado Livre.

Responsibility: data extraction only.
Brand normalization is handled downstream by the ETL transform layer.
"""

import scrapy


class NotebookSpider(scrapy.Spider):
    name = "notebook"
    start_urls = [
        "https://lista.mercadolivre.com.br/informatica/portateis-acessorios/notebooks/novo/"
    ]

    def parse(self, response):
        products = response.css("div.ui-search-result__wrapper")

        for product in products:
            title = (
                product.css("h2.poly-component__title::text").get()
                or product.css("a.poly-component__title::text").get()
                or product.css("h2.ui-search-item__title::text").get()
            )

            # ── Price Extraction ──────────────────────────────────────────────
            # - old_money: the original crossed-out price (using --previous class)
            # - new_money: the actual current price (using --current class or fallback)
            old_money_raw = product.css('.andes-money-amount--previous .andes-money-amount__fraction::text').get()
            
            new_money_raw = (
                product.css('.andes-money-amount--current .andes-money-amount__fraction::text').get() or
                product.css('.poly-price__current .andes-money-amount__fraction::text').get() or
                product.css('.andes-money-amount:not(.andes-money-amount--previous) .andes-money-amount__fraction::text').get()
            )

            # ── Brand Extraction ──────────────────────────────────────────────
            # Try specific brand component first, then fallback to discoverability tag
            brand_raw = (
                product.css('.poly-component__brand::text').get() or
                product.css('span.ui-search-item__brand-discoverability::text').get()
            )

            # Sales & rating share the same CSS class; the first occurrence is the
            # rating and the last is the sales count text (e.g. '+1.2 mil vendidos').
            phrase_labels = product.css("span.poly-phrase-label::text").getall()

            yield {
                "name": title,
                "brand": brand_raw,
                "seller": product.css("span.poly-component__seller::text").get(),
                "reviews_rating_number": phrase_labels[0] if phrase_labels else None,
                "sales_bucket": phrase_labels[-1] if phrase_labels else None,
                "old_money": old_money_raw,
                "new_money": new_money_raw,
                "url": (
                    product.css("a.poly-component__title::attr(href)").get()
                    or product.css("a.ui-search-link::attr(href)").get()
                ),
            }

        # Pagination: follow the next page if the button is not disabled.
        has_next = (
            response.css(
                "li.andes-pagination__button--next:not(.andes-pagination__button--disabled)"
            ).get()
            is not None
        )

        if has_next:
            base_url = response.meta.get("base_url", response.url.split("_Desde_")[0])
            current_page = response.meta.get("current_page", 1)
            next_page = current_page + 1
            offset = (next_page - 1) * 50 + 1
            next_url = f"{base_url}_Desde_{offset}_NoIndex_True"
            yield scrapy.Request(
                url=next_url,
                callback=self.parse,
                meta={"current_page": next_page, "base_url": base_url},
            )
