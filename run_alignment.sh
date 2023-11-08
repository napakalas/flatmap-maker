#!/bin/sh

pwdCommand=$(pwd)

# clean file logs
find "${pwdCommand}/alignment/logs" ! -name '.gitkeep' -maxdepth 1 -type f -delete

# create maps and generate logs
poetry run mapmaker --source "${pwdCommand}/alignment/flatmaps/rat-flatmap/manifest.json" \
                    --output "${pwdCommand}/alignment/output" \
                    --ignore-git \
                    --debug \
                    --log "${pwdCommand}/alignment/logs/rat-npo.log"

poetry run mapmaker --source "${pwdCommand}/alignment/flatmaps/human-flatmap/male.manifest.json" \
                    --output "${pwdCommand}/alignment/output" \
                    --ignore-git \
                    --debug \
                    --log "${pwdCommand}/alignment/logs/male-npo.log"

poetry run mapmaker --source "${pwdCommand}/alignment/flatmaps/human-flatmap/female.manifest.json" \
                    --output "${pwdCommand}/alignment/output" \
                    --ignore-git \
                    --debug \
                    --log "${pwdCommand}/alignment/logs/female-npo.log"

# generate missing nodes and edges
poetry run python "${pwdCommand}/alignment/align.py" \
                    --log_file "${pwdCommand}/alignment/logs/rat-npo.log" \
                    --missing_file "${pwdCommand}/alignment/csv/npo_rat_missing_nodes.csv" \
                    --rendered_file "${pwdCommand}/alignment/csv/npo_rat_rendered.csv"

poetry run python "${pwdCommand}/alignment/align.py" \
                    --log_file "${pwdCommand}/alignment/logs/male-npo.log" \
                    --missing_file "${pwdCommand}/alignment/csv/npo_male_missing_nodes.csv" \
                    --rendered_file "${pwdCommand}/alignment/csv/npo_male_rendered.csv"

poetry run python "${pwdCommand}/alignment/align.py" \
                    --log_file "${pwdCommand}/alignment/logs/female-npo.log" \
                    --missing_file "${pwdCommand}/alignment/csv/npo_female_missing_nodes.csv" \
                    --rendered_file "${pwdCommand}/alignment/csv/npo_female_rendered.csv"
