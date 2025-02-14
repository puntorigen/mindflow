from mindflow import MindMap

def handle_node_event(event_name, **kwargs):
    """Handle node events from the mindmap."""
    if event_name == "node_created":
        node = kwargs["node"]
        parent = kwargs["parent"]
        print(f"Node created: '{node.text}' under parent '{parent.text}'")
    elif event_name == "node_text_changed":
        node = kwargs["node"]
        text = kwargs["text"]
        print(f"Node text changed to: '{text}'")
    elif event_name == "node_toggled":
        node = kwargs["node"]
        state = "collapsed" if node.is_collapsed else "expanded"
        print(f"Node '{node.text}' was {state}")

def create_demo_mindmap():
    mindmap = MindMap()
    
    # Bind to node events
    mindmap.bind_event("node_created", handle_node_event)
    mindmap.bind_event("node_text_changed", handle_node_event)
    mindmap.bind_event("node_toggled", handle_node_event)
    
    # Get the central node (first node in the dictionary)
    central = next(iter(mindmap.nodes.values()))
    central.text = "Mind Map Demo"
    
    # Create demo nodes
    backend = mindmap.create_child_node(central, "Backend API")
    testing = mindmap.create_child_node(central, "Testing")
    ideas = mindmap.create_child_node(central, "Ideas")
    features = mindmap.create_child_node(central, "New Features")
    research = mindmap.create_child_node(ideas, "Research")
    
    return mindmap

if __name__ == "__main__":
    app = create_demo_mindmap()
    app.mainloop()
