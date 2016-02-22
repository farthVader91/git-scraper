# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import pymongo

class MongoPipeline(object):

    pr_collection = 'pull_requests'
    issue_collection = 'issues'

    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI'),
            mongo_db=crawler.settings.get('MONGO_DATABASE', 'items')
        )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]

    def close_spider(self, spider):
        self.client.close()

    def persist_pr(self, item):
        query = {'organisation': item['organisation'],
                 'project': item['project'],
                 'handle': item['handle'],
                 'pr_no': item['pr_no'],
                 'pr_status': item['pr_status']}
        self.db[self.pr_collection].update(query, dict(item), upsert=True)

    def persist_iss(self, item):
        query = {
            'organisation': item['organisation'],
            'project': item['project'],
            'issue_no': item['issue_no'],
            'pr_no': item['pr_no']
        }
        self.db[self.issue_collection].update(query, dict(item), upsert=True)

    def process_item(self, item, spider):
        item_type = item.pop('_type')
        if item_type == 'pull_request':
            self.persist_pr(item)
        else:
            self.persist_iss(item)

        return item
