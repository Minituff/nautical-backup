#!/usr/bin/env bash

# Credit to: https://github.com/reddec/bash-db

# Get value by key
get () {
   if [[ "$1" == "--help" ]];
   then
      echo "Usage: db get <database> <key>"
      exit 0
   elif [[ -z "$2" ]];
   then
      echo "No key provided"
      exit 3
   fi

   db=$1;
   key=$(echo -n "$2" | base64 -w 0);
   sed -nr "s/^$key\ (.*$)/\1/p" $db | base64 -d
}

# List all keys
list () {
   if [[ "$1" == "--help" ]];
   then
      echo "Usage: db list <database>"
      exit 0
   fi

   db=$1;
   sed -nr "s/(^[^\ ]+)\ (.*$)/\1/p" $db | xargs -n 1 sh -c 'echo `echo -n $0 | base64 -d`'
}

# Get last added value 
last () {
   if [[ "$1" == "--help" ]];
   then
      echo "Usage: db last <database>"
      exit 0
   fi

   db=$1;
   sed -nr "\$s/(.*)\ (.*$)/\2/p;d" $db | base64 -d
}

# Put or updated record
put () {
   if [[ "$1" == "--help" ]];
   then
      echo "Usage: db put <database> <key> ?<value>"
      exit 0
   elif [[ -z "$2" ]];
   then
      echo "No key provided"
      exit 3
   fi;

   db=$1;
   key=$(echo -n "$2" | base64 -w 0);
   value=$3;
   if [ -z "$3" ]
   then
      value=$(base64 -w 0 <&0);
   else
      value=$(echo -n "$value" | base64 -w 0);
   fi

   if [ ! -f "$1" ]; then touch "$db"; fi;
   if [[ $(grep "^"$key"\ " $db) == "" ]]; then
      #Insert
      echo "$key $value" >> $db
   else
      #Replace
      sed -ir "s/^$key\ .*/$key $value/g" $db
   fi;
}

# Remove record by key
delete () {
   if [[ "$1" == "--help" ]];
   then
      echo "Usage: db delete <database> <key>"
      exit 0
   elif [[ -z "$2" ]];
   then
      echo "No key provided"
      exit 3
   fi

   db=$1;
   key=$(echo -n "$2" | base64 -w 0);
   sed -ri "/^"$key"\ .*/d" "$db"
}

help () {
   echo '
      Usage: db <get|list|last|put|delete> <database> [arguments...]

      db --help                        - Show this help message
      db <method> --help               - Show help message for a method
      db get <database> [key]          - Get value of record by key
      db list <database>               - Get all keys in database
      db last <database>               - Get the value of the last added record
      db put <database> [key] [?value] - Insert or update record.
      db delete <database> <key>       - Delete record by key'
   exit 0
}

# Start

if [[ -z "$1" || "$1" == "--help" ]];
then
   help
   exit 0
fi

if [[ "$1" =~ (get|list|last|put|delete) ]];
then
   if [[ -z "$2" ]];
   then
      echo "No database provided"
      exit 2
   else
      "$@"
   fi
else
   echo method "'$1'" not found
   help
   exit 1
fi