import stanza
from pdfminer.high_level import extract_text
import csv
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import requests
import threading

# Supported languages
LANG_OPTIONS = {
    "Hindi": "hi",
    "English": "en",
    "Marathi": "mr",
    "Tamil": "ta",
    "Telugu": "te",
    "Gujarati": "gu",
    "Kannada": "kn",
    "Malayalam": "ml",
    "Punjabi": "pa",
    "Urdu": "ur",
    "Bengali": "bn"
}


def check_internet_connection():
    """Test if we can connect to GitHub"""
    try:
        requests.get("https://raw.githubusercontent.com", timeout=5)
        return True
    except requests.exceptions.RequestException:
        return False


def setup_stanza(lang_code):
    """Set up Stanza with graceful offline handling"""
    try:
        # First check internet connectivity
        if not check_internet_connection():
            update_status("⚠️ No internet connection. Trying offline mode...")
            # Try to use already downloaded models
            return stanza.Pipeline(lang_code, download_method=None)

        # If we have internet, try the normal download
        update_status(f"📥 Downloading {lang_code} language model...")
        stanza.download(lang_code, verbose=False)
        return stanza.Pipeline(lang_code)

    except Exception as e:
        if "Cannot find" in str(e) and "download_method=None" in str(e):
            # This means the model isn't available offline
            messagebox.showerror("Error",
                                 f"The language model for '{lang_code}' is not installed locally and internet connection failed.\n\n"
                                 "Please connect to the internet and try again to download the model.")
            raise
        else:
            # Some other error
            messagebox.showerror("Error", f"Error setting up Stanza: {str(e)}")
            raise


def extract_text_from_pdf(pdf_path):
    try:
        text = extract_text(pdf_path)
        return text.strip()
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return ""


def pos_tag_text(nlp, text):
    doc = nlp(text)
    tagged_data = []
    for sent in doc.sentences:
        for word in sent.words:
            tagged_data.append([
                word.id, word.text, word.lemma, word.upos, word.xpos
            ])
    return tagged_data


def save_to_csv(tagged_data, output_csv_path):
    """Save tagged data to CSV file"""
    headers = ["ID", "Word", "Lemma", "UPOS", "XPOS"]
    with open(output_csv_path, mode='w', encoding='utf-8', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        writer.writerows(tagged_data)


def display_results_in_table(tagged_data):
    """Display results in a new window with a treeview table"""
    # Create a new window for the results
    results_window = tk.Toplevel(window)
    results_window.title("POS Tagging Results")
    results_window.geometry("800x600")

    # Create a frame for the table with scrollbars
    frame = tk.Frame(results_window)
    frame.pack(fill="both", expand=True, padx=10, pady=10)

    # Create scrollbars
    vsb = ttk.Scrollbar(frame, orient="vertical")
    hsb = ttk.Scrollbar(frame, orient="horizontal")

    # Configure the treeview
    tree = ttk.Treeview(frame, columns=("ID", "Word", "Lemma", "UPOS", "XPOS"),
                        show='headings',
                        yscrollcommand=vsb.set,
                        xscrollcommand=hsb.set)

    # Configure scrollbars
    vsb.config(command=tree.yview)
    vsb.pack(side="right", fill="y")
    hsb.config(command=tree.xview)
    hsb.pack(side="bottom", fill="x")

    # Configure column headings
    tree.heading("ID", text="ID")
    tree.heading("Word", text="Word")
    tree.heading("Lemma", text="Lemma")
    tree.heading("UPOS", text="UPOS")
    tree.heading("XPOS", text="XPOS")

    # Configure column widths
    tree.column("ID", width=50, anchor="center")
    tree.column("Word", width=150, anchor="w")
    tree.column("Lemma", width=150, anchor="w")
    tree.column("UPOS", width=100, anchor="center")
    tree.column("XPOS", width=100, anchor="center")

    # Insert data into the table
    for item in tagged_data:
        tree.insert("", "end", values=item)

    tree.pack(fill="both", expand=True)

    # Button frame
    button_frame = tk.Frame(results_window)
    button_frame.pack(fill="x", padx=10, pady=10)

    # Export button
    def export_to_csv():
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
            title="Export Results as CSV"
        )
        if file_path:
            save_to_csv(tagged_data, file_path)
            messagebox.showinfo("Export Successful", f"Results exported to {file_path}")

    export_btn = tk.Button(button_frame, text="Export to CSV", command=export_to_csv,
                           bg="#4CAF50", fg="white", font=("Arial", 10), pady=3)
    export_btn.pack(side="left", padx=5)

    # Count label
    count_label = tk.Label(button_frame, text=f"Total items: {len(tagged_data)}", font=("Arial", 10))
    count_label.pack(side="right", padx=5)


