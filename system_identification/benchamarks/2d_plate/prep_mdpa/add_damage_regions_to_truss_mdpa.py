#!/usr/bin/env python3
"""
Script to extract TrussElement3D2N elements and nodes based on coordinate criteria.
Criteria:
- Nodes between x = 0.005 and 0.01 for y = 0.0075
- Nodes between x = 0.03 and 0.035 for y = 0.0225

Usage:
    python3 analyze_truss.py                    # Interactive mode
    python3 analyze_truss.py --append           # Auto-append without prompts
    python3 analyze_truss.py --replace          # Auto-replace existing SubModelParts
    python3 analyze_truss.py --no-append        # Skip appending to MDPA file
"""

import sys

def parse_mdpa_file(filename):
    """Parse the MDPA file and extract nodes and TrussElement3D2N elements."""
    nodes = {}  # node_id: (x, y, z)
    truss_elements = {}  # element_id: [node1, node2]
    
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Parse nodes
        if line == "Begin Nodes":
            i += 1
            while i < len(lines):
                line = lines[i].strip()
                if line == "End Nodes":
                    break
                if line:
                    parts = line.split()
                    if len(parts) >= 4:
                        node_id = int(parts[0])
                        x, y, z = float(parts[1]), float(parts[2]), float(parts[3])
                        nodes[node_id] = (x, y, z)
                i += 1
        
        # Parse TrussElement3D2N elements
        elif line == "Begin Elements\tTrussElement3D2N" or line == "Begin Elements TrussElement3D2N":
            i += 1
            while i < len(lines):
                line = lines[i].strip()
                if line == "End Elements":
                    break
                if line:
                    parts = line.split()
                    if len(parts) >= 4:
                        elem_id = int(parts[0])
                        # Format: element_id property_id node1 node2
                        node1, node2 = int(parts[2]), int(parts[3])
                        truss_elements[elem_id] = [node1, node2]
                i += 1
        
        i += 1
    
    return nodes, truss_elements


def filter_nodes(nodes):
    """Filter nodes based on coordinate criteria."""
    filtered_nodes = {}
    
    for node_id, (x, y, z) in nodes.items():
        # Criteria 1: x between 0.005 and 0.01, y = 0.0075
        if 0.005 <= x <= 0.01 and abs(y - 0.0075) < 1e-6:
            filtered_nodes[node_id] = (x, y, z)
        # Criteria 2: x between 0.03 and 0.035, y = 0.0225
        elif 0.03 <= x <= 0.035 and abs(y - 0.0225) < 1e-6:
            filtered_nodes[node_id] = (x, y, z)
    
    return filtered_nodes


def filter_elements(truss_elements, filtered_node_ids, nodes):
    """Filter elements that connect to filtered nodes."""
    filtered_elements = {}
    
    for elem_id, [node1, node2] in truss_elements.items():
        # Check if both nodes are in the filtered set
        if node1 in filtered_node_ids and node2 in filtered_node_ids:
            filtered_elements[elem_id] = [node1, node2]
    
    return filtered_elements


def check_submodelpart_exists(filename, submodelpart_name):
    """Check if a SubModelPart already exists in the file."""
    with open(filename, 'r') as f:
        content = f.read()
    return f"Begin SubModelPart\t{submodelpart_name}" in content


def append_submodelpart_to_mdpa(filename, submodelpart_name, node_ids, element_ids):
    """Append a new SubModelPart to the MDPA file."""
    # Debug output
    print(f"  DEBUG: Appending {submodelpart_name} with {len(node_ids)} nodes and {len(element_ids)} elements")
    
    submodelpart_text = f"\nBegin SubModelPart\t{submodelpart_name}\n"
    submodelpart_text += "\tBegin SubModelPartData\n"
    submodelpart_text += "\tEnd SubModelPartData\n"
    submodelpart_text += "\tBegin SubModelPartTables\n"
    submodelpart_text += "\tEnd SubModelPartTables\n"
    submodelpart_text += "\tBegin SubModelPartNodes\n"
    for node_id in sorted(node_ids):
        submodelpart_text += f"\t\t{node_id}\n"
    submodelpart_text += "\tEnd SubModelPartNodes\n"
    submodelpart_text += "\tBegin SubModelPartElements\n"
    for elem_id in sorted(element_ids):
        submodelpart_text += f"\t\t{elem_id}\n"
    submodelpart_text += "\tEnd SubModelPartElements\n"
    submodelpart_text += "\tBegin SubModelPartConditions\n"
    submodelpart_text += "\tEnd SubModelPartConditions\n"
    submodelpart_text += "\tBegin SubModelPartGeometries\n"
    submodelpart_text += "\tEnd SubModelPartGeometries\n"
    submodelpart_text += "\tBegin SubModelPartConstraints\n"
    submodelpart_text += "\tEnd SubModelPartConstraints\n"
    submodelpart_text += "End SubModelPart\t\n"
    
    with open(filename, 'a') as f:
        f.write(submodelpart_text)


