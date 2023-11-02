If you would like to add features to Nautical, it is important that all our tests pass.
Here is a brief overview of how to run our unit tests.

## Pre-requisites
```bash
apt install jq rsync curl tzdata
```
This was done on an Ubuntu machine.

## Installing Ruby

```bash
sudo apt-get install ruby-full
```
We need `Ruby 3` or greater

## Install requirements
```bash
gem install bashcov simplecov-cobertura simplecov-html
```
We use this instead of adding a `Gemfile` to the repo.

## Run the tests
```bash
bashcov ./tests/tests.sh
```
