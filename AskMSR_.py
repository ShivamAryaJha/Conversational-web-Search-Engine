
import requests as rq, string, re, nltk
from bs4 import BeautifulSoup
from nltk.tokenize import sent_tokenize
from nltk import pos_tag
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

def what(words, answer, boolean):                 # function block for what questions
    answer_string = ''
    if boolean == True:    # wikipedia answer or just google search result ?
        sent = sent_tokenize(answer)[0]
        sent = re.sub("[\(\[].*?[\)\]]", "", sent)
        return sent

    elif words[1] == 'is' or words[1] == 'was':   
        for i in words[2:]:
            answer_string += i + ' '
        answer_string += words[1] + ' ' + answer
    return answer_string

def where(words, answer):                         # function block for where questions
    answer_string, place, verb = '', ' at ', ''
    a_words = answer.split(' ')
    tagged_a = pos_tag([a_words[0]])
    tagged_q = pos_tag([words[-1]])

    if tagged_q[0][1][0] == 'V':
        verb = words[-1]
    if tagged_a[0][1] == 'IN':
        place = ''

    if words[1] == 'is' or words[1] == 'was':
        if tagged_q[0][1][0] == 'V':
            for i in words[2:-1]:
                answer_string += i + ' '
        else:
            for i in words[2:]:
                answer_string += i + ' '
        answer_string += words[1] + ' ' + verb  + place + answer

    elif words[1] == 'did' or words[1] == 'do':
        for i in words[2:]:
            answer_string += i + ' '
        answer_string += place + answer
    return answer_string

def who(query, answer, words):                 # function block for who questions
    aux = ['is', 'was']
    ans_string = ''
    if words[1] in aux and words[2] != 'the':
        for w in words[2:]:
            ans_string += w + ' '
        ans_string += words[1] + ' ' + answer

    else: ans_string = query.replace('who', answer)
    return ans_string

def when(words, answer):                       # function block for when questions
    answer_string, prep, cn, verb = '', ' during ', 0, ''
    months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
    prep = ' during '                              # Checking which prepositions to insert based on time format
    for m in months: 
        if answer.find(m) != -1: cn += 1
    if cn == 1: prep = 'on '
    a_words = answer.split(' ')
    tagged_a = pos_tag([a_words[0]])
    tagged_q = pos_tag([words[-1]])

    if tagged_q[0][1][0] == 'V':
        verb = words[-1]
    if tagged_a[0][1] == 'IN':
        prep = ''
    if words[1] == 'is' or words[1] == 'was':
        if tagged_q[0][1][0] == 'V':
            for i in words[2:-1]:
                answer_string += i + ' '
        else:
            for i in words[2:]:
                answer_string += i + ' '
        answer_string += words[1] + ' ' + verb  + prep + answer
    elif words[1] == 'did' or words[1] == 'do':
        for i in words[2:]:
            answer_string += i + ' '
        answer_string += prep + answer
    return answer_string


# actual runtime code begins from here

translator = str.maketrans('', '', string.punctuation)        # removing punctuation for pre-processing
driver_path =".\\geckodriver.exe"                             # path of the Firefox webdriver for Selenium
options = Options()                                           # Browser automation options to simulate browser behaviour
options.headless = True

# A kind introduction by our chatbot
print("\nHey dear friend!\nI'm a QnA assistant who'll help you answer most of your queries. However, I can only deal with questions \nbeginning with What, Who, Where and When. To leave the program, please type Exit.\n\n")

while(True):  # an infinite loop of questions

    boolean = False          
    browser = webdriver.Firefox(service = Service(driver_path), options= options)  # initilaize new instance of browser for web scraping
    orig_query = input("Hey, what can I help you know today? \n>>> ")              # Python command line input
    query = orig_query.lower()                                                     # preprocessing
    if query == "exit":                                                            # exiting condition by user
        print("..until we meet again then, \nGood-Bye :) ") 
        break
    query = query.translate(translator)                                            # remove punctutation
    search_query = query.replace(' ', '+')
    browser.get("https://www.google.com/search?q=" + search_query + "&start=0#dobc=en")    # perform google search using our query

    answer = 'nan'
    try: header = browser.find_element(By.CLASS_NAME, 'ULSxyf')                    # Class name for google card in top results
    except:
        print("Sorry, I don't know the answer to that. \n")
        continue
    dict = header.find_elements(By.XPATH, "//div[@class='LTKOO sY7ric']")          # cLASS NAME FOR DICTIONARY TYPE definitions

    if len(dict) > 0: 
        answer = dict[0].find_element(By.TAG_NAME, 'span').text                    
    else:
        bold = header.find_elements(By.TAG_NAME, 'b')                              # if bold text is found, capture that 
        if len(bold) > 0:
            answer = bold[0].text
    
    if len(answer) < 5:
        get_header = header.find_elements(By.XPATH, '//div[@aria-level="3"]')      # otherwise if a particular text size is there, scrape that instead
        if len(get_header) > 0:
            answer = get_header[0].text
        if len(answer) < 5:
            people = header.find_elements(By.XPATH, "//div[@class='bVj5Zb FozYP']")  # if cards of individuals and people are displayed by google
            if len(people) > 0:
                answer = ""
                for p in people: answer += p.text + ' & '
                answer = answer.strip('& ')

    if len(answer) < 5 :
        boolean = True                           # if nothing else works, try finding the search query on Wikipedia
        try: wiki = browser.find_element(By.PARTIAL_LINK_TEXT, "wikipedia").get_attribute("href")      # get link of closest wikipedia page
        except:
            print("Sorry, I don't know the answer to that. \n")
            continue
        page = rq.get(wiki)                      # HTTP GET and scrape the Wikipedia page
        soup = BeautifulSoup(page.content, 'html.parser')   # Using bs4 to scrape

        para_list = soup.find_all('p')           # Scraping all paragraphs on the Wiki page
        for p in para_list:
            if len(p.get_text()) > 5:
                answer = p.get_text()            # Keeping only first paragrah for our purpose
                break

    browser.quit()                              # Close the Selenium instance
    words = query.split(' ')                    # Word- tokenization

    # Calling functions for their corresponding question formats
    if words[0] == 'what':
        answer = what(words, answer, boolean)
    elif words[0] == 'when':
        answer = when(words, answer.strip())
    elif words[0] == 'who':
        answer = who(query, answer, words)
    elif words[0] == 'where':
        answer = where(words, answer.strip())
    else:
        answer = "Sorry, I don't know the answer to that. \n"
    
    answer = answer.capitalize()                     # Capitalize into sentence case
    print("ANS: ", answer.strip(), "\n")             # Print the final answer