def remove_submodelpart_from_mdpa(filename, submodelpart_name):
    """Remove a SubModelPart from the MDPA file."""
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    new_lines = []
    skip = False
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Check if this is the start of the SubModelPart to remove
        if line.strip() == f"Begin SubModelPart\t{submodelpart_name}":
            skip = True
            # Skip until we find the matching End SubModelPart
            while i < len(lines):
                if lines[i].strip() == "End SubModelPart\t":
                    i += 1
                    # Also skip the blank line after End SubModelPart if present
                    if i < len(lines) and lines[i].strip() == "":
                        i += 1
                    break
                i += 1
            skip = False
            continue
        
        if not skip:
            new_lines.append(line)
        i += 1
    
    with open(filename, 'w') as f:
        f.writelines(new_lines)


def remove_ids_from_submodelpart(filename, submodelpart_name, node_ids_to_remove, element_ids_to_remove):
    """Remove specific node IDs and element IDs from a SubModelPart."""
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    new_lines = []
    in_submodelpart = False
    in_nodes_section = False
    in_elements_section = False
    i = 0
    
    node_ids_to_remove = set(node_ids_to_remove)
    element_ids_to_remove = set(element_ids_to_remove)
    
    while i < len(lines):
        line = lines[i]
        
        # Check if we're entering the target SubModelPart
        if line.strip() == f"Begin SubModelPart\t{submodelpart_name}":
            in_submodelpart = True
            new_lines.append(line)
            i += 1
            continue
        
        # Check if we're leaving the SubModelPart
        if in_submodelpart and line.strip() == "End SubModelPart\t":
            in_submodelpart = False
            in_nodes_section = False
            in_elements_section = False
            new_lines.append(line)
            i += 1
            continue
        
        # Check if we're in the nodes section
        if in_submodelpart and line.strip() == "Begin SubModelPartNodes":
            in_nodes_section = True
            new_lines.append(line)
            i += 1
            continue
        
        if in_submodelpart and line.strip() == "End SubModelPartNodes":
            in_nodes_section = False
            new_lines.append(line)
            i += 1
            continue
        
        # Check if we're in the elements section
        if in_submodelpart and line.strip() == "Begin SubModelPartElements":
            in_elements_section = True
            new_lines.append(line)
            i += 1
            continue
        
        if in_submodelpart and line.strip() == "End SubModelPartElements":
            in_elements_section = False
            new_lines.append(line)
            i += 1
            continue
        
        # Filter nodes
        if in_nodes_section:
            try:
                node_id = int(line.strip())
                if node_id not in node_ids_to_remove:
                    new_lines.append(line)
                # else: skip this line (node is removed)
            except ValueError:
                # Not a node ID line, keep it
                new_lines.append(line)
            i += 1
            continue
        
        # Filter elements
        if in_elements_section:
            try:
                element_id = int(line.strip())
                if element_id not in element_ids_to_remove:
                    new_lines.append(line)
                # else: skip this line (element is removed)
            except ValueError:
                # Not an element ID line, keep it
                new_lines.append(line)
            i += 1
            continue
        
        # Default: keep the line
        new_lines.append(line)
        i += 1
    
    with open(filename, 'w') as f:
        f.writelines(new_lines)


