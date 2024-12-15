import re
import plotly.graph_objects as go

# Function to extract depths
def extract_depths(content: str) -> dict:
    depth_pattern = re.compile(r'insertSoilBorder\((-?\d+\.\d+E[+-]?\d+) m \+zMudline\);')
    layer_pattern = re.compile(r'soil\((\d+)\)\.soilCurves = (Layer\d+_SoilCurves\d+);')
    
    depths = {}
    current_depth = None
    
    for line in content:
        # Match soil border depth
        depth_match = depth_pattern.search(line)
        if depth_match:
            current_depth = float(depth_match.group(1))
        
        # Match layer and associate with the last matched depth
        layer_match = layer_pattern.search(line)
        if layer_match and current_depth is not None:
            layer_id = layer_match.group(2)
            depths[layer_id] = current_depth
    
    return depths

# Function to extract soil curves
def extract_soil_curves(file: str):
    curves = {"outer_dia": [], "depth": [], "p-y": [], "t-z": [], "q-z": []}
    py_pattern = re.compile(r'(Layer\d+_SoilCurves\d+)\.addManualPY\(([\d\.\-E\+]+), Array\((.*?)\), Array\((.*?)\)')
    tz_pattern = re.compile(r'(Layer\d+_SoilCurves\d+)\.addManualTZ\(([\d\.\-E\+]+), Array\((.*?)\), Array\((.*?)\)')
    qz_pattern = re.compile(r'(Layer\d+_SoilCurves\d+)\.addManualQZ\(([\d\.\-E\+]+), Array\((.*?)\), Array\((.*?)\)')

    # Handle both file-like object and file path
    if hasattr(file, 'read'): # If file is a file-like object (from Streamlit)
        content = file.read().decode('utf-8').splitlines() # Decode bytes to string and split into lines
    else: # If file is a file path
        with open(file, 'r') as file:
            content = file.readlines()

    # Extract depths
    layer_depths = extract_depths(content)
    
    for line in content:
        # Match p-y data
        py_match = py_pattern.search(line)
        if py_match:
            layer_id = py_match.group(1)
            outer_diameter = float(py_match.group(2))
            depth = layer_depths.get(layer_id, None)
            if depth is not None:
                displacements = [float(x.replace(" m", "")) for x in py_match.group(3).split(", ")]
                forces = [float(x.replace(" kPa", "")) for x in py_match.group(4).split(", ")]
                curves["outer_dia"].append(outer_diameter)
                curves["depth"].append(depth)
                curves["p-y"].append((displacements, forces))
        
        # Match t-z data
        tz_match = tz_pattern.search(line)
        if tz_match:
            layer_id = tz_match.group(1)
            outer_diameter = float(tz_match.group(2))
            depth = layer_depths.get(layer_id, None)
            if depth is not None:
                displacements = [float(x.replace(" m", "")) for x in tz_match.group(3).split(", ")]
                forces = [float(x.replace(" kPa", "")) for x in tz_match.group(4).split(", ")]
                curves["outer_dia"].append(outer_diameter)
                curves["t-z"].append((displacements, forces))
        
        # Match q-z data
        qz_match = qz_pattern.search(line)
        if qz_match:
            layer_id = qz_match.group(1)
            outer_diameter = float(qz_match.group(2))
            depth = layer_depths.get(layer_id, None)
            if depth is not None:
                displacements = [float(x.replace(" m", "")) for x in qz_match.group(3).split(", ")]
                forces = [float(x.replace(" kPa", "")) for x in qz_match.group(4).split(", ")]
                curves["outer_dia"].append(outer_diameter)
                curves["q-z"].append((displacements, forces))

    return curves

