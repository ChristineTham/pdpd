#!/usr/bin/env bash

# build dpd.db from scratch using dps backup_tsv and making goldendict

git fetch

git checkout origin/main -- backup_tsv/dpd_headwords.tsv

git checkout origin/main -- backup_tsv/dpd_roots.tsv

set -e
test -e dpd.db || touch dpd.db

dps/scripts/backup_all_dps.py

# Define filenames
FILENAMES=("sbs.tsv" "russian.tsv" "dpd_roots.tsv" "dpd_headwords.tsv")

# Copy files from backup_tsv/ to temp/
for file in "${FILENAMES[@]}"; do
    cp -rf ./backup_tsv/$file ./temp/$file
done

# Copy files from dps/backup/ to backup_tsv/
for file in "${FILENAMES[@]}"; do
    cp -rf ./dps/backup/$file ./backup_tsv/$file
done

bash/build_db.sh

dps/scripts/add_combined_view.py

# Move files back from temp/ to backup_tsv/ after all other scripts have completed
for file in "${FILENAMES[@]}"; do
    mv -f ./temp/$file ./backup_tsv/$file
done

exporter/exporter.py

git checkout -- pyproject.toml



