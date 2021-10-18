import sys
import string
import spacy
from difflib import SequenceMatcher


################################################### GLOBALS ##########################################################

## cONTAINS UNIQUE ENTITIES OF EACH CATEGORY
company_entities_dict= {}
location_entities_dict = {}
address_entities_list = []
serial_number_entities_list = []
goods_entities_list = []

## CONTAINS A LIST OF SUFFIXES USED FOR ORGANISATIONS
company_suffixes_list = []

#########################################################################################################################



##### en_core_web_lg is the NER model and opentapioca is the NEL model
nlp = spacy.load("en_core_web_lg") # Large model
nlp.add_pipe('opentapioca') # For Entity Linking


##### TXT DOCUMENT HAS LIST OF SUFFIXES OF ORGANISATIONS
with open("suffixes list.txt","r") as file:
    file_str = file.read()
    company_suffixes_list = file_str.lower().splitlines()


#########################################################################################################################


#########################################################   HELPER METHODS ##############################################3######

"""
find_suffix_in_company_name : INPUT : entity as string
CHECK EVERY WORD IN ENTITY AND FIND IF THERE'S ANY COMMONLY USED ORGANISATION SUFFIX
RETURN TEH SUFFIX OR -1 IF NONE S FOUND
"""
def find_suffix_in_company_name(entity_value):
    global company_suffixes_list
    entity_value_list = entity_value.split(" ")
    for value in entity_value_list:
        if(value.lower() in company_suffixes_list):
            return value
    return -1


"""
normalise_string : INPUT : STRING
1. LOWER CASE
2. REMOVE WHITESPACE
3. REMOVE PUNCTUATIONS : 
{'%', '#', '$', ':', '[', '+', '!', '*', ',', '_', '=', "'", '/', '"', '~', ';', ')', '@', '`', '.', '?', '>', '|', '^', '(', '{', '<', '-', ']', '&', '\\', '}'}
RETURN STRING
"""
def normalise_string(entity_str):
    entity_str = entity_str.lower().replace(" ","")
    exclude = set(string.punctuation)
    entity_str =  ''.join(ch for ch in entity_str if ch not in exclude)
    return entity_str


"""
compare_strings_sequence_match : INPUTS : 2 STRINGS TO COMPARE AND MIN MATCH THRESHOLD
1. NORMALISE BOTH STRINGS
2. DIFFLIB'S SEQUENCERMATCHER IS USED
3. IF SIMLARITY GREATER THAN(OR EQUAL TO) THRESHOLD RETURN TRUE
ELSE, RETURN FALSE
"""
def compare_strings_sequence_match(str1 ,str2 ,compare_ratio=0.8):
    str1 = normalise_string(str1)
    str2 = normalise_string(str2)
    sim_score = SequenceMatcher(None, str1, str2).ratio()
    if(sim_score >= compare_ratio):
        return True
    else:
        return False


"""
check_if_name_exists : INPUT : STRING
1. REMOVE ORGANISATION SUFFIXES
2. COMPARE STRING WITH ALL VALUES IN COMAPNY NAME DICTIONARY

"""
def check_if_name_exists(entity_value):
    global company_entities_dict
    ## process the input string 
    comapny_suffix = find_suffix_in_company_name(entity_value)
    ## 1. strip suffixes of the string 
    entity_str1 = entity_value.replace(comapny_suffix,"") if(comapny_suffix != -1) else entity_value
    ## 2. Comare with all 

    for entity_str2 in company_entities_dict.values():
        comapny_suffix = find_suffix_in_company_name(entity_str2)
        entity_str2 = entity_str2.replace(comapny_suffix,"") if(comapny_suffix != -1) else entity_str2
        if(compare_strings_sequence_match(entity_str1, entity_str2,0.9)):
            return True
    return False


"""
check_if_exists_in_dict_ : INPUT : COMPANY NAMES/LOCATION DICTIONARY , INPUT SRING , MATCHING THRESHOLD
COMPARES INPUT TO EACH VALUE IN DICTIONARY, 
RETURNS TRUE IF MATCH FOUND

"""
def check_if_exists_in_dict_(dict_to_compare_in , entity_str1,compare_ratio):
    for entity_str2 in dict_to_compare_in.values():
        if(compare_strings_sequence_match(entity_str1, entity_str2,compare_ratio)):
            return True
    return False

"""
check_if_exists_in_list_ : INPUT : SNO, GOODS, ADDRESS LISTS , INPUT SRING , MATCHING THRESHOLD
COMPARES INPUT TO EACH VALUE IN LIST, 
RETURNS TRUE IF MATCH FOUND

"""
def check_if_exists_in_list_(list_to_compare_in , entity_str1,compare_ratio):
    for entity_str2 in list_to_compare_in:
        if(compare_strings_sequence_match(entity_str1, entity_str2,compare_ratio)):
            return True
    return False


################################################################################################################################


################################################### NEN SYSTEMS FOR ENTITTIES ################################################3


