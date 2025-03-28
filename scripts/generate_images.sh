#!/bin/bash

# Make sure the scripts directory exists
mkdir -p scripts

# Make sure the images directory exists
mkdir -p docs/images

# Install mmdc (Mermaid CLI) if not already installed
if ! command -v mmdc &> /dev/null; then
    echo "Installing Mermaid CLI..."
    npm install -g @mermaid-js/mermaid-cli
fi

# Generate PNGs from Mermaid files
echo "Generating PNG images from Mermaid files..."

for mmd_file in docs/images/*.mmd; do
    base_name=$(basename "$mmd_file" .mmd)
    png_file="docs/images/$base_name.png"
    
    echo "Processing $mmd_file -> $png_file"
    mmdc -i "$mmd_file" -o "$png_file" -t neutral
done

echo "Image generation complete!" 