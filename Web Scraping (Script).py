#IMPORTING MODULES

from selenium import webdriver
from bs4 import BeautifulSoup
from urllib.request import urlopen as urlReq
import time
import re
from datetime import date,timedelta

#SETING CHECK-IN AND CHECK-OUT DATES

trip_days= 3
y_c,m_c,d_c = date.today().isoformat().split('-')
y_f,m_f,d_f = (date.today()+timedelta(days=trip_days)).isoformat().split('-')

check_in_date = d_c+"/"+m_c+"/"+y_c
check_out_date = d_f+"/"+m_f+"/"+y_f

#SETTING THE MAIN WEBPAGE URL

myurl = "https://me.cleartrip.com/hotels/results?city=Miami&country=US&state=&dest_code=&area=&poi=&hotelId=&hotelName=&chk_in="+check_in_date+"&chk_out="+check_out_date+"&org=&num_rooms=1&adults1=2&children1=0&utm_source=google&utm_medium=organic&utm_campaign=Hotel_Page_Buttons&utm_content=seo_srp_sw"

#READING CONTENTS FROM MAIN WEBPAGE

count = 0 
browser = webdriver.Firefox(executable_path="/home/abhishek/Web Scraping/geckodriver")

try:
	browser.get(myurl)

except Exception as e:
	print("Error Message : Could not fetch the requested webpage")

time.sleep(5)

last_height = browser.execute_script("return document.body.scrollHeight")

while True:
    
    browser.execute_script("window.scrollTo(0,document.body.scrollHeight);")
    
    time.sleep(3)
    
    new_height = browser.execute_script("return document.body.scrollHeight")
    
    if(new_height == last_height):
        break
        
    if(count>5): #LIMITS THE NUMBER OF HOTEL LINKS FETCHED
        break
    last_height= new_height
    count+=1



html = browser.page_source

browser.quit()

#GETTING INDIVIDUAL HOTEL LINKS

Hotel_Links = []

soup = BeautifulSoup(html,'html.parser')
container=soup.findAll("a",{"class":"hotelDetails"})


for index,elements in enumerate(container):
    
    if(elements.get('title')!=None):
        
        Hotel_Links.append("https://me.cleartrip.com"+elements.get('href'))


