#!/bin/bash
PRONAME=stupidmenu.py
if pgrep -x $PRONAME > /dev/null
then
   killall -s SIGUSR1 $PRONAME
else
    $HOME/.stupidmenu/$PRONAME
    killall -s SIGUSR1 $PRONAME
fi


