#!/usr/bin/env python3
"""
Test script to verify snap functionality
"""
import sys
import os
import pygame

# Add the parent directory to the path so we can import from shared
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from game_gui import GameGUI

def test_snap_functionality():
    """Test the snap functionality without running the full GUI"""
    print("Testing snap functionality...")
    
    # Initialize pygame (required for image handling)
    pygame.init()
    
    # Create a game instance
    game = GameGUI()
    
    # Test correct position calculation
    for i in range(len(game.pieces)):
        piece_id = game.pieces[i]['id']
        correct_pos = game.get_correct_position(piece_id)
        print(f"Piece {piece_id}: correct position = {correct_pos}")
    
    # Test snap detection
    piece_rect = pygame.Rect(50, 50, 166, 166)  # Simulate a piece position
    correct_pos = (100, 100)
    
    is_near = game.is_near_correct_position(piece_rect, correct_pos)
    print(f"Piece at (50,50) near correct position (100,100): {is_near}")
    
    piece_rect = pygame.Rect(90, 90, 166, 166)  # Closer position
    is_near = game.is_near_correct_position(piece_rect, correct_pos)
    print(f"Piece at (90,90) near correct position (100,100): {is_near}")
    
    print("Snap functionality test completed!")
    pygame.quit()

if __name__ == "__main__":
    test_snap_functionality()
