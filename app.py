import psycopg2
import numpy
from InstructorEmbedding import INSTRUCTOR

model = INSTRUCTOR('hkunlp/instructor-base')

def get_conn():
    return psycopg2.connect(
        user="postgres",
        password="postgres",
        host="localhost",  # Change if your db server isn't local
        port="5433",  # Default port for PostgreSQL, change if your port is different
        database="rules_hound"
    )

def search(text):
    conn = get_conn()
    cur = conn.cursor()

    instruction = 'Represent the Magic the Gathering rules question for retrieval'
    embedding = model.encode([[instruction,text]])
    vector = "{0}".format(numpy.ravel(embedding).tolist())
    query = 'SELECT section_number, text from rules ORDER BY %s <=> embedding LIMIT 5'
    cur.execute(query, (vector, ))
    results = cur.fetchall()
    print(results)

    cur.close()
    conn.close()
