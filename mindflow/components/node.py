import uuid
from typing import Optional, List
import customtkinter as ctk
import tkinter.font as tkfont

from .connector import Connector

class Node:
    """Represents a node in the mind map."""
    
    def __init__(self, canvas: ctk.CTkCanvas, x: int, y: int, text: str = "New Node", parent: Optional['Node'] = None):
        """Initialize a node.
        
        Args:
            canvas: The canvas to draw on
            x: X coordinate
            y: Y coordinate
            text: Node text
            parent: Parent node, if any
        """
        self.canvas = canvas
        self.x = x
        self.y = y
        self.text = text
        self._parent = None  # Initialize _parent before setting it through property
        self.parent = parent  # Use property setter
        self.children: List['Node'] = []
        
        # Create unique id for this node
        self.id = str(uuid.uuid4())
        
        # Calculate size based on text
        font = tkfont.Font(family="Helvetica", size=12)
        text_width = font.measure(text)
        text_height = font.metrics("linespace")
        padding = 10
        
        # Create rectangle
        self.rect_id = canvas.create_rectangle(
            x - text_width/2 - padding,
            y - text_height/2 - padding,
            x + text_width/2 + padding,
            y + text_height/2 + padding,
            fill="#2D2D2D",
            outline="#CCCCCC",
            width=1,
            tags=("node", self.id)
        )
        
        # Create text
        self.text_id = canvas.create_text(
            x, y,
            text=text,
            fill="#FFFFFF",
            font=("Helvetica", 12),
            tags=("text", self.id)
        )
        
        # Bind events to both rectangle and text
        for item_id in [self.rect_id, self.text_id]:
            canvas.tag_bind(item_id, "<Button-1>", self._on_click)
            canvas.tag_bind(item_id, "<B1-Motion>", self._on_drag)
            canvas.tag_bind(item_id, "<ButtonRelease-1>", self._on_release)
    
    def _on_click(self, event):
        """Handle click event."""
        # Get the mindmap instance
        mindmap = self.canvas.master
        mindmap._start_drag(self, event)
        return "break"
    
    def _on_drag(self, event):
        """Handle drag event."""
        # Get the mindmap instance
        mindmap = self.canvas.master
        mindmap._drag(event)
        return "break"
    
    def _on_release(self, event):
        """Handle release event."""
        # Get the mindmap instance
        mindmap = self.canvas.master
        mindmap._end_drag(event)
        return "break"
    
    @property
    def parent(self) -> Optional['Node']:
        """Get the parent node."""
        return self._parent
    
    @parent.setter
    def parent(self, value: Optional['Node']):
        """Set the parent node and update children list."""
        # Remove from old parent's children
        if self._parent and self in self._parent.children:
            self._parent.children.remove(self)
        
        self._parent = value
        
        # Add to new parent's children
        if value and self not in value.children:
            value.children.append(self)
    
    def move(self, dx: int, dy: int):
        """Move the node and update connections.
        
        Args:
            dx: Change in x coordinate
            dy: Change in y coordinate
        """
        self.x += dx
        self.y += dy
        
        # Move visual elements
        self.canvas.move(self.rect_id, dx, dy)
        self.canvas.move(self.text_id, dx, dy)
        
        # Update connections
        if hasattr(self, 'connector'):
            self.connector.update()
        
        for child in self.children:
            if hasattr(child, 'connector'):
                child.connector.update()
    
    def set_active(self, active: bool = True):
        """Set the active state of the node.
        
        Args:
            active: Whether the node should be active
        """
        self.canvas.itemconfig(
            self.rect_id,
            outline="#007ACC" if active else "#4A4A4A"
        )
    
    def delete(self):
        """Remove the node and its visual elements."""
        # Delete children first
        for child in self.children[:]:  # Create a copy since list will be modified
            child.delete()
        
        # Delete connector
        if hasattr(self, 'connector'):
            self.connector.delete()
        
        # Delete visual elements
        self.canvas.delete(self.rect_id)
        self.canvas.delete(self.text_id)
        
        # Remove from parent
        if self.parent:
            self.parent.children.remove(self)
