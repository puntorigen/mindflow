from typing import TYPE_CHECKING
import customtkinter as ctk

if TYPE_CHECKING:
    from .node import Node

class Connector:
    """Represents a connection line between two nodes in the mind map."""
    
    def __init__(self, canvas: ctk.CTkCanvas, source: 'Node', target: 'Node'):
        """Initialize a connector between two nodes.
        
        Args:
            canvas: The canvas to draw on
            source: The parent node
            target: The child node
        """
        self.canvas = canvas
        self.source = source
        self.target = target
        
        self.line_id = self.canvas.create_line(
            source.x, source.y,
            target.x, target.y,
            fill="#4A4A4A",
            tags=("line", target.id)
        )
        self.canvas.tag_lower(self.line_id)
    
    def update(self):
        """Update the connector's position based on its nodes."""
        self.canvas.coords(
            self.line_id,
            self.source.x, self.source.y,
            self.target.x, self.target.y
        )
    
    def delete(self):
        """Remove the connector from the canvas."""
        self.canvas.delete(self.line_id)
