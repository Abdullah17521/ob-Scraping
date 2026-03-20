BOT_NAME = 'scrapy_project'

SPIDER_MODULES = ['scrapy_project.spiders']
NEWSPIDER_MODULE = 'scrapy_project.spiders'

ROBOTSTXT_OBEY = False
DOWNLOAD_DELAY = 1.5
CONCURRENT_REQUESTS = 8
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1.0
AUTOTHROTTLE_MAX_DELAY = 3.0
RANDOMIZE_DOWNLOAD_DELAY = True

FEED_EXPORT_ENCODING = 'utf-8-sig'

DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': 400,
}
