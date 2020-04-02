#!/bin/bash
set -e

cd "$(dirname "$0")"
source ./bin/activate

exec "$@"
