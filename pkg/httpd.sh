#!/usr/bin/env bash

set -o errexit
set -o nounset

# function start() {
#   SOCAT_PORT=8069
#   echo "Listening at http://localhost:$SOCAT_PORT..."
#   socat TCP-LISTEN:$SOCAT_PORT,pktinfo,reuseaddr,fork SYSTEM:"'${SHELL}' '${BASH_SOURCE[0]}' request" 2>&1 &
#   SOCAT_PID=$!
#   echo $SOCAT_PID >/tmp/socat.pid
#   echo "Listening on port $SOCAT_PORT (PID $SOCAT_PID)..."
#   wait "$SOCAT_PID"
# }

function start() {
  SOCAT_PORT=8069
  echo "Starting TCP server at http://localhost:$SOCAT_PORT..."
  /usr/bin/socat TCP-LISTEN:$SOCAT_PORT,pktinfo,reuseaddr,fork SYSTEM:"'${SHELL}' '${BASH_SOURCE[0]}' request"
}

function stop() {
  if [[ -f /tmp/socat.pid ]]; then
    echo "Stopping server..."
    SOCAT_PID=$(cat /tmp/socat.pid)
    kill $SOCAT_PID
    rm -f /tmp/socat.pid
  else
    echo 'Socat is not running'
  fi
}

function request() {
  echo "Received a request"

  read -r first_line

  HTTP_METHOD="$(echo "${first_line}" | cut -d' ' -f 1)"
  HTTP_PATH="$(echo "${first_line}" | cut -d' ' -f 2)"

  log "Received HTTP request: $HTTP_METHOD $HTTP_PATH"
  write_http "HTTP/1.1 200 OK"
  write_http "Content-Type: text/plain"
  write_http "Server: Shell Script"
  write_http
  write_http 'Hello, World!'
  write_http
  log "Sent HTTP response"
}

function send_response() {
  write_http "$1"
  write_http "$2"
  write_http "Connection: close"
  write_http "Server: Shell Script"
  write_http
  write_http "$3"
  write_http
  log "Sent HTTP response"
}

function log() {
  {
    echo -en "\e[1;32m[$(date) ${HTTP_METHOD} ${SOCAT_PEERADDR}:${SOCAT_PEERPORT}${HTTP_PATH}] "
    echo -en "\e[0m"
    echo "${@}"
  } >&2
}

function write_http() {
  printf $"%s\r\n" "${1:-}"
}

operation="${1:-help}"
shift 1
case "${operation}" in
start) start "${@}" ;;
request) request "${@}" ;;
stop) stop "${@}" ;;
help | -h | --help)
  echo "USAGE: ${BASH_SOURCE[0]} <operation> [flags...]"
  echo "Operations:"
  echo "  - help    - Show this message."
  echo "  - start   - run the webserver."
  echo "  - stop    - stop the webserver."
  echo "  - request - handle a request on stdin, dump the response to stdout."
  exit 0
  ;;
*)
  echo "ERROR: Invalid operation ${operation@Q}."
  echo "Run '${BASH_SOURCE[0]} --help' for script usage."
  exit 1
  ;;
esac
