---
name: searchattractions
description: Search Taipei Day Trip attractions by keyword or MRT area. Use when the user asks to find or search Taipei attractions.
---

# TDT Search

Use this skill when the user asks to search for Taipei attractions.

## Workflow

1. Identify the user's search keyword.
2. Call the TDT MCP `searchattractions` tool with the keyword.
3. Use the returned results as the source of truth.
4. Do not invent attractions that were not returned by the MCP.
5. Present the matching attractions clearly, and every attraction only present id, name,category,description,address
6. If the MCP returns no results, tell the user that no matching attractions were found.

## Example

User:
「幫我找士林的景點」

Action:
- Call `searchattractions` with the keyword `士林`.

Then present the returned attractions to the user.