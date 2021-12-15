#!/bin/sh

git pull
sudo docker-compose build lambo
sudo docker-compose up -d