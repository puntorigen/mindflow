from typing import Dict, Optional
import customtkinter as ctk

from .node import Node

class MindMap(ctk.CTk):
    """Main mind map application window."""
    
    def __init__(self, *args, **kwargs):
        """Initialize the mind map window."""
        super().__init__(*args, **kwargs)
        
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
        
        # Event system
        self._event_handlers = {}  # Store event handlers
        
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
        self.bind("<space>", self.toggle_active_node)
        self.bind("<n>", self.create_node_at_active)  # New binding
    
    def bind_event(self, event_name: str, handler):
        """Bind a handler to a custom event.
        
        Args:
            event_name: Name of the event to bind to
            handler: Function to call when event occurs
        """
        if event_name not in self._event_handlers:
            self._event_handlers[event_name] = []
        self._event_handlers[event_name].append(handler)
    
    def emit_event(self, event_name: str, **kwargs):
        """Emit a custom event.
        
        Args:
            event_name: Name of the event to emit
            **kwargs: Additional data to pass to handlers
        """
        if event_name in self._event_handlers:
            for handler in self._event_handlers[event_name]:
                handler(event_name=event_name, **kwargs)
    
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
        """Move a node and all its children.
        
        Args:
            node: Node to move
            dx: Change in x coordinate
            dy: Change in y coordinate
        """
        # Move the node's visual elements
        node.x += dx
        node.y += dy
        self.canvas.move(node.rect_id, dx, dy)
        self.canvas.move(node.text_id, dx, dy)
        self.canvas.move(node.bg_id, dx, dy)
        self.canvas.move(node.collapse_indicator, dx, dy)
        
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
    
    def add_child_node_at(self, parent: Node, text: str, side: str = "right") -> Node:
        """Add a child node to the specified parent on the given side."""
        # Calculate base position
        if side == "left":
            new_x = parent.x - 200  # Move left from parent
        else:
            new_x = parent.x + 200  # Move right from parent
            
        # Calculate vertical position based on existing children
        siblings = [n for n in self.nodes.values() 
                   if n.parent == parent and 
                   ((side == "left" and n.x < parent.x) or 
                    (side == "right" and n.x > parent.x))]
        
        if siblings:
            # Place below the last sibling
            last_sibling = max(siblings, key=lambda n: n.y)
            new_y = last_sibling.y + 80
        else:
            # First child on this side
            new_y = parent.y
        
        # Create the new node
        new_node = Node(
            self.canvas,
            new_x,
            new_y,
            text,
            parent
        )
        
        # Add to nodes dictionary
        self.nodes[new_node.id] = new_node
        
        # Update layout
        self._reposition_siblings(parent)
        self._update_connector_lines()
        self._reset_z_order()
        
        return new_node
    
    def _find_closest_node_in_direction(self, node: Node, direction: str) -> Optional[Node]:
        """Find the closest node in the specified direction based on visual position."""
        if not node:
            return None
            
        candidates = []
        base_vertical_threshold = 50
        base_horizontal_threshold = 50
        
        # Get all visible nodes except the current one
        other_nodes = []
        for n in self.nodes.values():
            if n == node:
                continue
                
            # Check if node is visible (not under a collapsed parent)
            current = n
            is_visible = True
            while current.parent:
                if current.parent.is_collapsed:
                    is_visible = False
                    break
                current = current.parent
            
            if is_visible:
                other_nodes.append(n)
        
        # First pass: find nodes in the specified direction and calculate their distances
        direction_nodes = []
        for other in other_nodes:
            dx = abs(other.x - node.x)
            dy = abs(other.y - node.y)
            direct_distance = (dx * dx + dy * dy) ** 0.5  # Euclidean distance
            
            if direction == "up" and other.y < node.y:
                direction_nodes.append((other, dx, dy, direct_distance))
            elif direction == "down" and other.y > node.y:
                direction_nodes.append((other, dx, dy, direct_distance))
            elif direction == "left" and other.x < node.x:
                direction_nodes.append((other, dx, dy, direct_distance))
            elif direction == "right" and other.x > node.x:
                direction_nodes.append((other, dx, dy, direct_distance))
        
        if not direction_nodes:
            return None
            
        # Sort by direct distance to find closest nodes
        direction_nodes.sort(key=lambda x: x[3])
        closest_distance = direction_nodes[0][3]
        
        # Dynamically adjust thresholds based on closest node and context
        if direction in ["left", "right"]:
            # For horizontal movement, be more lenient with vertical alignment
            # especially for parent-child relationships
            horizontal_threshold = max(
                base_horizontal_threshold,
                # Scale threshold with distance to closest node
                min(closest_distance * 1.5, 400)
            )
            
            # Check if any nodes are direct parent/children
            has_parent_child = any(
                other[0].parent == node or node.parent == other[0]
                for other in direction_nodes[:3]  # Check among closest nodes
            )
            
            if has_parent_child:
                horizontal_threshold = max(horizontal_threshold, 500)
        else:
            horizontal_threshold = base_horizontal_threshold
            
        vertical_threshold = base_vertical_threshold
        if len(direction_nodes) <= 2:
            vertical_threshold = 150
            horizontal_threshold = max(horizontal_threshold, 300)
        
        # Second pass: score candidates with adjusted thresholds
        for other, dx, dy, direct_distance in direction_nodes:
            if direction in ["up", "down"]:
                if dx < vertical_threshold:
                    # Score based on horizontal alignment and vertical distance
                    alignment_score = dx / vertical_threshold
                    distance_score = direct_distance / 1000
                    score = alignment_score * 0.6 + distance_score * 0.4
                    candidates.append((other, score, direct_distance))
            else:  # left/right
                if dy < horizontal_threshold:
                    # For horizontal movement, consider parent-child relationships
                    is_parent_child = (other.parent == node or node.parent == other)
                    # Normalize vertical offset relative to horizontal distance
                    alignment_score = dy / (dx + 1)  # Add 1 to avoid division by zero
                    distance_score = direct_distance / 1000
                    
                    # Combined score with different weights
                    score = alignment_score * 0.5 + distance_score * 0.5
                    if is_parent_child:
                        score *= 0.7  # Significant bonus for parent-child relationships
                    candidates.append((other, score, direct_distance))
        
        if not candidates:
            return None
        
        # Sort by score (lower is better)
        candidates.sort(key=lambda x: x[1])
        return candidates[0][0]
    
    def navigate_left(self, event=None):
        """Move to the closest node to the left."""
        if not self.active_node:
            return
        
        next_node = self._find_closest_node_in_direction(self.active_node, "left")
        if next_node:
            self.set_active_node(next_node)
    
    def navigate_right(self, event=None):
        """Move to the closest node to the right."""
        if not self.active_node:
            return
        
        next_node = self._find_closest_node_in_direction(self.active_node, "right")
        if next_node:
            self.set_active_node(next_node)
    
    def navigate_up(self, event=None):
        """Move to the closest node above."""
        if not self.active_node:
            return
        
        next_node = self._find_closest_node_in_direction(self.active_node, "up")
        if next_node:
            self.set_active_node(next_node)
    
    def navigate_down(self, event=None):
        """Move to the closest node below."""
        if not self.active_node:
            return
        
        next_node = self._find_closest_node_in_direction(self.active_node, "down")
        if next_node:
            self.set_active_node(next_node)
    
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
        if self.dragged_node.children and self.dragged_node.is_collapsed:
            self.canvas.tag_raise(self.dragged_node.collapse_indicator)
    
    def _drag(self, event):
        """Handle node drag event."""
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
        
        # Ensure dragged node and its elements stay on top
        self.canvas.tag_raise(self.dragged_node.rect_id)
        self.canvas.tag_raise(self.dragged_node.text_id)
        if self.dragged_node.children and self.dragged_node.is_collapsed:
            self.canvas.tag_raise(self.dragged_node.collapse_indicator)
    
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
            
            # Remove from old parent's children
            if old_parent:
                old_parent.children.remove(self.dragged_node)
            
            # Add to new parent's children
            new_parent.children.append(self.dragged_node)
            self.dragged_node.parent = new_parent
            
            # Determine if we need to flip direction
            old_direction = "right" if self.dragged_node.x > old_parent.x else "left"
            
            # For new direction, if it's root's child, use default direction
            # Otherwise, check relative position to its parent
            if new_parent.parent is None:
                new_direction = "right"
            else:
                new_direction = "right" if new_parent.x > new_parent.parent.x else "left"
            
            # If direction changed, flip the node and its subtree
            if old_direction != new_direction:
                self._flip_node_subtree(self.dragged_node)
            
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
                # Check if either node is under a collapsed parent
                current = node
                should_draw = True
                while current.parent:
                    if current.parent.is_collapsed:
                        should_draw = False
                        break
                    current = current.parent
                
                if should_draw:
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
        for line in self.canvas.find_withtag("line"):
            self.canvas.tag_lower(line)
        
        # Layer nodes above lines
        for node in self.nodes.values():
            # Background
            self.canvas.tag_raise(node.bg_id)
            # Rectangle
            self.canvas.tag_raise(node.rect_id)
            # Text
            self.canvas.tag_raise(node.text_id)
            # Collapse indicator
            if node.children:
                self.canvas.tag_raise(node.collapse_indicator)
    
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
    
    def _flip_node_subtree(self, node: Node):
        """Flip a node and its entire subtree to the opposite direction."""
        if not node.parent:
            return
            
        def flip_node_position(node, parent_x):
            # Calculate and flip the node's position
            dx = node.x - parent_x
            node.x = parent_x - dx
            
            # Update visual elements
            bbox = self.canvas.bbox(node.rect_id)
            width = bbox[2] - bbox[0]
            self.canvas.coords(node.rect_id,
                             node.x - width/2, bbox[1],
                             node.x + width/2, bbox[3])
            self.canvas.coords(node.text_id, node.x, node.y)
            
            # Recursively flip children
            for child in node.children:
                flip_node_position(child, node.x)
        
        # Start the recursive flip from the top node
        flip_node_position(node, node.parent.x)
    
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
        
        self.emit_event("node_text_changed", node=self.editing_node, text=new_text)
    
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

    def toggle_active_node(self, event=None):
        """Toggle collapse state of active node."""
        if not self.active_node:
            return
            
        if self.active_node.toggle_collapse():
            self._update_node_visibility()
            self._update_connector_lines()
            self.emit_event("node_toggled", node=self.active_node)
    
    def _update_node_visibility(self):
        """Update visibility of nodes based on collapse state."""
        for node in self.nodes.values():
            # Check if node should be hidden (under a collapsed parent)
            current = node
            should_hide = False
            while current.parent:
                if current.parent.is_collapsed:
                    should_hide = True
                    break
                current = current.parent
            
            # Update visibility
            state = "hidden" if should_hide else "normal"
            self.canvas.itemconfig(node.rect_id, state=state)
            self.canvas.itemconfig(node.text_id, state=state)
            self.canvas.itemconfig(node.bg_id, state=state)
            
            # Update collapse indicator
            if not should_hide:
                node._update_collapse_indicator()
            else:
                self.canvas.itemconfig(node.collapse_indicator, state="hidden")

    def create_child_node(self, parent_node: Node, text: str = "New Node") -> Node:
        """Create a new child node with proper connections.
        
        Args:
            parent_node: Parent node to create child under
            text: Text for the new node
            
        Returns:
            The newly created node
        """
        # Calculate position for new node
        x = parent_node.x + 150  # Horizontal distance from parent
        y = parent_node.y
        
        # Create the node
        new_node = Node(self.canvas, x, y, text, parent=parent_node)
        self.nodes[new_node.id] = new_node
        
        # Add to parent's children
        parent_node.children.append(new_node)
        
        # Create connector line
        line_id = self.canvas.create_line(
            parent_node.x, parent_node.y,
            new_node.x, new_node.y,
            fill="#CCCCCC",
            width=2
        )
        new_node.connector = line_id
        
        # Update parent's collapse indicator
        parent_node._update_collapse_indicator()
        
        # Layout the nodes
        self._layout_nodes()
        
        # Emit creation event
        self.emit_event("node_created", node=new_node, parent=parent_node)
        
        return new_node

    def add_child_node_at(self, parent: Node, text: str = "New Node", side: str = None) -> Node:
        """Add a child node at the specified parent node.
        
        Args:
            parent: Parent node
            text: Text for the new node
            side: Side to add node on ('left' or 'right', None for automatic)
            
        Returns:
            The newly created node
        """
        # Create the node using create_child_node
        new_node = self.create_child_node(parent, text)
        
        # Update layout
        self._layout_nodes()
        
        return new_node

    def _layout_nodes(self):
        """Layout all nodes."""
        for node in self.nodes.values():
            if node.parent:
                self._reposition_siblings(node.parent)
                self._update_connector_lines()
                self._reset_z_order()

    def create_node_at_active(self, event=None):
        """Create a new node at the active node."""
        if not self.active_node:
            return
        
        # Create new node using create_child_node
        new_node = self.create_child_node(self.active_node)
        
        # Set it as active
        self.set_active_node(new_node)
        
        # Start editing the new node
        self._start_editing(new_node)