def update_status(msg):
    status_label.config(text=msg)
    window.update_idletasks()


def process_pdf(pdf_path, lang_code):
    """Main processing function to tag text and display results"""
    update_status("🔄 Extracting text from PDF...")
    text = extract_text_from_pdf(pdf_path)

    if not text:
        update_status("❌ No text extracted.")
        messagebox.showerror("Error", "No text extracted from the PDF.")
        return False

    update_status("🧠 Setting up NLP pipeline...")
    nlp = setup_stanza(lang_code)

    update_status("📝 Performing POS tagging...")
    tagged_data = pos_tag_text(nlp, text)

    update_status("✅ Done! Displaying results.")
    display_results_in_table(tagged_data)
    return True


# Function to run the tagging in a separate thread to keep UI responsive
def run_pos_tagging_thread():
    pdf_path = entry_pdf.get()
    if not pdf_path or not os.path.exists(pdf_path):
        messagebox.showerror("Error", "Please select a valid PDF file.")
        return

    lang_display = lang_dropdown.get()
    lang_code = LANG_OPTIONS.get(lang_display)
    if not lang_code:
        messagebox.showerror("Error", "Please select a language.")
        return

    # Disable the button to prevent multiple clicks
    btn_run.config(state=tk.DISABLED)

    # Run in thread to keep UI responsive
    threading.Thread(
        target=run_with_error_handling,
        args=(pdf_path, lang_code),
        daemon=True
    ).start()


def run_with_error_handling(pdf_path, lang_code):
    try:
        process_pdf(pdf_path, lang_code)
    except Exception as e:
        update_status(f"❌ Error: {str(e)}")
        print(f"Error in processing: {e}")
    finally:
        # Re-enable the button when done
        btn_run.config(state=tk.NORMAL)


# ---------------- TKINTER UI ----------------

def select_pdf():
    pdf_path = filedialog.askopenfilename(
        title="Select PDF File",
        filetypes=[("PDF files", "*.pdf")]
    )
    if pdf_path:
        entry_pdf.delete(0, tk.END)
        entry_pdf.insert(0, pdf_path)


# Setup Tkinter window
window = tk.Tk()
window.title("Multilingual PDF POS Tagger")
window.geometry("550x280")
window.resizable(False, False)

# Apply a clean theme for the UI
style = ttk.Style()
if 'clam' in style.theme_names():  # Check if clam theme is available
    style.theme_use('clam')

# Header
header_frame = tk.Frame(window, bg="#4CAF50", height=50)
header_frame.pack(fill="x")
header_label = tk.Label(header_frame, text="Multilingual PDF POS Tagger",
                        font=("Arial", 16, "bold"), bg="#4CAF50", fg="white")
header_label.pack(pady=10)

# Main content
main_frame = tk.Frame(window, padx=20, pady=10)
main_frame.pack(fill="both", expand=True)

# PDF selection
tk.Label(main_frame, text="Select PDF File", font=("Arial", 12)).pack(anchor="w", pady=(10, 5))
file_frame = tk.Frame(main_frame)
file_frame.pack(fill="x")

entry_pdf = tk.Entry(file_frame, width=50)
entry_pdf.pack(side=tk.LEFT, padx=5)

btn_browse = ttk.Button(file_frame, text="Browse", command=select_pdf)
btn_browse.pack(side=tk.LEFT, padx=5)

# Language selection
tk.Label(main_frame, text="Select Language", font=("Arial", 12)).pack(anchor="w", pady=(10, 5))
lang_dropdown = ttk.Combobox(main_frame, values=list(LANG_OPTIONS.keys()), state="readonly", width=20)
lang_dropdown.pack(anchor="w")
lang_dropdown.set("Hindi")  # Default selection

# Run button
btn_run = tk.Button(main_frame, text="Run POS Tagging", command=run_pos_tagging_thread,
                    bg="#4CAF50", fg="white", font=("Arial", 12), pady=5)
btn_run.pack(pady=20)

# Status bar
status_frame = tk.Frame(window, bg="#f0f0f0", height=30)
status_frame.pack(fill="x", side="bottom")
status_label = tk.Label(status_frame, text="", fg="gray", font=("Arial", 10), bg="#f0f0f0")
status_label.pack(pady=5)

# Check connectivity at startup
if check_internet_connection():
    status_label.config(text="✅ Internet connection available")
else:
    status_label.config(text="⚠️ No internet connection - will use local models if available", fg="orange")

window.mainloop()