Description of the logic for building the systems
=================================================

PART1 
=======

1. COMPANY NAMES: 
==================
a.        Used Spacy's Named Entity Recognition(NER)+ NEL (Named Entity Linking)model: Opentapioca to retrive if the entity is an organisation name in its Knowledge base
"ORG" label is returned in NER and in linking it retrieves a Knowledge base key.
	So what I have doen is , I used the key to determine the uniqueness of the entity: For eg: M&S and Marks and Spensers refer to same organisation and hence has same KEY in KB and  I used that to eliminate duplicates

b.      If its not recognised by Spacy's Model but has general organisation suffixes like Ltd, Inc etc(collected a few common ones in suffixes list.txt), then I strip down teh suffixes nd I normalise the entity , removing spaces, punctuation, making them lower case and then use difflib's sequence matcher to compare the strings, If new, add to list

c.      Even if it doesnt contain suffixes, as its given its an organisation name, I do a sequence match to determine if its a duplicate or not


2. LOCATION
============

a.  Used Spacy's Named Entity Recognition(NER)+ NEL (Named Entity Linking)model: Opentapioca to retrive if the entity is an organisation name in its Knowledge base
"LOC" label is returned in NER and in linking it retrieves a Knowledge base key.
	So what I have doen is , I used the key to determine the uniqueness of the entity: For eg: LONDON,ENG AND LONDON,UK refer to same LOCATION and hence has same KEY in KB and  I used that to eliminate duplicates

b. Else I normalise the entity , removing spaces, punctuation, making them lower case and then use difflib's sequence matcher to compare the strings  If new, add to list

3.SERIAL NUMBER
================

I  normalise the entity , removing spaces, punctuation, making them lower case and then use difflib's sequence matcher to compare the strings at THRESHOLD 1.0 i.e. they should match exactly as even a single digit change WOU:D MEAN THEY ARE DIFFEREN ENTITIES


4. ADDRESS
================

I  normalise the entity , removing spaces, punctuation, making them lower case and then use difflib's sequence matcher to compare the strings at THRESHOLD 1.0 i.e. they should match exactly as even a single digit change (door number )WOU:D MEAN THEY ARE DIFFEREN ENTITIES

5. GOODS
=========

I  normalise the entity , removing spaces, punctuation, making them lower case and then use difflib's sequence matcher to compare the strings at THRESHOLD 0.9 i.e. they should match close enough considering spelling errors




==========================================================================================================================================================================

PART2 
========

Here, entity normalisation ais simiar to above logic.


1.In order to simulate Live stream parsing , I took an predefined stream in (input_stream.txt) and I use a loop such that at instanat I have only the current and past values and not the next values

2. I have included a hierarchy where I use Spacy's KB first , then custom company suffix detection logic and at last general normalisation and matching 

What I did was as I get a new value I check if its and ORG , then add it there and keep track of the output list s index and key in KB to create cluster in future with the output index lis t


## OUTPUT LIST IS A LIST OF LISTS EACH ELEMENT IS A CLUSTER OF SIMILAR ENTITTIES
output_list = []
## THIS CONNECTS THE INDEX OF AN ENTITY IN output_list TO KEYS OF PREVIOUSLY SEGREGATED ENTITITES , INORDER TO PROPERLY CLUSTERISE THEM
## fOR EG. IF ORG "ABC" IS AT INDEX 1 OF output_list and ITS SPACY KEY IS Q123 , THEN output_list_indices_dict[1] = Q123
output_list_indices_dict = {}







===================================================================================================================================================================================


This obviously doesnt work for all cases , especially if the entity (organisation name or location) is not there in Spacy's KB . 



















