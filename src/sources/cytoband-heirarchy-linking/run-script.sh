# Band-level cross-linking
python copilot-generated-create-ucsc-codesystem.py \
  --input ../../../data/cytoband/ucsc_source_data.txt \
  --output ../../../data/cytoband/copilot-generated-human-cytoband-with-links.codesystem.json \
  --link-across-centromere \
  --centromere-levels band
