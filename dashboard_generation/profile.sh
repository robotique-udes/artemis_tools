#!/usr/bin/env bash

python -m cProfile -o profile.prof $1
snakeviz profile.prof
