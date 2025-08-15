# app.py - Main Shiny Application (Phase 1)
import os
import sqlalchemy as sa
from pathlib import Path
from shiny import App, ui, render, reactive
from shiny.types import FileInfo
import pandas as pd
from datetime import datetime

# Import our modules
from db.connection import DatabaseManager
from core.document_manager import DocumentManager

# Initialize database and document manager
db = DatabaseManager()
doc_manager = DocumentManager(db)

# UI Definition
app_ui = ui.page_fluid(
    ui.h1("RQDA Web App - Document Management"),
    
    ui.navset_card_tab(
        ui.nav_panel(
            "Files",
            ui.row(
                ui.column(
                    4,
                    ui.h3("Upload Files"),
                    ui.input_file("file_upload", "Choose text files:", multiple=True, accept=".txt"),
                    ui.br(),
                    ui.input_action_button("upload_btn", "Upload Files", class_="btn-primary"),
                    ui.br(), ui.br(),
                    
                    ui.h3("File List"),
                    ui.output_data_frame("file_list"),
                ),
                ui.column(
                    8,
                    ui.h3("File Viewer"),
                    ui.output_ui("file_viewer"),
                    ui.br(),
                    ui.output_ui("text_selector")
                )
            )
        ),
        ui.nav_panel(
            "About",
            ui.p("RQDA Web App - Phase 1: Core Document Management"),
            ui.p("Upload text files and view their contents with basic text selection.")
        )
    )
)

def server(input, output, session):
    # Reactive values for storing data
    selected_file_id = reactive.Value(None)
    selected_text_info = reactive.Value(None)
    
    @reactive.Effect
    @reactive.event(input.upload_btn)
    def upload_files():
        """Handle file upload"""
        if input.file_upload() is not None:
            files_info = input.file_upload()
            
            for file_info in files_info:
                try:
                    # Read file content
                    content = file_info["datapath"].read_text(encoding='utf-8')
                    
                    # Save to database
                    doc_manager.create_file(
                        name=file_info["name"],
                        content=content
                    )
                    
                    ui.notification_show(f"Successfully uploaded: {file_info['name']}", type="success")
                    
                except Exception as e:
                    ui.notification_show(f"Error uploading {file_info['name']}: {str(e)}", type="error")
    
    @output
    @render.data_frame
    def file_list():
        """Display list of uploaded files"""
        files_df = doc_manager.get_all_files()
        
        # Make it interactive for selection
        return render.DataGrid(
            files_df[['id', 'name', 'date_created', 'size']],
            selection_mode="single"
        )
    
    @reactive.Effect
    def handle_file_selection():
        """Handle file selection from the data grid"""
        selected_rows = file_list.data_view(selected=True)
        if len(selected_rows) > 0:
            file_id = selected_rows.iloc[0]['id']
            selected_file_id.set(file_id)
    
    @output
    @render.ui
    def file_viewer():
        """Display selected file content"""
        if selected_file_id() is None:
            return ui.p("Select a file from the list to view its content.")
        
        file_data = doc_manager.get_file(selected_file_id())
        if file_data is None:
            return ui.p("File not found.")
        
        # Create a text area with the file content that allows text selection
        content_html = file_data['content'].replace('\n', '<br>')
        
        javascript_code = """
        function getSelectedText() {
            var selectedText = "";
            var startPos = 0;
            var endPos = 0;
            
            if (window.getSelection) {
                var selection = window.getSelection();
                selectedText = selection.toString();
                
                if (selectedText.length > 0) {
                    var range = selection.getRangeAt(0);
                    var preCaretRange = range.cloneRange();
                    var container = document.getElementById('text-content');
                    preCaretRange.selectNodeContents(container);
                    preCaretRange.setEnd(range.startContainer, range.startOffset);
                    startPos = preCaretRange.toString().length;
                    endPos = startPos + selectedText.length;
                    
                    // Send selection info to Shiny
                    Shiny.setInputValue('selected_text', {
                        text: selectedText,
                        start: startPos,
                        end: endPos
                    });
                }
            }
        }
        """
        
        return ui.div(
            ui.h4(f"File: {file_data['name']}"),
            ui.div(
                ui.HTML(f"""
                <div id="text-content" style="
                    border: 1px solid #ddd; 
                    padding: 15px; 
                    max-height: 400px; 
                    overflow-y: auto;
                    background-color: #f9f9f9;
                    font-family: 'Courier New', monospace;
                    line-height: 1.6;
                    cursor: text;
                    user-select: text;
                " onmouseup="getSelectedText()">
                    {content_html}
                </div>
                
                <script>
                {javascript_code}
                </script>
                """)
            )
        )
    
    @output
    @render.ui  
    def text_selector():
        """Display selected text information"""
        if input.selected_text() is not None:
            selection = input.selected_text()
            return ui.div(
                ui.h5("Selected Text:"),
                ui.div(
                    f"Text: '{selection['text']}'",
                    ui.br(),
                    f"Position: {selection['start']} - {selection['end']}",
                    style="background-color: #e8f4fd; padding: 10px; border-left: 4px solid #007bff;"
                )
            )
        return ui.div()

# Create the app
app = App(app_ui, server)
