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

## OUTPUT LIST IS A LIST OF LISTS EACH ELEMENT IS A CLUSTER OF SIMILAR ENTITTIES
output_list = []
## THIS CONNECTS THE INDEX OF AN ENTITY IN output_list TO KEYS OF PREVIOUSLY SEGREGATED ENTITITES , INORDER TO PROPERLY CLUSTERISE THEM
## fOR EG. IF ORG "ABC" IS AT INDEX 1 OF output_list and ITS SPACY KEY IS Q123 , THEN output_list_indices_dict[1] = Q123
output_list_indices_dict = {}
#########################################################################################################################



##### en_core_web_lg is the NER model and opentapioca is the NEL model
nlp = spacy.load("en_core_web_lg") # Large model
nlp.add_pipe('opentapioca') # For Entity Linking


##### TXT DOCUMENT HAS LIST OF SUFFIXES OF ORGANISATIONS
with open("suffixes list.txt","r") as file:
    file_str = file.read()
    company_suffixes_list = file_str.lower().splitlines()

##### TXT DOCUMENT HAS INPUT STRING
with open("input_stream.txt","r") as file:
    file_str = file.read()
    input_str = file_str.splitlines()





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
            return True , entity_str2
    return False , ""


"""
check_if_exists_in_dict_ : INPUT : COMPANY NAMES/LOCATION DICTIONARY , INPUT SRING , MATCHING THRESHOLD
COMPARES INPUT TO EACH VALUE IN DICTIONARY, 
RETURNS TRUE IF MATCH FOUND

"""
def check_if_exists_in_dict_(dict_to_compare_in , entity_str1,compare_ratio):
    for entity_str2 in dict_to_compare_in.values():
        if(compare_strings_sequence_match(entity_str1, entity_str2,compare_ratio)):
            return True , entity_str2
    return False , ""

"""
check_if_exists_in_list_ : INPUT : SNO, GOODS, ADDRESS LISTS , INPUT SRING , MATCHING THRESHOLD
COMPARES INPUT TO EACH VALUE IN LIST, 
RETURNS TRUE IF MATCH FOUND

"""
def check_if_exists_in_list_(list_to_compare_in , entity_str1,compare_ratio):
    for entity_str2 in list_to_compare_in:
        if(compare_strings_sequence_match(entity_str1, entity_str2,compare_ratio)):
            return True , entity_str2
    return False , ""


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
    global company_entities_dict ,company_suffixes_list , output_list ,output_list_indices_dict
    flag = False

    ## Processing for NLP model
    entity_value_str = str(entity_value) + " is in US" ## Added the string as NER/NEL fails to recognise well for single words
    doc = nlp(entity_value_str)
    for span in doc.ents:
        if(span.label_ == "ORG"):
            flag = True
            if(span.kb_id_ not in company_entities_dict.keys()):
                company_entities_dict[span.kb_id_] = entity_value                
                output_list.append([entity_value])
                output_list_indices_dict[len(output_list)-1] = span.kb_id_
            else:
                output_list[[k for k, v in output_list_indices_dict.items() if v == span.kb_id_][0]].append(entity_value)
    
    ## If not detected by Spacy's model, custom process it
    if(flag == False):
        if(find_suffix_in_company_name(entity_value) != -1):
            flag = True
            ret , entity_str2 = check_if_name_exists(entity_value)
            if(ret == False):
                company_entities_dict[entity_value] = entity_value ## Add value if its not a duplicate
                output_list.append([entity_value])
                output_list_indices_dict[len(output_list)-1] = entity_value
            else:
                output_list[[k for k, v in output_list_indices_dict.items() if v == entity_str2][0]].append(entity_value)
    return flag


"""
entity_location   : INPUT : input entity as string
1. USING SPACY'S NER+NEL(NAMED ENTITY LINKING) PIPELINE TO TEST IF THIS LOCATION NAME HAS BEEN DEFINED IN SPACY'S KB(KNOWLEDGE BASE) 
        If Yes, and If its not it our list, we add it or if its a duplicate , ignore it
2. CUSTOM PROCESSING :
        1. NORMALISE IT: REMOVE SPACING , PUNCTUATION, 
        If its not it our list, we add it or if its a duplicate , ignore it

"""
def entity_location(entity_value):
    global location_entities_dict , output_list , output_list_indices_dict
    entity_value_str = str(entity_value).title() + " is in the US" ## Added the string as NER/NEL fails to recognise well for single words
    doc = nlp(entity_value_str)
    flag = False
    if(len(doc.ents) >= 2):
        for span_index in range(len(doc.ents) - 1):
            #print(doc.ents[span_index].kb_id_,doc.ents[span_index].text,entity_value)
            if(doc.ents[span_index].label_ == "LOC"):
                flag = True
                if((any(char.isdigit() for char in entity_value)) or ('road' in entity_value.lower()) or ('street' in entity_value.lower())):
                    entity_address(entity_value)
                    return True

                else:
                    if(doc.ents[span_index].kb_id_ not in location_entities_dict.keys()):
                        location_entities_dict[doc.ents[span_index].kb_id_] = entity_value
                        output_list.append([entity_value])
                        output_list_indices_dict[len(output_list)-1] = doc.ents[span_index].kb_id_
                        break
                    else:
                        output_list[[k for k, v in output_list_indices_dict.items() if v == doc.ents[span_index].kb_id_][0]].append(entity_value)
                        break
    return flag



