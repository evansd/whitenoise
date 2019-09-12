#!/bin/bash

# We want to exit with an error if any check fails, but we want all checks to
# run each time so we get all the error messages, so we track the error status
# manually.
status=0

echo 'Running Black ...'
black --check --diff .
status=$(( $status + $? ))

echo
echo

echo 'Running flake8 ...'
flake8 --show-source
status=$(( $status + $? ))

# We add up all the exit statuses of the lint commands. If the total is
# greater than zero then at least one command failed so we exit with an error
# status.
if [[ "$status" > 0 ]]; then
  status=1
fi

exit "$status"
