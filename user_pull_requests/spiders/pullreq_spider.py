
import re
import urlparse
import scrapy
import calendar
from datetime import datetime
from user_pull_requests.items import (
    PullRequestItem,
    IssueItem)

class PullRequestSpider(scrapy.Spider):
    name = 'pullrequests'
    start_urls = [
        'https://www.hackerearth.com/sprints/open-source-india-hacks-2016/'
    ]
    allowed_domains = [
        "hackerearth.com",
        # Restrict scraping through github for now
        "github.com",
    ]

    failed_urls = []

    def parse(self, response):
        # generic url format string for parsing through closed issues,
        # merged & open pull requests.
        path_fmt = '{category}?q=is%3A{status}+created%3A>{time_str}'
        xstr = "//*[contains(text(),'View Project')]/@href"
        for repo_url in response.xpath(xstr).extract():
            repo_url = repo_url.strip()
            if repo_url[-1] != '/':
                repo_url = '{}/'.format(repo_url)
            # construct urls for open pull requests
            open_pr_path = path_fmt.format(
                category='pulls',
                status='open',
                time_str='2016-01-29')
            open_pr_url = urlparse.urljoin(repo_url, open_pr_path)

            # construct url for merged pull requests
            merged_pr_path = path_fmt.format(
                category='pulls',
                status='merged',
                time_str='2016-01-29')
            merged_pr_url = urlparse.urljoin(repo_url, merged_pr_path)

            # construct url for closed issues
            closed_issues_path = path_fmt.format(
                category='issues',
                status='closed',
                time_str='2016-01-29')
            closed_issues_url = urlparse.urljoin(repo_url, closed_issues_path)

            # extract organisation & project from repo url
            url_parts = urlparse.urlparse(repo_url)
            organisation, project = url_parts.path.split('/')[1:3]

            # delegate to next level parsers
            yield scrapy.Request(
                open_pr_url, callback=self.parse_pulls,
                meta={
                    'status': 'open',
                    'organisation': organisation,
                    'project': project})
            yield scrapy.Request(
                merged_pr_url, callback=self.parse_pulls,
                meta={'status': 'merged',
                      'organisation': organisation,
                      'project': project})
            yield scrapy.Request(
                closed_issues_url, callback=self.parse_github_issues,
                meta={'organisation': organisation,
                      'project': project})

    def get_next_page_url(self, response):
        # identify if more pages pending and make recursive calls
        pg_xstr = "//*[@class='pagination']/*[contains(text(), 'Next')]"
        next_btn = response.xpath(pg_xstr)
        if not next_btn:
            # implies only 1 page of results exist; return
            return None
        if next_btn.xpath('@class').extract()[0] != "next_page disabled":
            # implies there are still more pages to go...
            next_url = urlparse.urljoin(
                    response.url,
                    next_btn.xpath('@href').extract()[0])
            return next_url

    def parse_pulls(self, response):
        status = response.meta['status']
        organisation = response.meta['organisation']
        project = response.meta['project']

        issue_listing_xstr = '//*[@id="js-repo-pjax-container"]/div[2]/div[1]/div/ul/li'
        issue_listing = response.xpath(issue_listing_xstr)
        # skip if there are no issues
        if not issue_listing:
            print "No issues at {}. Skipping...".format(response.url)
            return

        for li in issue_listing:
            item = PullRequestItem()
            pr_no = li.xpath('@id').re(r'issue_(\d+)')[0]

            item['organisation'] = organisation
            item['project'] = project
            item['handle'] =li.xpath(
                'div[2]/div/span/a/@aria-label').re(
                    r'^View all pull requests opened by (.+)$')[0]
            item['pr_no'] = pr_no 
            item['pr_status'] = status
            dt_str = li.xpath(
                'div[2]/div[1]/span/time/@datetime').extract()[0]
            dt = datetime.strptime(dt_str,
                                   '%Y-%m-%dT%H:%M:%SZ')
            item['datetime'] = dt
            item['url'] = 'https://github.com/{organisation}/{project}/issues/{pr_no}'.format(
                    organisation=organisation,
                    project=project,
                    pr_no=pr_no)
            item['_type'] = 'pull_request'
            # item['datetime'] = calendar.timegm(dt.timetuple())
            yield item

            next_page_url = self.get_next_page_url(response)
            if next_page_url:
                yield scrapy.Request(
                    next_page_url,
                    callback=self.parse_pulls,
                    meta={
                        'status': status,
                        'organisation': organisation,
                        'project': project
                    })


    def parse_github_issues(self, response):
        organisation = response.meta['organisation']
        project = response.meta['project']
        href_xstr = "//div[@class='issues-listing']//*[contains(@class, 'issue-title-link')]/@href"
        for href in response.xpath(href_xstr).extract():
            url = urlparse.urljoin(response.url, href)
            yield scrapy.Request(
                    url, callback=self.parse_closed_github_issues,
                    meta={
                        'organisation': organisation,
                        'project': project,
                    })

        next_page_url = self.get_next_page_url(response)
        if next_page_url:
            yield scrapy.Request(
                next_page_url,
                callback=self.parse_github_issues,
                meta={
                    'organisation': organisation,
                    'project': project
                })


    def parse_closed_github_issues(self, response):
        project = response.meta['project']
        organisation = response.meta['organisation']
        issue_no = response.url.rstrip('/').split('/')[-1]
        # extract issue labels
        label_xstr = "//*[contains(@class, 'discussion-item-labeled')]/div/span[2]/a/text()"
        labels = response.xpath(label_xstr).extract()
        # check if issue contains a merged pull request
        pull_req_xstr = "//span[contains(@class, 'state-merged')]/following-sibling::h3/a/span/text()"
        pull_reqs = response.xpath(pull_req_xstr).re('#(\d+)')
        if len(pull_reqs) == 0:
            print 'skipping...', response.url
            return
        for pr_no in pull_reqs:
            item = IssueItem()
            item.update({
                'organisation': organisation,
                'project': project,
                'issue_no': issue_no,
                'pr_no': pr_no,
                'labels': labels,
                '_type': 'issue',
                'url': 'https://github.com/{organisation}/{project}/issues/{pr_no}'.format(
                    organisation=organisation,
                    project=project,
                    pr_no=pr_no),
                })
            yield item

