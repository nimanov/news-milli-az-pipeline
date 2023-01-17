# Pipline for scraping "https://news.milli.az/" website
First all news that belongs to today and yesterday are scraped and written to the database, then only the new news are
added. The uniqueness of urls is ensured by adding CONSTRAINT to the "url" column of the table while creating table. 
The error that will be raised due to the uniqueness CONSTRAINT of the "url" column is handled and by this way it is guaranteed
that only new news urls will be added to the database.

## Docker
#### Creating network for containers to communicate.
```docker
docker network create myNetwork
```
#### PostgreSQL database (This part can be skipped if the database container is already created in apa.az project)

Downloading PostgreSQL image
```docker
docker pull postgres 
```
Running PostgreSQL container from the postgres image in "myNetwork" network with below credentials.
```docker
docker run --name postgres-cnt-0 -e POSTGRES_USER=nurlan -e POSTGRES_PASSWORD=1234  --network="myNetwork" -d postgres
```
Creating "neurotime" database inside the "postgres-cnt-0" container.
```docker
docker exec -it postgres-cnt-0 bash
# psql -U nurlan
# create database neurotime;
```

#### Application dockerization
Building an image of the application
```docker
docker image build -t news_az:1.0 .
```
Running a container from the image in "myNetwork" network.
```docker
docker run  --name news_az_cnt --network="myNetwork" -d  news_az:1.0
```
