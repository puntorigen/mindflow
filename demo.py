from mindflow import MindMap

def create_demo_mindmap():
    mindmap = MindMap()
    
    # Get the central node (first node in the dictionary)
    central = next(iter(mindmap.nodes.values()))
    central.text = "Mind Map Demo"
    
    # Create left branch
    projects = mindmap.add_child_node_at(central, "Projects", side="left")
    mindmap.add_child_node_at(projects, "Website Redesign")
    mobile_app = mindmap.add_child_node_at(projects, "Mobile App")
    mindmap.add_child_node_at(mobile_app, "UI Design")
    mindmap.add_child_node_at(mobile_app, "Backend API")
    mindmap.add_child_node_at(mobile_app, "Testing")
    
    # Create right branch
    ideas = mindmap.add_child_node_at(central, "Ideas", side="right")
    features = mindmap.add_child_node_at(ideas, "New Features")
    mindmap.add_child_node_at(features, "Dark Mode")
    mindmap.add_child_node_at(features, "Export Options")
    mindmap.add_child_node_at(features, "Templates")
    
    research = mindmap.add_child_node_at(ideas, "Research")
    mindmap.add_child_node_at(research, "User Feedback")
    mindmap.add_child_node_at(research, "Competitors")
    
    return mindmap

if __name__ == "__main__":
    app = create_demo_mindmap()
    app.mainloop()
