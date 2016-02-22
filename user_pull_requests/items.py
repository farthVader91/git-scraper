# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from bson.json_util import dumps

class BaseItem(scrapy.Item):
    _type = scrapy.Field()
    url = scrapy.Field()

class PullRequestItem(BaseItem):
    # define the fields for your item here like:
    # name = scrapy.Field()
    organisation = scrapy.Field()
    project = scrapy.Field()
    handle = scrapy.Field()
    pr_no = scrapy.Field(serializer=int)
    pr_status = scrapy.Field()
    datetime = scrapy.Field(serializer=dumps)

class IssueItem(BaseItem):
    organisation = scrapy.Field()
    project = scrapy.Field()
    issue_no = scrapy.Field(serializer=int)
    pr_no = scrapy.Field(serializer=int)
    labels = scrapy.Field()