"""
entity_company_name : INPUT : input entity as string
1. USING SPACY'S NER+NEL(NAMED ENTITY LINKING) PIPELINE TO TEST IF THIS ORGANISATION NAME HAS BEEN DEFINED IN SPACY'S KB(KNOWLEDGE BASE) 
        If Yes, and If its not it our list, we add it or if its a duplicate , ignore it
2. CUSTOM PROCESSING :
        1. CHECK IF ANY COMMONLY USED ORGANISATION PREFIXES ARE THERE : eg. Ltd, IF YES, REMOVE THEM,
        2. NORMALISE IT: REMOVE SPACING , PUNCTUATION, 
        If its not it our list, we add it or if its a duplicate , ignore it
"""
def entity_company_name(entity_value):
    global company_entities_dict ,company_suffixes_list
    flag = False

    ## Processing for NLP model
    entity_value_str = str(entity_value) + " is in US" ## Added the string as NER/NEL fails to recognise well for single words
    doc = nlp(entity_value_str)
    for span in doc.ents:
        if(span.label_ == "ORG"):
            flag = True
            if(span.kb_id_ not in company_entities_dict.keys()):
                company_entities_dict[span.kb_id_] = entity_value
    
    ## If not detected by Spacy's model, custom process it
    if(flag == False):
        ret = check_if_name_exists(entity_value)
        if(ret == False):
            company_entities_dict[entity_value] = entity_value ## Add value if its not a duplicate


"""
entity_location   : INPUT : input entity as string
1. USING SPACY'S NER+NEL(NAMED ENTITY LINKING) PIPELINE TO TEST IF THIS LOCATION NAME HAS BEEN DEFINED IN SPACY'S KB(KNOWLEDGE BASE) 
        If Yes, and If its not it our list, we add it or if its a duplicate , ignore it
2. CUSTOM PROCESSING :
        1. NORMALISE IT: REMOVE SPACING , PUNCTUATION, 
        If its not it our list, we add it or if its a duplicate , ignore it

"""
def entity_location(entity_value):
    global location_entities_dict
    entity_value_str = str(entity_value).title() + " is in the US" ## Added the string as NER/NEL fails to recognise well for single words
    doc = nlp(entity_value_str)
    flag = False
    if(len(doc.ents) >= 2):
        for span_index in range(len(doc.ents) - 1):
            #print(doc.ents[span_index].kb_id_,doc.ents[span_index].text,entity_value)
            if(doc.ents[span_index].label_ == "LOC"):
                flag = True
                if(doc.ents[span_index].kb_id_ not in location_entities_dict.keys()):
                    location_entities_dict[doc.ents[span_index].kb_id_] = entity_value
                    break
                else:
                    break
    if(flag == False):
        ret = check_if_exists_in_dict_(location_entities_dict , entity_value,0.9)
        if(ret == False):
            location_entities_dict[entity_value] = entity_value



"""
entity_serial_number   : INPUT : input entity as string
CUSTOM PROCESSING :
        1. NORMALISE IT: REMOVE SPACING , PUNCTUATION, CHECK WITH ABSOLUTE ACCURACY VALUE AS A SINGLE CHARACTER CHNAGE(DIGITS,ALPHABETS) COULD MEAN DIFFERENT ENTTTIES
        If its not it our list, we add it or if its a duplicate , ignore it
"""

def entity_serial_number(entity_value):
    global serial_number_entities_list 
    if(len(serial_number_entities_list) >0):
        ret = check_if_exists_in_list_(serial_number_entities_list,entity_value,1.0)
        if(ret == False):
                serial_number_entities_list.append(entity_value)
    else:
        serial_number_entities_list.append(entity_value)



"""
entity_address   : INPUT : input entity as string
CUSTOM PROCESSING :
        1. NORMALISE IT: REMOVE SPACING , PUNCTUATION, CHECK WITH ABSOLUTE ACCURACY VALUE AS A SINGLE CHARACTER CHNAGE(DIGITS,ALPHABETS) COULD MEAN DIFFERENT ENTTTIES
        If its not it our list, we add it or if its a duplicate , ignore it
"""

def entity_address(entity_value):
    global address_entities_list
    if(len(address_entities_list) >0):
        ret = check_if_exists_in_list_(address_entities_list,entity_value,1.0)
        if(ret == False):
                address_entities_list.append(entity_value)
    else:
        address_entities_list.append(entity_value)


"""
entity_goods   : INPUT : input entity as string
CUSTOM PROCESSING :
        1. NORMALISE IT: REMOVE SPACING , PUNCTUATION, CHECK WITH 90% ACCURACY VALUE AS A SLIGHT ERRORS IN  CHARACTERS  COULD STILL MEAN DIFFERENT ENTTTIES
        If its not it our list, we add it or if its a duplicate , ignore it
"""
def entity_goods(entity_value):
    global goods_entities_list
    if(len(goods_entities_list) >0):
        ret = check_if_exists_in_list_(goods_entities_list,entity_value,0.9)
        if(ret == False):
            goods_entities_list.append(entity_value)
    else:
        goods_entities_list.append(entity_value)


############################################### PARSER  #######################################################33333333

if __name__ == "__main__":

    if(sys.argv[1] == "-c"):                               ################### COMPANY NAME ########################
        for i in range(2, len(sys.argv)):
            entity_company_name(str(sys.argv[i]))
        print(list(company_entities_dict.values()))
    
    
    elif(sys.argv[1] == "-l"):                            ################### COMPANY LOCATION ########################
        for i in range(2, len(sys.argv)):
            entity_location(str(sys.argv[i]))
        print(list(location_entities_dict.values()))
    
    
    elif(sys.argv[1] == "-s"):                              ################### SERIAL NUMBERS ########################
        for i in range(2, len(sys.argv)):
            entity_serial_number(str(sys.argv[i]))
        print(serial_number_entities_list)
    
    
    elif(sys.argv[1] == "-a"):                              ################### COMPANY ADDRESS ########################
        for i in range(2, len(sys.argv)):
            entity_address(str(sys.argv[i]))
        print(address_entities_list)
    
    
    elif(sys.argv[1] == "-g"):                              ################### GOODS ########################
        for i in range(2, len(sys.argv)):
            entity_goods(str(sys.argv[i]))
        print(goods_entities_list)

#########################################################################################################################################