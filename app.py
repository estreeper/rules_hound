import psycopg2
import numpy
from InstructorEmbedding import INSTRUCTOR
import openai
import requests
import re
import os

COSINE_THRESHOLD = 0.12

# ANSI escape sequences for different text colors
color_red = "\033[91m"
color_green = "\033[92m"
color_yellow = "\033[93m"
color_blue = "\033[94m"
color_reset = "\033[0m"

openai.api_key = os.environ['openai_api_key']
model = INSTRUCTOR('hkunlp/instructor-base')
def get_conn():
    return psycopg2.connect(
        user="postgres",
        password="postgres",
        host="localhost",  # Change if your db server isn't local
        port="5432",  # Default port for PostgreSQL, change if your port is different
        database="rules_hound"
    )

def search(text):
    pattern = r'\[\[(.*?)\]\]'  # Regular expression pattern to match double square brackets and extract the content inside
    matches = re.findall(pattern, text)  # Find all matches of the pattern in the text

    original_text = text

    text_for_rich_vectorization = original_text
    text_for_empty_vectorization = original_text
    text_for_answering = original_text
    card_citations = []
    for name in matches:
        response = requests.get(f'https://api.scryfall.com/cards/named?fuzzy={name}')
        # Example: Replace the pattern in the original text with the response text
        if response.status_code == 200:

            #TODO - HANDLE FACES
            response_card = response.json()
            card_name = response_card['name']
            mana_cost = response_card['mana_cost']
            type_line = response_card['type_line']
            oracle_text = response_card['oracle_text']

            has_pt = False
            if 'power' in response_card:
                power = response_card['power']
                toughness = response_card['toughness']
                has_pt = True

            text_for_rich_vectorization = text_for_rich_vectorization.replace(f'[[{name}]]', f'[[{oracle_text}]]')
            text_for_empty_vectorization = text_for_empty_vectorization.replace(f'[[{name}]]', '')

            text_for_answering_replacement = f'[[{card_name}:{mana_cost}:{type_line}:{oracle_text}]]'
            if has_pt:
                text_for_answering_replacement = text_for_answering_replacement[:-2] + f':{power}/{toughness}'
            text_for_answering = text_for_answering.replace(f'[[{name}]]', text_for_answering_replacement)

            card_citation = f'{card_name} - {mana_cost}\n{type_line}\n{oracle_text}'
            if has_pt:
                card_citation = card_citation[:-2] + f'\n{power}/{toughness}'
            card_citations.append(card_citation)


    conn = get_conn()
    cur = conn.cursor()

    instruction = 'Represent the Magic the Gathering rules question for retrieval'

    rich_embedding = model.encode([[instruction,text_for_rich_vectorization]])
    rich_vector = "{0}".format(numpy.ravel(rich_embedding).tolist())

    empty_embedding = model.encode([[instruction,text_for_empty_vectorization]])
    empty_vector = "{0}".format(numpy.ravel(empty_embedding).tolist())

    query = 'SELECT section_number, text, %s <=> embedding AS cosine_similarity from rules ORDER BY cosine_similarity LIMIT 10'
    cur.execute(query, (rich_vector, ))
    rich_results = cur.fetchall()

    cur.execute(query, (empty_vector, ))
    empty_results = cur.fetchall()

    cur.close()
    conn.close()
    results = rich_results + empty_results
    filtered_results = []
    for result in results:
        cosine_distance = result[2]
        if cosine_distance < COSINE_THRESHOLD:
            filtered_results.append(result)
    results = filtered_results
    print('\n\n')

    



    
    # response = openai.Completion.create(
    #     model="text-davinci-003",
    #     prompt=f"You are a Magic the Gathering rules expert. Answer the following question using the provided relevant comprehensive rules. Do not tell the user to read the rules, that is your job. Keep your answer as relevant as possible\n \
    #     Question: {text} \n \
    #     Context: {str(results)}",
    #     max_tokens=2000
    #     )


    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": 'You are a Magic the Gathering rules expert. Answer the following question using the provided relevant comprehensive rules. Do not tell the user to read the rules, that is your job. Keep your answer as relevant as possible.'},
                {"role": "user", "content": f'Question: {text_for_answering} \n Context: {str(results)}'}
        ])
    response_content = response['choices'][0]['message']['content']

    print(color_blue)
    print(text)
    print(color_green)
    print(response_content)
    print(color_reset)

    print(color_yellow)
    print("-- CITED CARDS --")
    for card in card_citations:
        print(card)
        print('\n')
    print(color_reset)

    print(color_yellow)
    print("-- CITED RULES --")
    for result in results:
        rule_num = result[0]
        if rule_num in response_content or (rule_num[-1] == '.' and f' {rule_num[:-1]} ' in response_content):
            rule_text = result[1]
            print(f'[{rule_num}]: {rule_text}')
    print(color_reset)
    
while True:
    question = input("Please enter your question:\n")
    search(question)