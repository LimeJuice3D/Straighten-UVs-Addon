# Lime Juice's Blender Toolkit
A series of addons I made for my 3D workflow.

# Straight UVs Addon

UV editing tool for straightening outer UV edges.

## Features:
**Straighten UVs**
- Align outside edges of a UV to the X or Y axis.
- Inner verts can be smoothed using the Smooth Iterations property.

Smooth Inner Verts
- Smooths inside vertices in order to conform with newly straightened edges.

## Installation:
1. Download ZIP file
2. Extract straight_uvs.py
3. In blender > preferences > addons, select Install from Disk (top right dropdown) and select straight_uvs.py

This addon is currently untested and in-development, and as such the addon is feature-limited and prone to bugs.
As of currently, the addon is ineffective on 1-face width UVs or UV sections, and if any UVs were ripped 
instead of unwrapped using seams the addon will not recognise these rips as valid disconnected edges.
