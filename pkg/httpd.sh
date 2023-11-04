#!/usr/bin/env bash

# Create a temporary FIFO and store its name in a variable
HTTP_OUT_FILE=$(mktemp /tmp/http_out.XXXXXX)

# Ensure the FIFO is removed when the script exits
# The trap command will execute `rm -f "$HTTP_OUT_FILE"` upon receiving EXIT signal
trap 'rm -f "$HTTP_OUT_FILE"; exit' EXIT INT TERM

while true; do
    cat $HTTP_OUT_FILE | nc -l -p 1500 -q 1 > >(# parse the netcat output, to build the answer redirected to the pipe "out".
        export REQUEST=
        while read line; do
            line=$(echo "$line" | tr -d '[\r\n]')

            if echo "$line" | grep -qE '^GET /'; then    # if line starts with "GET /"
                REQUEST=$(echo "$line" | cut -d ' ' -f2) # extract the request
            elif [ "x$line" = x ]; then                  # empty line / end of request
                HTTP_200="HTTP/1.1 200 OK"
                HTTP_LOCATION="Location:"
                HTTP_404="HTTP/1.1 404 Not Found"
                # call a script here
                # Note: REQUEST is exported, so the script can parse it (to answer 200/403/404 status code + content)
                if echo $REQUEST | grep -qE '^/echo/'; then
                    printf "%s\n%s %s\n\n%s\n" "$HTTP_200" "$HTTP_LOCATION" $REQUEST ${REQUEST#"/echo/"} >$HTTP_OUT_FILE
                elif echo $REQUEST | grep -qE '^/date'; then
                    date >$HTTP_OUT_FILE
                elif echo $REQUEST | grep -qE '^/stats'; then
                    vmstat -S M >$HTTP_OUT_FILE
                elif echo $REQUEST | grep -qE '^/net'; then
                    CONTENT=$(ifconfig)
                    # Ensure to use printf "%b" to count all bytes correctly.
                    CONTENT_LENGTH=$(printf "%b" "$CONTENT" | wc -c)
                    # Use printf with "%s" to avoid any additional characters.
                    printf "%s\r\n%s\r\n%s\r\n\r\n%s" "HTTP/1.1 200 OK" "Content-Type: text/plain" "Content-Length: $CONTENT_LENGTH" "$CONTENT" >$HTTP_OUT_FILE
                else
                    printf "%s\n%s %s\n\n%s\n" "$HTTP_404" "$HTTP_LOCATION" $REQUEST "Resource $REQUEST NOT FOUND!" >$HTTP_OUT_FILE
                fi
            fi
        done
    )
done