def main():
    filename = "Structure_truss_coarse.mdpa"
    
    # Parse command line arguments
    auto_append = False
    auto_replace = False
    no_append = False
    
    if len(sys.argv) > 1:
        if '--append' in sys.argv:
            auto_append = True
        elif '--replace' in sys.argv:
            auto_append = True
            auto_replace = True
        elif '--no-append' in sys.argv:
            no_append = True
    
    print("Parsing MDPA file...")
    nodes, truss_elements = parse_mdpa_file(filename)
    print(f"Total nodes: {len(nodes)}")
    print(f"Total TrussElement3D2N elements: {len(truss_elements)}")
    print()
    
    print("Filtering nodes...")
    filtered_nodes = filter_nodes(nodes)
    filtered_node_ids = set(filtered_nodes.keys())
    print(f"Filtered nodes: {len(filtered_nodes)}")
    print()
    
    print("Filtering elements...")
    filtered_elements = filter_elements(truss_elements, filtered_node_ids, nodes)
    print(f"Filtered TrussElement3D2N elements: {len(filtered_elements)}")
    print()
    
    # Print results
    print("=" * 80)
    print("FILTERED NODES")
    print("=" * 80)
    print("Format: NodeID\tX\tY\tZ")
    print("-" * 80)
    
    # Group by y coordinate for better readability
    nodes_y_0075 = {nid: coords for nid, coords in filtered_nodes.items() 
                    if abs(coords[1] - 0.0075) < 1e-6}
    nodes_y_0225 = {nid: coords for nid, coords in filtered_nodes.items() 
                    if abs(coords[1] - 0.0225) < 1e-6}
    
    if nodes_y_0075:
        print("\nNodes with y = 0.0075 (x between 0.005 and 0.01):")
        for node_id in sorted(nodes_y_0075.keys()):
            x, y, z = nodes_y_0075[node_id]
            print(f"{node_id}\t{x:.6f}\t{y:.6f}\t{z:.6f}")
    
    if nodes_y_0225:
        print("\nNodes with y = 0.0225 (x between 0.03 and 0.035):")
        for node_id in sorted(nodes_y_0225.keys()):
            x, y, z = nodes_y_0225[node_id]
            print(f"{node_id}\t{x:.6f}\t{y:.6f}\t{z:.6f}")
    
    print()
    print("=" * 80)
    print("FILTERED TRUSS ELEMENTS")
    print("=" * 80)
    print("Format: ElementID\tNode1\tNode2\t(Node1_coords) -> (Node2_coords)")
    print("-" * 80)
    
    # Group by y coordinate
    elements_y_0075 = {}
    elements_y_0225 = {}
    
    for elem_id, [node1, node2] in filtered_elements.items():
        if node1 in nodes_y_0075:
            elements_y_0075[elem_id] = [node1, node2]
        elif node1 in nodes_y_0225:
            elements_y_0225[elem_id] = [node1, node2]
    
    if elements_y_0075:
        print("\nElements with y = 0.0075:")
        for elem_id in sorted(elements_y_0075.keys()):
            node1, node2 = elements_y_0075[elem_id]
            x1, y1, z1 = nodes[node1]
            x2, y2, z2 = nodes[node2]
            print(f"{elem_id}\t{node1}\t{node2}\t({x1:.6f}, {y1:.6f}, {z1:.6f}) -> ({x2:.6f}, {y2:.6f}, {z2:.6f})")
    
    if elements_y_0225:
        print("\nElements with y = 0.0225:")
        for elem_id in sorted(elements_y_0225.keys()):
            node1, node2 = elements_y_0225[elem_id]
            x1, y1, z1 = nodes[node1]
            x2, y2, z2 = nodes[node2]
            print(f"{elem_id}\t{node1}\t{node2}\t({x1:.6f}, {y1:.6f}, {z1:.6f}) -> ({x2:.6f}, {y2:.6f}, {z2:.6f})")
    
    # Save to file
    output_file = "truss_filtered_results.txt"
    with open(output_file, 'w') as f:
        f.write("FILTERED NODES\n")
        f.write("=" * 80 + "\n")
        f.write("Format: NodeID\tX\tY\tZ\n")
        f.write("-" * 80 + "\n")
        
        if nodes_y_0075:
            f.write("\nNodes with y = 0.0075 (x between 0.005 and 0.01):\n")
            for node_id in sorted(nodes_y_0075.keys()):
                x, y, z = nodes_y_0075[node_id]
                f.write(f"{node_id}\t{x:.6f}\t{y:.6f}\t{z:.6f}\n")
        
        if nodes_y_0225:
            f.write("\nNodes with y = 0.0225 (x between 0.03 and 0.035):\n")
            for node_id in sorted(nodes_y_0225.keys()):
                x, y, z = nodes_y_0225[node_id]
                f.write(f"{node_id}\t{x:.6f}\t{y:.6f}\t{z:.6f}\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("FILTERED TRUSS ELEMENTS\n")
        f.write("=" * 80 + "\n")
        f.write("Format: ElementID\tNode1\tNode2\t(Node1_coords) -> (Node2_coords)\n")
        f.write("-" * 80 + "\n")
        
        if elements_y_0075:
            f.write("\nElements with y = 0.0075:\n")
            for elem_id in sorted(elements_y_0075.keys()):
                node1, node2 = elements_y_0075[elem_id]
                x1, y1, z1 = nodes[node1]
                x2, y2, z2 = nodes[node2]
                f.write(f"{elem_id}\t{node1}\t{node2}\t({x1:.6f}, {y1:.6f}, {z1:.6f}) -> ({x2:.6f}, {y2:.6f}, {z2:.6f})\n")
        
        if elements_y_0225:
            f.write("\nElements with y = 0.0225:\n")
            for elem_id in sorted(elements_y_0225.keys()):
                node1, node2 = elements_y_0225[elem_id]
                x1, y1, z1 = nodes[node1]
                x2, y2, z2 = nodes[node2]
                f.write(f"{elem_id}\t{node1}\t{node2}\t({x1:.6f}, {y1:.6f}, {z1:.6f}) -> ({x2:.6f}, {y2:.6f}, {z2:.6f})\n")
    
    print()
    print(f"Results saved to: {output_file}")
    
    # Generate SubModelPart sections
    submodelpart_file = "truss_damage_submodelparts.txt"
    with open(submodelpart_file, 'w') as f:
        # SubModelPart for y = 0.0075 (truss_damage_1)
        if nodes_y_0075 or elements_y_0075:
            f.write("Begin SubModelPart\ttruss_damage_1\n")
            f.write("\tBegin SubModelPartData\n")
            f.write("\tEnd SubModelPartData\n")
            f.write("\tBegin SubModelPartTables\n")
            f.write("\tEnd SubModelPartTables\n")
            f.write("\tBegin SubModelPartNodes\n")
            for node_id in sorted(nodes_y_0075.keys()):
                f.write(f"\t\t{node_id}\n")
            f.write("\tEnd SubModelPartNodes\n")
            f.write("\tBegin SubModelPartElements\n")
            for elem_id in sorted(elements_y_0075.keys()):
                f.write(f"\t\t{elem_id}\n")
            f.write("\tEnd SubModelPartElements\n")
            f.write("\tBegin SubModelPartConditions\n")
            f.write("\tEnd SubModelPartConditions\n")
            f.write("\tBegin SubModelPartGeometries\n")
            f.write("\tEnd SubModelPartGeometries\n")
            f.write("\tBegin SubModelPartConstraints\n")
            f.write("\tEnd SubModelPartConstraints\n")
            f.write("End SubModelPart\t\n")
            f.write("\n")
        
        # SubModelPart for y = 0.0225 (truss_damage_2)
        if nodes_y_0225 or elements_y_0225:
            f.write("Begin SubModelPart\ttruss_damage_2\n")
            f.write("\tBegin SubModelPartData\n")
            f.write("\tEnd SubModelPartData\n")
            f.write("\tBegin SubModelPartTables\n")
            f.write("\tEnd SubModelPartTables\n")
            f.write("\tBegin SubModelPartNodes\n")
            for node_id in sorted(nodes_y_0225.keys()):
                f.write(f"\t\t{node_id}\n")
            f.write("\tEnd SubModelPartNodes\n")
            f.write("\tBegin SubModelPartElements\n")
            for elem_id in sorted(elements_y_0225.keys()):
                f.write(f"\t\t{elem_id}\n")
            f.write("\tEnd SubModelPartElements\n")
            f.write("\tBegin SubModelPartConditions\n")
            f.write("\tEnd SubModelPartConditions\n")
            f.write("\tBegin SubModelPartGeometries\n")
            f.write("\tEnd SubModelPartGeometries\n")
            f.write("\tBegin SubModelPartConstraints\n")
            f.write("\tEnd SubModelPartConstraints\n")
            f.write("End SubModelPart\t\n")
    
    print(f"SubModelPart sections saved to: {submodelpart_file}")
    
    # Determine if we should append to MDPA file
    if no_append:
        print("\n✗ SubModelParts were not appended to the MDPA file (--no-append flag).")
        print(f"  You can manually copy them from {submodelpart_file}")
        return
    
    # Ask user if they want to append to the MDPA file (unless auto mode)
    print()
    print("=" * 80)
    print("APPENDING TO MDPA FILE")
    print("=" * 80)
    
    mdpa_filename = filename
    
    if not auto_append:
        append_to_file = input(f"\nDo you want to append these SubModelParts to {mdpa_filename}? (yes/no): ").strip().lower()
        if append_to_file not in ['yes', 'y']:
            print("\n✗ SubModelParts were not appended to the MDPA file.")
            print(f"  You can manually copy them from {submodelpart_file}")
            return
    else:
        print(f"\nAuto-appending SubModelParts to {mdpa_filename}...")
    
    # Check and append truss_damage_1
    if nodes_y_0075 or elements_y_0075:
        if check_submodelpart_exists(mdpa_filename, "truss_damage_1"):
            print(f"\nSubModelPart 'truss_damage_1' already exists in {mdpa_filename}.")
            
            if auto_replace:
                replace_1 = True
                print("Auto-replacing (--replace flag)...")
            elif auto_append:
                print("Skipping (already exists, use --replace to force replacement)")
                replace_1 = False
            else:
                replace_1 = input("Do you want to replace it? (yes/no): ").strip().lower() in ['yes', 'y']
            
            if replace_1:
                remove_submodelpart_from_mdpa(mdpa_filename, "truss_damage_1")
                append_submodelpart_to_mdpa(mdpa_filename, "truss_damage_1", 
                                            list(nodes_y_0075.keys()), list(elements_y_0075.keys()))
                print("✓ SubModelPart 'truss_damage_1' replaced successfully!")
            else:
                print("✗ Skipped 'truss_damage_1'")
        else:
            append_submodelpart_to_mdpa(mdpa_filename, "truss_damage_1", 
                                       list(nodes_y_0075.keys()), list(elements_y_0075.keys()))
            print("✓ SubModelPart 'truss_damage_1' appended successfully!")
    
    # Check and append truss_damage_2
    if nodes_y_0225 or elements_y_0225:
        if check_submodelpart_exists(mdpa_filename, "truss_damage_2"):
            print(f"\nSubModelPart 'truss_damage_2' already exists in {mdpa_filename}.")
            
            if auto_replace:
                replace_2 = True
                print("Auto-replacing (--replace flag)...")
            elif auto_append:
                print("Skipping (already exists, use --replace to force replacement)")
                replace_2 = False
            else:
                replace_2 = input("Do you want to replace it? (yes/no): ").strip().lower() in ['yes', 'y']
            
            if replace_2:
                remove_submodelpart_from_mdpa(mdpa_filename, "truss_damage_2")
                append_submodelpart_to_mdpa(mdpa_filename, "truss_damage_2", 
                                            list(nodes_y_0225.keys()), list(elements_y_0225.keys()))
                print("✓ SubModelPart 'truss_damage_2' replaced successfully!")
            else:
                print("✗ Skipped 'truss_damage_2'")
        else:
            append_submodelpart_to_mdpa(mdpa_filename, "truss_damage_2", 
                                       list(nodes_y_0225.keys()), list(elements_y_0225.keys()))
            print("✓ SubModelPart 'truss_damage_2' appended successfully!")
    
    # Note: Keeping all nodes and elements in the main "truss" SubModelPart
    # The damage elements are now in both "truss" and "truss_damage_X" SubModelParts
    
    print(f"\n✓ Done! Check {mdpa_filename} for the updated SubModelParts.")
    print(f"Note: Damage elements are included in both 'truss' and 'truss_damage_X' SubModelParts.")


if __name__ == "__main__":
    main()
