import plotly.io as pio  # Import plotly.io for saving
from spring_visualize_function import extract_soil_curves, create_interactive_plot_fixed_y2
import streamlit as st
from io import BytesIO

# Streamlit title
st.title("COSPIN Spring Visualizer")

# File uploader
file = st.file_uploader("Upload COSPIN spring text output file", type=["txt"])

# Check if a file is uploaded
if file is not None:
    try:
        # Extract soil curves
        soil_curves = extract_soil_curves(file)

        # Create interactive plot
        fig = create_interactive_plot_fixed_y2(soil_curves)

        # Display the plot in the app
        st.plotly_chart(fig)

        # Convert Plotly figure to HTML and encode as bytes
        html_content = pio.to_html(fig)  # Get HTML content as a string
        html_buffer = BytesIO(html_content.encode("utf-8"))  # Encode string as bytes

        # Download button for HTML file
        st.download_button(
            label="Download Figure as HTML",
            data=html_buffer,
            file_name="soil_curve_plot.html",
            mime="text/html"
        )

    except Exception as e:
        st.error(f"An error occurred: {e}")
else:
    st.info("Please upload a COSPIN spring text output file to begin.")
