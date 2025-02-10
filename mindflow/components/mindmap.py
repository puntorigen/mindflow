from typing import Dict, Optional
import customtkinter as ctk

from .node import Node

class MindMap(ctk.CTk):
    """Main mind map application window."""
    
    def __init__(self):
        """Initialize the mind map window."""
        super().__init__()
        
        self.title("MindMap")
        self.geometry("800x600")
        
        # Configure grid
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Create canvas
        self.canvas = ctk.CTkCanvas(
            self,
            bg="#1E1E1E",
            highlightthickness=0
        )
        self.canvas.grid(row=0, column=0, sticky="nsew")
        
        # Initialize state
        self.nodes: Dict[str, Node] = {}
        self.active_node: Optional[Node] = None
        self.dragged_node: Optional[Node] = None
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.dragging = False
        self.last_side = "right"  # Track which side to add nodes to
        
        # Panning state
        self.panning = False
        self.pan_start_x = 0
        self.pan_start_y = 0
        
        # Create central node
        self.create_central_node("Central Topic")
        
        # Bind canvas events for panning
        self.canvas.bind("<Button-1>", self._start_pan)
        self.canvas.bind("<B1-Motion>", self._pan)
        self.canvas.bind("<ButtonRelease-1>", self._end_pan)
        
        # Bind keyboard events
        self.bind("<Tab>", self.add_child_node)
        self.bind("<Return>", self.add_sibling_node)
        self.bind("<Left>", self.navigate_left)
        self.bind("<Right>", self.navigate_right)
        self.bind("<Up>", self.navigate_up)
        self.bind("<Down>", self.navigate_down)
        self.bind("<Control-Up>", self.move_node_up)
        self.bind("<Control-Down>", self.move_node_down)
    
    def create_central_node(self, text: str):
        """Create the central node of the mind map."""
        canvas_center_x = self.canvas.winfo_reqwidth() // 2
        canvas_center_y = self.canvas.winfo_reqheight() // 2
        
        node = Node(self.canvas, canvas_center_x, canvas_center_y, text)
        self.nodes[node.id] = node
        self.set_active_node(node)
    
    def set_active_node(self, node: Node):
        """Set the active node and update visual feedback."""
        if self.active_node:
            self.active_node.set_active(False)
        self.active_node = node
        node.set_active(True)
    
    def _calculate_node_position(self, parent_node: Node) -> tuple[int, int]:
        """Calculate the position for a new child node.
        
        Args:
            parent_node: The parent node to calculate position relative to
            
        Returns:
            Tuple of (x, y) coordinates for the new node
        """
        base_offset_x = 150  # Horizontal distance from parent
        sibling_spacing = 50  # Vertical space between siblings
        
        # If this is the root node's child, alternate sides
        if parent_node.parent is None:
            if self.last_side == "right":
                self.last_side = "left"
                base_offset_x = -base_offset_x
            else:
                self.last_side = "right"
        else:
            # For other nodes, maintain the same side as the parent
            if parent_node.x < parent_node.parent.x:
                base_offset_x = -abs(base_offset_x)
            else:
                base_offset_x = abs(base_offset_x)
        
        # Calculate x position
        new_x = parent_node.x + base_offset_x
        
        # Calculate y position
        if not parent_node.children:
            new_y = parent_node.y
        else:
            # Position below the last child
            last_child = parent_node.children[-1]
            new_y = last_child.y + sibling_spacing
        
        return new_x, new_y
    
    def _reposition_node_and_subtree(self, node: Node, dx: int, dy: int):
        """Recursively move a node and all its descendants.
        
        Args:
            node: The node to move
            dx: Change in x coordinate
            dy: Change in y coordinate
        """
        node.move(dx, dy)
        for child in node.children:
            self._reposition_node_and_subtree(child, dx, dy)
    
    def _reposition_siblings(self, parent: Node):
        """Reposition all children of a node to be evenly spaced.
        
        Args:
            parent: The parent node whose children need repositioning
        """
        if not parent.children:
            return
            
        # Sort children by vertical position
        children = sorted(parent.children, key=lambda n: n.y)
        
        # Calculate desired positions
        base_y = parent.y - ((len(children) - 1) * 50) / 2
        for i, child in enumerate(children):
            target_x = parent.x + 150
            target_y = base_y + (i * 50)
            
            # Move the child and its subtree
            dx = target_x - child.x
            dy = target_y - child.y
            self._reposition_node_and_subtree(child, dx, dy)

    def add_child_node(self, event=None):
        """Add a child node to the currently active node."""
        if not self.active_node:
            return
        
        # Calculate position for new node
        new_x, new_y = self._calculate_node_position(self.active_node)
        
        # Create new node
        new_node = Node(
            self.canvas,
            new_x,
            new_y,
            "New Node",
            self.active_node
        )
        
        self.nodes[new_node.id] = new_node
        self._reposition_siblings(self.active_node)
        self.set_active_node(new_node)
        
        # Update connection lines
        self._update_connector_lines()
        self._reset_z_order()
    
    def add_sibling_node(self, event=None):
        """Add a sibling node at the same level as the active node."""
        if not self.active_node or not self.active_node.parent:
            return
            
        parent = self.active_node.parent
        new_x, new_y = self._calculate_node_position(parent)
        
        # Create new node
        new_node = Node(
            self.canvas,
            new_x,
            new_y,
            "New Node",
            parent
        )
        
        self.nodes[new_node.id] = new_node
        self._reposition_siblings(parent)
        self.set_active_node(new_node)
        
        # Update connection lines
        self._update_connector_lines()
        self._reset_z_order()
    
    def navigate_left(self, event=None):
        """Move to the parent node of the active node."""
        if self.active_node and self.active_node.parent:
            self.set_active_node(self.active_node.parent)
    
    def navigate_right(self, event=None):
        """Move to the first child node of the active node."""
        if self.active_node and self.active_node.children:
            self.set_active_node(self.active_node.children[0])
    
    def navigate_up(self, event=None):
        """Move to the previous sibling of the active node."""
        if not self.active_node or not self.active_node.parent:
            return
            
        siblings = self.active_node.parent.children
        current_index = siblings.index(self.active_node)
        
        if current_index > 0:
            self.set_active_node(siblings[current_index - 1])
    
    def navigate_down(self, event=None):
        """Move to the next sibling of the active node."""
        if not self.active_node or not self.active_node.parent:
            return
            
        siblings = self.active_node.parent.children
        current_index = siblings.index(self.active_node)
        
        if current_index < len(siblings) - 1:
            self.set_active_node(siblings[current_index + 1])
    
    def move_node_up(self, event=None):
        """Move the active node up in its sibling order."""
        if not self.active_node or not self.active_node.parent:
            return
            
        siblings = self.active_node.parent.children
        current_index = siblings.index(self.active_node)
        
        if current_index > 0:
            # Swap positions in the parent's children list
            siblings[current_index], siblings[current_index - 1] = siblings[current_index - 1], siblings[current_index]
            self._reposition_siblings(self.active_node.parent)
    
    def move_node_down(self, event=None):
        """Move the active node down in its sibling order."""
        if not self.active_node or not self.active_node.parent:
            return
            
        siblings = self.active_node.parent.children
        current_index = siblings.index(self.active_node)
        
        if current_index < len(siblings) - 1:
            # Swap positions in the parent's children list
            siblings[current_index], siblings[current_index + 1] = siblings[current_index + 1], siblings[current_index]
            self._reposition_siblings(self.active_node.parent)
    
    def _start_drag(self, node: Node, event):
        """Start dragging a node."""
        if node.parent is None:  # Don't allow dragging the root node
            return
            
        self.dragged_node = node
        self.drag_start_x = event.x_root - self.winfo_rootx()  # Convert to canvas coordinates
        self.drag_start_y = event.y_root - self.winfo_rooty()
        self.dragging = True
        
        # Set as active node when clicked
        self.set_active_node(node)
        
        # Highlight potential parent nodes
        self._highlight_potential_parents()
        
        # Raise the dragged node above all other elements
        self.canvas.tag_raise(node.rect_id)
        self.canvas.tag_raise(node.text_id)
    
    def _drag(self, event):
        """Handle node dragging."""
        if not self.dragging or not self.dragged_node:
            return
            
        # Convert event coordinates to canvas coordinates
        canvas_x = event.x_root - self.winfo_rootx()
        canvas_y = event.y_root - self.winfo_rooty()
        
        # Calculate the movement delta
        dx = canvas_x - self.drag_start_x
        dy = canvas_y - self.drag_start_y
        
        # Move the node and its children
        self._move_node_and_children(self.dragged_node, dx, dy)
        
        # Update the start position for the next movement
        self.drag_start_x = canvas_x
        self.drag_start_y = canvas_y
        
        # Update connector lines
        self._update_connector_lines()
    
    def _end_drag(self, event):
        """End dragging a node."""
        if not self.dragging or not self.dragged_node:
            return
            
        # Convert event coordinates to canvas coordinates
        canvas_x = event.x_root - self.winfo_rootx()
        canvas_y = event.y_root - self.winfo_rooty()
        
        # Find the closest potential parent
        new_parent = self._find_closest_potential_parent(canvas_x, canvas_y)
        
        if new_parent and new_parent != self.dragged_node.parent:
            old_parent = self.dragged_node.parent
            self.dragged_node.parent = new_parent  # This will handle children list updates
            
            # Reposition nodes
            self._reposition_siblings(old_parent)
            self._reposition_siblings(new_parent)
        else:
            # If no new parent, return to original position
            self._reposition_siblings(self.dragged_node.parent)
        
        # Reset highlighting
        for node in self.nodes.values():
            self.canvas.itemconfig(node.rect_id, outline="#CCCCCC", width=1)
            if node == self.active_node:
                self.canvas.itemconfig(node.rect_id, outline="#0078D4", width=2)
        
        # Update all connector lines
        self._update_connector_lines()
        
        # Reset drag state
        self.dragging = False
        self.dragged_node = None
        
        # Reset z-order
        self._reset_z_order()
    
    def _update_connector_lines(self):
        """Update connector lines."""
        # Remove all connector lines
        for item in self.canvas.find_withtag("line"):
            self.canvas.delete(item)
        
        # Draw new connector lines
        for node in self.nodes.values():
            if node.parent:
                self.canvas.create_line(
                    node.x, node.y,
                    node.parent.x, node.parent.y,
                    fill="#CCCCCC",
                    width=2,
                    tags="line"
                )
        
        # Make sure lines are below nodes
        self._reset_z_order()
    
    def _find_closest_potential_parent(self, x: int, y: int) -> Optional[Node]:
        """Find the closest potential parent node to the given coordinates."""
        closest_node = None
        min_distance = float('inf')
        
        for node in self.nodes.values():
            if not self._can_be_parent(node, self.dragged_node):
                continue
            
            # Get node bounds
            bbox = self.canvas.bbox(node.rect_id)
            if not bbox:
                continue
                
            # Check if cursor is inside or very close to the node
            if (bbox[0] - 10 <= x <= bbox[2] + 10 and
                bbox[1] - 10 <= y <= bbox[3] + 10):
                # Calculate distance to node center
                center_x = (bbox[0] + bbox[2]) / 2
                center_y = (bbox[1] + bbox[3]) / 2
                distance = ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5
                
                if distance < min_distance:
                    min_distance = distance
                    closest_node = node
        
        return closest_node
    
    def _reset_z_order(self):
        """Reset the z-order of all elements."""
        # Put lines at the bottom
        for item in self.canvas.find_withtag("line"):
            self.canvas.tag_lower(item)
        
        # Put rectangles above lines
        for node in self.nodes.values():
            self.canvas.tag_raise(node.rect_id)
            # Put text above rectangles
            self.canvas.tag_raise(node.text_id)
        
        # Put dragged node on top if exists
        if self.dragged_node:
            self.canvas.tag_raise(self.dragged_node.rect_id)
            self.canvas.tag_raise(self.dragged_node.text_id)
    
    def _highlight_potential_parents(self):
        """Highlight nodes that can be potential parents."""
        if not self.dragged_node:
            return
            
        # Reset all nodes to normal state
        for node in self.nodes.values():
            self.canvas.itemconfig(node.rect_id, outline="#CCCCCC", width=1)
        
        # Highlight potential parents
        for node in self.nodes.values():
            if self._can_be_parent(node, self.dragged_node):
                self.canvas.itemconfig(node.rect_id, outline="#00FF00", width=2)
    
    def _can_be_parent(self, potential_parent: Node, dragged_node: Node) -> bool:
        """Check if a node can be a parent of the dragged node."""
        if potential_parent == dragged_node:
            return False
        if potential_parent == dragged_node.parent:
            return False
        if potential_parent.parent is None and dragged_node.parent.parent is None:
            return True  # Allow moving between root's children
        
        # Check if potential_parent is not a descendant of dragged_node
        current = potential_parent
        while current:
            if current == dragged_node:
                return False
            current = current.parent
        return True
    
    def _move_node_and_children(self, node: Node, dx: int, dy: int):
        """Move a node and all its descendants by a delta."""
        # Move the node's visual elements
        self.canvas.move(node.rect_id, dx, dy)
        self.canvas.move(node.text_id, dx, dy)
        
        # Update node's position
        node.x += dx
        node.y += dy
        
        # Move all children recursively
        for child in node.children:
            self._move_node_and_children(child, dx, dy)
    
    def _start_pan(self, event):
        """Start panning the canvas."""
        # Only start panning if we clicked on the canvas background
        if not self.canvas.find_withtag("current"):
            self.panning = True
            self.pan_start_x = event.x
            self.pan_start_y = event.y
            self.canvas.configure(cursor="fleur")  # Change cursor to indicate panning
    
    def _pan(self, event):
        """Pan the canvas."""
        if not self.panning:
            return
            
        # Calculate movement
        dx = event.x - self.pan_start_x
        dy = event.y - self.pan_start_y
        
        # Move all canvas objects
        for item in self.canvas.find_all():
            self.canvas.move(item, dx, dy)
        
        # Update node positions
        for node in self.nodes.values():
            node.x += dx
            node.y += dy
        
        # Update start position for next movement
        self.pan_start_x = event.x
        self.pan_start_y = event.y
    
    def _end_pan(self, event):
        """End panning the canvas."""
        self.panning = False
        self.canvas.configure(cursor="")  # Reset cursor
