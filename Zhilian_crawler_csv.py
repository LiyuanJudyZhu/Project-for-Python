
# 导包
import urllib.request
import urllib.parse
from lxml import etree
import time
from selenium import webdriver
import os
import csv


# 存储智联招聘工作信息
# 分析
# 一级页面
# 职位(job)  工资(salary)  经验experience
# 学历education  福利welfare   公司company  people人数
# 二级页面
# 职位信息jobInfo  公司地址address、公司概况companyInfo
class JobItem(object):
    def __init__(self, job="", salary="", experience="", education="", welfare="", company="", people="", jobInfo="", address="", companyInfo="",name="",page=""):
        self.job = job
        self.salary = salary
        self.experience = experience
        self.education = education
        self.welfare = welfare
        self.company = company
        self.people = people
        self.jobInfo = jobInfo
        self.address = address
        self.companyInfo = companyInfo
        self.name = name



# 爬取页面
# 起始页、结束页
# url
# 应该要输入城市
# https://sou.zhaopin.com/?jl=%E5%B9%BF%E5%B7%9E&sf=0&st=0&kw=python%E5%AE%9E%E4%B9%A0&kt=3
# https://sou.zhaopin.com/?p=3&jl=%E5%B9%BF%E5%B7%9E&kw=python
# 得出结论
# https://sou.zhaopin.com/?p=页码&jl=城市&kw=工作
# 需要注意url的编码格式，可以使用urlencode
class zhilianSpider(object):
    def __init__(self, start_page, end_page, city, job, url):
        self.start_page = start_page
        self.end_page = end_page
        self.city = city
        self.job = job
        self.url = url

        # 请求头
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36'
        }

        # selenium
        # 无头模式
        chrome_opt = webdriver.ChromeOptions()
        chrome_opt.add_argument("--headless")

        # 浏览器驱动对象
        self.browser = webdriver.Chrome(options=chrome_opt)

    # 请求模块
    # 一级界面
    def first_job_request(self, url):
        # 模拟浏览器运行
        # 发起请求
        print("一级界面：", url)
        self.browser.get(url)
        time.sleep(1)
        return self.browser.page_source


    def second_job_request(self, url, callback, item):
        # 创建请求
        req = urllib.request.Request(url, headers=self.headers)
        print("二级页面：", url)
        # 发起请求
        res = urllib.request.urlopen(req)

        # 回调函数
        # 为什么要有这个东西，是这样的，我们从一级界面中获取了job的url然后，我们利用这个url发起请求，这个时候得到相应，然后回调出解析二级界面的函数
        yield callback(res.read().decode("utf-8"), item)

    # 解析模块
    # 一级界面
    def first_job_parse(self, html):
        html_etree = etree.HTML(html)

        # 一页的职位
        job_list = html_etree.xpath('//div[@id="listContent"]/div')
        # print("job_list", job_list)

        for job in job_list:
            try:
                # 创建职位对象
                jobitem = JobItem()
                # 职位
                jobitem.job = job.xpath('.//span[contains(@class,"jobname__title")]/@title')[0]
                # print("jobitem.job", jobitem.job)
                # 工资
                jobitem.salary = job.xpath('.//p[contains(@class, "job__saray")]/text()')[0]
                # 经验要求
                jobitem.experience = job.xpath('.//li[2]/text()')[0]
                # 学历要求
                jobitem.education = job.xpath('.//li[3]/text()')[0]
                # 福利
                a= "、".join(job.xpath(".//div[contains(@class,'welfare')]//text()"))
                jobitem.welfare=a.strip(' 、')
                # 公司链接
                jobitem.company = job.xpath('.//div[@class="contentpile__content__wrapper__item clearfix"]/a/@href')[0]

                #公司名称
                jobitem.name = job.xpath('.//a[contains(@class,"company_title")]/@title')[0]
                # 人数
                jobitem.people = job.xpath('.//div[contains(@class,"job__comdec")]/span[2]/text()')[0]
                #
                # second_url = job.xpath('.//a[contains(@zp-stat-id,"jd_click")]/@href')[0]
                # yield self.second_job_request(url=second_url, callback=self.second_job_parse, item=jobitem)


            except:
                print('下一页')

            data=[
                jobitem.job,
                jobitem.salary,
                jobitem.experience,
                jobitem.education,
                jobitem.welfare,
                jobitem.company,
                jobitem.name,
                jobitem.people,
                # jobItem.address
            ]

            print(data)
            if data:
                self.writePage(data)

    def second_job_parse(self, html, item):
        html_tree = etree.HTML(html)
        jobItem = item
        # print(jobItem.job)
        # jobItem.companyInfo = r"\n".join(html_tree.xpath("//div[@class='jjtxt']//text()"))
        jobItem.address = html_tree.xpath("//p[@class='add-txt']//text()")[0] if html_tree.xpath("//p[@class='add-txt']//text()") else "未提供地址"
        # jobItem.jobInfo = r"\n".join(html_tree.xpath("//div[contains(@class,'pos-common')]//text()"))

        return jobItem

    def writePage(self,data):
        with open(str(self.job)+'.csv','a',newline="",encoding='gb18030') as f:
            writer = csv.writer(f)
            writer.writerow(data)


    # 对外接口
    def crawl_spider(self):

        for page in range(int(self.start_page), int(self.end_page)+1):
            # 处理url
            page_url = self.url.format(str(page), self.city, self.job)
            # 发起一级界面的请求
            html_text = self.first_job_request(page_url)

            # 解析界面
            # 在解析完一级界面的时候
            # 发起对二级界面的请求
            # 并且回调对二级界面的解析
            self.first_job_parse(html_text)

            page=etree.HTML(html_text)
            r2=page.xpath('//span[@class="soupager__index soupager__index--active"]/text()')
            if not r2:
                break
        self.browser.close()


# 主函数
def main():
    url = "https://sou.zhaopin.com/?p={}&jl={}&kw={}"



    # 开始页
    start_page = '1'
    # 结束页
    end_page = '100'

    # 请输入城市
    city = "广州"
    # 职位
    job = "数据分析师"
    # 初始化爬虫对象
    zhilian = zhilianSpider(start_page=start_page, end_page=end_page, city=city, job=job, url=url)
    # 调用接口
    zhilian.crawl_spider()


if __name__ == '__main__':
    main()
