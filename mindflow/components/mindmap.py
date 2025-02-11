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
        
        # Text editing state
        self.editing_node: Optional[Node] = None
        self.text_editor: Optional[ctk.CTkEntry] = None
        
        # Panning state
        self.panning = False
        self.pan_start_x = 0
        self.pan_start_y = 0
        
        # Create central node
        self.create_central_node("Central Topic")
        
        # Bind events
        self.canvas.bind("<<NodeClicked>>", self._on_node_clicked)
        self.canvas.bind("<<NodeDragged>>", self._on_node_dragged)
        self.canvas.bind("<<NodeDropped>>", self._on_node_dropped)
        
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
    
    def set_active_node(self, node: Optional[Node]):
        """Set the active node and update visual feedback."""
        # Remove highlight from previous active node
        if self.active_node:
            self.canvas.itemconfig(self.active_node.rect_id, outline="#CCCCCC", width=1)
        
        # Update active node
        self.active_node = node
        
        # Highlight new active node
        if node:
            self.canvas.itemconfig(node.rect_id, outline="#0078D4", width=2)
            # Ensure the node and its text are above others
            self.canvas.tag_raise(node.rect_id)
            self.canvas.tag_raise(node.text_id)
    
    def _calculate_node_position(self, parent_node: Node) -> tuple[int, int]:
        """Calculate the position for a new child node."""
        base_offset_x = 150  # Horizontal distance from parent
        min_sibling_spacing = 60  # Minimum vertical space between siblings
        
        # If this is the root node's child, alternate sides
        if parent_node.parent is None:
            # First child always goes to the right
            if not parent_node.children:
                self.last_side = "right"
                base_offset_x = abs(base_offset_x)
            else:
                if self.last_side == "right":
                    self.last_side = "left"
                    base_offset_x = -abs(base_offset_x)
                else:
                    self.last_side = "right"
                    base_offset_x = abs(base_offset_x)
        else:
            # For other nodes, maintain the same side as the parent
            if parent_node.x < parent_node.parent.x:
                base_offset_x = -abs(base_offset_x)
            else:
                base_offset_x = abs(base_offset_x)
        
        # Calculate x position
        new_x = parent_node.x + base_offset_x
        
        # Calculate initial y position
        if not parent_node.children:
            new_y = parent_node.y
        else:
            # Calculate the total space needed for existing children
            total_space = self._calculate_subtree_space(parent_node)
            last_child = parent_node.children[-1]
            
            # Position below the last child with minimum spacing
            new_y = last_child.y + max(min_sibling_spacing, total_space / (len(parent_node.children) + 1))
        
        return new_x, new_y
    
    def _reposition_siblings(self, parent_node: Node):
        """Reposition all children of a node to maintain proper spacing."""
        if not parent_node or not parent_node.children:
            return
            
        # Sort children by vertical position
        children = sorted(parent_node.children, key=lambda n: n.y)
        
        # Calculate required vertical space for each node and its subtree
        node_spaces = []
        for child in children:
            space = self._calculate_subtree_space(child)
            node_spaces.append(space)
        
        # Start positioning from the parent's y position
        current_y = parent_node.y - sum(node_spaces) / 2
        
        # Position each child and its subtree
        for i, child in enumerate(children):
            # Calculate vertical offset needed for this subtree
            space_needed = node_spaces[i]
            
            # Position the child at the center of its allocated space
            target_y = current_y + space_needed / 2
            
            # Move the child and its entire subtree
            dy = target_y - child.y
            if abs(dy) > 1:  # Only move if the change is significant
                self._move_node_and_subtree(child, 0, dy)
            
            # Update current_y for next child
            current_y += space_needed
    
    def _calculate_subtree_space(self, node: Node) -> float:
        """Calculate the vertical space needed for a node and its subtree."""
        MIN_NODE_HEIGHT = 40  # Minimum vertical space per node
        SIBLING_PADDING = 20  # Minimum padding between sibling nodes
        
        if not node.children:
            return MIN_NODE_HEIGHT + SIBLING_PADDING
        
        # Calculate space needed for children
        child_space = sum(self._calculate_subtree_space(child) for child in node.children)
        
        # Return maximum of minimum node height or children's total space
        return max(MIN_NODE_HEIGHT + SIBLING_PADDING, child_space)
    
    def _move_node_and_subtree(self, node: Node, dx: int, dy: int):
        """Move a node and its entire subtree by the specified delta."""
        # Move the node
        node.x += dx
        node.y += dy
        self.canvas.move(node.rect_id, dx, dy)
        self.canvas.move(node.text_id, dx, dy)
        
        # Move all children recursively
        for child in node.children:
            self._move_node_and_subtree(child, dx, dy)
    
    def add_child_node(self, event=None):
        """Add a child node to the active node."""
        # Don't create node if we're editing
        if self.text_editor:
            return "break"
            
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
        # Don't create node if we're editing
        if self.text_editor:
            return "break"
            
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
        """Move to the parent node if on right side, or first child if on left side."""
        if not self.active_node:
            return
            
        # If node is on the right side of its parent (or is root's right child), go to parent
        if not self.active_node.parent or self.active_node.x > self.active_node.parent.x:
            if self.active_node.parent:
                self.set_active_node(self.active_node.parent)
        # If node is on the left side, try to go to first child
        else:
            children = sorted(self.active_node.children, key=lambda n: n.y)
            if children:
                self.set_active_node(children[0])
    
    def navigate_right(self, event=None):
        """Move to the parent node if on left side, or first child if on right side."""
        if not self.active_node:
            return
            
        # If node is on the left side of its parent (or is root's left child), go to parent
        if not self.active_node.parent or self.active_node.x < self.active_node.parent.x:
            if self.active_node.parent:
                self.set_active_node(self.active_node.parent)
        # If node is on the right side, try to go to first child
        else:
            children = sorted(self.active_node.children, key=lambda n: n.y)
            if children:
                self.set_active_node(children[0])
    
    def navigate_up(self, event=None):
        """Move to the sibling node above the current node."""
        if not self.active_node or not self.active_node.parent:
            return
            
        siblings = sorted(self.active_node.parent.children, key=lambda n: n.y)
        current_index = siblings.index(self.active_node)
        
        if current_index > 0:
            self.set_active_node(siblings[current_index - 1])
    
    def navigate_down(self, event=None):
        """Move to the sibling node below the current node."""
        if not self.active_node or not self.active_node.parent:
            return
            
        siblings = sorted(self.active_node.parent.children, key=lambda n: n.y)
        current_index = siblings.index(self.active_node)
        
        if current_index < len(siblings) - 1:
            self.set_active_node(siblings[current_index + 1])
    
    def move_node_up(self, event=None):
        """Move the current node up in its sibling order."""
        if not self.active_node or not self.active_node.parent:
            return
            
        siblings = sorted(self.active_node.parent.children, key=lambda n: n.y)
        current_index = siblings.index(self.active_node)
        
        if current_index > 0:
            # Swap positions in the list
            siblings[current_index], siblings[current_index - 1] = siblings[current_index - 1], siblings[current_index]
            self._reposition_siblings(self.active_node.parent)
            self._update_connector_lines()
    
    def move_node_down(self, event=None):
        """Move the current node down in its sibling order."""
        if not self.active_node or not self.active_node.parent:
            return
            
        siblings = sorted(self.active_node.parent.children, key=lambda n: n.y)
        current_index = siblings.index(self.active_node)
        
        if current_index < len(siblings) - 1:
            # Swap positions in the list
            siblings[current_index], siblings[current_index + 1] = siblings[current_index + 1], siblings[current_index]
            self._reposition_siblings(self.active_node.parent)
            self._update_connector_lines()
    
    def _on_node_clicked(self, event):
        """Handle node click event."""
        node = event.widget.getvar("data")
        self._start_drag(node, event)
        
    def _on_node_dragged(self, event):
        """Handle node drag event."""
        self._drag(event)
        
    def _on_node_dropped(self, event):
        """Handle node drop event."""
        self._end_drag(event)
    
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
        self._move_node_and_subtree(self.dragged_node, dx, dy)
        
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
                
            # Calculate distance to node center
            dx = x - node.x
            dy = y - node.y
            distance = (dx * dx + dy * dy) ** 0.5
            
            if distance < min_distance:
                min_distance = distance
                closest_node = node
        
        # Only return the node if it's within a reasonable distance
        if min_distance < 50:  # Adjust this threshold as needed
            return closest_node
        return None
    
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
    
    def _start_editing(self, node: Node):
        """Start editing a node's text."""
        if self.text_editor:
            self._finish_editing()
        
        self.editing_node = node
        
        # Get node text position and size
        bbox = self.canvas.bbox(node.text_id)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Create text editor
        self.text_editor = ctk.CTkEntry(
            self.canvas,  # Parent is canvas, not self
            width=max(100, text_width + 20),
            height=text_height + 10,
            fg_color="#2D2D2D",
            text_color="#FFFFFF",
            border_width=0
        )
        
        # Position editor
        canvas_x = node.x
        canvas_y = node.y
        editor_window = self.canvas.create_window(
            canvas_x, canvas_y,
            window=self.text_editor,
            tags="editor"
        )
        
        # Set initial text and select all
        self.text_editor.insert(0, node.text)
        self.text_editor.select_range(0, 'end')
        self.text_editor.focus()
        
        # Bind editor events
        self.text_editor.bind("<Return>", lambda e: self._finish_editing(e) or "break")
        self.text_editor.bind("<Escape>", lambda e: self._cancel_editing(e) or "break")
        self.text_editor.bind("<FocusOut>", self._finish_editing)
    
    def _finish_editing(self, event=None):
        """Finish editing and save changes."""
        if not self.text_editor or not self.editing_node:
            return
            
        # Update node text
        new_text = self.text_editor.get().strip()
        if new_text:
            self.editing_node.update_text(new_text)
        
        # Clean up
        self.canvas.delete("editor")
        self.text_editor.destroy()
        self.text_editor = None
        self.editing_node = None
    
    def _cancel_editing(self, event=None):
        """Cancel editing without saving changes."""
        if not self.text_editor:
            return
            
        # Clean up without saving
        self.canvas.delete("editor")
        self.text_editor.destroy()
        self.text_editor = None
        self.editing_node = None
    
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
