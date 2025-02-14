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
        self.children: List['Node'] = []
        self.is_collapsed = False
        
        # Create unique id for this node
        self.id = str(uuid.uuid4())
        
        # Create visual elements
        self.rect_id = self.canvas.create_rectangle(
            x - 50, y - 15,
            x + 50, y + 15,
            fill="#2D2D2D",
            outline="#CCCCCC",
            width=1,
            tags=("node", self.id)
        )
        
        # Create text
        self.text_id = self.canvas.create_text(
            x, y,
            text=text,
            fill="#FFFFFF",
            font=("Arial", 12),
            tags=("text", self.id)
        )
        
        # Create collapse indicator (hidden by default)
        self.collapse_indicator = self.canvas.create_text(
            x + 55, y,  # Position it further to the right
            text="▶",
            fill="#CCCCCC",  # Lighter color to match lines
            font=("Arial", 12, "bold"),  # Larger and bolder
            state="hidden",
            tags=("collapse_indicator", self.id)
        )
        
        # Create invisible background for better click detection
        bbox = self.canvas.bbox(self.text_id)
        padding = 5
        self.bg_id = self.canvas.create_rectangle(
            bbox[0] - padding, bbox[1] - padding,
            bbox[2] + padding, bbox[3] + padding,
            fill="",
            outline="",
            width=0
        )
        
        # Ensure proper z-order
        self.canvas.tag_lower(self.bg_id, self.text_id)
        
        # Store reference to this node
        self.canvas.setvar(f"node_{self.id}", self)
        
        # Bind events
        for item_id in [self.rect_id, self.text_id, self.bg_id]:
            self.canvas.tag_bind(item_id, "<Button-1>", self._on_click)
            self.canvas.tag_bind(item_id, "<B1-Motion>", self._on_drag)
            self.canvas.tag_bind(item_id, "<ButtonRelease-1>", self._on_release)
            self.canvas.tag_bind(item_id, "<Double-Button-1>", self._on_double_click)
        
        # Set parent if provided
        if parent:
            self.parent = parent
            self._update_collapse_indicator()  # Initialize indicator state
    
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
    
    def _on_double_click(self, event):
        """Handle double click event."""
        # Get the mindmap instance
        mindmap = self.canvas.master
        # Call mindmap's edit method directly
        mindmap._start_editing(self)
        return "break"  # Prevent event from propagating
        
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
            self._parent._update_collapse_indicator()  # Update old parent's indicator
        
        self._parent = value
        
        # Add to new parent's children
        if value and self not in value.children:
            value.children.append(self)
            value._update_collapse_indicator()  # Update new parent's indicator
    
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
        self.canvas.move(self.bg_id, dx, dy)
        self.canvas.move(self.collapse_indicator, dx, dy)
        
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
    
    def update_text(self, new_text: str):
        """Update the node's text."""
        self.text = new_text
        self.canvas.itemconfig(self.text_id, text=new_text)
        
        # Update background rectangle size
        bbox = self.canvas.bbox(self.text_id)
        padding = 5
        self.canvas.coords(self.bg_id,
                         bbox[0] - padding, bbox[1] - padding,
                         bbox[2] + padding, bbox[3] + padding)
    
    def toggle_collapse(self) -> bool:
        """Toggle collapse state of the node.
        
        Returns:
            bool: True if state changed, False if node has no children
        """
        if not self.children:
            return False
            
        self.is_collapsed = not self.is_collapsed
        self._update_collapse_indicator()
        return True
    
    def _update_collapse_indicator(self):
        """Update the collapse indicator visibility and symbol."""
        # Only show indicator if node has children AND is collapsed
        if self.children and self.is_collapsed:
            self.canvas.itemconfig(self.collapse_indicator, state="normal")
            self.canvas.coords(self.collapse_indicator, self.x + 55, self.y)
            self.canvas.tag_raise(self.collapse_indicator)  # Always on top
        else:
            # Hide indicator in all other cases
            self.canvas.itemconfig(self.collapse_indicator, state="hidden")
    
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
        self.canvas.delete(self.bg_id)
        self.canvas.delete(self.collapse_indicator)
        
        # Remove from parent
        if self.parent:
            self.parent.children.remove(self)
