import psycopg2
import numpy
from InstructorEmbedding import INSTRUCTOR

model = INSTRUCTOR('hkunlp/instructor-base')

conn = psycopg2.connect(
    user="postgres",
    password="postgres",
    host="localhost",  # Change if your db server isn't local
    port="5432",  # Default port for PostgreSQL, change if your port is different
    database="rules_hound"
)

cur = conn.cursor()

cur.execute('CREATE EXTENSION IF NOT EXISTS vector')
cur.execute('CREATE TABLE IF NOT EXISTS rules (id SERIAL PRIMARY KEY, section_number VARCHAR(10), text TEXT, embedding vector(768))')

def embed(instruction, text):
    embedding = model.encode([[instruction,text]])
    return numpy.ravel(embedding).tolist()

with open('mtgutf8.txt', 'r') as f:
    for line in f:
        section_number, text = line.split(' ', 1)
        print(line)
        embedding = embed('Represent the Magic the Gathering Rule for retrieval', text)
        print(embedding)
        cur.execute('INSERT INTO rules (section_number, text, embedding) VALUES (%s, %s, %s)', (section_number, text, embedding))

conn.commit()
cur.close()
conn.close()
