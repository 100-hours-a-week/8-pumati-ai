from icrawler.builtin import GoogleImageCrawler

google_crawler = GoogleImageCrawler(storage={'root_dir': './app/model_inference/fine_tuning_data/badges'})
google_crawler.crawl(keyword='badge icon flat design', max_num=150)