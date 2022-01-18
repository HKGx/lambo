#!/bin/sh

set -xe

git pull
docker-compose build lambo
docker-compose up -d