#VISITING EACH HOTEL LINK TO EXTRACT NECESSARY INFORMATION AND CREATE A JSON FILE FOR EACH HOTEL
try:

	i=1
	for links in Hotel_Links:
	    
	    browser = webdriver.Firefox(executable_path="/home/abhishek/Web Scraping/geckodriver")
	    try:
	        browser.get(links)
	    except Exception as e:
	        print("Error Message : Could not fetch the requested webpage")
	        break;
	    time.sleep(1)

	    hotel_info_html = browser.page_source
	    
	    hotel_info_soup = BeautifulSoup(hotel_info_html,'html.parser')
	    
	    hotel_info_container=hotel_info_soup.findAll("div",{"class":"amenitiesCategory"})
	    
	    ######################################################################################################
	    
	    content = []

	    for divs in hotel_info_container:

	        texts = divs.findAll("div")

	        for x in texts:

	            paragraphs = x.findAll('p')

	            for y in paragraphs:

	                cont = y.text

	                if(cont!=None):
	                    content.append(cont)
	                    
	    About_Hotel = {}


	    for paragraphs in content:

	        sentence = str(paragraphs).split(":")
	        About_Hotel[sentence[0].lower()]= sentence[1:]

	    About_Hotel.pop('')
	    
	    ###############################################################################################################
	    
	    facts = []

	    for divs in hotel_info_container:

	        quick= divs.find("ul",{"class":"clearFix hotelStats"})
	        if(quick !=None):
	            facts.append(quick.text)

	    QF_temp=facts[0].split("\n")
	    
	    while True:
	        try:
	            QF_temp.remove('')

	        except Exception as e:
	            break;
	        
	        
	        
	    Quick_Facts = {}
	    try:
	        Quick_Facts["check-in"] = re.findall('\d+',QF_temp[0])[0]
	        Quick_Facts["check-out"] = re.findall('\d+',QF_temp[1])[0]
	        Quick_Facts["rooms"] = re.findall('\d+',QF_temp[2])[0]
	        Quick_Facts["floors"] = re.findall('\d+',QF_temp[3])[0]
	    
	    except Exception as e:
	        pass
	    
	    #################################################################################################################

	    Other = []

	    for divs in hotel_info_container:

	        quick= divs.find("ul",{"class":"checkList row"})
	        if(quick !=None):
	            Other.append(str(quick.parent.text))
	            
	            
	            
	    Other_Info = {}
	    for catagories in Other:
	        temp = []
	        sent = catagories.split("\n")

	        for index,x in enumerate(sent):
	            if(index>1):
	                temp.append(x)

	        Other_Info[sent[1].lower()] = temp
	        
	        
	        
	        
	    ###################################################################################################################
	    
	    
	    with open("Hotel_JSONs/Hotel "+str(i)+".json","w") as f:
	    
	        about_keys = About_Hotel.keys()
	        facts_keys = Quick_Facts.keys()
	        other_keys = Other_Info.keys()
	        f.write("{\n\n")
	        f.write("\"hotel_name\": " +"\""+ str(hotel_info_soup.title.text).split('|')[0].split(',')[0]+"\","+"\n\n")
	        f.write("\"hotel_url\": " +"\""+ str(links)+"\","+"\n\n")
	        f.write("\"hotel_address\": " +"\""+ str(hotel_info_soup.find("h1",{"itemprop":"name"}).find("small").text.replace('\n',"").replace('\t',"")) +"\","+ "\n\n")
	        
	        #There may not be any reviews for the hotel
	        if(hotel_info_soup.find("a",{"class":"reviewLink"})!=None):
	            f.write("\"hotel_reviews\":" + re.findall('\d+',hotel_info_soup.find("a",{"class":"reviewLink"}).text)[0]+",\n\n")
	        
	        else:
	            f.write("\"hotel_reviews\":"+"0,\n\n")
	        
	        f.write("\"hotel_rating\": " + re.findall('\d+',hotel_info_soup.find("span",{"class":"starRating"}).text)[0]+",\n\n")
	        
	        #Hotel is Unavailable if the price doesnt show up
	        if(hotel_info_soup.find("b",{"id":"b-min-price"})!=None):
	            f.write("\"hotel_price\": " + re.findall('\d+',hotel_info_soup.find("b",{"id":"b-min-price"}).text)[0]+",\n\n")
	        else:
	            f.write("\"hotel_price\": "+"\"Rooms Currently Unavailable\",\n\n")
	        
	        #f.write('\n')
	        f.write("\"hotel_info\": \n\n")
	        f.write("{\n")
	        for index,key in enumerate(about_keys):

	            f.write("\""+str(key)+"\"")
	            f.write(": ")
	            if(index == len(about_keys)-1):
	                f.write("\""+str(About_Hotel[key][0])+"\""+"\n")
	            else:
	                f.write("\""+str(About_Hotel[key][0])+"\","+"\n")

	        f.write("},\n")
	        
	        for key in facts_keys:

	            f.write("\""+str(key)+"\"")
	            f.write(": ")
	            f.write(str(Quick_Facts[key])+",\n")

	        
	        for index,key in enumerate(other_keys):

	            f.write("\""+str(key)+"\"")
	            f.write(": ")
	            f.write("[")
	            for j,x in enumerate(Other_Info[key]):
	                if(x!=''):
	                  
	                    if(j==len(Other_Info[key])-3):
	                        f.write("\""+str(x)+"\"")
	                    else:
	                        f.write("\""+str(x)+"\",")
	            
	            if(index == len(other_keys)-1):
	                f.write("]\n")
	                
	            else:
	                f.write("],\n")

	        f.write("}")
	    i+=1 


	    browser.quit()

except Exception as e:

	print("Error Message : Script Interrupted")