"""
entity_serial_number   : INPUT : input entity as string
CUSTOM PROCESSING :
        1. NORMALISE IT: REMOVE SPACING , PUNCTUATION, CHECK WITH ABSOLUTE ACCURACY VALUE AS A SINGLE CHARACTER CHNAGE(DIGITS,ALPHABETS) COULD MEAN DIFFERENT ENTTTIES
        If its not it our list, we add it or if its a duplicate , ignore it
"""

def entity_serial_number(entity_value):
    global serial_number_entities_list , output_list , output_list_indices_dict
    ret = False
    if(len(serial_number_entities_list) >0):
        ret , entity_str2 = check_if_exists_in_list_(serial_number_entities_list,entity_value,1.0)
        if(ret == False):
            serial_number_entities_list.append(entity_value)
            output_list.append([entity_value])
            output_list_indices_dict[len(output_list)-1] = entity_value
        else:
            serial_number_entities_list.append(entity_value)
            output_list[[k for k, v in output_list_indices_dict.items() if v == entity_str2][0]].append(entity_value)
    else:
        serial_number_entities_list.append(entity_value)
        output_list.append([entity_value])
        output_list_indices_dict[len(output_list)-1] = entity_value
    return ret



"""
entity_address   : INPUT : input entity as string
CUSTOM PROCESSING :
        1. NORMALISE IT: REMOVE SPACING , PUNCTUATION, CHECK WITH ABSOLUTE ACCURACY VALUE AS A SINGLE CHARACTER CHNAGE(DIGITS,ALPHABETS) COULD MEAN DIFFERENT ENTTTIES
        If its not it our list, we add it or if its a duplicate , ignore it
"""

def entity_address(entity_value):
    global address_entities_list , output_list , output_list_indices_dict
    ret = False
    if(len(address_entities_list) >0):
        ret , entity_str2 = check_if_exists_in_list_(address_entities_list,entity_value,1.0)
        if(ret == False):
            address_entities_list.append(entity_value)
            output_list.append([entity_value])
            output_list_indices_dict[len(output_list)-1] = entity_value
        else:
            address_entities_list.append(entity_value)
            output_list[[k for k, v in output_list_indices_dict.items() if v == entity_str2][0]].append(entity_value)
    else:
        address_entities_list.append(entity_value)
        output_list.append([entity_value])
        output_list_indices_dict[len(output_list)-1] = entity_value
    return ret


"""
entity_goods   : INPUT : input entity as string
CUSTOM PROCESSING :
        1. NORMALISE IT: REMOVE SPACING , PUNCTUATION, CHECK WITH 90% ACCURACY VALUE AS A SLIGHT ERRORS IN  CHARACTERS  COULD STILL MEAN DIFFERENT ENTTTIES
        If its not it our list, we add it or if its a duplicate , ignore it
"""
def entity_goods(entity_value):
    global goods_entities_list , output_list , output_list_indices_dict
    ret = False
    if(len(goods_entities_list) >0):
        ret , entity_str2 = check_if_exists_in_list_(goods_entities_list,entity_value,0.9)
        if(ret == False):
            goods_entities_list.append(entity_value)
            output_list.append([entity_value])
            output_list_indices_dict[len(output_list)-1] = entity_value
        else:
            goods_entities_list.append(entity_value)
            output_list[[k for k, v in output_list_indices_dict.items() if v == entity_str2][0]].append(entity_value)
    else:
        goods_entities_list.append(entity_value)
        output_list.append([entity_value])
        output_list_indices_dict[len(output_list)-1] = entity_value

    return True


############################################### PARSER  #######################################################33333333


if __name__ == "__main__":
    for string_ in input_str:
        ## CHECK IF THE ENTITY IS AN ORGANISATION'S NAME, IF NOT, CHECK IF ITS A LOCATION(LOCTION AND ADDRESS ARE SEPERATED WITHIN)
        ## CHECK IF ITS A SERIAL NUMBER AS IT'LL BE A MIX OF DIGITS AND ALPHABETS, IF ITS A STRING OF ALPHABETS ONLY, ITS A GOODS STRING
        if( entity_company_name(string_) == False):
          if(entity_location(string_) == False):
            if((any(char.isdigit() for char in string_)) and (any(char.isalpha() for char in string_))):
                entity_serial_number(string_)
            else:
                entity_goods(string_)

    print(output_list)
#########################################################################################################################################