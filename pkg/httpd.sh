#!/usr/bin/env bash

# Read the first line of the request
read request_line

# Extract the method and URI
method=$(echo "$request_line" | awk '{print $1}')
uri=$(echo "$request_line" | awk '{print $2}')

# Log the request to stderr
echo "$(date): $method $uri" >&2

# Prepare the response
http_response=""
content_type="Content-Type: text/plain\r\n"

case "$uri" in
"/")
    echo "got /"
    http_response="Welcome to the REST API server."
    ;;
"/date")
    echo "got date"
    http_response="$(date)"
    ;;
"/echo/"*)
    echo "got echo"
    # Remove '/echo/' from the URI to get the message
    http_response="${uri#/echo/}"
    ;;
*)
    http_response="Resource not found."
    ;;
esac

# Compute content length
content_length=$(echo -n "$http_response" | wc -c)

# Send HTTP headers
printf "HTTP/1.1 200 OK\r\n"
printf "%s" "$content_type"
printf "Content-Length: %d\r\n" "$content_length"
printf "\r\n"

# Send the response
printf "%s" "$http_response"
