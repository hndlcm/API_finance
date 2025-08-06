#!/bin/bash
tail -F app_data/logs/scan.txt | grep --line-buffered -v '(DEBUG)'