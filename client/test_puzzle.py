#!/usr/bin/env python3
"""
Simple test script to run the puzzle loading functionality
"""
import sys
import os

# Add the parent directory to the path so we can import from shared
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from puzzle import Puzzle

def test_puzzle():
    print("Testing puzzle loading and splitting...")
    
    # Test image URL (same as used in game_gui.py)
    image_url = "https://i.pinimg.com/1200x/97/c3/e0/97c3e03d8bc65b3f277908c07289141f.jpg"
    
    # Create a puzzle with 3x3 grid
    puzzle = Puzzle(image_url, grid_size=3)
    
    # Get the pieces
    pieces = puzzle.get_pieces()
    
    print(f"Successfully created puzzle with {len(pieces)} pieces")
    print(f"Piece size: {puzzle.piece_size}")
    
    # Print information about each piece
    for i, piece in enumerate(pieces):
        print(f"Piece {i}: ID = {piece['id']}, Image size = {piece['image'].get_size()}")

if __name__ == "__main__":
    test_puzzle()
