#!/bin/bash

THRESHOLD=95
ILAB_QUOTA=`cat /explore/nobackup/projects/ilab/.quota`
ILAB_QUOTA=$(echo $ILAB_QUOTA|tr -d '\n')
recipient="jordan.a.caraballo-vega@nasa.gov,melanie.frost@nasa.gov,caleb.s.spradlin@nasa.gov"

round() {
    printf "%.${2}f" "${1}"
}

if (( $(echo "${ILAB_QUOTA##* } > $THRESHOLD" | bc -l) )); then
    # setup subject
    rounded_value=`round "${ILAB_QUOTA##* }" 2`
    subject="ILAB Quota Critical - ${rounded_value}%"
    body="${ILAB_QUOTA}"
    MIME="MIME-Version: 1.0\nContent-Type: text/html\n"
    echo -e "To: $recipient\nSubject: $subject\n$MIME\n\n$body" | sendmail -t
fi

