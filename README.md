# rules_hound
Answers import MTG rules questions for you like where to find the Wizards Store Locator


Aaron's setup:

python3 -m venv venv
pip install aaron_requirements

sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
wget -qO- https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo tee /etc/apt/trusted.gpg.d/pgdg.asc &>/dev/null
sudo apt update
sudo apt install postgresql
sudo apt install postgresql-server-dev-15 # or so

sudo apt remove postgresql-14
sudo apt purge postgresql-14
sudo service postgresql start

get into postgres
CREATE DATABASE rules_hound;

sudo apt install gcc
cd /tmp
git clone --branch v0.4.4 https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install # may need sudo
