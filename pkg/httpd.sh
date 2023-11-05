#!/usr/bin/env bash

# Function to handle incoming requests
handle_request() {
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
      http_response="Welcome to the REST API server."
      ;;
    "/date")
      http_response="$(date)"
      ;;
    "/echo/"*)
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
}

SOCAT_PORT=8069
SOCAT_SOCAT_PIDFILE="/tmp/socat-${SOCAT_PIDFILE}.pid"

start_socat_server() {
  if [ -e "$SOCAT_PIDFILE" ]; then
    echo "Server already running."
    exit 1
  fi

  echo "Listening on port $SOCAT_PIDFILE..."
  trap 'stop_socat_server' TERM
  socat TCP-LISTEN:${SOCAT_PIDFILE},reuseaddr,fork EXEC:"$0 serve" &
  echo $! > "$SOCAT_PIDFILE"
}

stop_socat_server() {
  if [ ! -e "$SOCAT_PIDFILE" ]; then
    echo "Server not running."
    return
  fi

  PID=$(cat "$SOCAT_PIDFILE")
  echo "Stopping server..."
  kill $PID
  rm -f "$SOCAT_PIDFILE"
}

case "$1" in
  start)
    start_socat_server
    ;;
  stop)
    stop_socat_server
    ;;
  serve)
    handle_request
    ;;
  *)
    echo "Usage: $0 {start|stop|serve}"
    exit 1
    ;;
esac