def create_interactive_plot_fixed_y2(soil_curves):
    # Find the max and min y-values for p-y, t-z, and q-z (overall max/min)
    max_py = max(max([max(forces) for _, forces in soil_curves["p-y"]]), 0)
    min_tz = min(min([min(forces) for _, forces in soil_curves["t-z"]]), 0)
    max_tz = max(max([max(forces) for _, forces in soil_curves["t-z"]]), 0)
    max_qz = max(max([max(forces) for _, forces in soil_curves["q-z"]]), 0)

    fig = go.Figure()

    # Add traces for p-y curves
    for i, depth in enumerate(soil_curves["depth"]):
        py_displacement, py_force = soil_curves["p-y"][i]
        fig.add_trace(
            go.Scatter(
                x=py_displacement,
                y=py_force,
                mode='lines',
                name=f'p-y (Depth: {depth:.2f} m)',
                visible=(i == 0),
                xaxis='x1',
                yaxis='y1',
            )
        )

    # Add traces for t-z curves
    for i, depth in enumerate(soil_curves["depth"]):
        tz_displacement, tz_force = soil_curves["t-z"][i]
        fig.add_trace(
            go.Scatter(
                x=tz_displacement,
                y=tz_force,
                mode='lines',
                name=f't-z (Depth: {depth:.2f} m)',
                visible=(i == 0),
                xaxis='x2',
                yaxis='y2',
            )
        )

    # Add traces for q-z curves
    for i, depth in enumerate(soil_curves["depth"]):
        qz_displacement, qz_force = soil_curves["q-z"][i]
        fig.add_trace(
            go.Scatter(
                x=qz_displacement,
                y=qz_force,
                mode='lines',
                name=f'q-z (Depth: {depth:.2f} m)',
                visible=(i == 0),
                xaxis='x3',
                yaxis='y3',
            )
        )

    # Configure vertical stacking of subplots
    fig.update_layout(
        xaxis=dict(domain=[0.0, 1.0], anchor='y1',range=[-1.6, 4.0]),  # p-y
        # yaxis=dict(domain=[0.7, 1.0], title="p-y [kPa]", range=[0, max_py*1.1]),  # Adjust the range as needed
        yaxis=dict(domain=[0.7, 1.0], title="p-y [kPa]"),  # Adjust the range as needed
        xaxis2=dict(domain=[0.0, 1.0], anchor='y2',range=[-0.4, 1.0]),  # t-z
        # yaxis2=dict(domain=[0.35, 0.65], title="t-z [kPa]", range=[min_tz*1.1, max_tz*1.1]),
        yaxis2=dict(domain=[0.35, 0.65], title="t-z [kPa]"),
        xaxis3=dict(domain=[0.0, 1.0], anchor='y3',range=[-0.4, 1.0]),  # q-z
        yaxis3=dict(domain=[0.0, 0.3], title="q-z [kPa]", range=[0, max_qz*1.1]),
    )

    # Create slider for depth control
    steps = []
    for i, depth in enumerate(soil_curves["depth"]):
        step = dict(
            method="update",
            args=[
                {"visible": [False] * len(fig.data)},  # Hide all traces
                {"title": f"Soil Curves at Depth: {depth:.2f} m, Outer Diameter: {soil_curves['outer_dia'][i]:.1f} m"},
            ],
        )
        # Enable visibility for the current depth's traces
        step["args"][0]["visible"][i] = True  # p-y
        step["args"][0]["visible"][i + len(soil_curves["depth"])] = True  # t-z
        step["args"][0]["visible"][i + 2 * len(soil_curves["depth"])] = True  # q-z
        
        # Add annotation for the maximum value at the top right of each subplot for each step
        py_displacement, py_force = soil_curves["p-y"][i]
        tz_displacement, tz_force = soil_curves["t-z"][i]
        qz_displacement, qz_force = soil_curves["q-z"][i]

        max_py_value = max(py_force)
        max_tz_value = max(tz_force)
        min_tz_value = min(tz_force)
        max_qz_value = max(qz_force)

        annotation = [
            dict(
                x=1.0, y=0.9,  # Top right of the first plot (p-y)
                xref="x1 domain", yref="y1 domain",  # Specific to p-y subplot
                text=f"Max: {max_py_value:.2f} kPa",
                showarrow=False,
                font=dict(size=13, color="black"),
                align="right",
                valign="top"
            ),
            dict(
                x=1.0, y=1.0,  # Top right of the second plot (t-z)
                xref="x2 domain", yref="y2 domain",  # Specific to t-z subplot
                text=f"Max: {max_tz_value:.2f} kPa",
                showarrow=False,
                font=dict(size=13, color="black"),
                align="right",
                valign="top"
            ),
            dict(
                x=1.0, y=0.0,  # Top right of the second plot (t-z)
                xref="x2 domain", yref="y2 domain",  # Specific to t-z subplot
                text=f"Min: {min_tz_value:.2f} kPa",
                showarrow=False,
                font=dict(size=13, color="black"),
                align="right",
                valign="bottom"
            ),
            dict(
                x=1.0, y=1.0,  # Top right of the third plot (q-z)
                xref="x3 domain", yref="y3 domain",  # Specific to q-z subplot
                text=f"Max: {max_qz_value:.2f} kPa",
                showarrow=False,
                font=dict(size=13, color="black"),
                align="right",
                valign="top"
            )
        ]
        
        # Append annotations for the current step
        step["args"][1].update({"annotations": annotation})

        steps.append(step)

    sliders = [dict(
        active=0,
        currentvalue={"prefix": "Element: ", "font": {"size": 20}},
        pad={"t": 50},
        steps=steps
    )]

    # Define the shapes for frames
    shapes = [
        # Frame for the p-y plot (top plot)
        dict(
            type="rect",
            xref="paper", yref="paper",
            x0=0.0, x1=1.0,  # Entire width
            y0=0.7, y1=1.0,  # Matches y-axis domain of p-y
            line=dict(color="black", width=1),
        ),
        # Frame for the t-z plot (middle plot)
        dict(
            type="rect",
            xref="paper", yref="paper",
            x0=0.0, x1=1.0,  # Entire width
            y0=0.35, y1=0.65,  # Matches y-axis domain of t-z
            line=dict(color="black", width=1),
        ),
        # Frame for the q-z plot (bottom plot)
        dict(
            type="rect",
            xref="paper", yref="paper",
            x0=0.0, x1=1.0,  # Entire width
            y0=0.0, y1=0.3,  # Matches y-axis domain of q-z
            line=dict(color="black", width=1),
        ),
    ]

    # Update layout with slider and styling
    fig.update_layout(
        shapes=shapes,
        sliders=sliders,
        height=800,  # Set the height for vertical stacking
        title="Soil Curves",
        xaxis3_title="Displacement [m]",
        template="plotly_white",
        showlegend=False,  # Avoid legend clutter
    )

    # Show the figure
    # fig.show()

    return fig

