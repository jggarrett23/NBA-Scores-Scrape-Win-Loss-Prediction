
# coding: utf-8

# In[1]:


import bs4 
import requests
from bs4 import BeautifulSoup as soup
import urllib
import pandas as pd
import re
import openpyxl


# In[2]:


headers = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36'}


# In[3]:


query='exercise cognition AND free full text[sb]'


# In[4]:


q = urllib.quote_plus(query)


# In[5]:


search_url='https://www.ncbi.nlm.nih.gov/pubmed/?term='+ q


# In[6]:


results=requests.get(search_url, headers=headers, timeout=5)


# In[7]:


if results.status_code != 200:
    print False
else:
    page = soup(results.content, "lxml")
    results.close()


# In[8]:


result_containers=page.findAll("div", {"class": "rprt"})


# In[9]:


results_url_list=[]
for searchWrapper in result_containers:
    article_link=searchWrapper.find('a')["href"].encode('ascii','ignore')
    new_url=search_url.replace(q,'')[:28]+article_link
    results_url_list.append(new_url)


# In[10]:


paper_link=[]
for new_link in results_url_list:
    abstract=requests.get(new_link, headers=headers, timeout=5)
    if abstract.status_code !=200:
        print False
    else:
        abstract_page=soup(abstract.content, "lxml")
        abstract.close()
        full_text_container=abstract_page.findAll("div", {"class": "icons portlet"})
        for wrapper in full_text_container:
            full_text_link=wrapper.find('a')["href"]
            paper_link.append(full_text_link.encode('ascii','ignore'))


# In[11]:


new_results={}
try:
    for link in paper_link:
        new_results[link]=requests.get(link, headers=headers, timeout=5)
        new_results[link].close()
except requests.exceptions.ConnectionError:
    pass


# In[ ]:


dic={}
working_links=[]
heading_container={}
table_container={}
for link in new_results.keys():
    if new_results[link].status_code != 200:
        print False, link, new_results[link].status_code
    else:
        full_text_page=soup(new_results[link].content, "lxml")
        title=full_text_page.title.text.strip().encode('ascii','ignore')
        heading_container[link]=full_text_page.findAll(re.compile(r'h\d+'))
        table_container[link]=full_text_page.findAll(re.compile(r'td'))
        for x in heading_container[link]:
            if re.search('Results',x.text, re.IGNORECASE):
                dic[title]={link: x.parent.get_text().strip().encode('ascii','ignore')}
                working_links.append(link)
            if 'Results' in x:
                dic[title]={link: x.parent.get_text().strip().encode('ascii','ignore')}
                working_links.append(link)
        for table in table_container[link]:
            if re.search('Results', table.text, re.IGNORECASE):
                dic[title]={link: table.parent.get_text().strip().encode('ascii','ignore')}
                working_links.append(link)
            if 'Results' in table:
                dic[title]={link: table.parent.get_text().strip().encode('ascii','ignore')}
                working_links.append(link)
number_of_failures=len(new_results.keys())-len(set(working_links))
print 'Unable to get data from %s links.'%number_of_failures


# In[ ]:


dataset=pd.DataFrame(columns=['Title','Link','Text'])


# In[ ]:


dataset['Title']=dic.keys()


# In[ ]:


for title in dic.keys():
    for n in range(len(dataset)):
        if title == dataset['Title'][n]:
            dataset.loc[n, 'Link']=dic[title].items()[0][0]
            dataset.loc[n, 'Text']=dic[title].items()[0][1]


# In[ ]:


book = openpyxl.load_workbook('/Users/owner/Desktop/Article_Database 2.xlsx')


# In[ ]:


writer = pd.ExcelWriter('/Users/owner/Desktop/Article_Database 2.xlsx', engine='openpyxl') 


# In[ ]:


writer.book = book


# In[ ]:


writer.sheets = dict((ws.title, ws) for ws in book.worksheets)


# In[ ]:


dataset.to_excel(writer, 'Sheet1', index=False)


# In[ ]:


writer.save()


# In[ ]:


foo = table_container['http://www.jehp.net/article.asp?issn=2277-9531;year=2018;volume=7;issue=1;spage=57;epage=57;aulast=Jiannine']


# In[ ]:


for f in foo:
    if 'Results' in f.text:
        print 'In text.', f
    if 'Results' in f:
        print 'In other.', f

